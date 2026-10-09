#!/usr/bin/env python3
"""prompts/ の全条件を sdctl で生成する。既に存在する画像はスキップする。

使い方: generate.py <出力ディレクトリ> [--scenes s01,s02] [--methods a,b]
出力:   <出力ディレクトリ>/<scene_id>/<method_id>_<seed>.png
"""
import argparse
import pathlib
import subprocess

import yaml

HERE = pathlib.Path(__file__).resolve().parent
SEEDS = [101, 202, 303, 404]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--scenes")
    ap.add_argument("--methods")
    args = ap.parse_args()
    out = pathlib.Path(args.outdir)
    scenes = yaml.safe_load((HERE / "scenes.yaml").read_text())
    want_s = set(args.scenes.split(",")) if args.scenes else None
    want_m = set(args.methods.split(",")) if args.methods else None
    for s in scenes:
        if want_s and s["id"] not in want_s:
            continue
        for pf in sorted((HERE / "prompts" / s["id"]).glob("*.yaml")):
            if want_m and pf.stem not in want_m:
                continue
            for seed in SEEDS:
                dst = out / s["id"] / f"{pf.stem}_{seed}.png"
                if dst.exists():
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    [
                        "sdctl", "txt2img",
                        "--params", str(HERE / "params.yaml"),
                        "--prompt", str(pf),
                        "--width", str(s["width"]), "--height", str(s["height"]),
                        "--seed", str(seed),
                        "-o", str(dst),
                    ],
                    check=True,
                )


if __name__ == "__main__":
    main()
