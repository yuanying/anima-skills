#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
P=params.yaml
while IFS=$'\t' read -r name w h seed prompt; do
  [ -f "$name.png" ] && continue
  sdctl txt2img --params "$P" --model moss-image_moss_image_sft_bf16 \
    --text-encoder qwen3.5_9b_bf16.safetensors \
    --vae flux2-vae.safetensors \
    --distilled-cfg-scale 5 --seed "$seed" -n "" --width "$w" --height "$h" \
    -o "$name.png" "$prompt <lora:kutara_moss.v3:1>"
done < prompts.tsv
