#!/usr/bin/env python3
"""
Danbooru tag search engine for Anima prompt generation.

Usage:
    python tag_search.py QUERY [--limit N]

Output: JSON array to stdout.
"""

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "tags.json"


def normalize(text: str) -> str:
    text = text.casefold().replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def score_entry(query: str, query_norm: str, entry: dict) -> float:
    tag_norm = normalize(entry["t"])
    ja = entry.get("j", "")
    aliases = entry.get("a", "")

    s = 0.0

    if tag_norm == query_norm:
        s = 100.0
    elif tag_norm.startswith(query_norm):
        length_penalty = max(0, len(tag_norm) - len(query_norm)) * 0.5
        s = max(0.0, 80.0 - length_penalty)
    else:
        idx = tag_norm.find(query_norm)
        if idx >= 0:
            pos_penalty = min(idx * 3, 30)
            len_penalty = max(0, len(tag_norm) - len(query_norm)) * 0.3
            s = max(0.0, 60.0 - pos_penalty - len_penalty)

    if s == 0.0 and ja and query in ja:
        s = 50.0

    if s == 0.0 and aliases:
        for alias in re.split(r"[,\n]+", aliases):
            if query in alias.strip():
                s = 40.0
                break

    if s == 0.0 and len(query_norm) >= 3:
        ratio = SequenceMatcher(None, query_norm, tag_norm).ratio()
        if ratio >= 0.75:
            s = 30.0 + (ratio - 0.75) * 40.0

    if s > 0 and entry.get("x", 0) == 1:
        s *= 0.3

    return s


def search(query: str, limit: int, data: list) -> list:
    query_norm = normalize(query)

    scored = []
    for entry in data:
        s = score_entry(query, query_norm, entry)
        if s > 0:
            scored.append((s, entry))

    scored.sort(key=lambda x: (-x[0], -x[1].get("p", 0)))

    results = []
    for s, entry in scored[:limit]:
        related = [t.strip().replace("_", " ") for t in re.split(r"[,\n]+", entry.get("r", "")) if t.strip()]
        results.append({
            "tag": entry["t"].replace("_", " "),
            "ja": entry.get("j", ""),
            "description": entry.get("d", ""),
            "related_tags": related,
            "post_count": entry.get("p", 0),
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Danbooru tags")
    parser.add_argument("query", help="Search query (English or Japanese)")
    parser.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    parser.add_argument("--data", type=Path, default=DATA_PATH, help="Path to tags.json")
    args = parser.parse_args()

    data_path: Path = args.data
    if not data_path.exists():
        print(f"ERROR: data file not found: {data_path}", file=sys.stderr)
        print("Run: python skills/anima-prompt/scripts/build_data.py", file=sys.stderr)
        sys.exit(1)

    with data_path.open(encoding="utf-8") as f:
        data = json.load(f)

    results = search(args.query, args.limit, data)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
