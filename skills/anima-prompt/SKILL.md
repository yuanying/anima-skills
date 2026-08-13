---
name: anima-prompt
description: |
  Anima（circlestone-labs/Anima）向けの最適化されたプロンプトを生成するスキル。人数の制限なく、位置ごとにキャラクターを描き分ける。
  トリガー: "anima-prompt", "/anima-prompt", "animaプロンプト", "Animaのプロンプト生成", "anima prompt"
  使用場面: (1) Animaモデルで画像を生成する前にプロンプトを作りたいとき、(2) 複数キャラクターの構成を整理したいとき、(3) タグ構造がわからないとき
---

Anima モデル向けのプロンプトをインタラクティブに組み立てます。

## タグ検索エンジンの使い方

Danbooru タグをキーワード（英語・日本語）で検索できます:

```bash
python skills/anima-prompt/scripts/tag_search.py "long hair" --limit 5
python skills/anima-prompt/scripts/tag_search.py "青い目" --limit 5
```

出力は JSON 配列。`tag` フィールドはスペース区切り（Anima 形式）で返ります。
タグの確信がない場合はプロンプト組み立て前に検索して確認する。

---

## Anima プロンプト規則（厳守）

### プロンプト構造（固定順序）

全体シーンを1文で述べ、そのあと各キャラクターを「位置ブロック」に分けて記述する。**インデントは意味のある構造なので必ず入れる**（キャラブロック内は半角スペース4つ）。

```
<quality, meta, year, safety>,
<count>,
<全体シーンを述べる1文>
<位置語>,
    <そのキャラを述べる1文（外見 + 服装 + 動作）>
    <対応する Danbooru タグ列>,
<位置語>,
    <...>            ← キャラの数だけ繰り返す
<@artist>, <style>,        ← 任意。指定がなければ行ごと省く
<camera, composition>,
<environment, lighting>
```

`<>` は指定があるときだけ埋める。**任意の行に埋めるものが無ければ、その行ごと省く**（空のカンマを残さない）。

キャラクターの人数に上限はない。ただし人数が増えるほど属性の混線が起きやすくなる（後述）。

### タグ記法

- 全て**小文字・スペース区切り**（アンダースコア不使用）
- 例外: `score_7`, `score_1` 等のスコアタグのみアンダースコア
- アーティストタグは `@` 必須: `@wlop`, `@fkey`（`@` がないと効果が極めて弱い）
- キャラクター名の作品名は括弧: `hatsune miku (vocaloid)`
- `BREAK` タグは Anima では効果なし → 使用しない
- GelbooruとDanbooruでタグが異なる場合はGelbooru優先
- **代名詞（`he` / `she` / `it`）は自然文で使わない**。Anima は指示対象の解決が苦手で、特に `it` は何を指すか解釈できない。`the girl on the left`, `the plate` のように名詞で書く

### 重み付け

括弧記法は使えるが、**Anima は SDXL より高い重みを必要とする**。SDXL の感覚で `(chibi:1.2)` と書いてもほぼ効かない。

```
(chibi:2)
```

効かせたい要素は 1.5〜2.0 を目安にする。

### 品質タグ

公式推奨の既定はこれ:

```
masterpiece, best quality, score_7, highres, newest, year 2025
```

> **重要**: `score_9`, `score_8` を積むのは避ける。Anima の Aesthetic 版は既に高品質側に調整済みで、`score_*` タグを重ねると**逆に品質が劣化する**（公式 README 明記）。また `score_9` / `score_8` は Pony v7 のバイアスを引き継ぎ NSFW 方向に振れることがある。
>
> - **Aesthetic 版 / Turbo 版**: `score_*` を全て省略し、`masterpiece, best quality` とアーティストタグで制御する
> - **Base 版**: `score_7` のみ付ける

人間評価系の品質タグ（強→弱）: `masterpiece`, `best quality`, `good quality`, `normal quality`, `low quality`, `worst quality`

### 安全タグ

**勝手に決めず、必ずユーザーに確認する**（フェーズ1 ステップ6）。既定値は設けない。

| タグ | 用途 |
|---|---|
| `safe` | 全年齢向け |
| `sensitive` | 軽い色気・肌見せ |
| `nsfw` | 成人向け方向 |
| `explicit` | 強い成人向け方向 |
| （指定なし） | 安全タグを入れない。モデルの既定挙動に任せる |

安全タグはポジティブ側にのみ置く。**対になるタグをネガティブに入れない**（`safe` を選んだからといって `nsfw, explicit` をネガティブに足したりしない）。

### キャラクター外見の記述（上から下へ）

キャラブロックのタグ列はこの順に並べる。自然文側も概ねこの順に沿わせる。

