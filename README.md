# Lenny-RAG

A retrieval-augmented generation (RAG) tool that lets me ask natural-language product strategy questions against ~300 episodes of Lenny's Podcast — and get an answer grounded in what the guests actually said, with episode citations, instead of a generic LLM guess.

## The problem

Lenny's Podcast has hundreds of hours of high-signal product thinking from top PMs and founders, but that knowledge is practically inaccessible day-to-day: re-listening isn't feasible, there's no search, and generic Google results don't surface episode-specific insight. The frameworks that would actually help during a strategy review or a product diagnosis go unused because there's no fast way to find them.

## How it works

1. **Ingestion** (`ingest.py`) — chunks each transcript into ~500-token windows with 50-token overlap (so an idea doesn't get split mid-thought), embeds each chunk with Voyage AI, and stores it in a local ChromaDB collection. Ingestion is idempotent — it checks chunk IDs before embedding, so re-running never wastes API spend re-embedding what's already there. A `--test` flag ingests 5 transcripts first as a cost-safe dry run before committing to the full ~300.
2. **Retrieval** (`rag.py`) — embeds the incoming question, pulls the top-8 most similar chunks from ChromaDB.
3. **Generation** (`rag.py`) — sends the retrieved chunks to Claude with a system prompt that restricts it to answering *only* from the provided excerpts, forces inline `[Episode Name]` citations on every claim, and requires it to say plainly when the transcripts don't cover the question rather than improvise.
4. **Interfaces** — a CLI (`query.py`) for fast iteration, and a minimal Streamlit UI (`app.py`) for actual use, with retrieved sources shown in a collapsible panel for verification.

## Why this is a good example of my product work

This was scoped like a real feature, not a script: a [PRD](./PRD.md) with a specific user and success metrics, a [design brief](./DESIGN.md) for the UX, an [ERD](./ERD.md) for the ChromaDB data model, and a [technical brief](./PROJECT_BRIEF.md) that pinned down chunking strategy, retrieval config, and cost estimates before writing code. The build decisions reflect product judgment as much as engineering — grounding-only answers over fluent-but-wrong ones, a cost guard before a $0.30 ingestion run, honest "not covered" responses over hallucinated confidence.

## Tech stack

- **Embeddings:** Voyage AI (`voyage-3.5`)
- **Vector store:** ChromaDB (local, persisted to disk)
- **Generation:** Claude API (Sonnet)
- **UI:** Streamlit
- **Tokenization:** tiktoken (`cl100k_base`) for chunk sizing

## Running it locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.template .env  # add ANTHROPIC_API_KEY and VOYAGE_API_KEY

# Point TRANSCRIPTS_DIR (see .env.template) at your own transcript corpus —
# the Lenny's Podcast transcripts used here aren't included in this repo.

python ingest.py --test   # verify the pipeline on 5 transcripts first
python ingest.py          # full ingestion

python query.py "How do top PMs think about retention?"
# or
streamlit run app.py
```

> The transcript corpus itself isn't included in this repo — redistributing ~300 full podcast transcripts publicly isn't something I have rights to do. This repo is the pipeline and product thinking, not the underlying content.

## More documentation

- [PRD.md](./PRD.md) — problem statement, user stories, scope
- [DESIGN.md](./DESIGN.md) — UX principles, user flows, component inventory
- [ERD.md](./ERD.md) — ChromaDB data model
- [PROJECT_BRIEF.md](./PROJECT_BRIEF.md) — chunking strategy, retrieval config, cost estimates
