-- schema.sql for pgvector-qa-spike
-- Run this once in the Supabase SQL editor of an empty project.
-- Written to match ingest.py (columns it inserts) and query.py (the match_chunks RPC it calls).

-- 1. pgvector extension
create extension if not exists vector with schema extensions;

-- 2. Table that ingest.py writes to
-- voyage-3 returns 1024 dimensional embeddings.
create table if not exists public.document_chunks (
  id              bigint generated always as identity primary key,
  content         text    not null,
  embedding       extensions.vector(1024) not null,
  source_document text    not null,
  chunk_index     integer not null,
  created_at      timestamptz not null default now()
);

-- 3. Lock the table down.
-- Tables created from SQL have row level security OFF, which would expose this table
-- to the public anon key. With RLS on and no policies, only the service_role key
-- (used by the local scripts) can read or write it.
alter table public.document_chunks enable row level security;

-- 4. Similarity search function that query.py calls over RPC.
-- Cosine distance: similarity = 1 - distance.
create or replace function public.match_chunks(
  query_embedding  extensions.vector(1024),
  match_threshold  float,
  match_count      int
)
returns table (
  id              bigint,
  content         text,
  source_document text,
  chunk_index     integer,
  similarity      float
)
language sql
stable
set search_path = public, extensions
as $$
  select
    dc.id,
    dc.content,
    dc.source_document,
    dc.chunk_index,
    1 - (dc.embedding <=> query_embedding) as similarity
  from public.document_chunks dc
  where 1 - (dc.embedding <=> query_embedding) > match_threshold
  order by dc.embedding <=> query_embedding
  limit match_count;
$$;

-- 5. No approximate index on purpose.
-- An ivfflat index built on a tiny table silently returned zero results (see README).
-- At this size an exact scan is fast and correct. On a larger table, consider:
--   create index on public.document_chunks using hnsw (embedding extensions.vector_cosine_ops);
-- and measure recall before trusting it.
