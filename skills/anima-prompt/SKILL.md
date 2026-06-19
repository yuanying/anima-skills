---
name: anima-prompt
description: |
  Anima（circlestone-labs/Anima）向けの最適化されたプロンプトを生成するスキル。1〜2人のキャラクターに対応。
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

### タグ構造（固定順序）

```
[quality/meta/year/safe] [count] [character+appearance] [series] [artist] [style] [tags] [environment] [nltags]
```

### タグ記法

- 全て**小文字・スペース区切り**（アンダースコア不使用）
- 例外: `score_9`, `score_8` 等のスコアタグのみアンダースコア
- アーティストタグは `@` 必須: `@wlop`, `@fkey`（`@` がないと効果が極めて弱い）
- キャラクター名の作品名は括弧: `hatsune miku (vocaloid)`
- `BREAK` タグは Anima では効果なし → 使用しない
- GelbooruとDanbooruでタグが異なる場合はGelbooru優先

### 品質タグ

```
masterpiece, best quality, score_9, score_8, score_7, highres, newest, year 2025
```

> **注意**: `score_9`, `score_8` は Pony v7 のバイアスを引き継ぎ、NSFW 方向に若干バイアスがかかることがある。スタイル維持を優先する場合は `score_7` のみ使用するか品質タグを省略してアーティストタグで制御する。

### 安全タグ（必須）

| タグ | 用途 |
|---|---|
| `safe` | 全年齢向け（ポジティブ必須。ネガティブに `nsfw, explicit` を追加） |
| `sensitive` | 軽い色気・肌見せ |
| `nsfw` | 成人向け方向 |
| `explicit` | 強い成人向け方向 |

### キャラクター外見の記述（上から下へ）

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
left hand holding a plate, right hand making a v sign beside her face, both hands clearly visible
```

4本指・3本指キャラ:
```
exactly four fingers on each hand, four digits on each hand, thumb and three fingers, no fifth finger
```

### 複数キャラクターの描き分け（重要）

- **3人まで**は適切な書き方で安定（5人も可能だが試行錯誤が必要）
- キャラクターを区別する属性が**対照的**（黒髪×金髪など）な方が安定
- 人数タグを品質タグの直後に必ず明示
- キャラクターごとに「**位置 + 外見 + 動作**」を一塊で記述
- ネガティブに `duplicate, twins, clone` を追加

**位置指定**:
- 左右: `On the left`, `On the right`
- 奥行き: `in the foreground`, `in the background`

**タグ形式**:
```
2girls, duo, holding each other's hands,

angel girl, red halo, long white hair, red eyes, red angel wings, black sundress,
devil girl, white horns, long black hair, blue eyes, blue demon wings, white sundress,

floating in midair, bodies facing each other
```

**自然言語形式（位置起点）**:
```
2girls. On the left is a girl with long black hair and blue eyes, wearing a dark blazer. On the right is a girl with short blonde hair and red eyes, wearing a white blouse.
```

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

### 自然言語補助（nltags）

タグで表現できない複雑な場面を最後の1文で補助する（**最大1文、安易に使わない**）:
```
A blonde woman kneels in shallow beach water while her white dress flows with the waves.
```

タグと自然言語の間で改行を入れない（追従性が落ちる）。

### ネガティブプロンプト

**基本**:
```
worst quality, low quality, early, old, score_1, score_2, score_3, cartoon, graphic, painting, crayon, graphite, abstract, glitch, deformed, mutated, ugly, disfigured, long body, bad anatomy, bad hands, missing fingers, extra fingers, extra digits, fewer digits, cropped, very displeasing, artist name, blurry, jpeg artifacts, lowres, censor
```

- `safe` の場合は末尾に `, nsfw, explicit` を追加
- 複数キャラの場合は末尾に `, duplicate, twins, clone` を追加

---

$ARGUMENTS

## フェーズ1: 情報収集（1問ずつ確認）

`$ARGUMENTS` と会話の文脈からすでに判明している項目はスキップする。

### ステップ1: キャラクター数
何人のキャラクターを描くかを確認する（1人 or 2人）。

### ステップ2: キャラクター情報

**1人の場合:**
- キャラクター名（作品名）: 例「初音ミク（ボーカロイド）」「オリジナルキャラ」
- 外見: 髪型・髪色・目の色・体型など（服装は含めない）
- 服装・小物（省略可）

**2人の場合:** 上記をキャラクター1・キャラクター2それぞれについて確認する。

キャラクター名・作品名が不明な場合は外見説明のみでも可。

### ステップ3: シーン・構図・ポーズ
何をしているシーンか、どんな構図かを確認する。
例: 「全身立ち絵、カメラ目線、笑顔」「上半身、本を読んでいる」「2人で向き合っている」

### ステップ4: アーティストスタイル
好みの画師名か画風を確認する（省略可）。**2名以上は画面が不安定になるため1名を推奨**。

### ステップ5: 背景・環境・ライティング
背景や光源の要望を確認する（省略可）。

### ステップ6: 安全レベル
`safe` / `sensitive` / `nsfw` / `explicit` のいずれかを確認する。

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

### quality_meta_year_safe の構成
```
masterpiece, best quality, score_9, score_8, score_7, highres, newest, year 2025, <safe_tag>
```

### count の決定

| 人数 | タグ |
|---|---|
| 1人（女性） | `1girl` |
| 1人（男性） | `1boy` |
| 2人（女性2） | `2girls` |
| 2人（男性2） | `2boys` |
| 2人（混合） | `1girl, 1boy` |

---

## フェーズ4: 出力

### 出力1: prompt.yaml

意味単位ごとに改行し、キャラクターブロック内のサブ要素はインデント（2スペース）する。

**1人の場合:**
```yaml
prompt: |
  masterpiece, best quality, score_9, score_8, score_7, highres, newest, year 2025, <safe_tag>,
  <count>,
  <character_name> (<series>),
    <appearance>,
    <clothing>,
  <@artist>,
  <style_tags>,
  <action, composition, expression, camera>,
  <environment, lighting>
negative_prompt: "<negative>"
```

**2人の場合:**
```yaml
prompt: |
  masterpiece, best quality, score_9, score_8, score_7, highres, newest, year 2025, <safe_tag>,
  <count>,
  <character1_name> (<series1>),
    <appearance1>,
  <character2_name> (<series2>),
    <appearance2>,
  <@artist>,
  <action, position_tags>,
  <environment, lighting>
negative_prompt: "<negative>"
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
