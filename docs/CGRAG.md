# CGRAG (Contextual Retrieval)

## Overview

CGRAG provides sub-100ms contextual retrieval using FAISS vector search.

## Features

- Document indexing with smart chunking (512 words, 50 word overlap)
- Batched embedding generation (sentence-transformers)
- FAISS vector search
- Token budget management (8000 tokens default)
- Relevance filtering (70% threshold)

## Supported Formats

- `.md` — Markdown
- `.py` — Python
- `.txt` — Plain text
- `.yaml` / `.json` — Config files
- `.rst` — ReStructuredText

## Indexing

```bash
# Index documentation
docker-compose run --rm backend python -m app.cli.index_docs /path/to/docs

# Indexes saved to ./backend/data/faiss_indexes/
```

## Configuration

```bash
RECALL_INDEX_PATH=/data/faiss_indexes/
RECALL_CHUNK_SIZE=512
RECALL_TOKEN_BUDGET=8000
RECALL_MIN_RELEVANCE=0.7
```

## How It Works

1. **Chunking** — Documents split into 512-word chunks with 50-word overlap
2. **Embedding** — Chunks converted to vectors via sentence-transformers
3. **Indexing** — Vectors stored in FAISS index
4. **Query** — User query embedded, nearest neighbors found
5. **Filtering** — Results above 70% relevance included
6. **Budget** — Context trimmed to 8000 tokens

## Performance

- Retrieval: <100ms
- Typical context: 3-5 relevant chunks
- Token budget enforced per query

## Integration

CGRAG automatically activates in Two-Stage mode:
1. Stage 1 uses smaller model → more room for CGRAG context
2. Relevant docs injected into prompt
3. Stage 2 receives enriched context
