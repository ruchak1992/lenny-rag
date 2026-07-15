"""
CLI for querying Lenny-RAG.

Usage:
  python query.py "How do top PMs think about retention?"
  python query.py "..." --verbose    # also prints the retrieved chunks
"""

import argparse
from rag import ask


def main():
    parser = argparse.ArgumentParser(description="Query Lenny's Podcast transcripts")
    parser.add_argument("question", help="Your product strategy question")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print retrieved chunks before the answer",
    )
    args = parser.parse_args()

    print("\nRetrieving and generating...\n")
    answer, chunks = ask(args.question)

    if args.verbose:
        print("=== Retrieved Chunks ===")
        for i, c in enumerate(chunks, 1):
            print(f"\n[{i}] {c['episode']}")
            print(c["text"][:300] + "...")
        print("\n" + "=" * 40 + "\n")

    print(answer)


if __name__ == "__main__":
    main()
