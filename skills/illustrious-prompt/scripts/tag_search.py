#!/usr/bin/env python3
"""
Danbooru tag search engine for Illustrious XL prompt generation.

Usage:
    python tag_search.py QUERY [--limit N] [--underscore]

Output: JSON array to stdout.

The tag database is shared with the anima-prompt skill. This script looks for
data/tags.json inside its own skill directory first, then falls back to the
sibling anima-prompt skill so the 27MB dataset is not duplicated in the repo.
"""

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_CANDIDATES = [
    SKILL_DIR / "data" / "tags.json",
    SKILL_DIR.parent / "anima-prompt" / "data" / "tags.json",
]


def resolve_data_path() -> Path | None:
    for candidate in DATA_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


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


def format_tag(raw: str, underscore: bool) -> str:
    """Illustrious accepts both forms; parentheses always need escaping."""
    tag = raw if underscore else raw.replace("_", " ")
    return tag.replace("(", r"\(").replace(")", r"\)")


def search(query: str, limit: int, data: list, underscore: bool) -> list:
    query_norm = normalize(query)

    scored = []
    for entry in data:
        s = score_entry(query, query_norm, entry)
        if s > 0:
            scored.append((s, entry))

    scored.sort(key=lambda x: (-x[0], -x[1].get("p", 0)))

    results = []
    for s, entry in scored[:limit]:
        related = [
            format_tag(t.strip(), underscore)
            for t in re.split(r"[,\n]+", entry.get("r", ""))
            if t.strip()
        ]
        results.append({
            "tag": format_tag(entry["t"], underscore),
            "ja": entry.get("j", ""),
            "description": entry.get("d", ""),
            "related_tags": related,
            "post_count": entry.get("p", 0),
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Danbooru tags for Illustrious XL")
    parser.add_argument("query", help="Search query (English or Japanese)")
    parser.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    parser.add_argument(
        "--underscore",
        action="store_true",
        help="Return tags in underscore form (default: space separated)",
    )
    parser.add_argument("--data", type=Path, default=None, help="Path to tags.json")
    args = parser.parse_args()

    data_path = args.data or resolve_data_path()
    if data_path is None or not data_path.exists():
        print("ERROR: tags.json not found. Looked in:", file=sys.stderr)
        for candidate in DATA_CANDIDATES:
            print(f"  - {candidate}", file=sys.stderr)
        print("Run: python skills/anima-prompt/scripts/build_data.py", file=sys.stderr)
        sys.exit(1)

    with data_path.open(encoding="utf-8") as f:
        data = json.load(f)

    results = search(args.query, args.limit, data, args.underscore)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
