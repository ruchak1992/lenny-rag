"""
Core RAG logic shared by query.py and app.py.
Handles embedding the query, retrieving chunks from ChromaDB, and generating the answer.
"""

import os
from dotenv import load_dotenv
import voyageai
import chromadb
import anthropic

load_dotenv()

CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
COLLECTION_NAME = "lenny_transcripts"

# top-8 gives enough context for a nuanced answer without blowing up the prompt
TOP_K = 8

SYSTEM_PROMPT = """\
You are a product strategy advisor with deep knowledge of Lenny's Podcast.

Rules:
- Answer using ONLY the transcript excerpts provided. Do not use outside knowledge.
- Cite every claim inline with [Episode Name] — e.g. "Focus on the critical few metrics [Shreyas Doshi]."
- Be concrete and structured: use headers and bullets so the answer is scannable.
- When the question involves Glance (a lockscreen product), apply the frameworks directly \
to that context. Don't give generic advice — make it specific to Glance.
- If the excerpts don't cover the question, respond with exactly: \
"The transcripts don't cover this topic." Do not extrapolate or invent.

Answer format:
1. Direct answer (2–4 bullets or a short paragraph, with inline citations)
2. Frameworks / deeper insights from the transcripts (with citations)
3. "Applied to Glance" section — only include this when the question is relevant to Glance\
"""


def retrieve(question: str, n_results: int = TOP_K) -> list[dict]:
    """Embed the question and pull the top-k most similar chunks from ChromaDB."""
    voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
    result = voyage.embed([question], model="voyage-3", input_type="query")
    query_embedding = result.embeddings[0]

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(name=COLLECTION_NAME)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas"],
    )

    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({"text": doc, "episode": meta["episode"]})

    return chunks


def generate(question: str, chunks: list[dict]) -> str:
    """Send retrieved chunks + question to Claude and return a structured answer."""
    context = "\n\n---\n\n".join(
        f"[{c['episode']}]\n{c['text']}" for c in chunks
    )

    user_message = f"Transcript excerpts:\n\n{context}\n\n---\n\nQuestion: {question}"

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text


def ask(question: str) -> tuple[str, list[dict]]:
    """Full pipeline: retrieve relevant chunks, generate answer. Returns (answer, chunks)."""
    chunks = retrieve(question)
    answer = generate(question, chunks)
    return answer, chunks
