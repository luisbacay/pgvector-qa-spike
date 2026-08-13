# pgvector-qa-spike

Learning spike for Course 2, Chapter 2 (Building and Evaluating Advanced RAG).

Goal: build the smallest possible document Q&A pipeline using Supabase pgvector
for vector storage and retrieval, and the Claude API for generation.

This is a spike, not a product. Code here is exploratory and not held to
MulTech production standards. Purpose is to prove the concept and build
real understanding of pgvector as a vector store, not to ship anything.

## What this proves

- Documents can be chunked and embedded
- Embeddings can be stored and queried in Supabase via pgvector
- Retrieved chunks can be passed to Claude API for grounded answers
- End to end: ask a question, get an answer sourced from your own documents

## Stack

- Supabase (Postgres + pgvector extension)
- Claude API (Anthropic)
- Python (or Node, TBD based on course material)

## Status

Not started. Scaffold only, no working code yet.

## Setup (to fill in once build starts)

1. Supabase project with pgvector extension enabled
2. `.env` with `SUPABASE_URL`, `SUPABASE_KEY`, `ANTHROPIC_API_KEY`
3. Install dependencies
4. Run ingestion script to chunk + embed + store a test document
5. Run query script to ask a question against it

## Notes

Do not commit `.env`. Do not commit real API keys. This is a public-facing
repo policy default until Luis confirms visibility (currently private).
