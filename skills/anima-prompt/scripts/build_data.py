#!/usr/bin/env python3
"""
Convert ref/sd-webui-prompt-dictionary JS data to a compact JSON for tag_search.py.
Run once from the repo root:
    python skills/anima-prompt/scripts/build_data.py
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_JS = REPO_ROOT / "ref" / "sd-webui-prompt-dictionary" / "data" / "runtime_js" / "00_prompt_dictionary_data.js"
OUT_JSON = Path(__file__).resolve().parent.parent / "data" / "tags.json"

PREFIX = "window.PROMPT_DICTIONARY_DATA = "
MAX_DESC = 200


def main() -> None:
    if not SRC_JS.exists():
        print(f"ERROR: source not found: {SRC_JS}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading {SRC_JS} ...", file=sys.stderr)
    raw = SRC_JS.read_text(encoding="utf-8")

    if not raw.startswith(PREFIX):
        print("ERROR: unexpected JS format", file=sys.stderr)
        sys.exit(1)

    body = raw[len(PREFIX):]
    if body.endswith(";\n"):
        body = body[:-2]
    elif body.endswith(";"):
        body = body[:-1]

    print("Parsing JSON...", file=sys.stderr)
    entries = json.loads(body)
    print(f"  {len(entries)} entries loaded", file=sys.stderr)

    compact = []
    for e in entries:
        desc = (e.get("description") or "")[:MAX_DESC]
        compact.append({
            "t": e.get("tag", ""),
            "j": e.get("ja", ""),
            "d": desc,
            "a": e.get("aliases", ""),
            "r": e.get("related_tags", ""),
            "p": int(e.get("post_count") or 0),
            "x": 1 if str(e.get("is_deprecated", "0")) in {"1", "true", "True", "TRUE"} else 0,
        })

    # Sort by post_count descending so popular tags surface first in linear search
    compact.sort(key=lambda e: e["p"], reverse=True)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing {OUT_JSON} ...", file=sys.stderr)
    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(compact, f, ensure_ascii=False, separators=(",", ":"))

    size_mb = OUT_JSON.stat().st_size / 1024 / 1024
    print(f"Done: {len(compact)} entries, {size_mb:.1f} MB", file=sys.stderr)


if __name__ == "__main__":
    main()
