# PRD — Lenny-RAG

## Overview
Lenny-RAG is a personal RAG (Retrieval-Augmented Generation) tool that lets you query ~300 episodes of Lenny's Podcast transcripts using natural language. You ask a product strategy question, the system retrieves the most relevant transcript chunks, and Claude generates a structured answer grounded in what Lenny's guests actually said — with episode citations. It exists to replace the current "go without" pattern with a fast, trustworthy weekly habit.

## Problem Statement
Lenny's Podcast contains hundreds of hours of high-quality product thinking from top PMs and founders. That knowledge is practically inaccessible: re-listening isn't feasible, search doesn't exist, and generic Google results don't surface episode-specific insight. The result is that valuable frameworks and mental models go unused when they're most needed — during strategy reviews, product diagnoses, and decision-making.

## User Personas

**Rucha — PM at Glance**
- Role: Senior PM working on a lockscreen product (Glance)
- Goals: Apply frameworks from top PMs to real product challenges; get grounded answers fast
- Frustrations: Insights buried in 300+ hours of audio; no way to search across episodes; generic advice doesn't apply to her specific context
- Usage pattern: Weekly, before strategy reviews or when diagnosing a specific problem (e.g. retention, onboarding, growth)

## Goals & Success Metrics
| Goal | Metric | Target |
|------|--------|--------|
| Useful answers | Answers feel actionable and relevant | 7/10 queries per week |
| Grounded answers | Every answer cites ≥1 episode | 100% of answered questions |
| Honest coverage | System flags when corpus doesn't cover a question | Always |
| Low friction | Time from question to answer | < 10 seconds |
| Low ingestion cost | One-time embedding cost | Within Voyage free tier |

## Scope — v1

**In:**
- One-time ingestion of ~300 local transcript files into ChromaDB
- Test ingestion on 5 transcripts before full run (cost guard)
- Idempotent ingestion — skips already-ingested chunks by ID
- CLI query tool (`query.py`) for fast testing
- Streamlit web UI (`app.py`) — minimal
- Structured answers with inline `[Episode Name]` citations
- Collapsible "Sources" section showing retrieved chunks
- Honest "not covered" response when corpus doesn't address the question
- System prompt applies Lenny frameworks to Glance context when relevant
- Project setup: venv, `requirements.txt`, `.env` template, `.gitignore`

**Out:**
- Multi-user access or auth
- New episode auto-ingestion
- Conversation memory or follow-up question threading
- Re-ranking or hybrid search
- Mobile UI
- Sharing, export, or team features

## User Stories
- As Rucha, I want to ask a freeform product strategy question so that I get an answer grounded in what Lenny's guests actually said
- As Rucha, I want answers to cite specific episodes so that I can verify claims or go deeper
- As Rucha, I want Claude to apply Lenny's frameworks to my Glance context so that answers are immediately actionable, not generic
- As Rucha, I want the system to say "I don't know" when transcripts don't cover a topic so that I don't act on hallucinated advice
- As Rucha, I want to run ingestion once and skip already-ingested chunks so that I don't waste embedding quota on re-runs
- As Rucha, I want a CLI tool to test queries quickly so that I can iterate without loading a UI
- As Rucha, I want a minimal Streamlit UI so that asking questions feels natural and readable

## Assumptions
| # | Assumption | Rationale |
|---|------------|-----------|
| 1 | Transcripts are in a single flat folder as .txt or .md files | User confirmed |
| 2 | Voyage `voyage-2` model used for embeddings | User selected; general-purpose, within free tier |
| 3 | ChromaDB runs locally with a hardcoded `persist_directory` | Prevents accidental DB reset |
| 4 | No session history — each query is stateless | Keeps v1 simple; user confirmed |
| 5 | System prompt always frames answers in context of Glance | User confirmed this is always desired |
| 6 | Sources section collapsed by default in UI | Keeps UI minimal; user confirmed |
