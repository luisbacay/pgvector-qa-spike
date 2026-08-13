"""
query.py

Takes a question, embeds it with Voyage AI, retrieves the most relevant
chunks from Supabase (pgvector), and passes them to Claude to generate
a grounded answer.

Usage:
    python query.py "What is the hex value of nuvaris-teal?"
"""

import os
import sys
from dotenv import load_dotenv
import voyageai
from supabase import create_client
import anthropic

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
VOYAGE_API_KEY = os.environ["VOYAGE_API_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

MATCH_THRESHOLD = 0.2   # tuned lower to account for query/document asymmetric embeddings
MATCH_COUNT = 3         # how many chunks to retrieve

voyage_client = voyageai.Client(api_key=VOYAGE_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def embed_query(question: str) -> list[float]:
    """
    Embeds the question. input_type='query' tells Voyage this is a
    search query, not a document -- Voyage optimizes the embedding
    differently than it does for ingestion.
    """
    result = voyage_client.embed(
        [question],
        model="voyage-3",
        input_type="query",
    )
    return result.embeddings[0]


def retrieve_chunks(query_embedding: list[float]) -> list[dict]:
    """
    Calls the match_chunks Postgres function via Supabase RPC.

    NOTE: the embedding is formatted as a pgvector text literal string
    with fixed-point notation, not a raw Python list, to avoid any
    float-formatting edge cases crossing the RPC boundary.
    """
    embedding_str = "[" + ",".join(f"{x:.10f}" for x in query_embedding) + "]"

    response = supabase.rpc(
        "match_chunks",
        {
            "query_embedding": embedding_str,
            "match_threshold": MATCH_THRESHOLD,
            "match_count": MATCH_COUNT,
        },
    ).execute()

    return response.data


def generate_answer(question: str, chunks: list[dict]) -> str:
    """
    Passes the question and retrieved chunks to Claude, instructed to
    answer only from the given context.
    """
    if not chunks:
        context = "No relevant context was retrieved."
    else:
        context = "\n\n---\n\n".join(chunk["content"] for chunk in chunks)

    prompt = f"""Answer the question using ONLY the context below. If the
context does not contain the answer, say so explicitly instead of guessing
or using outside knowledge.

Context:
{context}

Question: {question}"""

    response = claude_client.messages.create(
        model="claude-sonnet-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def main():
    if len(sys.argv) < 2:
        print('Usage: python query.py "your question here"')
        sys.exit(1)

    question = sys.argv[1]

    print(f"Question: {question}\n")

    print("Embedding query...")
    query_embedding = embed_query(question)

    print("Retrieving chunks from Supabase...")
    chunks = retrieve_chunks(query_embedding)
    print(f"Retrieved {len(chunks)} chunk(s)\n")

    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i+1} (similarity: {chunk['similarity']:.4f}) ---")
        print(chunk["content"][:200] + "...")
        print()

    print("Generating answer with Claude...\n")
    answer = generate_answer(question, chunks)

    print("=" * 60)
    print("ANSWER:")
    print(answer)
    print("=" * 60)


if __name__ == "__main__":
    main()