```
skin/ears/horns/halo/wings,
hair color, hair length, hair style,
eyes, pupils, eyelashes, eyebrows,
expression,
neckwear,
upper clothes,
lower clothes,
legwear,
shoes,
accessories/tail/wings
```

衣装はタグだけでなく素材・構造の説明文も有効:
```
white flowy maxi dress with layered chiffon skirt, delicate lace trim
```

### 手・ポーズの制御

手・腕の役割を左右で明示すると安定する:

```
# 悪い例（皿を持つ手がピースしてしまう）
holding plate, v sign

# 良い例
left hand holding a plate, right hand making a v sign beside the face, both hands clearly visible
```

手が崩れる場合は**ポジティブ側で指を明示**すると安定する（ネガティブに列挙するだけでは足りない）:
```
fingers, fingernails, both hands clearly visible
```

4本指・3本指キャラ:
```
exactly four fingers on each hand, four digits on each hand, thumb and three fingers, no fifth finger
```

### キャラクターの描き分け（重要）

複数キャラクターの最大の失敗要因は**属性の混線**（片方の髪色がもう片方に移るなど）。これを防ぐのが位置ブロック構造の目的。

- 人数タグを品質タグの直後に必ず明示する
- キャラクターごとに「**位置語 + 1文の説明 + タグ列**」を一塊にし、他のキャラの記述を挟まない
- **キャラクター名を出す場合は、名前の直後にそのキャラの外見を続けて書く**。名前だけを並べるとモデルが「誰がどの外見か」を取り違える（公式 README 明記）
- キャラクターを区別する属性が**対照的**（黒髪×金髪など）な方が安定
- **3人までは安定**。4人以上は可能だが試行錯誤が必要
- 特定のキャラだけに小物を付けたい場合は、タグではなく**自然文で所属を書く**（`the girl on the left is wearing glasses`）

**位置語**: 各キャラブロックの見出しになる。人数と構図に応じて選ぶ。

| 構図 | 位置語 |
|---|---|
| 2人 | `On the left,` / `On the right,` |
| 3人 | `On the left,` / `In the center,` / `On the right,` |
| 4人以上 | `On the far left,` / `Second from the left,` / `Second from the right,` / `On the far right,` |
| 奥行き | `In the foreground,` / `In the background,` |
| 1人 | 位置語は使わない（全体シーン文の直後にキャラブロックを置く） |

**キャラブロックの中身**: 1行目が自然文、2行目が Danbooru タグ列。両方をインデントして、どのキャラに属する記述かを視覚的に固定する。

```
On the left,
    a lively girl with short black hair wearing a red bomber jacket looks slightly confused at her notebook.
    1girl, short hair, black hair, red jacket, bomber jacket, confused, holding notebook,
```

- 自然文は「印象 + 髪 + 服 + 動作」の順。タグにない語彙（`ash blonde`、素材や質感の説明など）はここで自由に書いてよい
- タグ列は自然文の内容を Danbooru 語彙に写したもの。**先頭に `1girl` / `1boy` を置いて所属を明示する**
- タグ列は自然文の言い換えであり、矛盾させない

### カメラ・構図

```
shot size, camera position, camera angle, lens, focus, composition
```

ダイナミック化に便利なタグ:
```
dynamic diagonal composition, extreme dutch angle, dramatic perspective, strong foreshortening, foreground blur, layered depth
```

### 背景・光・エフェクト

背景は場所だけでなく時間・天候・小物・奥行きも含める（弱い例 → 強い例）:
```
beach, sunset
→
beach, beach waves, orange sky, sparkling sea surface, wet sand, palm trees, sunset haze
```

光・エフェクトはプロンプト後半にまとめる:
```
backlighting, rim light, lens flare, depth of field, bokeh, volumetric lighting
```

### 全体シーン文

人数タグの直後に置く**必須要素**。「誰が・どこで・何をしているか」を1文で述べ、後続の位置ブロックの土台にする:
```
Three characters are studying together at a wooden table inside a quiet library.
```

- **1文に収める**。ここで各キャラの外見を書き込まない（それは位置ブロックの仕事）
- 場所・全体の行為・空気感までにとどめる

自然文とタグ列は隣接させ、**間に空行を入れない**（空行が入ると追従性が落ちる）。改行とインデントは構造として必要なので入れてよい。

### ネガティブプロンプト

**基本（公式推奨・既定はこちら）**:
```
worst quality, low quality, score_1, score_2, score_3, artist name, blurry, jpeg artifacts, chromatic aberration
```

Anima は CFG による本物のネガティブプロンプトを持つため、短くても効く。まずはこれで試す。

