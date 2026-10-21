---
name: moss-prompt
description: |
  MOSS-Image（SFT / Base）向けのプロンプトを組み立てるスキル。タグ列・自然文キャプション・JSON レイアウトを使い分け、2 人以上や文字の配置はレイアウトで描き分ける。
  トリガー: "moss-prompt", "/moss-prompt", "mossプロンプト", "MOSS-Imageのプロンプト生成", "moss prompt", "moss-image prompt"
  使用場面: (1) MOSS-Image で画像を生成する前にプロンプトを作りたいとき、(2) 複数キャラクターや文字の位置を指定したいとき、(3) キャラ LoRA を MOSS-Image で使うとき
---

$ARGUMENTS

## 書き方を選ぶ

| 描くもの | 書き方 |
|---|---|
| 1 人のキャラ（キャラ LoRA を含む） | タグ列 |
| 普通の場面・風景・写真風 | 自然文キャプション |
| 2 人以上、文字の位置、ポスター、複数コマ | JSON レイアウト |

細かい絵でも、位置を決める必要がなければレイアウトにしない。

## 共通の規則

- 英語で書く。描く文字だけは原文の言語のまま
- 重み `(x:1.2)`、`BREAK`、括弧のエスケープ `\(` は使わない（効かず、文字のまま渡る）
- 品質タグは無くてよい。付けるなら `best quality, highres` まで
- 画風・媒体を必ず書く（`anime illustration`, `beautiful anime-style coloring`, `photograph` など）。書かないとピクセルアート調などにぶれる
- アーティストは指定があるときだけ `@名前` で入れる
- 書かなかった部分はモデルが決める。全身なら下衣・靴まで書く
- LoRA タグ `<lora:名前:強さ>` はプロンプトの末尾（レイアウトなら JSON の後ろ）
- `[a:b:数字]` の形の文字列は書かない（Forge が prompt editing として書き換える）

## タグ列

```
<quality>, <トリガー or キャラ名>, <作品名>, <@artist>, <count>, solo, <外見>, <服装>, <動作・表情>, <場所・背景>, <光>, <構図> <lora:...>
```

- 小文字・スペース区切り・カンマ区切り。作品名はキャラ名の後ろに別のタグとして置く（`hatsune miku, vocaloid`）
- キャラ LoRA のトリガーは学習キャプションと同じ位置（多くは先頭）
- 髪型・眼鏡などキャラを決める特徴は書く。風で髪がなびく構図では髪型が変わりやすいので、髪型タグを必ず書く
- 真横の横顔（`from side`）では前髪などの特徴が弱まる
- 埋めるものが無い項目は省く（空のカンマを残さない）
- 確信のないタグは検索する:

```bash
python skills/moss-prompt/scripts/tag_search.py "セーラー服" --limit 3
```

## 自然文キャプション

まとまった英語の散文で、画風・媒体 → 被写体と動作 → 外見・服装 → 場所 → 光・色・雰囲気 → 描く文字、の順に書く。位置関係は言葉で書く。

## 文字描画

- 描く文字は引用符で囲み、原文どおり（言語・大文字小文字・句読点）に書く。プレースホルダにしない
- 改行したい位置に改行（自然文なら実際の改行、レイアウトなら `\n`）を入れる
- 書体・色・大きさ・置き場所も書く
- 服や小物に意味のない文字が出ることがある。無地にしたい物は `plain` と書く

## JSON レイアウト

左上原点のピクセル座標で下書きを書き、スクリプトで変換する。座標は手で計算しない。

**下書き（draft.json）:**

```json
{
  "width": 1216,
  "height": 832,
  "bbox_coord_space": "abs",
  "bbox_format": "xyxy",
  "summary": {
    "meta": ["illustration"],
    "canvas": "single",
    "caption": "Anime illustration of an empty classroom after school, sunlight through the windows, a green chalkboard with handwritten chalk text."
  },
  "items": [
    {
      "label": "text",
      "caption": "White chalk handwriting on the green chalkboard, two lines.",
      "text": "Today's lesson:\nMOSS-Image LoRA",
      "bbox": [220, 60, 900, 300]
    },
    {
      "label": "object",
      "caption": "kutara natsumi, 1girl, dark brown hair in a low ponytail with blunt bangs, glasses, grey eyes, as a teacher, wearing a white blouse and a long navy skirt, standing in front of the chalkboard on the left, pointing at the text",
      "bbox": [60, 160, 460, 832]
    },
    {
      "label": "object",
      "caption": "kutara aki, short black bob cut with blunt bangs, black eyes, as a student, wearing a school uniform with a sweater vest, sitting at a desk on the right, raising one hand, smiling",
      "bbox": [700, 340, 1160, 832]
    }
  ]
}
```

