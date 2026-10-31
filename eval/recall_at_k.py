"""
Score retrieval against the golden set: recall@k and MRR, with and without reranking.

Usage (from the Lenny-RAG folder):
  python eval/recall_at_k.py
  CHROMA_DIR=./chroma_db_pre_tailfix_backup python eval/recall_at_k.py   # score a different index
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag import retrieve, TOP_K  # noqa: E402
from ingest import TRANSCRIPTS_DIR  # noqa: E402

GOLDEN = json.loads((Path(__file__).parent / "golden_set.json").read_text())


def check_episode_names():
    """Fail fast if an expected episode doesn't match a transcript file — a typo would count as a miss."""
    known = {p.stem for p in Path(TRANSCRIPTS_DIR).glob("*.txt")}
    bad = {e for item in GOLDEN["questions"] for e in item["expected"]} - known
    if bad:
        sys.exit(f"Unknown episode names in golden_set.json: {sorted(bad)}")


def first_hit_rank(chunks: list[dict], expected: list[str]):
    """1-based rank of the first chunk from an expected episode, or None if absent."""
    for rank, c in enumerate(chunks, 1):
        if c["episode"] in expected:
            return rank
    return None


def score(rerank: bool) -> dict:
    by_type = defaultdict(lambda: {"hits": 0, "n": 0})
    rr_sum, misses, ranks = 0.0, [], []
    for item in GOLDEN["questions"]:
        chunks = retrieve(item["q"], rerank=rerank)
        rank = first_hit_rank(chunks, item["expected"])
        ranks.append(rank)
        by_type[item["type"]]["n"] += 1
        if rank:
            by_type[item["type"]]["hits"] += 1
            # MRR rewards putting the right episode at #1, not just somewhere in the top k
            rr_sum += 1 / rank
        else:
            misses.append(("MISS", item["id"], "got: " + ", ".join(sorted({c["episode"] for c in chunks})[:4])))
        if rank and rank > 3:
            misses.append(("LOW ", item["id"], f"right episode only at rank {rank}"))
    n = len(GOLDEN["questions"])
    hits = sum(t["hits"] for t in by_type.values())
    # Stricter cutoffs: recall@8 alone saturates when the right episode is usually near the top
    at = {k: sum(1 for r in ranks if r and r <= k) for k in (1, 3)}
    off_topic = [retrieve(q, rerank=rerank)[0]["score"] for q in GOLDEN["off_topic"]]
    return {"hits": hits, "n": n, "mrr": rr_sum / n, "by_type": by_type, "at": at,
            "misses": misses, "off_topic_top": off_topic}


def main():
    check_episode_names()
    print(f"Index: {os.getenv('CHROMA_DIR', './chroma_db')}   k={TOP_K}\n")
    for label, rerank in [("vector only", False), ("vector + rerank", True)]:
        r = score(rerank)
        types = "  ".join(f"{t} {v['hits']}/{v['n']}" for t, v in sorted(r["by_type"].items()))
        print(f"{label:16} recall@{TOP_K} = {r['hits']}/{r['n']} ({r['hits'] / r['n']:.0%})"
              f"   @3 = {r['at'][3]}/{r['n']}   @1 = {r['at'][1]}/{r['n']}"
              f"   MRR = {r['mrr']:.2f}   [{types}]")
        print(f"{'':16} off-topic top score: max {max(r['off_topic_top']):.3f}")
        for tag, qid, detail in r["misses"]:
            print(f"{'':16}   {tag} {qid:24} {detail}")
        print()


if __name__ == "__main__":
    main()