**拡張（崩れが出たときだけ足す）**:
```
early, old, cartoon, graphic, painting, crayon, graphite, abstract, glitch, deformed, mutated, ugly, disfigured, long body, bad anatomy, bad hands, missing fingers, extra fingers, extra digits, fewer digits, cropped, very displeasing, lowres, censor
```

**状況別の追加**:

| 状況 | 追加するタグ |
|---|---|
| 複数キャラ | `duplicate, twins, clone` |
| 手足が崩れる | 上記「拡張」の指・手系を全部（ポジティブ側の `fingers, fingernails` と併用） |
| 意図せず獣化する | `anthro, furry, animal ears` ※獣耳キャラを描く場合は除く |

### モデルの限界（プロンプトで解決できないもの）

- **写実は不可**。意図的にイラスト特化で訓練されている。`photorealistic`, `realistic` を積んでも効果は薄い
- **文字描画は単語〜短いフレーズまで**。長文の看板・本文などは破綻する
- プロンプトが短い・情報不足だと意図しない内容が出やすい。安全タグと十分な記述で防ぐ

---

$ARGUMENTS

## フェーズ1: 情報収集（1問ずつ確認）

`$ARGUMENTS` と会話の文脈からすでに判明している項目はスキップする。

### ステップ1: キャラクター数
何人のキャラクターを描くかを確認する。人数に上限はないが、4人以上は破綻しやすいことを伝える。

### ステップ2: キャラクター情報

各キャラクターについて以下を確認する。**2人以上の場合は1人ずつ順に聞き、まとめて聞かない**（属性が混ざるため）。

- 画面上の**位置**（左・中央・右・手前・奥など）※2人以上の場合のみ
- キャラクター名（作品名）: 例「初音ミク（ボーカロイド）」「オリジナルキャラ」
- 外見: 髪型・髪色・目の色・体型など（服装は含めない）
- 服装・小物（省略可）
- そのキャラの動作・表情

キャラクター名・作品名が不明な場合は外見説明のみでも可。

### ステップ3: シーン・構図
全員が**どこで何をしている**場面かと、どんな構図かを確認する。ここで得た答えが全体シーン文になる。
例: 「図書館で3人が一緒に勉強している」「全身立ち絵、カメラ目線」「2人で向き合っている」

### ステップ4: アーティストスタイル
好みの画師名か画風を確認する（省略可）。

- **ユーザーが指定しなかった場合はアーティストタグを入れない**。勝手に画師名を補わない（画風が意図せず固定され、モデル本来の画風が失われる）
- **2名以上は画面が不安定になるため1名を推奨**
- ユーザーから「おすすめは？」と聞かれた場合に限り候補を挙げる。`@fkey, @jima` の組み合わせは比較的安定した結果が出る実績がある
- アーティストタグで画風が決まる場合は `style` 系タグを重ねない（競合して不安定になる）

### ステップ5: 背景・環境・ライティング
背景や光源の要望を確認する（省略可）。

### ステップ6: 安全タグ
`safe` / `sensitive` / `nsfw` / `explicit` / 指定なし のどれにするかを**必ずユーザーに確認する**。
勝手に `safe` を補わない。「指定なし」を選ばれた場合は安全タグ自体をプロンプトから省く。

### ステップ7: アスペクト比
画像の比率を確認する（省略時は `1:1`）:

| アスペクト比 | width | height |
|---|---|---|
| 1:1 | 1024 | 1024 |
| 9:16 | 768 | 1344 |
| 16:9 | 1344 | 768 |
| 3:4 | 768 | 1024 |
| 4:3 | 1024 | 768 |
| 2:3 | 768 | 1152 |
| 3:2 | 1152 | 768 |

**解像度の制約**:
- 有効範囲は 512²〜1536² 相当。総画素は**約1MP（1024×1024 相当）を狙う**
- 幅・高さとも **16の倍数**にする
- 1MP の中でキャラが十分な面積を占めるように構図を決める（小さすぎると顔・手が崩れる）
- 21:9 〜 9:21 の極端な比率も一応動くが不安定

---

## フェーズ2: タグ検索（必要に応じて）

収集した情報をタグに変換する際、確信がないタグは検索して確認する。
必要最小限にとどめ、全タグを検索する必要はない。

例:
```bash
# 服装タグを確認したい場合
python skills/anima-prompt/scripts/tag_search.py "セーラー服" --limit 3
# ポーズタグを確認したい場合
python skills/anima-prompt/scripts/tag_search.py "hand on hip" --limit 3
```

---

## フェーズ3: プロンプト組み立て

収集した情報とタグ検索結果を組み合わせてプロンプトを組み立てる。

### quality_meta_year_safety の構成
```
masterpiece, best quality, score_7, highres, newest, year 2025, <safety_tag>
```

- Aesthetic 版 / Turbo 版を使う場合は `score_7` を落とす
- ステップ6 で「指定なし」を選ばれた場合は `<safety_tag>` ごと省き、末尾のカンマも残さない

