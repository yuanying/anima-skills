#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
P=params.yaml
H="kutara aki, femboy, bob cut, blunt bangs, solo"
# name|width|height|seed|prompt
while IFS='|' read -r name w h seed prompt; do
  [ -z "$name" ] && continue
  out=${name}.png
  [ -f "$out" ] && continue
  sdctl txt2img --params "$P" --model moss-image_moss_image_sft_bf16 \
    --text-encoder qwen3.5_9b_bf16.safetensors \
    --vae flux2-vae.safetensors \
    --distilled-cfg-scale 5 --seed "$seed" -n "" --width "$w" --height "$h" \
    -o "$out" "$H, $prompt <lora:kutara_moss.v3:1>"
done <<'LIST'
01_school_rooftop|832|1216|201|school uniform, white shirt, black pants, standing on school rooftop, fence, blue sky, wind, looking at viewer, smile, cowboy shot
02_konbini_night|832|1216|202|oversized black hoodie, holding plastic bag, in front of convenience store at night, fluorescent light, looking at viewer, upper body
03_aquarium|832|1216|203|beige cardigan, white shirt, standing in aquarium, looking up at large fish tank, blue light, from behind, looking back, full body
04_arcade|1216|832|204|varsity jacket, playing crane game, arcade, colorful lights, excited, open mouth, from side, upper body
05_riverbank_bicycle|1216|832|205|white t-shirt, denim shorts, riding bicycle, riverbank, sunset, orange sky, wind, smile, full body
06_classroom_desk|1024|1024|206|school uniform, sweater vest, sitting at desk in classroom, head resting on arms, sleepy, afternoon sunlight, close-up
07_ferris_wheel|832|1216|207|navy coat, inside ferris wheel gondola, night city view through window, sitting, blush, looking at viewer, upper body
08_art_studio|832|1216|208|oversized shirt, paint on face, holding paintbrush, painting on canvas, art studio, easel, smile, cowboy shot
09_headphones_room|1024|1024|209|grey sweatshirt, wearing headphones, sitting on floor, bedroom, music, eyes closed, smile, from above
10_camping|1216|832|210|green parka, sitting by campfire, camping tent, forest at night, holding mug, warm light, looking at viewer, full body
11_rain_window|832|1216|211|white shirt, leaning on window, rain on window, cloudy, melancholic, looking outside, from side, upper body
12_shrine_new_year|832|1216|212|kimono, standing at shinto shrine, torii, new year, snow, praying, hands together, eyes closed, cowboy shot
LIST
