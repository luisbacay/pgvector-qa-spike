"""
ingest.py

Chunks a text/markdown document, generates embeddings using Voyage AI,
and stores the chunks + embeddings in Supabase (pgvector).

Usage:
    python ingest.py test_document.md
"""

import os
import sys
from dotenv import load_dotenv
import voyageai
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]  # service_role key
VOYAGE_API_KEY = os.environ["VOYAGE_API_KEY"]

CHUNK_SIZE = 500      # characters per chunk, simple spike-level chunking
CHUNK_OVERLAP = 50    # characters of overlap between chunks

voyage_client = voyageai.Client(api_key=VOYAGE_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Naive fixed-size character chunking with overlap.
    This is deliberately simple for the spike -- no sentence-boundary
    awareness, no Sentence-Window or Auto-merging technique. Those are
    stretch goals, not part of this baseline.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """
    Calls Voyage AI to embed a batch of text chunks.
    input_type='document' tells Voyage these are documents being indexed,
    not a query -- Voyage optimizes the embedding differently for each.
    """
    result = voyage_client.embed(
        chunks,
        model="voyage-3",
        input_type="document",
    )
    return result.embeddings


def store_chunks(chunks: list[str], embeddings: list[list[float]], source_document: str):
    """
    Inserts each chunk + its embedding into the document_chunks table.
    """
    rows = []
    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        rows.append({
            "content": chunk,
            "embedding": embedding,
            "source_document": source_document,
            "chunk_index": index,
        })

    response = supabase.table("document_chunks").insert(rows).execute()
    return response


def main():
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <path_to_document>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    print(f"Read {len(text)} characters from {file_path}")

    chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"Split into {len(chunks)} chunks")

    print("Generating embeddings via Voyage AI...")
    embeddings = embed_chunks(chunks)
    print(f"Generated {len(embeddings)} embeddings, dimension {len(embeddings[0])}")

    print("Storing in Supabase...")
    result = store_chunks(chunks, embeddings, source_document=file_path)
    print(f"Stored {len(result.data)} rows in document_chunks")


if __name__ == "__main__":
    main()
