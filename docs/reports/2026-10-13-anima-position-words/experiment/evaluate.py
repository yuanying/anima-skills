#!/usr/bin/env python3
"""ブラインド評価の準備・集計と、レポート用の図の作成。

使い方:
  evaluate.py prepare <生成画像ディレクトリ> <評価用ディレクトリ> [--methods a,b] [--scenes a01,p01] [--salt N]
      <評価用>/<scene>/<code>.jpg（4 seed の 2x2 グリッド。code は X1..Xn をシーンごとにシャッフル）と key.yaml を作る
      8 seed のときは <code>_1.jpg（前半 4 seed）と <code>_2.jpg（後半 4 seed）に分ける
  evaluate.py aggregate <評価用ディレクトリ> <出力名> [--methods a,b] [--scenes a01,p01]
      <評価用>/rater_*/results_<scene>.csv（評価者ごとの判定）を書き方の名前に戻し、
      2 人の評価者の判定を項目ごとに AND で統合する（どちらかが 0 なら 0）。
      <出力名>.csv（統合した判定）、<出力名>_raters.csv（評価者ごとの判定）、<出力名>.md（集計表）をこのディレクトリに書く
  evaluate.py figures <生成画像ディレクトリ> <結果 CSV> <画像の接頭辞> [<scene>/<method>/<seed> ...]
      ../images/<接頭辞>sheet_<scene>.webp（行=書き方、列=seed。緑枠=成功、赤枠=失敗）と
      代表例 ../images/<接頭辞>pick_<scene>_<method>_<seed>.webp を作る

共通オプション（サブコマンドの前に置く）: --scenes-file <シーン定義 YAML,...>（既定 scenes.yaml。カンマ区切りで複数可）、--seeds 101,202,...（既定 101/202/303/404）
"""
import argparse
import csv
import pathlib
import random
import sys
from collections import defaultdict

import yaml
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_prompts import METHODS as ALL_METHODS  # noqa: E402
from generate import SEEDS  # noqa: E402

ITEMS = ["single", "count", "identity", "action", "camera", "position"]
ITEM_JA = {"single": "1枚の絵", "count": "人数", "identity": "属性", "action": "動作", "camera": "カメラ", "position": "位置"}
GROUP_JA = {"action": "動作", "camera": "カメラ", "position": "位置"}
IMAGES = HERE.parent / "images"


SCENES_FILES = [HERE / "scenes.yaml"]


def load_scenes(want=None):
    sc = [s for f in SCENES_FILES for s in yaml.safe_load(f.read_text())]
    return [s for s in sc if not want or s["id"] in want]


