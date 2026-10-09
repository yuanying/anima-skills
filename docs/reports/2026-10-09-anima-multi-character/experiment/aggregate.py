#!/usr/bin/env python3
"""評価者が書いたブラインドの CSV を方式名に戻して結合し、集計表を作る。

使い方: aggregate.py <評価用ディレクトリ>
入力:   <評価用ディレクトリ>/results_<scene>.csv と key.yaml
出力:   results.csv（全画像の判定。method 列つき）と summary.md（集計表）をこのディレクトリに書く
success は 5 項目から計算し直す。
"""
import csv
import pathlib
import sys
from collections import defaultdict

import yaml

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_prompts import METHODS  # noqa: E402

ITEMS = ["count", "identity", "position", "pose", "composition"]
ITEM_JA = {"count": "人数", "identity": "属性", "position": "位置・役割", "pose": "ポーズ", "composition": "構図"}


def main():
    ev = pathlib.Path(sys.argv[1])
    key = yaml.safe_load((ev / "key.yaml").read_text())
    scenes = yaml.safe_load((HERE / "scenes.yaml").read_text())
    rows = []
    for s in scenes:
        with open(ev / f"results_{s['id']}.csv", newline="") as f:
            for r in csv.DictReader(f):
                vals = {k: int(r[k]) for k in ITEMS}
                rows.append({
                    "scene": r["scene"].strip(), "method": key[r["code"].strip()], "seed": int(r["seed"]),
                    **vals, "success": int(all(vals.values())), "score": sum(vals.values()),
                    "note": r.get("note", "").strip(),
                })
    assert len(rows) == len(scenes) * len(METHODS) * 4, len(rows)
    rows.sort(key=lambda r: (r["scene"], list(METHODS).index(r["method"]), r["seed"]))
    with open(HERE / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["scene", "method", "seed", *ITEMS, "success", "score", "note"])
        w.writeheader()
        w.writerows(rows)

    by_m = defaultdict(list)
    by_ms = defaultdict(list)
    for r in rows:
        by_m[r["method"]].append(r)
        by_ms[(r["method"], r["scene"])].append(r)
    order = sorted(METHODS, key=lambda m: (-sum(r["success"] for r in by_m[m]), -sum(r["score"] for r in by_m[m])))
    out = []
    out.append("## 方式別の総合成績（12 シーン × 4 seed = 48 枚）\n")
    out.append("| 順位 | 方式 | 成功 | 成功率 | 平均スコア | " + " | ".join(ITEM_JA[i] for i in ITEMS) + " |")
    out.append("|---|---|---|---|---|" + "---|" * len(ITEMS))
    for i, m in enumerate(order, 1):
        rs = by_m[m]
        n = len(rs)
        succ = sum(r["success"] for r in rs)
        items = " | ".join(f"{sum(r[it] for r in rs) / n:.0%}" for it in ITEMS)
        out.append(f"| {i} | `{m}` | {succ}/{n} | {succ / n:.0%} | {sum(r['score'] for r in rs) / n:.2f} | {items} |")
    out.append("\n## シーン別の成功数（4 枚中）\n")
    out.append("| 方式 | " + " | ".join(s["id"] for s in scenes) + " | 計 |")
    out.append("|---|" + "---|" * (len(scenes) + 1))
    for m in order:
        cells = [str(sum(r["success"] for r in by_ms[(m, s["id"])])) for s in scenes]
        out.append(f"| `{m}` | " + " | ".join(cells) + f" | {sum(r['success'] for r in by_m[m])} |")
    tot = [str(sum(r["success"] for r in rows if r["scene"] == s["id"])) for s in scenes]
    out.append("| 全方式計（36 枚中） | " + " | ".join(tot) + f" | {sum(r['success'] for r in rows)} |")
    (HERE / "summary.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
