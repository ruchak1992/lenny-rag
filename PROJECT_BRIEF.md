## Chunking strategy

- **Chunk size:** ~500 tokens
- **Overlap:** 50 tokens between consecutive chunks
- **Why:** Embeddings work better on focused chunks; overlap prevents cutting mid-idea
- **Tokenizer:** `tiktoken` with `cl100k_base` encoding

## Retrieval strategy

- **Top-k:** 8 chunks per query (good default — enough context, not too many tokens)
- **Similarity:** Default cosine similarity in ChromaDB
- **Metadata:** Each chunk stores `episode` name and `chunk_index` for citation

## Answer generation

- **Model:** `claude-sonnet-4-5` (or current latest)
- **System prompt should:**
  - Position Claude as a product strategy advisor
  - Instruct it to answer using ONLY the provided transcript excerpts
  - Cite sources by episode name in [brackets]
  - Say honestly when excerpts don't cover the question
  - When user asks about Glance, apply PM frameworks from transcripts to that context
  - Be concrete and structured, not generic

## Cost expectations

- **Ingestion (one-time):** ~$0.30 in Voyage embeddings (300 transcripts × ~15k tokens × $0.06/M). Voyage free tier covers this.
- **Each query:** ~$0.01-0.05 (mostly Claude tokens for the answer)
- **Chunking and ChromaDB:** Free (runs locally)

## Workflow request

1. **Set up the project** — create venv, requirements.txt, .gitignore, .env template
2. **Start with a test ingestion** — ingest only 5 transcripts first to verify the pipeline works end-to-end before running on all 300. The user wants to avoid wasted embedding cost from re-running.
3. **Build query.py** (CLI) before app.py — easier to test
4. **Then app.py** (Streamlit UI) once retrieval is solid
5. **Always explain key choices** — chunk size, top-k, prompt design, etc. The user wants to understand, not just have working code.

## What "done" looks like

The user can:
- Run `python ingest.py` once to build the vector DB
- Run `streamlit run app.py` to open the web UI
- Ask questions like *"Glance is a lockscreen product struggling with day-7 retention. How would Lenny's guests approach diagnosing this?"* and get a grounded answer with episode citations.

## Notes on style

- Keep code clean and well-commented (this is a learning project)
- Prefer simple, readable solutions over clever ones
- Default to small batch sizes and incremental progress so the user can interrupt and inspect
- When making non-obvious choices (e.g. chunk overlap of 50, top-k of 8), briefly note the reasoning in a comment or message