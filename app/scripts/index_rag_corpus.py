#!/usr/bin/env python3
"""Index TTB RAG corpus into Chroma (optional — requires pip install labelforge[rag])."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    try:
        from src.rag.retriever import _get_index

        _get_index()
        print("RAG corpus indexed successfully.")
    except Exception as exc:
        print(f"RAG indexing skipped or failed: {exc}")
        print("Install optional deps: pip install -e '.[rag]'")


if __name__ == "__main__":
    main()
