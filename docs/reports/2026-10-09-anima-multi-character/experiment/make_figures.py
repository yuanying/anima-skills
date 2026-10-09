#!/usr/bin/env python3
"""レポート用の画像を作る。

使い方: make_figures.py <生成画像ディレクトリ> [<scene>/<method>/<seed> ...]
出力:   ../images/sheet_<scene>.webp … シーンごとのコンタクトシート（行=方式、列=seed。成功した画像は緑枠、失敗は赤枠）
        ../images/pick_<scene>_<method>_<seed>.webp … 引数で指定した代表例（長辺 768px）
"""
import csv
import pathlib
import sys

import yaml
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_prompts import METHODS  # noqa: E402
from generate import SEEDS  # noqa: E402

OUT = HERE.parent / "images"
CELL = 240
LABEL_W = 250
PAD = 6


def main():
    src = pathlib.Path(sys.argv[1])
    OUT.mkdir(exist_ok=True)
    ok = {}
    with open(HERE / "results.csv", newline="") as f:
        for r in csv.DictReader(f):
            ok[(r["scene"], r["method"], int(r["seed"]))] = r["success"] == "1"
    font = ImageFont.load_default(size=20)
    scenes = yaml.safe_load((HERE / "scenes.yaml").read_text())
    for s in scenes:
        scale = CELL / max(s["width"], s["height"])
        cw, chh = int(s["width"] * scale), int(s["height"] * scale)
        W = LABEL_W + len(SEEDS) * (cw + PAD) + PAD
        H = 34 + len(METHODS) * (chh + PAD) + PAD
        sheet = Image.new("RGB", (W, H), "white")
        d = ImageDraw.Draw(sheet)
        for j, seed in enumerate(SEEDS):
            d.text((LABEL_W + PAD + j * (cw + PAD) + 4, 6), f"seed {seed}", fill="black", font=font)
        for i, m in enumerate(METHODS):
            y = 34 + PAD + i * (chh + PAD)
            d.text((8, y + chh // 2 - 12), m, fill="black", font=font)
            for j, seed in enumerate(SEEDS):
                x = LABEL_W + PAD + j * (cw + PAD)
                im = Image.open(src / s["id"] / f"{m}_{seed}.png").convert("RGB").resize((cw, chh))
                sheet.paste(im, (x, y))
                color = (40, 170, 70) if ok[(s["id"], m, seed)] else (210, 50, 50)
                d.rectangle([x - 3, y - 3, x + cw + 2, y + chh + 2], outline=color, width=3)
        sheet.save(OUT / f"sheet_{s['id']}.webp", quality=70, method=6)
    for spec in sys.argv[2:]:
        sid, m, seed = spec.split("/")
        im = Image.open(src / sid / f"{m}_{seed}.png").convert("RGB")
        im.thumbnail((768, 768))
        im.save(OUT / f"pick_{sid}_{m}_{seed}.webp", quality=75, method=6)


if __name__ == "__main__":
    main()
