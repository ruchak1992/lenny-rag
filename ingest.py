"""
Ingest Lenny's Podcast transcripts into ChromaDB.

Usage:
  python ingest.py --test   # ingest 5 transcripts first to verify the pipeline
  python ingest.py          # ingest all transcripts (idempotent — skips existing chunks)
"""

import os
import argparse
import glob
from pathlib import Path
from dotenv import load_dotenv
import tiktoken
import voyageai
import chromadb

load_dotenv()

TRANSCRIPTS_DIR = os.getenv("TRANSCRIPTS_DIR", "./Lenny's Podcast Transcripts Archive [public]")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
COLLECTION_NAME = "lenny_transcripts"

# Ingestion and queries must use the same model, or retrieval silently returns junk.
# voyage-3 was retired by Voyage in 2026; changing this requires a full re-ingest.
EMBED_MODEL = "voyage-3.5"

# 500-token chunks with 50-token overlap.
# Overlap prevents a key idea from being split across chunk boundaries.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def chunk_text(text: str, slug: str) -> list[dict]:
    """Split a transcript into overlapping token-window chunks."""
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)

    chunks = []
    start = 0
    idx = 0

    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_str = enc.decode(chunk_tokens)

        chunks.append({
            "id": f"{slug}_{idx}",
            "text": chunk_str,
            "episode": slug,
            "chunk_index": idx,
        })

        idx += 1
        # Slide forward by (CHUNK_SIZE - CHUNK_OVERLAP) so adjacent chunks share 50 tokens
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def episode_slug(filepath: str) -> str:
    """Use the filename (minus extension) as the human-readable episode label."""
    return Path(filepath).stem


def ingest(test_mode: bool = False):
    # glob.escape prevents [ ] in the folder name from being treated as a character class
    pattern = os.path.join(glob.escape(TRANSCRIPTS_DIR), "*.txt")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"No .txt files found in: {TRANSCRIPTS_DIR}")
        return

    if test_mode:
        files = files[:5]
        print(f"TEST MODE — ingesting {len(files)} transcripts\n")
    else:
        print(f"Ingesting {len(files)} transcripts\n")

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))

    total_new = 0
    total_skipped = 0

    for filepath in files:
        slug = episode_slug(filepath)
        text = Path(filepath).read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_text(text, slug)

        # Check which IDs are already in the DB — idempotency guard
        existing_ids = set(collection.get(ids=[c["id"] for c in chunks])["ids"])
        new_chunks = [c for c in chunks if c["id"] not in existing_ids]
        skipped = len(chunks) - len(new_chunks)

        if not new_chunks:
            print(f"  SKIP  {slug!r} — {skipped} chunks already ingested")
            total_skipped += skipped
            continue

        # Voyage max batch size is 128
        BATCH = 128
        for i in range(0, len(new_chunks), BATCH):
            batch = new_chunks[i : i + BATCH]
            texts = [c["text"] for c in batch]
            result = voyage.embed(texts, model=EMBED_MODEL, input_type="document")
            embeddings = result.embeddings

            collection.add(
                ids=[c["id"] for c in batch],
                embeddings=embeddings,
                documents=[c["text"] for c in batch],
                metadatas=[
                    {"episode": c["episode"], "chunk_index": c["chunk_index"]}
                    for c in batch
                ],
            )

        total_new += len(new_chunks)
        print(f"  OK    {slug!r} — {len(new_chunks)} chunks added ({skipped} skipped)")

    print(f"\nDone. {total_new} new chunks added, {total_skipped} already existed.")
    print(f"Vector DB persisted at: {CHROMA_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        action="store_true",
        help="Ingest only 5 transcripts (cost-safe dry run)",
    )
    args = parser.parse_args()
    ingest(test_mode=args.test)
