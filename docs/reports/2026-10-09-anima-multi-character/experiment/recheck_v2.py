#!/usr/bin/env python3
"""修正版スキル（skill-v2 / skill-v2-tags）の再検証。評価の準備・集計・図の作成を行う。

比較する 4 方式: 旧スキル（skill-position-blocks）、hybrid-tags-nl、skill-v2、skill-v2-tags。
旧 2 方式の画像は前回と同じ seed で生成済みのもの（同条件で再生成するとピクセル単位で一致する）を使い、
新 2 方式と混ぜて同じ評価者がブラインドで判定し直す。

使い方:
  recheck_v2.py prepare <生成画像ディレクトリ> <評価用ディレクトリ>
      <評価用>/<scene>/<code>.jpg（4 seed の 2x2 グリッド、code は R1..R4）と key.yaml を作る
  recheck_v2.py aggregate <評価用ディレクトリ>
      <評価用>/results_<scene>.csv を方式名に戻して results_v2.csv と summary_v2.md を書く
  recheck_v2.py figures <生成画像ディレクトリ> [<scene>/<method>/<seed> ...]
      ../images/v2_sheet_<scene>.webp（行=方式、列=seed、緑枠=成功）と代表例 ../images/v2_pick_*.webp を作る
"""
import csv
import pathlib
import random
import sys
from collections import defaultdict

import yaml
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from generate import SEEDS  # noqa: E402

METHODS = ["skill-position-blocks", "hybrid-tags-nl", "skill-v2", "skill-v2-tags"]
ITEMS = ["count", "identity", "position", "pose", "composition"]
ITEM_JA = {"count": "人数", "identity": "属性", "position": "位置・役割", "pose": "ポーズ", "composition": "構図"}
IMAGES = HERE.parent / "images"


def scenes():
    return yaml.safe_load((HERE / "scenes.yaml").read_text())


