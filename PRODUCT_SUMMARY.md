# Lenny-RAG — Product Summary

*As of 2026-10-28*

## Problem

Lenny's Podcast has about 300 episodes of top-tier product thinking, but you can't search across it. The advice is there, just impossible to pull up during a strategy review or a product diagnosis.

## Solution

You ask a product question in plain English. The tool finds the most relevant transcript passages, and Claude answers from those passages alone. Each point cites its episode, and the advice is applied to Glance when the question is about Glance.

## How it works

1. **Ingest:** Split all 299 transcripts into 13,279 overlapping chunks of about 500 tokens. Each chunk is embedded with Voyage and stored in a local ChromaDB database.
2. **Retrieve:** Embed the question the same way and pull the 8 closest chunks.
3. **Generate:** Claude Sonnet answers using only those chunks, with `[Episode]` citations.
4. **Use:** A command-line tool for quick tests, and a simple Streamlit web app with an expandable list of sources.

## Models and RAG techniques

Answers come from Claude Sonnet 4.6 (`claude-sonnet-4-6`, up to 1,500 tokens), and embeddings from Voyage `voyage-3.5`.

**Techniques used**

1. **Chunking with overlap:** About 500-token chunks, each sharing 50 tokens with the next, so an idea isn't cut in half.
2. **Semantic search:** Questions and chunks are compared by meaning (cosine similarity of embeddings), not keywords.
3. **Separate settings for questions and documents:** Voyage embeds short questions and long passages differently.
4. **One embedding model for both sides:** Ingestion and queries must match, so the model is a single shared setting.
5. **Top-8 retrieval:** Enough context for a nuanced answer without filling the prompt with noise.
6. **Grounded answers:** Claude may use only the retrieved excerpts.
7. **Citations on every claim:** Each chunk carries its episode name.
8. **Saying "not covered":** Claude must say so rather than guess.
9. **Safe re-runs:** Fixed chunk IDs mean already-stored chunks are skipped.

**Not used yet:** Re-ranking, hybrid keyword search (BM25), query rewriting, conversation memory, and an evaluation set. An evaluation set and re-ranking would most likely improve answers.

## Product decisions

- **Accuracy over fluency:** If the transcripts don't cover a question, it says so instead of guessing.
- **Trust through citations:** Every claim names its episode, so you can check it.
- **Cost guardrails:** It runs a 5-transcript test first and skips chunks that are already stored. The whole corpus costs under $1 to embed, and each query costs a few cents.
- **A deliberately small v1:** No chat memory, re-ranking, auto-ingesting new episodes, or multiple users.

## Recent maintenance

Voyage retired the `voyage-3` embedding model the tool was built on, so every query failed. We moved it to `voyage-3.5` and re-embedded the full corpus. That should have cost $0, since about 6.6M tokens fits inside the 200M-token free tier. The model name now lives in one shared setting, so ingestion and queries can't use different models again. The app is running, and the fix is committed on the `voyage-3.5-migration` branch but not pushed.

## Next

- **Not measured yet:** The PRD target that 7 out of 10 answers feel useful.
- **Possible next features:** Re-ranking or hybrid search for better results, follow-up questions, and adding new episodes automatically.
- **Worth adding:** A simple alert for when a provider retires a model, since this break went unnoticed.