**変換:**

```bash
python skills/moss-prompt/scripts/compile_layout.py draft.json \
  --yaml prompt.yaml --suffix "<lora:name:1>" --negative ""
```

生成サイズは下書きの `width` / `height` と同じにする（スクリプトが最後に表示する）。位置の確認は `python skills/moss-prompt/scripts/overlay_layout.py draft.json out.png`。

**項目:**

- `summary.caption`: 全体の場面・画風・光。人物の外見は書かない
- `summary.meta`: 媒体（`illustration`, `poster`, `photograph` など）
- `summary.canvas`: `single` / `multi_panel` / `collage`
- `items[].label`: `object` / `character` / `text`
- `items[].caption`: その枠に見えるもの。text なら書体・色・置き場所
- `items[].text`: text item の描く文字（改行は `\n`）
- 任意で `tags` / `palette`（文字列の配列）。それ以外の項目は書かない

**人物:** 1 人 1 item にし、caption を「トリガー（名前）, 外見の特徴, 服装, 位置, 動作」の順で書く。1 人ずつ学習した LoRA でも特徴は混ざらない。人物どうしの関係（背中合わせ、もたれて眠るなど）は `summary.caption` と各人物の動作に書く。

**枠:**

- 枠は配置の注釈で、枠線を描く指示ではない
- 人物の枠は全身・上半身が入る大きさにする。隣の人物と少し重ねてよい
- 大きな物（ベンチ、テーブル）にも枠を付ける
- 文字の枠は文字数・改行に対して読める大きさにする
- 画像のまわりに白いフチが出たら、seed を変えるか、`summary.caption` の末尾に `The illustration fills the entire canvas edge to edge, with no white border or margin.` を足す

## ネガティブプロンプト

既定は空。全年齢に寄せたいとき・崩れたときは次を使う。成人向けを出すなら `nsfw` を外す。

```
nsfw, worst quality, bad anatomy, watermark, jpeg artifact
```

## 解像度

総画素 1M（既定）/ 1.5M / 2M。幅・高さとも 16 の倍数。

| 比 | 1M | 1.5M | 2M |
|---|---|---|---|
| 1:1 | 1024 × 1024 | 1248 × 1248 | 1440 × 1440 |
| 2:3 | 832 × 1216 | 1008 × 1504 | 1168 × 1744 |
| 3:2 | 1216 × 832 | 1504 × 1008 | 1744 × 1168 |
| 3:4 | 880 × 1184 | 1072 × 1440 | 1232 × 1648 |
| 4:3 | 1184 × 880 | 1440 × 1072 | 1648 × 1232 |
| 9:16 | 768 × 1360 | 928 × 1648 | 1072 × 1904 |
| 16:9 | 1360 × 768 | 1648 × 928 | 1904 × 1072 |

## 出力

**prompt.yaml（タグ列）:**

```yaml
prompt: "kutara natsumi, 1girl, solo, glasses, low ponytail, blunt bangs, beige trench coat, holding transparent umbrella, looking back, rain, city street at night, neon lights, from behind, cowboy shot <lora:kutara_moss.v3:1>"
negative_prompt: ""
```

**prompt.yaml（自然文・文字あり）:** リテラルブロック `|` で改行を保つ。

```yaml
prompt: |
  A soft anime illustration with beautiful anime-style coloring. A wide view of a refrigerator beside a kitchen counter, warm morning light. A small yellow sticky note on the refrigerator door is handwritten in black marker:
  "Buy milk and eggs!
  Two cartons of milk, a dozen eggs."
negative_prompt: ""
```

**prompt.yaml（レイアウト）:** `compile_layout.py --yaml` の出力をそのまま使い、`draft.json` と生成サイズも示す。

**params.yaml と sdctl:**

```yaml
steps: 50
cfg_scale: 3
sampler: Euler
scheduler: simple
override_settings:
  moss_uncond_skip_layers: "22"
```

```bash
sdctl txt2img --params params.yaml --prompt prompt.yaml \
  --model moss-image_moss_image_sft_bf16 \
  --text-encoder qwen3.5_9b_bf16.safetensors \
  --vae flux2-vae.safetensors \
  --distilled-cfg-scale 5 \
  --width <w> --height <h> -o <output>.png
```

- `--text-encoder` / `--vae` は毎回付ける（前のモデルのモジュールが残ると失敗する）
- `--distilled-cfg-scale 5` は shift。省略すると 3.5 になる
- CFG は 3。短いプロンプトなら 6 まで上げてよい
- Base は `--model moss-image_moss_image_base_bf16`