def prepare(src, dst):
    shuffled = METHODS[:]
    random.Random(20261010).shuffle(shuffled)
    key = {f"R{i + 1}": m for i, m in enumerate(shuffled)}
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "key.yaml").write_text(yaml.safe_dump(key, sort_keys=False))
    font = ImageFont.load_default(size=28)
    for s in scenes():
        scale = 768 / max(s["width"], s["height"])
        cw, chh = int(s["width"] * scale), int(s["height"] * scale)
        (dst / s["id"]).mkdir(exist_ok=True)
        for code, m in key.items():
            grid = Image.new("RGB", (cw * 2 + 8, chh * 2 + 8), "black")
            for i, seed in enumerate(SEEDS):
                im = Image.open(src / s["id"] / f"{m}_{seed}.png").convert("RGB").resize((cw, chh))
                d = ImageDraw.Draw(im)
                d.rectangle([0, 0, 150, 40], fill="black")
                d.text((8, 4), f"seed {seed}", fill="white", font=font)
                grid.paste(im, ((i % 2) * (cw + 8), (i // 2) * (chh + 8)))
            grid.save(dst / s["id"] / f"{code}.jpg", quality=88)


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return c - h, c + h


def aggregate(ev):
    key = yaml.safe_load((ev / "key.yaml").read_text())
    sc = scenes()
    rows = []
    for s in sc:
        with open(ev / f"results_{s['id']}.csv", newline="") as f:
            for r in csv.DictReader(f):
                vals = {k: int(r[k]) for k in ITEMS}
                rows.append({
                    "scene": r["scene"].strip(), "method": key[r["code"].strip()], "seed": int(r["seed"]),
                    **vals, "success": int(all(vals.values())), "score": sum(vals.values()),
                    "note": r.get("note", "").strip(),
                })
    assert len(rows) == len(sc) * len(METHODS) * len(SEEDS), len(rows)
    rows.sort(key=lambda r: (r["scene"], METHODS.index(r["method"]), r["seed"]))
    with open(HERE / "results_v2.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["scene", "method", "seed", *ITEMS, "success", "score", "note"])
        w.writeheader()
        w.writerows(rows)

    three = {s["id"] for s in sc if s["count"].startswith("3")}
    by_m = defaultdict(list)
    by_ms = defaultdict(list)
    idx = {}
    for r in rows:
        by_m[r["method"]].append(r)
        by_ms[(r["method"], r["scene"])].append(r)
        idx[(r["scene"], r["method"], r["seed"])] = r
    out = ["## 方式別の成績（12 シーン × 4 seed = 48 枚、再判定）\n"]
    out.append("| 方式 | 成功 | 成功率（95% CI） | 2 人の構図 | 3 人の構図 | 平均スコア | " + " | ".join(ITEM_JA[i] for i in ITEMS) + " |")
    out.append("|---|---|---|---|---|---|" + "---|" * len(ITEMS))
    for m in METHODS:
        rs = by_m[m]
        n = len(rs)
        succ = sum(r["success"] for r in rs)
        lo, hi = wilson(succ, n)
        two = [r for r in rs if r["scene"] not in three]
        thr = [r for r in rs if r["scene"] in three]
        items = " | ".join(f"{sum(r[it] for r in rs) / n:.0%}" for it in ITEMS)
        out.append(
            f"| `{m}` | {succ}/{n} | {succ / n:.0%}（{lo:.0%}〜{hi:.0%}） | {sum(r['success'] for r in two)}/{len(two)} | "
            f"{sum(r['success'] for r in thr)}/{len(thr)} | {sum(r['score'] for r in rs) / n:.2f} | {items} |"
        )
    out.append("\n## シーン別の成功数（4 枚中）\n")
    out.append("| 方式 | " + " | ".join(s["id"] for s in sc) + " | 計 |")
    out.append("|---|" + "---|" * (len(sc) + 1))
    for m in METHODS:
        cells = [str(sum(r["success"] for r in by_ms[(m, s["id"])])) for s in sc]
        out.append(f"| `{m}` | " + " | ".join(cells) + f" | {sum(r['success'] for r in by_m[m])} |")
    out.append("\n## 対ごとの比較（同じシーン・seed で片方だけ成功した組の数）\n")
    out.append("| A | B | A だけ成功 | B だけ成功 |")
    out.append("|---|---|---|---|")
    for a, b in [("skill-v2", "skill-position-blocks"), ("skill-v2", "hybrid-tags-nl"),
                 ("skill-v2-tags", "skill-v2"), ("skill-v2-tags", "skill-position-blocks")]:
        wa = wb = 0
        for s in sc:
            for seed in SEEDS:
                x, y = idx[(s["id"], a, seed)]["success"], idx[(s["id"], b, seed)]["success"]
                wa += x and not y
                wb += y and not x
        out.append(f"| `{a}` | `{b}` | {wa} | {wb} |")
    # 旧 2 方式は前回も判定しているので、判定の一致度を見る
    old = {}
    with open(HERE / "results.csv", newline="") as f:
        for r in csv.DictReader(f):
            old[(r["scene"], r["method"], int(r["seed"]))] = r
    out.append("\n## 前回判定との一致（旧 2 方式、成功/失敗の一致率）\n")
    out.append("| 方式 | 前回の成功 | 今回の成功 | 成功/失敗の一致 |")
    out.append("|---|---|---|---|")
    for m in METHODS[:2]:
        rs = by_m[m]
        prev = sum(int(old[(r["scene"], m, r["seed"])]["success"]) for r in rs)
        agree = sum(int(old[(r["scene"], m, r["seed"])]["success"]) == r["success"] for r in rs)
        out.append(f"| `{m}` | {prev}/{len(rs)} | {sum(r['success'] for r in rs)}/{len(rs)} | {agree}/{len(rs)} |")
    (HERE / "summary_v2.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


def figures(src, picks):
    IMAGES.mkdir(exist_ok=True)
    ok = {}
    with open(HERE / "results_v2.csv", newline="") as f:
        for r in csv.DictReader(f):
            ok[(r["scene"], r["method"], int(r["seed"]))] = r["success"] == "1"
    font = ImageFont.load_default(size=20)
    cell, label_w, pad = 240, 250, 6
    for s in scenes():
        scale = cell / max(s["width"], s["height"])
        cw, chh = int(s["width"] * scale), int(s["height"] * scale)
        sheet = Image.new("RGB", (label_w + len(SEEDS) * (cw + pad) + pad, 34 + len(METHODS) * (chh + pad) + pad), "white")
        d = ImageDraw.Draw(sheet)
        for j, seed in enumerate(SEEDS):
            d.text((label_w + pad + j * (cw + pad) + 4, 6), f"seed {seed}", fill="black", font=font)
        for i, m in enumerate(METHODS):
            y = 34 + pad + i * (chh + pad)
            d.text((8, y + chh // 2 - 12), m, fill="black", font=font)
            for j, seed in enumerate(SEEDS):
                x = label_w + pad + j * (cw + pad)
                sheet.paste(Image.open(src / s["id"] / f"{m}_{seed}.png").convert("RGB").resize((cw, chh)), (x, y))
                color = (40, 170, 70) if ok[(s["id"], m, seed)] else (210, 50, 50)
                d.rectangle([x - 3, y - 3, x + cw + 2, y + chh + 2], outline=color, width=3)
        sheet.save(IMAGES / f"v2_sheet_{s['id']}.webp", quality=70, method=6)
    for spec in picks:
        sid, m, seed = spec.split("/")
        im = Image.open(src / sid / f"{m}_{seed}.png").convert("RGB")
        im.thumbnail((768, 768))
        im.save(IMAGES / f"v2_pick_{sid}_{m}_{seed}.webp", quality=75, method=6)


def main():
    cmd, *rest = sys.argv[1:]
    if cmd == "prepare":
        prepare(pathlib.Path(rest[0]), pathlib.Path(rest[1]))
    elif cmd == "aggregate":
        aggregate(pathlib.Path(rest[0]))
    elif cmd == "figures":
        figures(pathlib.Path(rest[0]), rest[1:])
    else:
        sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
