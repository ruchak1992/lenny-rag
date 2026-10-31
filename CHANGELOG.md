# Changelog

What changed, why, and what we measured. Newest first.

## 2026-10-31 — Landing page + focused results view

**Why.** The first redesign only restyled the single-input page; it still didn't look like a
product or invite exploration. The "minimal chrome" principle in `DESIGN.md` was the constraint, so
it was replaced (see Design Principle 3).

**Change** (`app.py`). Two views in one Streamlit app, switched by session state:
- **Landing:** nav bar; hero with gradient background, headline, the ask box and example-question
  chips, plus a sample-answer card; stats strip (299 episodes · 13,204 passages · 8 sources ·
  30 → 8 reranked); scrolling guest strip (pauses for reduced-motion users); 8 clickable framework
  cards (LNO, Sean Ellis test, 7 Powers, Positioning, Shape Up, Opportunity solution tree, Radical
  Candor, Working backwards) that each ask a question; a 3-step "How it works"; footer.
- **Results:** back-to-home link, a follow-up ask box, the question as a large serif heading, the
  answer in a card, and sources below.
- Fonts: Fraunces (headings) and Inter (body) from Google Fonts. Every stat on the page is a real,
  measured number.

**Verified** in Chrome via Playwright: no Streamlit exceptions or console errors; framework card →
answer with 13 citation pills; follow-up off-topic question → "Not covered" panel and input clears;
back link returns to landing; no horizontal scroll at 390px phone width.

## 2026-10-31 — Redesigned web UI

**Why.** The app was a default-styled Streamlit page: plain title, raw `[Episode]` brackets in the
answer, and no visible "not covered" state, which `DESIGN.md` calls for.

**Change** (`app.py`, new `.streamlit/config.toml`). Stays within the design brief (answer first,
one input, no sidebar, sources collapsed):
- Warm theme matching `PRODUCT_SUMMARY.html` (off-white background, burnt-orange accent, serif
  headings); Streamlit menu reduced to minimal.
- Hero header, a single input row with the Ask button, and four example-question chips on the
  empty page.
- Progress shown as steps ("Finding the most relevant passages…" → "Writing an answer from 8
  passages…") instead of a generic spinner — `app.py` now calls `retrieve()` and `generate()`
  separately.
- `[Episode]` citations render as small pills; Claude's own headings are scaled down so the
  question stays the most prominent text. Model output has `<` escaped before rendering as HTML.
- A calm "Not covered" panel (labelled in text, not just colour), and its sources are labelled
  "Closest passages found (not relevant enough to answer)".
- Sources show each excerpt's reranker relevance score, and a count of distinct episodes.

**Verified** in Chrome via Playwright: example chip → answer with 12 citation pills; typed off-topic
question → "Not covered" panel; input clears after asking; layout holds at 390px phone width; no
console errors.

## 2026-10-31 — Retrieval golden set + recall@k script

**Added** `eval/golden_set.json` (40 questions + 4 off-topic) and `eval/recall_at_k.py`.
Each question lists the episode(s) that answer it; expected episodes were verified by searching
the transcripts and reading the context (passing mentions excluded — e.g. a case-insensitive
search for "DORA" falsely matched 23 times in Tom Conrad). Question types: 13 named
(uses the framework's own name), 24 paraphrased (describes the idea without naming it),
3 applied (Glance-flavoured). The script reports recall@8/@3/@1 and MRR, vector-only vs reranked,
and the top score for off-topic questions. `CHROMA_DIR=... python eval/recall_at_k.py` scores
any index.

**Baseline** (current index, `chroma_db/`):

| | recall@8 | @3 | @1 | MRR |
|---|---|---|---|---|
| vector only | 40/40 | 34/40 | 28/40 | 0.80 |
| vector + rerank | 40/40 | 39/40 | 33/40 | 0.90 |

**Limitation.** recall@8 is saturated — every question hits — so it can't show further gains.
Most questions target one framework owned by one guest, and episode intros list the topics
covered, which makes them easy to find. @1/@3/MRR still discriminate. Next: add harder questions
about details deep inside episodes and questions that need several guests.

## 2026-10-31 — Fold tiny transcript tails into the previous chunk

**Problem.** The sliding window (500 tokens, step 450) left a short scrap at the end of most
transcripts. 75 of 299 episodes ended in a chunk under 100 tokens, 9 under 10 tokens
(`"."`, `" episode."`, `":58]"`), and 46 tails contained *no new text at all* — they sat
entirely inside the previous chunk's 50-token overlap. Near-empty chunks are vaguely similar
to everything, so they surfaced at the top of off-topic queries (e.g. "best pizza in Goa" →
rank #1 was a chunk containing only `"."`).

**Change** (`ingest.py`).
- New `MIN_CHUNK_TOKENS = 100`. If the next window would be shorter than that, the current
  chunk extends to the end of the transcript instead (largest chunk is now 547 tokens).
- The loop stops once a chunk reaches the end of the transcript, so a fully redundant tail is
  never created.
- Empty transcripts now produce no chunks (previously would have been skipped by the old loop
  too; now explicit).

**Measured (offline, before re-embedding).** 13,279 → 13,204 chunks; 75/299 episodes affected,
the other 224 chunk identically; smallest chunk 101 tokens; every episode's last chunk still
reaches the end of its transcript.

**Re-ingest.** Required — chunk IDs (`{episode}_{idx}`) are reused, so the idempotency check would
otherwise keep the old tail chunks. Built into a fresh `chroma_db_new/` (13,204 chunks, matching
the offline count), then swapped in as `chroma_db/`; the previous index is kept as
`chroma_db_pre_tailfix_backup/`.

**Measured after.** Golden set unchanged between old and new index (identical recall/MRR) —
expected, since junk tails only win when no real chunk matches. Off-topic top reranker score
dropped 0.456 → 0.439 (the `"."` chunk that ranked #1 for "best pizza in Goa" is gone).

## 2026-10-31 — Two-stage retrieval with a reranker

**Change** (`rag.py`). Vector search now pulls 30 candidates (`RERANK_CANDIDATES`); Voyage
`rerank-2.5` scores each (question, chunk) pair and keeps the best 8. `retrieve(..., rerank=False)`
restores the old behaviour. Each returned chunk now carries a `score`.

**Measured** (4 test questions, top-8 overlap before vs after):
- "What does Shreyas Doshi say about the LNO framework?" — 4/8 replaced; four off-topic chunks
  (Kunal Shah, John Cutler, Oji Udezue, Farhan Thawar) swapped for Shreyas chunks, one lifted
  from rank #25. Clear win.
- "How should a PM decide what not to build?" — 4/8 replaced; reranker scores flat (0.63–0.70).
- Glance day-7 retention question — 5/8 replaced; low scores (0.42–0.56), mixed quality.
  Bottleneck is recall, not ordering.
- "Best pizza place in Goa?" — top reranker score 0.456, too close to real questions (0.559) to
  use as a refusal threshold without tuning. Exposed the junk tail chunks fixed above.

## 2026-10 — Migrate embeddings from voyage-3 to voyage-3.5

voyage-3 was retired by Voyage. Full re-ingest; old index kept as `chroma_db_voyage3_backup/`.
