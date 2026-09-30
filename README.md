# pgvector-qa-spike

A document Q&A pipeline built from scratch: Supabase pgvector for storage and retrieval, Voyage AI for embeddings, and Claude for grounded answers. No LangChain or LlamaIndex, so every layer is visible.

I built it while working through DeepLearning.AI's "Building and Evaluating Advanced RAG". It is a learning project, not a product. Tested on Python 3.14 on Windows.

## What it does

1. `ingest.py` splits a markdown document into 500 character chunks with 50 characters of overlap, embeds them with Voyage AI (`voyage-3`, `input_type="document"`, 1024 dimensions), and stores the chunks and embeddings in a Supabase table called `document_chunks`.
2. `query.py` embeds the question, calls a Postgres function named `match_chunks` over Supabase RPC to fetch the 3 closest chunks above a cosine similarity threshold of 0.2, and asks Claude to answer only from those chunks.

## Sample run

```
$ python ingest.py test_document.md
Split into 6 chunks
Generated 6 embeddings, dimension 1024
Stored 6 rows in document_chunks

$ python query.py "When did Project Halcyon start?"
Retrieved 3 chunk(s)
--- Chunk 1 (similarity: 0.5068) ---
ANSWER: Project Halcyon started in March 2025.

$ python query.py "What is Project Halcyon's annual budget?"
Retrieved 3 chunk(s)
--- Chunk 1 (similarity: 0.4194) ---
ANSWER: The context does not contain any information about Project Halcyon's annual budget.
```

## Setup

1. Create a Supabase project. Open the SQL editor, paste `schema.sql`, and run it. It enables pgvector, creates the table and the `match_chunks` function, and turns on row level security.
2. Copy `.env.example` to `.env` and fill in four values: `SUPABASE_URL`, `SUPABASE_KEY`, `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`.
3. Install dependencies: `pip install -r requirements.txt`
4. Ingest the test document: `python ingest.py test_document.md`
5. Ask a question: `python query.py "When did Project Halcyon start?"`

Security notes:
- `SUPABASE_KEY` is the `service_role` key, which bypasses row level security. It is for local scripts only and must never go into browser code.
- The table has row level security on and no policies, so the public anon key cannot read or write it.

## What broke

In my first build, ingestion reported success, but every question returned nothing. I bypassed one layer at a time (embeddings, storage, retrieval) until the cause turned out to be the vector index. An ivfflat index built with `lists=100` on a table of five rows silently returned zero results, because ivfflat splits rows into lists and searches only a few of them per query, so it needs far more rows than this. I dropped the index. At this size an exact scan is fast and correct, and `schema.sql` deliberately creates no approximate index.

## Other decisions

- The similarity threshold is 0.2, lower than you might expect, because Voyage embeds documents and queries differently and scores between them run lower.
- The query embedding is sent to Postgres as a fixed-point text literal and not as a raw Python list, to avoid float formatting edge cases across the RPC boundary.
- Claude is told to answer only from the retrieved context and to say so if the context does not contain the answer.

## Tests

1. Grounded answer: `python query.py "When did Project Halcyon start?"` returns "Project Halcyon started in March 2025." The top chunk scored 0.5068.
2. Refusal: `python query.py "What is Project Halcyon's annual budget?"` returns "The context does not contain any information about Project Halcyon's annual budget." The document never mentions a budget.

Both were run on a fresh Supabase project, using only this repo's `schema.sql` and scripts.

## Limits

- The 0.2 threshold does not filter out unrelated chunks. The unanswerable question above still retrieved three chunks scoring 0.35 to 0.42, so the refusal comes from the prompt instruction and not from retrieval. A higher threshold or a reranker is the next thing to try, and I have not measured either.
- Fixed-size character chunking, with no semantic splitting.
- No evaluation harness and no automated test suite. The two tests above are manual.
- One small document and no approximate index. On a larger table, add an HNSW index and measure recall before trusting it.
- Exploratory code, not production code.

## Test data

`test_document.md` is synthetic. Project Halcyon, its dates, team and figures are invented for testing. It mentions product names only as flavor, and nothing in it describes a real project.
