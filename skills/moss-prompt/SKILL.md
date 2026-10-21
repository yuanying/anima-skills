---
name: moss-prompt
description: |
  MOSS-Image（OpenMOSS の 5B single-stream DiT。SFT / Base）向けのプロンプトを組み立てるスキル。場面に応じてタグ列・自然文キャプション・JSON レイアウトを選び、2 人以上や文字の配置はレイアウトで描き分ける。
  トリガー: "moss-prompt", "/moss-prompt", "mossプロンプト", "MOSS-Imageのプロンプト生成", "moss prompt", "moss-image prompt"
  使用場面: (1) MOSS-Image で画像を生成する前にプロンプトを作りたいとき、(2) 複数キャラクターや文字の位置を指定したいとき（JSON レイアウト）、(3) キャラ LoRA を MOSS-Image で使うときの書き方がわからないとき
---

MOSS-Image 向けのプロンプトをインタラクティブに組み立てます。

対象モデル: MOSS-Image-SFT（既定）/ MOSS-Image-Base。Forge Neo の sd-webui で `sdctl` から生成する前提。

根拠の出典:

- **公式ガイド**: [USERGUIDE.md](https://github.com/OpenMOSS/MOSS-Image/blob/main/USERGUIDE.md)
- **公式 enhancer**: [moss-image-prompt-enhancer](https://github.com/OpenMOSS/MOSS-Image/tree/main/skills/moss-image-prompt-enhancer)（`SKILL.md`, `references/layout.md`, `scripts/compile_prompt.py`）
- **モデルカード**: [MOSS-Image-SFT](https://huggingface.co/OpenMOSS-Team/MOSS-Image-SFT)
- **技術レポート**: [arXiv 2610.23374](https://arxiv.org/abs/2610.23374)
- **検証レポート**: `docs/reports/2026-10-20-moss-image-lora-prompts/`（このリポジトリ。SFT + キャラ LoRA で、タグ列 1 人 24 枚と JSON レイアウト 2 人 4 枚ほか）

## タグ検索エンジンの使い方

Danbooru タグをキーワード（英語・日本語）で検索できます:

```bash
python skills/moss-prompt/scripts/tag_search.py "long hair" --limit 5
python skills/moss-prompt/scripts/tag_search.py "青い目" --limit 5
```

- 出力は JSON 配列。`tag` はスペース区切り。括弧はエスケープしない（下の「タグ記法」）
- `post_count` はそのタグの学習量の目安
- タグの確信がない場合はプロンプト組み立て前に検索して確認する

タグデータ（`tags.json`）は `anima-prompt` スキルと共有している。見つからない場合は
`python skills/anima-prompt/scripts/build_data.py` で生成する。

---

## MOSS-Image プロンプト規則（厳守）

### 大前提: Anima とも Illustrious とも書き方が違う

| 項目 | Anima | Illustrious | **MOSS-Image** |
|---|---|---|---|
| テキストエンコーダ | Qwen3 0.6B | CLIP | **Qwen3.5-9B**（最大 4096 トークン） |
| 主体 | 1 行目タグ + 自然文 | Danbooru タグ | **タグ列 / 自然文 / JSON レイアウトのどれでも**（混ぜてもよい） |
| 複数キャラの描き分け | 位置語つきの自然文 | `BREAK` | **JSON レイアウト**（1 人 1 item） |
| 重み `(x:1.2)` | 1.5〜2.0 が必要 | 1.05〜1.3 | **効かない**（Forge は重みを無効にして文字のまま渡す） |
| `BREAK` | 効果なし | 効く | **使わない**（ただの単語として渡る） |
| 括弧のエスケープ | 不要 | `\(` 必須 | **不要** |
| アーティスト | `@wlop` | `wlop` | **`@wlop`** |
| 品質タグ | `masterpiece, best quality, score_7, ...` | `masterpiece, best quality, amazing quality` | **無くてよい**（タグ列なら `best quality, highres` まで） |
| ネガティブ | 公式推奨の短いリスト | ポジティブ並みに効く。長め | **既定は空**（下の「ネガティブプロンプト」） |
| CFG | 4〜5 | 5〜5.5 | **3**（短いプロンプトは 6 まで） |
| steps / sampler | 30〜50 / `ER SDE` | 20〜28 / `Euler a` | **50 / `Euler` + `simple`** |
| 文字描画 | 単語まで | 短い単語まで | **長文・改行まで得意** |

重み・`BREAK` について: Forge Neo の MOSS-Image エンジンはプロンプトの重みを無効にしており（`EmphasisNone`, `disable_weights=True`）、`(blue eyes:1.3)` は括弧ごと文字として渡る。

### 書き方を選ぶ

MOSS-Image は自然文・タグ列・JSON レイアウトのどれでも学習している（公式ガイド）。描くものに応じて選ぶ。

| 描くもの | 書き方 | 根拠 |
|---|---|---|
| 1 人のキャラ（特にタグで学習したキャラ LoRA） | **タグ列** | 検証: 24 枚中 22 枚でキャラの特徴を保った |
| 普通の場面・風景・写真風・イラスト（キャラ LoRA なし） | **自然文キャプション** | 公式 enhancer の既定 |
| 2 人以上の人物 | **JSON レイアウト** | 検証: 4 枚とも 2 人の特徴が混ざらず、位置もおおむね枠どおり |
| 文字の位置を決めたい・ポスター・複数コマ・物どうしの配置 | **JSON レイアウト** | 公式 enhancer |

- 細かい絵だからといって自動でレイアウトにしない（公式 enhancer）。位置を決める必要があるときだけ使う
- 描く文字が 1 つで、位置にこだわらないなら自然文で足りる

### タグ記法（タグ列のとき）

**推奨順**（公式ガイド）: Quality → Score → Meta → Year → Character → Series → Artist → General

```
best quality, highres, hatsune miku, vocaloid, @foo bar, 1girl, blue hair
```

- 全て**小文字・スペース区切り・カンマ区切り**
- 作品名は**別のタグとして**キャラ名の後ろに置く（`hatsune miku, vocaloid`）。Danbooru のタグ名自体に括弧が含まれるもの（`artoria pendragon (fate)`）はそのまま書き、エスケープしない
- アーティストタグは `@` を付ける（`@foo bar`）
- 品質タグは任意。付けるなら公式例の `best quality, highres` までにし、積み増さない（公式 enhancer は冗長な品質タグを避けるよう書いている）
- `score_*` は公式の順序に「Score」の枠があるが、効き方は未確認。既定では入れない
- 一般タグの後ろに短い英語の句を足してもよい（自然文とタグ列は混ぜてよい: 公式ガイド）

**キャラ LoRA を使うとき**は、学習キャプションと同じ形でトリガーワードを先頭に置く。検証で効いた形:

```
kutara natsumi, 1girl, solo, glasses, large breasts, grey turtleneck sweater, ribbed sweater, sitting in cafe, holding coffee cup with both hands, smile, looking at viewer, wooden table, warm lighting, cowboy shot <lora:kutara_moss.v3:1>
```

- `<トリガー>, <人数>, solo, <キャラを決める外見タグ>, <服装>, <動作・表情>, <場所・背景>, <光>, <構図>` の順。品質タグを付けるならトリガーの前（公式の順序）。検証は品質タグなしで行った
- **LoRA タグ `<lora:名前:強さ>` はプロンプトの末尾**に付ける（検証で効いた）
- 学習に無い背景・服装（オフィス、雨の街、浴衣、着物、キャンプなど）でもキャラの特徴は保たれる（検証）
- **髪型が変わりやすい構図では髪型タグを書く**。風に髪をなびかせる全身（`wind, hand on own hair`）で、結んだ髪が長いストレートに変わった（検証）。`low ponytail` などを明示する（効果は未確認）
- **真横の横顔（`from side`）ではぱっつん前髪などの特徴が弱まる**（検証）。前髪が特徴のキャラは `from side` を避けるか、seed を多めに回す
- **書かなかった部分はモデルが決める**。カーディガンだけ指定したらスカートと黒タイツが付いた（検証）。全身を描くなら下衣・靴まで書く

### 自然文キャプション

公式 enhancer の書き方に従う。

- **英語のまとまった散文**で書く（学習データが最も多い: 公式ガイド）。日本語・中国語も通るが、既定は英語
- 被写体と動作、外見、場所、カメラ・フレーミング、**画風（媒体）**、光、素材、色、雰囲気を、見えるものとして書く
- 位置関係は言葉で書く（`on the left side of the table`）。座標や JSON の項目をキャプションに混ぜない
- **画風は必ず書く**（`anime illustration`, `photograph`, `watercolor painting` など）。指定しないとイラスト調とピクセルアート調の間でぶれる、`flat coloring` より `beautiful anime-style coloring` の方がアニメ調が安定した、という報告がある（[くろくまそふと](https://kurokumasoft.com/2026/10/18/moss-image/)。公式ではない）
- 頼まれていない画風の変更、冗長な品質タグ、恣意的な語数制限はしない（公式 enhancer）
- 指示に含まれる引用文が、描く文字とは限らない。描く文字と、参考情報・制約を区別する（公式 enhancer）

### 文字描画

- **描く文字は引用符で囲み、元の言語のまま、句読点・大文字小文字も変えずに書く**（公式 enhancer）。翻訳しない
- **改行を制御したいときは、文字の中に改行を入れる**（自然文なら実際の改行か `\n`、レイアウトなら JSON 文字列の `\n`）。自動でも改行されるが期待どおりとは限らない（公式ガイド）。明示した改行は文字の精度も上げる（技術レポート 6 章）
- プレースホルダ（`headline here`）でなく、実際の文言を書く（公式 enhancer）
- 書体・色・大きさ・置き場所（看板、黒板のチョーク、Tシャツのプリントなど）も書く
- 検証: `KUTARA DAYS`（太字のタイトル）、`Two lives, one summer.`（イタリック）、`Today's lesson:\nMOSS-Image LoRA`（黒板のチョーク、`\n` どおり 2 行）、`謹賀新年` はどれも正確に出た
- **意図しない文字が出ることがある**。うちわやスウェットに意味のない文字が出た（検証）。無地にしたい物は `plain grey sweatshirt` のように無地と書く（効果は未確認）。書く文字を決めてしまうのも手

### JSON レイアウト

位置を決めたいときに使う（実験的機能: 公式ガイド）。**座標は手で計算しない**。左上原点のピクセルで下書きを書き、変換スクリプトで学習時の形にする。

**下書き（draft.json）**: 公式 enhancer の形式。

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
      "caption": "kutara natsumi, 1girl, dark brown hair in a low ponytail with blunt bangs, glasses, grey eyes, large breasts, as a teacher, wearing a white blouse and a long navy skirt, standing in front of the chalkboard on the left, holding a piece of chalk, pointing at the text",
      "bbox": [60, 160, 460, 832]
    },
    {
      "label": "object",
      "caption": "kutara aki, femboy, short black bob cut with blunt bangs, black eyes, as a student, wearing a school uniform with a sweater vest, sitting at a desk on the right, raising one hand, smiling",
      "bbox": [700, 340, 1160, 832]
    }
  ]
}
```

**変換**:

```bash
python skills/moss-prompt/scripts/compile_layout.py draft.json \
  --yaml prompt.yaml --suffix "<lora:kutara_moss.v3:1>" --negative ""
```

- 出力は 1 行の JSON（`abs_centralized` / `yxyx`。`[y_min, x_min, y_max, x_max]`、キャンバス中心が原点）。端数は外側に丸め、キャンバスからはみ出した枠や未知の項目はエラーにする（公式の `compile_prompt.py` と同じ規則）
- `--suffix` は JSON の後ろに付ける文字列。**LoRA タグは JSON の後ろ**に付ける（検証で効いた）
- **生成サイズは下書きの `width` / `height` と同じにする**。サイズはプロンプトに入らない（公式ガイド）。スクリプトが最後に `--width` / `--height` を表示する
- 生成後の位置の確認: `python skills/moss-prompt/scripts/overlay_layout.py draft.json out.png` で枠を重ねた画像を作れる（text は赤、それ以外は緑）

**項目の書き方**:

- `summary.caption`: 全体の場面・画風・光。各人物の外見はここに書かない
- `summary.meta`: 媒体・ジャンル（`["illustration"]`, `["poster"]`, `["photograph"]` など）。検証は `illustration` と `poster` で行った
- `summary.canvas`: `single`（既定）/ `multi_panel`（複数コマ）/ `collage`
- `items[].label`: `object` / `character` / `text`。人物は `object` で検証した 4 枚がすべて通った。`character` でも同じように描き分けられた（1 枚）
- `items[].caption`: その枠に見えるものだけを書く。text item には書体・色・置き場所を書く
- `items[].text`: text item に必須。描く文字そのもの（改行は `\n`）。独立に置きたい文字は別の item にする
- `tags` / `palette`（任意の文字列配列）も使える。役に立つときだけ
- 公式の項目以外（`id`, `children` など）は書かない（変換スクリプトがエラーにする）

**人物の item の caption** は「**トリガー（名前）, 外見の特徴, 服装, 位置, 動作**」の順に 1 つにまとめる（検証で 2 人の特徴が混ざらなかった形）:

```
kutara natsumi, 1girl, dark brown hair in a low ponytail with blunt bangs, glasses, grey eyes, large breasts, wearing a grey ribbed turtleneck sweater, sitting on the right, gentle smile, holding a coffee cup with both hands
```

- タグと短い句を混ぜてよい。キャラを決める外見（髪型・髪色・眼鏡など）は必ず書く
- 1 人ずつしか学習していないキャラ LoRA でも、別々の item にすれば 2 人の特徴は混ざらなかった（検証。眼鏡と結んだ髪は natsumi だけ、ボブは aki だけ）
- 人物どうしの関係（背中合わせ、肩にもたれて眠る、先生が指して生徒が手を挙げる）は、`summary.caption` と各人物の動作に書けば再現された（検証）

**枠の決め方**:

- 枠は配置の注釈で、**枠線やパネルを描けという指示ではない**（公式 enhancer）。見た目は caption に、全体の扱いは `summary.caption` に書く
- 人物は全身や上半身が入る大きさにする。枠から少しはみ出すことはある（検証）
- 重なりは許される（隣り合う人物の枠は少し重ねてよい）
- 文字の枠は、文字数・改行・解像度に対して読める大きさにする（公式 `layout.md`）
- 大きな物（ベンチ、テーブル）にも枠を付けると配置が安定する（検証で使った形）

**画像のまわりに白いフチが付くことがある**（検証: 公園の場面の特定の seed で再現し、別の seed 2 つでは出なかった）。出たら `summary.caption` の末尾に `The illustration fills the entire canvas edge to edge, with no white border or margin.` を足す。同じ seed でフチが消えた（1 例）。まず seed を変えるだけでもよく、最初から入れる必要はない

**Forge の prompt editing 構文に注意**: `[a:b:数字]` の形の文字列は、モデルに届く前に Forge が書き換える。通常の JSON（`"bbox":[...]`）は影響を受けない（Forge の構文解析で確認）。変換スクリプトはこの形を見つけると警告する。

### 安全・成人向けの扱い

**勝手に決めず、必ずユーザーに確認する**（フェーズ1 ステップ7）。

| 方針 | ネガティブ | ポジティブ |
|---|---|---|
| 全年齢向けにしたい | 公式推奨ネガティブ（`nsfw` を含む）を入れる | 何も足さない |
| 成人向けもありうる | `nsfw` を**入れない**（空、または `nsfw` を除いた推奨ネガティブ） | 必要な描写を書く |
| 指定なし | 空（モデルの既定） | 何も足さない |

- 公式ガイドの推奨ネガティブは `nsfw` で始まる。成人向けを出すなら外す必要がある
- Danbooru のレーティングタグ（`safe` / `sensitive` / `explicit`）がポジティブで効くかは未確認。入れるならユーザーの指定があるときだけ
- ComfyUI の公式ワークフローの `enable_prompt_upsampler`（LLM でプロンプトを膨らませる）は、成人向けでは OFF にする必要があるという報告がある（[くろくまそふと](https://kurokumasoft.com/2026/10/18/moss-image/)）。sdctl / Forge では関係しない

### アーティストタグ

- **ユーザーが指定しなかった場合は入れない**。勝手に画風を固定しない
- 書式は `@名前`（公式ガイドの例 `@foo bar`）。タグ列では Character / Series の後ろに置く。自然文やレイアウトでは `in the style of @foo bar` のように画風の説明として書く（効き方は未確認）
- 複数混ぜるかどうかもユーザーに任せる

### ネガティブプロンプト

**既定は空**。モデルカードの既定が空で、検証もすべて空（`-n ""`）で行い、品質の問題は出なかった。

**公式推奨（崩れが出たとき・全年齢にしたいとき）**:

```
nsfw, worst quality, bad anatomy, watermark, jpeg artifact
```

- 成人向けを出すなら `nsfw` を外す
- 推奨ネガティブを入れたときの違いは、このリポジトリでは未検証

### 解像度

総画素 **1M / 1.5M / 2M** を推奨。0.25M（512×512）から 4M まで外挿できる。任意のアスペクト比。**幅・高さとも正の 16 の倍数**（違うとエラー）（公式ガイド）。

| アスペクト比 | 1M（既定） | 1.5M | 2M |
|---|---|---|---|
| 1:1 | 1024 × 1024 | 1248 × 1248 | 1440 × 1440 |
| 2:3 | 832 × 1216 | 1008 × 1504 | 1168 × 1744 |
| 3:2 | 1216 × 832 | 1504 × 1008 | 1744 × 1168 |
| 3:4 | 880 × 1184 | 1072 × 1440 | 1232 × 1648 |
| 4:3 | 1184 × 880 | 1440 × 1072 | 1648 × 1232 |
| 9:16 | 768 × 1360 | 928 × 1648 | 1072 × 1904 |
| 16:9 | 1360 × 768 | 1648 × 928 | 1904 × 1072 |

- 1216×832 / 832×1216 / 1024×1024 で問題なし（検証）
- 1 枚の時間は、1024×1024 / 50 steps で約 35〜45 秒だった（RTX PRO 5000）。画素数にほぼ比例して延びる
- JSON レイアウトは、下書きの `width` / `height` で生成する

### モデルの限界・既知の問題

- **画風がぶれる**: 画風を書かないとイラスト調・ピクセルアート調などにぶれる（二次情報）。必ず媒体と画風を書く
- **意図しない文字**: 服や小物に意味のない文字が出る（検証）
- **白いフチ**: レイアウトで画像の周りに白いフチが付くことがある（検証）
- **縦の色の縞**（SFT）: コミュニティが軽減用の LoRA を出している（[MOSS-Image-SFT-DeBand](https://huggingface.co/MATLOWAI/MOSS-Image-SFT-DeBand)。公式 README の Community projects）
- **未検証のこと**: タグ列だけで 2 人を出したとき、3 人以上のレイアウト、キャラ LoRA なしの自然文、推奨ネガティブを入れたとき、CFG を上げたとき、Base での結果
- SFT は Base より文字描画とレイアウトがよい（モデルカードの比較）。生成だけなら SFT を使う。Base は LoRA 学習の土台

---

$ARGUMENTS

## フェーズ1: 情報収集（1問ずつ確認）

`$ARGUMENTS` と会話の文脈からすでに判明している項目はスキップする。

### ステップ1: モデルと LoRA
SFT（既定）か Base か、キャラ LoRA を使うかを確認する。LoRA を使うなら、名前・強さ・**トリガーワード**・学習キャプションの形（タグ列か文か）を聞く。

### ステップ2: 何を描くか（書き方の判断）
人数と、描く文字があるか、位置を決めたいものがあるかを確認し、「書き方を選ぶ」の表で書き方を決めてユーザーに伝える。

- 2 人以上 → JSON レイアウト
- 文字の位置を決めたい・ポスター・複数コマ → JSON レイアウト
- 1 人のキャラ（LoRA あり）→ タグ列
- それ以外 → 自然文キャプション

### ステップ3: キャラクター情報

各キャラクターについて以下を確認する。**2 人以上の場合は 1 人ずつ順に聞き、まとめて聞かない**（属性が混ざるため）。

- 画面上の**位置**（左・中央・右・手前・奥など）※2 人以上の場合のみ
- キャラクター名（作品名）または LoRA のトリガー
- 外見: 髪型・髪色・目の色・体型など。**キャラを決める特徴（髪型、眼鏡など）は必ず聞く**（髪型が変わる失敗を防ぐ）
- 服装・小物。全身を描くなら下衣・靴まで（書かないとモデルが決める）
- 動作・表情

### ステップ4: シーン・構図
どこで何をしている場面か、どんな構図か（引き/寄り、カメラ角度）を確認する。横顔（`from side`）を選ぶときは、前髪などの特徴が弱まることを伝える。

### ステップ5: 描く文字
画像に入れる文字があるか確認する。あれば**文言そのもの**（言語・大文字小文字・句読点・改行も）、置き場所、書体・色を聞く。

### ステップ6: 画風・アーティスト
媒体と画風（アニメイラスト、写真、水彩など）を確認する。**画風は必ず決める**（書かないとぶれる）。

- アーティストは**ユーザーが指定したときだけ**入れる
- 指定がなければ、画風は媒体の説明（`anime illustration`, `beautiful anime-style coloring` など）で決める

### ステップ7: 安全・成人向けの扱い
「全年齢向けにしたい / 成人向けもありうる / 指定なし」のどれかを**必ずユーザーに確認する**。答えでネガティブの `nsfw` の扱いを決める（「安全・成人向けの扱い」）。

### ステップ8: 背景・光
背景や光源の要望を確認する（省略可）。

### ステップ9: アスペクト比と解像度
「解像度」の表から選ぶ（省略時は 1M の `1:1` = 1024×1024）。レイアウトのときは、ここで決めたサイズで下書きを書く。

---

## フェーズ2: タグ検索（必要に応じて）

タグ列や、人物 item の caption に書くタグで確信がないものは検索して確認する。
必要最小限にとどめ、全タグを検索する必要はない。

```bash
# キャラクター名と作品名を確認
python skills/moss-prompt/scripts/tag_search.py "初音ミク" --limit 3
# 服装タグを確認
python skills/moss-prompt/scripts/tag_search.py "セーラー服" --limit 3
```

自然文キャプションではタグに無い語彙を自由に使ってよい。

---

## フェーズ3: プロンプト組み立て

### タグ列

```
<quality>, <LoRA トリガー or キャラ名>, <作品名>, <@artist>, <count>, solo, <外見>, <服装>, <動作・表情>, <場所・背景>, <光>, <構図>
```

- `<quality>` は任意（`best quality, highres`）。LoRA を使うときはトリガーを学習キャプションと同じ位置（多くは先頭）に置く
- 1 人なら `1girl, solo` / `1boy, solo`
- `<>` は指定があるときだけ埋める。埋めるものが無ければ項目ごと省く（空のカンマを残さない）
- 末尾に LoRA タグ

### 自然文キャプション

1 段落〜数段落の英語の散文。画風・媒体 → 被写体と動作 → 外見・服装 → 場所・背景 → 光・色・雰囲気 → 描く文字（引用符つき）の順を目安にする。

### JSON レイアウト

1. 決めた解像度で `draft.json` を書く（「JSON レイアウト」）
2. `compile_layout.py` で `prompt.yaml` に変換する
3. 出力された JSON を読み、文言・人数・枠の位置を確認する。エラーは下書きを直して再変換する（手で変換後の JSON を書かない）

### 最終チェック

- [ ] 重み `(x:1.2)`・`BREAK`・`\(` を使っていないか
- [ ] 描く文字が原文どおりか（言語・句読点・大文字小文字・改行）
- [ ] 画風（媒体）を書いたか
- [ ] アーティストタグをユーザーの指定なしに入れていないか
- [ ] ネガティブの `nsfw` がステップ7 の答えと合っているか
- [ ] 幅・高さが 16 の倍数か。レイアウトなら下書きと同じサイズか
- [ ] LoRA タグがプロンプト（レイアウトなら JSON）の後ろにあるか

---

## フェーズ4: 出力

### 出力1: prompt.yaml

**タグ列（1 人・キャラ LoRA）:**

```yaml
prompt: "kutara natsumi, 1girl, solo, glasses, large breasts, low ponytail, blunt bangs, beige trench coat, holding transparent umbrella, looking back, rain, city street at night, neon lights, reflections, from behind, cowboy shot <lora:kutara_moss.v3:1>"
negative_prompt: ""
```

**自然文キャプション（文字あり）:**

```yaml
prompt: |
  A soft anime illustration with beautiful anime-style coloring. A wide view of a refrigerator beside a kitchen counter with a fruit bowl, warm morning light from a window on the left. A small yellow sticky note on the refrigerator door is handwritten in black marker:
  "Buy milk and eggs!
  Two cartons of milk, a dozen eggs."
negative_prompt: ""
```

YAML はリテラルブロック `|` を使うと、描く文字の改行がそのまま保たれる。

**JSON レイアウト（2 人）:** `compile_layout.py --yaml` の出力をそのまま使う。

```yaml
prompt: |-
  {"summary":{"meta":["illustration"],"canvas":"single","caption":"Anime illustration of ..."},"items":[...],"bbox_coord_space":"abs_centralized","bbox_format":"yxyx"} <lora:kutara_moss.v3:1>
negative_prompt: ""
```

レイアウトのときは `draft.json`（編集用）と `prompt.yaml`（生成用）の両方を渡し、**生成サイズ**を明記する。

### 出力2: params.yaml と sdctl コマンド

```yaml
# params.yaml
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
  --width <w> --height <h> \
  -o <output>.png
```

| パラメータ | 値 | 根拠 |
|---|---|---|
| steps | 50 以上 | 公式ガイド |
| sampler / scheduler | `Euler` / `simple` | 公式ガイド（Euler）、Forge のプリセット |
| CFG | 3（短いプロンプトは 6 まで上げてよい） | 公式ガイド |
| shift | 5（`--distilled-cfg-scale 5`） | 公式ガイド。**省略すると Forge の既定 3.5 になる** |
| SLG | 負の枝で層 22 をスキップ（`moss_uncond_skip_layers: "22"`） | 公式ガイド。空にすると無効（写実寄りになるが細部が崩れることがある） |

- **`--text-encoder` と `--vae` は毎回付ける**。前のモデル（Anima など）のモジュールが残ると `You do not have Qwen3.5 state dict!` で失敗する。モジュール名（`sdctl modules` の左列）でもフルパスでも指定できる
- Base を使うなら `--model moss-image_moss_image_base_bf16`
- MOSS-Image から Anima / Illustrious に戻すときは、そちらのモジュール指定が要る（Illustrious なら `params.yaml` の `override_settings` に `forge_additional_modules: []`）。詳細は `sd-generate` スキル
- seed を固定して比べるときは `--seed <n>` を付ける
- 生成後、レイアウトなら `overlay_layout.py` で枠を重ねて位置を確認できる

出力時に、選んだ書き方とその理由、未検証の要素（3 人以上のレイアウト、推奨ネガティブなど）を使っている場合はその旨を添える。
