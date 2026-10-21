#!/usr/bin/env bash
# Follow-up checks (2026-10-21): module names for --text-encoder / --vae,
# the white border on the park scene, and label "character".
set -euo pipefail
cd "$(dirname "$0")"
COMPILE=../../../../../skills/moss-prompt/scripts/compile_layout.py
gen() { # draft seed output
  [ -f "$3.png" ] && return 0
  python3 "$COMPILE" "$1.json" --yaml "$3.yaml" --suffix "<lora:kutara_moss.v3:1>" --negative ""
  sdctl txt2img --params ../params.yaml --prompt "$3.yaml" \
    --model moss-image_moss_image_sft_bf16 \
    --text-encoder qwen3.5_9b_bf16.safetensors --vae flux2-vae.safetensors \
    --distilled-cfg-scale 5 --seed "$2" --width 1216 --height 832 -o "$3.png"
}
for s in 303 305 306; do
  gen v1_park_modules "$s" "v1_park_modules_$s"
  gen v2_park_noborder "$s" "v2_park_noborder_$s"
done
gen v3_cafe_character 301 v3_cafe_character_301