def prepare(src, dst, methods, scenes, salt):
    dst.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=28)
    key = {}
    for s in scenes:
        shuffled = methods[:]
        random.Random(f"{salt}-{s['id']}").shuffle(shuffled)
        key[s["id"]] = {f"X{i + 1}": m for i, m in enumerate(shuffled)}
        scale = 768 / max(s["width"], s["height"])
        cw, chh = int(s["width"] * scale), int(s["height"] * scale)
        (dst / s["id"]).mkdir(exist_ok=True)
        chunks = [SEEDS[i:i + 4] for i in range(0, len(SEEDS), 4)]
        for code, m in key[s["id"]].items():
            for n, chunk in enumerate(chunks, 1):
                grid = Image.new("RGB", (cw * 2 + 8, chh * 2 + 8), "black")
                for i, seed in enumerate(chunk):
                    im = Image.open(src / s["id"] / f"{m}_{seed}.png").convert("RGB").resize((cw, chh))
                    d = ImageDraw.Draw(im)
                    d.rectangle([0, 0, 150, 40], fill="black")
                    d.text((8, 4), f"seed {seed}", fill="white", font=font)
                    grid.paste(im, ((i % 2) * (cw + 8), (i // 2) * (chh + 8)))
                name = f"{code}.jpg" if len(chunks) == 1 else f"{code}_{n}.jpg"
                grid.save(dst / s["id"] / name, quality=88)
    (dst / "key.yaml").write_text(yaml.safe_dump(key, sort_keys=False))


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return c - h, c + h


def read_rater(path, key):
    rows = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            sid = r["scene"].strip()
            vals = {}
            for it in ITEMS:
                v = r[it].strip()
                vals[it] = None if v in ("-", "") else int(v)
            m = key[sid][r["code"].strip()]
            rows[(sid, m, int(r["seed"]))] = {**vals, "note": r.get("note", "").strip()}
    return rows


def success(vals):
    return int(all(v for v in vals.values() if v is not None))


def aggregate(ev, name, methods, scenes):
    key = yaml.safe_load((ev / "key.yaml").read_text())
    raters = sorted(p for p in ev.glob("rater_*") if p.is_dir())
    per = {}
    for rd in raters:
        got = {}
        for s in scenes:
            got.update(read_rater(rd / f"results_{s['id']}.csv", key))
        assert len(got) == len(scenes) * len(methods) * len(SEEDS), (rd, len(got))
        per[rd.name] = got
    group = {s["id"]: s["group"] for s in scenes}
    people = {s["id"]: s["count"][0] for s in scenes}
    order = {m: i for i, m in enumerate(methods)}
    keys = sorted(next(iter(per.values())), key=lambda k: (k[0], order[k[1]], k[2]))

    # 評価者ごとの判定と、項目ごとの AND による統合
    raw_rows, rows = [], []
    for k in keys:
        merged = {}
        for it in ITEMS:
            vs = [per[r][k][it] for r in per]
            merged[it] = None if vs[0] is None else int(all(vs))
        notes = " / ".join(f"{r}: {per[r][k]['note']}" for r in per if per[r][k]["note"])
        rows.append({"scene": k[0], "group": group[k[0]], "method": k[1], "seed": k[2],
                     **{it: "-" if merged[it] is None else merged[it] for it in ITEMS},
                     "success": success(merged), "note": notes})
        for r in per:
            v = per[r][k]
            raw_rows.append({"rater": r, "scene": k[0], "method": k[1], "seed": k[2],
                             **{it: "-" if v[it] is None else v[it] for it in ITEMS},
                             "success": success({it: v[it] for it in ITEMS}), "note": v["note"]})
    fields = ["scene", "group", "method", "seed", *ITEMS, "success", "note"]
    with open(HERE / f"{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    with open(HERE / f"{name}_raters.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rater", "scene", "method", "seed", *ITEMS, "success", "note"])
        w.writeheader()
        w.writerows(raw_rows)

    by_m = defaultdict(list)
    idx = {}
    for r in rows:
        by_m[r["method"]].append(r)
        idx[(r["scene"], r["method"], r["seed"])] = r
    n_img = len(scenes) * len(SEEDS)
    out = [f"## 書き方別の成績（{len(scenes)} シーン × {len(SEEDS)} seed = {n_img} 枚。2 人の評価者の AND）\n"]
    groups = [g for g in GROUP_JA if any(s["group"] == g for s in scenes)]
    out.append("| 書き方 | 成功 | 成功率（95% CI） | " + " | ".join(f"{GROUP_JA[g]}グループ" for g in groups)
               + " | 2 人 | 3 人 | " + " | ".join(ITEM_JA[i] for i in ITEMS) + " |")
    out.append("|---|---|---|" + "---|" * (len(groups) + 2 + len(ITEMS)))
    for m in methods:
        rs = by_m[m]
        succ = sum(r["success"] for r in rs)
        lo, hi = wilson(succ, len(rs))
        cells = []
        for g in groups:
            gs = [r for r in rs if r["group"] == g]
            cells.append(f"{sum(r['success'] for r in gs)}/{len(gs)}")
        for p in "23":
            ps = [r for r in rs if people[r["scene"]] == p]
            cells.append(f"{sum(r['success'] for r in ps)}/{len(ps)}")
        for it in ITEMS:
            vs = [r[it] for r in rs if r[it] != "-"]
            cells.append(f"{sum(vs) / len(vs):.0%}")
        out.append(f"| `{m}` | {succ}/{len(rs)} | {succ / len(rs):.0%}（{lo:.0%}〜{hi:.0%}） | " + " | ".join(cells) + " |")

    out.append(f"\n## シーン別の成功数（{len(SEEDS)} 枚中）\n")
    out.append("| 書き方 | " + " | ".join(s["id"] for s in scenes) + " | 計 |")
    out.append("|---|" + "---|" * (len(scenes) + 1))
    for m in methods:
        cells = [str(sum(idx[(s["id"], m, seed)]["success"] for seed in SEEDS)) for s in scenes]
        out.append(f"| `{m}` | " + " | ".join(cells) + f" | {sum(r['success'] for r in by_m[m])} |")

    out.append(f"\n## 項目別・シーン別の正答数（{len(SEEDS)} 枚中。左から 1枚の絵 / 人数 / 属性 / 動作 / カメラ / 位置）\n")
    out.append("| シーン | " + " | ".join(f"`{m}`" for m in methods) + " |")
    out.append("|---|" + "---|" * len(methods))
    for s in scenes:
        cells = []
        for m in methods:
            parts = []
            for it in ITEMS:
                vs = [idx[(s["id"], m, seed)][it] for seed in SEEDS]
                parts.append("-" if vs[0] == "-" else str(sum(vs)))
            cells.append(" ".join(parts))
        out.append(f"| {s['id']} {s['title']} | " + " | ".join(cells) + " |")

    out.append("\n## 対ごとの比較（同じシーン・seed で片方だけ成功した組の数）\n")
    out.append("| A | B | A だけ成功 | B だけ成功 |")
    out.append("|---|---|---|---|")
    for i, a in enumerate(methods):
        for b in methods[i + 1:]:
            ao = sum(1 for (sid, m, seed), r in idx.items() if m == a and r["success"] and not idx[(sid, b, seed)]["success"])
            bo = sum(1 for (sid, m, seed), r in idx.items() if m == b and r["success"] and not idx[(sid, a, seed)]["success"])
            out.append(f"| `{a}` | `{b}` | {ao} | {bo} |")

    if len(per) == 2:
        ra, rb = list(per)
        out.append(f"\n## 評価者間の一致（{ra} と {rb}、{len(keys)} 枚）\n")
        out.append("| 項目 | 一致率 | " + ra + " で 1 | " + rb + " で 1 |")
        out.append("|---|---|---|---|")
        for it in [*ITEMS, "success"]:
            if it == "success":
                pa = [success({x: per[ra][k][x] for x in ITEMS}) for k in keys]
                pb = [success({x: per[rb][k][x] for x in ITEMS}) for k in keys]
            else:
                ks = [k for k in keys if per[ra][k][it] is not None]
                pa = [per[ra][k][it] for k in ks]
                pb = [per[rb][k][it] for k in ks]
            agree = sum(1 for x, y in zip(pa, pb) if x == y)
            label = "成功" if it == "success" else ITEM_JA[it]
            out.append(f"| {label} | {agree}/{len(pa)}（{agree / len(pa):.0%}） | {sum(pa)} | {sum(pb)} |")
        out.append("\n### 評価者ごとの成功数\n")
        out.append("| 書き方 | " + " | ".join(per) + " | AND |")
        out.append("|---|" + "---|" * (len(per) + 1))
        for m in methods:
            cells = [str(sum(success({x: per[r][k][x] for x in ITEMS}) for k in keys if k[1] == m)) for r in per]
            out.append(f"| `{m}` | " + " | ".join(cells) + f" | {sum(r['success'] for r in by_m[m])} |")

    (HERE / f"{name}.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


def figures(src, results, prefix, picks):
    IMAGES.mkdir(exist_ok=True)
    ok = {}
    methods = []
    with open(results, newline="") as f:
        for r in csv.DictReader(f):
            ok[(r["scene"], r["method"], int(r["seed"]))] = r["success"] == "1"
            if r["method"] not in methods:
                methods.append(r["method"])
    scene_ids = {k[0] for k in ok}
    font = ImageFont.load_default(size=20)
    cell, label_w, pad = 240, 150, 6
    for s in load_scenes(scene_ids):
        scale = cell / max(s["width"], s["height"])
        cw, chh = int(s["width"] * scale), int(s["height"] * scale)
        W = label_w + len(SEEDS) * (cw + pad) + pad
        H = 34 + len(methods) * (chh + pad) + pad
        sheet = Image.new("RGB", (W, H), "white")
        d = ImageDraw.Draw(sheet)
        for j, seed in enumerate(SEEDS):
            d.text((label_w + pad + j * (cw + pad) + 4, 6), f"seed {seed}", fill="black", font=font)
        for i, m in enumerate(methods):
            y = 34 + pad + i * (chh + pad)
            d.text((8, y + chh // 2 - 12), m, fill="black", font=font)
            for j, seed in enumerate(SEEDS):
                x = label_w + pad + j * (cw + pad)
                im = Image.open(src / s["id"] / f"{m}_{seed}.png").convert("RGB").resize((cw, chh))
                sheet.paste(im, (x, y))
                color = (40, 170, 70) if ok[(s["id"], m, seed)] else (210, 50, 50)
                d.rectangle([x - 3, y - 3, x + cw + 2, y + chh + 2], outline=color, width=3)
        sheet.save(IMAGES / f"{prefix}sheet_{s['id']}.webp", quality=70, method=6)
    for spec in picks:
        sid, m, seed = spec.split("/")
        im = Image.open(src / sid / f"{m}_{seed}.png").convert("RGB")
        im.thumbnail((768, 768))
        im.save(IMAGES / f"{prefix}pick_{sid}_{m}_{seed}.webp", quality=75, method=6)


def main():
    global SEEDS, SCENES_FILES
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes-file")
    ap.add_argument("--seeds")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--methods")
    p.add_argument("--scenes")
    p.add_argument("--salt", default="20261013")
    a = sub.add_parser("aggregate")
    a.add_argument("ev")
    a.add_argument("name")
    a.add_argument("--methods")
    a.add_argument("--scenes")
    f = sub.add_parser("figures")
    f.add_argument("src")
    f.add_argument("results")
    f.add_argument("prefix")
    f.add_argument("picks", nargs="*")
    args = ap.parse_args()
    if args.scenes_file:
        SCENES_FILES = [pathlib.Path(x) for x in args.scenes_file.split(",")]
    if args.seeds:
        SEEDS = [int(x) for x in args.seeds.split(",")]
    if args.cmd == "figures":
        figures(pathlib.Path(args.src), pathlib.Path(args.results), args.prefix, args.picks)
        return
    methods = args.methods.split(",") if args.methods else list(ALL_METHODS)
    scenes = load_scenes(set(args.scenes.split(",")) if args.scenes else None)
    if args.cmd == "prepare":
        prepare(pathlib.Path(args.src), pathlib.Path(args.dst), methods, scenes, args.salt)
    else:
        aggregate(pathlib.Path(args.ev), args.name, methods, scenes)


if __name__ == "__main__":
    main()
