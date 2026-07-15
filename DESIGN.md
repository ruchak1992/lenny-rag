# Design Brief — Lenny-RAG

## Design Principles
1. **Answer first** — Lead with the answer, not metadata or scaffolding. Citations and sources come after.
2. **Honest over confident** — "Not covered" is a valid, intentional response — not an error state. Treat it accordingly.
3. **Minimal chrome** — No nav, no sidebar, no clutter. One input, one output. Nothing else on screen.
4. **Scannable structure** — Answers use headers and bullets so Rucha can skim before reading in full.
5. **Trust through citation** — Every claim is traceable. Episode names are always visible inline.

## User Flows

### Flow 1 — Web UI (app.py)
1. User opens Streamlit app in browser (`streamlit run app.py`)
2. Page shows a single text input: *"Ask a question about product strategy..."*
3. User types question and hits Enter or clicks Ask
4. Spinner appears: *"Thinking..."*
5. Answer renders as structured markdown with inline `[Episode Name]` citations
6. Below the answer: collapsed "Sources" section (user can expand to see retrieved chunks with episode name + text excerpt)
7. Input field clears, ready for the next question

### Flow 2 — CLI (query.py)
1. User runs `python query.py "How do top PMs think about retention?"`
2. Terminal prints the answer with inline citations
3. Optional `--verbose` flag prints the raw retrieved chunks before the answer

### Flow 3 — Ingestion (ingest.py)
1. User runs `python ingest.py --test` → ingests 5 transcripts, prints chunk count and confirmation
2. User inspects output, confirms it looks right
3. User runs `python ingest.py` → ingests all ~300 transcripts with progress output
4. Already-ingested chunks (matched by ID) are skipped automatically

## Component Inventory
- [ ] `QuestionInput` — single text field + submit button, clears after submission
- [ ] `AnswerBlock` — structured markdown answer with inline `[Episode Name]` citations
- [ ] `SourcesAccordion` — collapsed by default; expands to show top-8 retrieved chunks (episode name + text excerpt per chunk)
- [ ] `LoadingSpinner` — simple "Thinking..." state while retrieving + generating
- [ ] `NotCoveredBanner` — distinct but calm state when the corpus doesn't address the question; plain text, not a red error

## Accessibility Notes
- Keyboard-navigable: Enter submits the question; Tab moves between input and sources accordion
- Answer text minimum 16px, sufficient contrast ratio
- `NotCoveredBanner` must not rely on colour alone — use a text label (e.g. *"The transcripts don't cover this topic"*)
- Sources accordion must be keyboard-openable

## Open Design Decisions
- If Voyage or Claude API is slow (>10s), consider adding a streaming response to Streamlit so the answer appears token-by-token rather than all at once — defer to build phase
