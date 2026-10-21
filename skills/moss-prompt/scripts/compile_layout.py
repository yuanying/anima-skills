#!/usr/bin/env python3
"""
Compile a MOSS-Image layout draft into a one-line layout prompt.

Usage:
    python compile_layout.py DRAFT.json [--output PROMPT.txt]
    python compile_layout.py DRAFT.json --yaml prompt.yaml [--suffix "<lora:name:1>"] [--negative ""]

The draft is readable JSON with boxes in top-left-origin pixels:

    {
      "width": 1216, "height": 832,
      "bbox_coord_space": "abs", "bbox_format": "xyxy",
      "summary": {"meta": ["illustration"], "canvas": "single", "caption": "..."},
      "items": [{"label": "object", "caption": "...", "bbox": [x_min, y_min, x_max, y_max]}]
    }

The output is the form MOSS-Image was trained on: summary and items with
integer boxes in "abs_centralized" / "yxyx" ([y_min, x_min, y_max, x_max],
origin at the canvas center). Width and height are not part of the prompt, so
generate at the same size as the draft.

The draft schema and conversion follow the official prompt enhancer skill
(OpenMOSS/MOSS-Image, skills/moss-image-prompt-enhancer): fractional edges are
enclosed (floor min, ceil max) before subtracting the center, out-of-canvas
boxes are rejected instead of clipped, and unknown fields are rejected.
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT_FIELDS = {"width", "height", "bbox_coord_space", "bbox_format", "summary", "items"}
SUMMARY_FIELDS = {"caption", "meta", "canvas", "palette"}
ITEM_FIELDS = {"label", "caption", "bbox", "text", "tags", "palette"}
LABELS = ("object", "character", "text")
CANVASES = ("single", "multi_panel", "collage")

# A1111/Forge prompt editing syntax [from:to:when]. Forge parses it before the
# text reaches the MOSS-Image encoder, so such a span would be rewritten.
PROMPT_EDITING = re.compile(r"\[[^\[\]]*:[^\[\]]*:\s*[\d.]+\s*\]")


class DraftError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DraftError(message)


def check_fields(value, allowed: set, required: set, where: str) -> None:
    require(isinstance(value, dict), f"{where} must be an object")
    unknown = sorted(value.keys() - allowed)
    missing = sorted(required - value.keys())
    require(not unknown, f"{where}: unknown fields {unknown}")
    require(not missing, f"{where}: missing fields {missing}")


def check_text(value, where: str) -> None:
    require(isinstance(value, str) and value.strip() != "", f"{where} must be a nonempty string")


def check_strings(value, where: str) -> None:
    require(isinstance(value, list), f"{where} must be an array of strings")
    for i, v in enumerate(value):
        check_text(v, f"{where}[{i}]")


def centralize(box, width: int, height: int, where: str) -> list[int]:
    require(isinstance(box, list) and len(box) == 4, f"{where} must be [x_min, y_min, x_max, y_max]")
    require(
        all(type(v) in (int, float) and math.isfinite(v) for v in box),
        f"{where} must contain four finite numbers",
    )
    x0, y0, x1, y1 = box
    require(x0 < x1 and y0 < y1, f"{where} must have positive width and height")
    require(
        0 <= x0 and x1 <= width and 0 <= y0 and y1 <= height,
        f"{where} {box} is outside the {width}x{height} canvas",
    )
    return [
        math.floor(round(y0, 9)) - height // 2,
        math.floor(round(x0, 9)) - width // 2,
        math.ceil(round(y1, 9)) - height // 2,
        math.ceil(round(x1, 9)) - width // 2,
    ]


def compile_layout(draft) -> tuple[str, int, int]:
    check_fields(draft, ROOT_FIELDS, ROOT_FIELDS, "draft")
    width, height = draft["width"], draft["height"]
    for name, value in (("width", width), ("height", height)):
        require(type(value) is int and value > 0 and value % 16 == 0,
                f"{name} must be a positive multiple of 16 (got {value!r})")
    require(draft["bbox_coord_space"] == "abs", 'draft bbox_coord_space must be "abs"')
    require(draft["bbox_format"] == "xyxy", 'draft bbox_format must be "xyxy"')

    summary = draft["summary"]
    check_fields(summary, SUMMARY_FIELDS, {"caption"}, "summary")
    check_text(summary["caption"], "summary.caption")
    if "canvas" in summary:
        require(summary["canvas"] in CANVASES, f"summary.canvas must be one of {list(CANVASES)}")
    for key in ("meta", "palette"):
        if key in summary:
            check_strings(summary[key], f"summary.{key}")

    items = draft["items"]
    require(isinstance(items, list) and items, "items must be a nonempty array")
    compiled = []
    for i, item in enumerate(items):
        where = f"items[{i}]"
        check_fields(item, ITEM_FIELDS, {"label", "caption", "bbox"}, where)
        require(item["label"] in LABELS, f"{where}.label must be one of {list(LABELS)}")
        check_text(item["caption"], f"{where}.caption")
        if item["label"] == "text":
            require("text" in item, f"{where}: a text item needs the literal text to render")
        if "text" in item:
            check_text(item["text"], f"{where}.text")
        for key in ("tags", "palette"):
            if key in item:
                check_strings(item[key], f"{where}.{key}")
        compiled.append({
            key: centralize(value, width, height, f"{where}.bbox") if key == "bbox" else value
            for key, value in item.items()
        })

    layout = {
        "summary": summary,
        "items": compiled,
        "bbox_coord_space": "abs_centralized",
        "bbox_format": "yxyx",
    }
    prompt = json.dumps(layout, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return prompt, width, height


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise DraftError(f"invalid JSON number: {value}")


def to_yaml(prompt: str, negative: str | None) -> str:
    # The compiled prompt is a single physical line, so a literal block keeps it verbatim.
    lines = ["prompt: |-", f"  {prompt}"]
    if negative is not None:
        lines.append(f"negative_prompt: {json.dumps(negative, ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile a MOSS-Image layout draft")
    parser.add_argument("draft", type=Path, help="layout draft JSON (abs / xyxy)")
    out = parser.add_mutually_exclusive_group()
    out.add_argument("--output", type=Path, help="write the compiled prompt to this file")
    out.add_argument("--yaml", type=Path, help="write an sdctl prompt.yaml to this file")
    parser.add_argument("--suffix", default="", help='text appended after the JSON, e.g. "<lora:name:1>"')
    parser.add_argument("--negative", default=None, help="negative_prompt for --yaml (omitted if not given)")
    args = parser.parse_args()

    try:
        for path in (args.output, args.yaml):
            require(path is None or path.resolve() != args.draft.resolve(),
                    "the output must be a different file from the draft")
        draft = json.loads(args.draft.read_text(encoding="utf-8"),
                           object_pairs_hook=unique_keys, parse_constant=reject_constant)
        prompt, width, height = compile_layout(draft)
    except (OSError, ValueError, OverflowError) as e:
        parser.exit(2, f"ERROR: {e}\n")

    if PROMPT_EDITING.search(prompt):
        print("WARNING: the prompt contains [a:b:N]; Forge treats it as prompt editing syntax",
              file=sys.stderr)
    if args.suffix:
        prompt = f"{prompt} {args.suffix.strip()}"

    if args.yaml:
        args.yaml.parent.mkdir(parents=True, exist_ok=True)
        args.yaml.write_text(to_yaml(prompt, args.negative), encoding="utf-8")
        print(f"Wrote {args.yaml}", file=sys.stderr)
    elif args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(prompt + "\n", encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(prompt)
    print(f"Generate at --width {width} --height {height}", file=sys.stderr)


if __name__ == "__main__":
    main()
