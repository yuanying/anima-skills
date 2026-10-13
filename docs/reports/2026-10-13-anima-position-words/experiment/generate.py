#!/usr/bin/env python3
"""prompts/ の全条件を sdctl で生成する。既に存在する画像はスキップする。

使い方: generate.py <出力ディレクトリ> [--scenes a01,p01] [--methods pos-words,no-pos]
                    [--prompts <prompts ディレクトリ>] [--scenes-file <シーン定義 YAML,...>] [--seeds 101,202]
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
    ap.add_argument("--prompts", default=str(HERE / "prompts"))
    ap.add_argument("--scenes-file", default=str(HERE / "scenes.yaml"))
    ap.add_argument("--seeds")
    args = ap.parse_args()
    out = pathlib.Path(args.outdir)
    prompts = pathlib.Path(args.prompts)
    scenes = [s for f in args.scenes_file.split(",") for s in yaml.safe_load(pathlib.Path(f).read_text())]
    seeds = [int(x) for x in args.seeds.split(",")] if args.seeds else SEEDS
    want_s = set(args.scenes.split(",")) if args.scenes else None
    want_m = set(args.methods.split(",")) if args.methods else None
    for s in scenes:
        if want_s and s["id"] not in want_s:
            continue
        for pf in sorted((prompts / s["id"]).glob("*.yaml")):
            if want_m and pf.stem not in want_m:
                continue
            for seed in seeds:
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
