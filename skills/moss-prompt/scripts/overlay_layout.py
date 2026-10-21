#!/usr/bin/env python3
"""
Draw the boxes of a MOSS-Image layout draft on a generated image.

Usage:
    python overlay_layout.py DRAFT.json IMAGE.png [-o IMAGE_bbox.jpg]

Boxes are drawn from the draft (top-left-origin xyxy pixels): text items in red,
everything else in green. Requires Pillow. Use it to check whether the subjects
landed in their boxes; the boxes are never part of the generated image.
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

COLORS = {"text": (255, 0, 0)}
DEFAULT_COLOR = (0, 255, 0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Overlay layout boxes on an image")
    parser.add_argument("draft", type=Path, help="layout draft JSON (abs / xyxy)")
    parser.add_argument("image", type=Path, help="generated image")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="output path (default: <image>_bbox.jpg)")
    args = parser.parse_args()

    draft = json.loads(args.draft.read_text(encoding="utf-8"))
    image = Image.open(args.image).convert("RGB")
    if image.size != (draft["width"], draft["height"]):
        print(f"WARNING: image is {image.size[0]}x{image.size[1]} but the draft is "
              f"{draft['width']}x{draft['height']}", file=sys.stderr)

    draw = ImageDraw.Draw(image)
    for item in draft["items"]:
        color = COLORS.get(item["label"], DEFAULT_COLOR)
        draw.rectangle(item["bbox"], outline=color, width=4)

    output = args.output or args.image.with_name(f"{args.image.stem}_bbox.jpg")
    image.save(output, quality=90)
    print(output)


if __name__ == "__main__":
    main()
