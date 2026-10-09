#!/usr/bin/env python3
"""評価用のブラインド化した 2x2 グリッドを作る。

使い方: prepare_eval.py <生成画像ディレクトリ> <評価用出力ディレクトリ>
出力:   <評価用出力>/<scene_id>/<code>.jpg（4 seed を 2x2 に並べ、各セルに seed を書く）
        <評価用出力>/key.yaml（code -> method の対応。評価者には渡さない）
方式名は評価者に見せないよう、固定の乱数で M1..M9 に置き換える。
"""
import pathlib
import random
import sys

import yaml
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_prompts import METHODS  # noqa: E402
from generate import SEEDS  # noqa: E402

CELL_LONG = 768


def main():
    src, dst = map(pathlib.Path, sys.argv[1:3])
    methods = list(METHODS)
    rnd = random.Random(20261009)
    shuffled = methods[:]
    rnd.shuffle(shuffled)
    key = {f"M{i + 1}": m for i, m in enumerate(shuffled)}
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "key.yaml").write_text(yaml.safe_dump(key, sort_keys=False))
    font = ImageFont.load_default(size=28)
    scenes = yaml.safe_load((HERE / "scenes.yaml").read_text())
    for s in scenes:
        w, h = s["width"], s["height"]
        scale = CELL_LONG / max(w, h)
        cw, chh = int(w * scale), int(h * scale)
        paths = {m: [src / s["id"] / f"{m}_{seed}.png" for seed in SEEDS] for m in methods}
        if not all(p.exists() for ps in paths.values() for p in ps):
            continue  # 生成途中のシーンは飛ばす
        (dst / s["id"]).mkdir(exist_ok=True)
        for code, m in key.items():
            grid = Image.new("RGB", (cw * 2 + 8, chh * 2 + 8), "black")
            for i, (seed, path) in enumerate(zip(SEEDS, paths[m])):
                im = Image.open(path).convert("RGB").resize((cw, chh))
                d = ImageDraw.Draw(im)
                d.rectangle([0, 0, 150, 40], fill="black")
                d.text((8, 4), f"seed {seed}", fill="white", font=font)
                grid.paste(im, ((i % 2) * (cw + 8), (i // 2) * (chh + 8)))
            grid.save(dst / s["id"] / f"{code}.jpg", quality=88)


if __name__ == "__main__":
    main()
