# Lenny-RAG — Product Summary

*As of 2026-11-21*

## Problem

Lenny's Podcast has about 300 episodes of top-tier product thinking, but you can't search across it. The advice is there, just impossible to pull up during a strategy review or a product diagnosis.

## Solution

You ask a product question in plain English. The tool finds the most relevant transcript passages, and Claude answers from those passages alone. Each point cites its episode, and the advice is applied to Glance when the question is about Glance.

## How it works

1. **Ingest:** Split all 299 transcripts into 13,204 overlapping chunks of about 500 tokens. Each chunk is embedded with Voyage and stored in a local ChromaDB database.
2. **Retrieve:** Embed the question the same way, pull the 30 closest chunks, then have a reranker keep the 8 that actually answer it.
3. **Generate:** Claude Sonnet answers using only those chunks, with `[Episode]` citations.
4. **Use:** A command-line tool for quick tests, and a Streamlit web app: a landing page with the ask box, example questions and framework cards, and a focused results view with citation pills and the sources.

## Models and RAG techniques

Answers come from Claude Sonnet 4.6 (`claude-sonnet-4-6`, up to 1,500 tokens), reranking from Voyage `rerank-2.5`, and embeddings from Voyage `voyage-3.5`.

**Techniques used**

1. **Chunking with overlap:** About 500-token chunks, each sharing 50 tokens with the next, so an idea isn't cut in half. A short leftover at the end of a transcript is folded into the chunk before it, so no chunk is under 100 tokens.
2. **Semantic search:** Questions and chunks are compared by meaning (cosine similarity of embeddings), not keywords.
3. **Separate settings for questions and documents:** Voyage embeds short questions and long passages differently.
4. **One embedding model for both sides:** Ingestion and queries must match, so the model is a single shared setting.
5. **Two-stage retrieval:** A fast vector search finds 30 candidates, then a reranker reads the question next to each one and keeps the best 8.
6. **Grounded answers:** Claude may use only the retrieved excerpts.
7. **Citations on every claim:** Each chunk carries its episode name.
8. **Saying "not covered":** Claude must say so rather than guess.
9. **Safe re-runs:** Fixed chunk IDs mean already-stored chunks are skipped.
10. **Retrieval evaluation:** 40 test questions with known answer episodes score every change before it ships.

**Not used yet:** Hybrid keyword search (BM25), contextual chunk headers, speaker-turn chunking, query rewriting, and conversation memory.

## Product decisions

- **Accuracy over fluency:** If the transcripts don't cover a question, it says so instead of guessing.
- **Trust through citations:** Every claim names its episode, so you can check it.
- **Cost guardrails:** It runs a 5-transcript test first and skips chunks that are already stored. The whole corpus costs under $1 to embed, and each query costs a few cents.
- **A deliberately small v1:** No chat memory, auto-ingesting new episodes, or multiple users.
- **One change at a time:** Each retrieval change is measured on its own, so we know which one helped.

## What changed since October

Retrieval got measurably better and the app got a real front door: the right episode now ranks first for 33 of 40 test questions, up from 28.

| Date | Change | Why | Result |
| --- | --- | --- | --- |
| 2026-11-21 | Portfolio screenshots and demo GIF on GitHub | Show the tool without hosting it (hosting would expose API costs and transcript text) | README now shows the landing page, an answer, the not-covered state, phone layout and a 26-second demo |
| 2026-11-21 | Answers generated in the background | The landing page stayed on screen, dimmed, during the 15–30s wait | Clean progress view; answers open scrolled to the top |
| 2026-10-31 | Landing page and focused results view | The single-input page didn't look like a product or invite exploration | Hero with ask box, sample answer, stats, guest strip, 8 framework cards, how-it-works |
| 2026-10-31 | 40-question retrieval test set | Quality was judged by eye, so no change could be proven | Baseline below; caught one false match ("DORA" matching inside other words) |
| 2026-10-31 | Removed junk tail chunks | 75 episodes ended in near-empty chunks (".", " episode.") that ranked first for off-topic questions | 13,279 → 13,204 chunks, none under 100 tokens |
| 2026-10-31 | Reranking (30 candidates → best 8) | Vector search ranked chunks by topic, not by whether they answer | See table below |

Retrieval on the 40-question test set:

| | Right episode at #1 | In top 3 | In top 8 | MRR |
| --- | --- | --- | --- | --- |
| Vector search only | 28/40 | 34/40 | 40/40 | 0.80 |
| + reranking | 33/40 | 39/40 | 40/40 | 0.90 |

What we learned: the reranker's score can't decide "not covered" by itself yet (an off-topic question scored 0.46 against 0.56 for a real one), and the test set is too easy at top 8, so it needs harder questions next. Full detail is in [CHANGELOG.md](./CHANGELOG.md).

## Recent maintenance

Voyage retired the `voyage-3` embedding model the tool was built on, so every query failed. We moved it to `voyage-3.5` and re-embedded the full corpus. That should have cost $0, since about 6.6M tokens fits inside the 200M-token free tier. The model name now lives in one shared setting, so ingestion and queries can't use different models again. The fix is now merged to main and pushed to GitHub with the rest of the work above.

## Next

- **Not measured yet:** The PRD target that 7 out of 10 answers feel useful.
- **Harder test questions:** Details deep inside episodes and questions that need several guests, so the test set can show further gains.
- **Next retrieval changes, measured one at a time:** Add the episode name and topic to each chunk before embedding (contextual headers), then split chunks on speaker turns instead of token counts.
- **Possible next features:** Hybrid keyword search, follow-up questions, and adding new episodes automatically.
- **Worth adding:** A simple alert for when a provider retires a model, since the voyage-3 break went unnoticed.