### count の決定

| 人数 | タグ |
|---|---|
| 1人 | `1girl` / `1boy` |
| 2人 | `2girls` / `2boys` / `1girl, 1boy` |
| 3人以上 | `<N>people` に性別内訳を続ける（例: `3people, 2girls, 1boy`） |

性別内訳は同性のみなら1タグ（`3girls`）、混合なら多い方から並べる（`2girls, 1boy`）。

---

## フェーズ4: 出力

### 出力1: prompt.yaml

人数にかかわらず**このテンプレート1つ**を使う。意味単位ごとに改行し、キャラブロックの中身はインデント（4スペース）する。YAML はリテラルブロック `|` を使い、改行とインデントをそのまま保持する。

```yaml
prompt: |
  masterpiece, best quality, score_7, highres, newest, year 2025, <safety_tag>,
  <count>,
  <全体シーンを述べる1文>
  <位置語>,
      <キャラ1を述べる1文>
      <キャラ1のタグ列（1girl/1boy で始める）>,
  <位置語>,
      <キャラ2を述べる1文>
      <キャラ2のタグ列>,
  <@artist>, <style_tags>,
  <camera, composition>,
  <environment, lighting>
negative_prompt: "<negative>"
```

- キャラクター名がある場合は自然文の中で `hatsune miku (vocaloid)` の形で名指しする
- 1人の場合は位置語を省き、全体シーン文の直後にキャラブロック（インデント付き）を置く
- **ユーザーが指定しなかった任意項目は行ごと省く**。特に `<@artist>, <style_tags>` は指定がなければ丸ごと落とす
- 空行は入れない

**完成例（3人）:**

```yaml
prompt: |
  masterpiece, best quality, score_7, highres, newest, year 2025,
  3people, 2girls, 1boy,
  Three characters are studying together at a wooden table inside a quiet library.
  On the left,
      a lively girl with short black hair wearing a red bomber jacket looks slightly confused at the open notebook.
      1girl, short hair, black hair, red jacket, bomber jacket, confused, holding notebook,
  In the center,
      a gentle woman with long wavy ash blonde hair wearing a white blouse and a cardigan points at the notebook, teaching the girl on the left kindly.
      1girl, long hair, wavy hair, blonde hair, white blouse, cardigan, smile, pointing,
  On the right,
      an intellectual young man with black-framed glasses wearing a black turtleneck is deeply focused, reading a thick textbook.
      1boy, black-framed eyewear, black turtleneck, serious, reading, book,
  @wlop,
  upper body, from side, layered depth,
  indoors, library, wooden table, bookshelf, warm indoor lighting, depth of field
negative_prompt: "worst quality, low quality, score_1, score_2, score_3, artist name, blurry, jpeg artifacts, chromatic aberration, duplicate, twins, clone"
```

自然文には `ash blonde` のようにタグに存在しない語も使えるが、タグ列側は実在する Danbooru タグに落とす（この例では `blonde hair`）。確信がないタグは検索して確認する。

この例は**ユーザーが `@wlop` を指定した場合**のもの。安全タグと同様、アーティストタグも指定がなければその行ごと省く:

```yaml
prompt: |
  masterpiece, best quality, score_7, highres, newest, year 2025,
  1girl,
  A girl is standing in a sunlit classroom after school.
      a calm girl with long black hair in a sailor uniform looks out of the window.
      1girl, long hair, black hair, serafuku, looking to the side,
  upper body, from side,
  indoors, classroom, window, afternoon sunlight, depth of field
negative_prompt: "worst quality, low quality, score_1, score_2, score_3, artist name, blurry, jpeg artifacts, chromatic aberration"
```

### 出力2: sdctl コマンド

```bash
sdctl txt2img --prompt prompt.yaml \
  --width <w> --height <h> \
  --steps 30 \
  --cfg-scale 4.5 \
  --sampler "er_sde" \
  --scheduler "simple"
```

`params.yaml` がある場合は `--params params.yaml` を追加するよう案内する。

**生成パラメータの推奨範囲**: steps 30〜50 / CFG 4〜5。

**サンプラーの選び分け**:

| サンプラー | 特性 |
|---|---|
| `er_sde` | 既定。ニュートラルな画風・フラットな塗り・シャープな線 |
| `euler_a` | 線が柔らかい。CFG を高めにしても破綻しにくい |
| `dpmpp_2m_sde_gpu` | 変化に富むが不安定。バリエーション探索向け |
| `euler` | Turbo 版 / Aesthetic 版に向く |

結果が硬い・単調な場合は `euler_a`、構図を振りたい場合は `dpmpp_2m_sde_gpu` を提案する。
