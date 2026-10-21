#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
P=params.yaml
H="kutara natsumi, 1girl, solo, glasses, large breasts"
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
01_office_desk|1216|832|101|black suit, white shirt, sitting at desk, office, typing on laptop, from side, looking at screen, window, daytime, upper body
02_cafe_sweater|832|1216|102|grey turtleneck sweater, ribbed sweater, sitting in cafe, holding coffee cup with both hands, smile, looking at viewer, wooden table, warm lighting, cowboy shot
03_beach_bikini|832|1216|103|orange bikini, standing on beach, ocean, blue sky, wind, hand on own hair, smile, full body, barefoot
04_rain_umbrella|832|1216|104|beige trench coat, holding transparent umbrella, rain, city street at night, neon lights, reflections, looking back, from behind, cowboy shot
05_library_closeup|1024|1024|105|white blouse, cardigan, reading book, library, bookshelves, close-up, face focus, looking down, soft light
06_kitchen_apron|832|1216|106|white t-shirt, jeans, apron, cooking in kitchen, holding ladle, smile, open mouth, looking at viewer, cowboy shot
07_park_onepiece|832|1216|107|white sundress, straw hat, walking in park, cherry blossoms, petals, spring, smile, full body, from below
08_bed_hoodie|1216|832|108|grey hoodie, black shorts, lying on stomach on bed, holding smartphone, bedroom, legs up, looking at viewer, blush
09_station_winter|832|1216|109|navy coat, red scarf, train station platform, snow, breath, hands in pockets, looking away, upper body
10_kimono_festival|832|1216|110|yukata, holding paper fan, summer festival, lanterns, night, fireworks, smile, looking at viewer, cowboy shot
11_gym_sportswear|832|1216|111|sports bra, leggings, gym, stretching, arms up, sweat, from side, full body
12_sofa_dutch|1024|1024|112|cardigan, miniskirt, sitting on sofa, crossed legs, living room, dutch angle, hand on cheek, smile, looking at viewer
LIST
