---
name: anima-prompt
description: |
  Anima（circlestone-labs/Anima）向けの最適化されたプロンプトを生成するスキル。人数の制限なく、位置ごとにキャラクターを自然文で描き分ける。
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

**2 行で書く。** 1 行目に全体に関わるタグをまとめ、2 行目に全体シーン文と各キャラクターの自然文を **1 段落** で続ける。

```
<quality, meta, year, safety>, <count>, <キャラ名>, <@artist>, <style>, <scene tags>, <camera, composition>, <environment, lighting>.
<全体シーンを述べる1文> <位置語>, <キャラ1の名前>, <外見>, <服装>, <動作>. <位置語>, <キャラ2の名前>, <...>. <持ち物の持ち主を言い直す1文>
```

- 1 行目はタグのカンマ列挙で、末尾をピリオドで閉じる。`<キャラ名>` には登場キャラの名前（作品名つき、LoRA のトリガーなど）だけを並べ、外見は書かない
- 2 行目のキャラの文は「**位置語, 名前, 外見, 服装, 動作.**」の 1 文にする。キャラの数だけ続けるが、**改行・インデント・見出しで区切らない**
- キャラごとに持ち物があるときは、段落の最後に持ち主を 1 文で言い直す（任意。後述）
- `<>` は指定があるときだけ埋める。**埋めるものが無ければ、その項目ごと省く**（空のカンマを残さない）

キャラクターの人数に上限はない。ただし人数が増えるほど失敗が増える（後述）。

1 人の絵はこの検証の対象外なので、従来の形（「出力1」の「1人の場合」）を使う。

この構造は 2〜3 人で 9 通りの書き方を比べた検証（`docs/reports/2026-10-09-anima-multi-character/`）で決めた。この形（`hybrid-tags-nl`）は成功率 81% で 1 位、旧来の「位置語の見出し + インデントしたブロック」は 71% だった。修正後の再検証でも、この構造は旧来の形より多く成功した（同じ評価者による再判定で 73% と 65%）。相互作用のない 2 人並びでは、旧来の形が 4 枚とも左右 2 枚の分割コマになった。この構造では 1 枚もならなかった。

3 人以上でも、キャラごとの Danbooru タグ列は足さない。各キャラの文の直後にタグ列を足した形も試したが、3 人の構図の成功数・人数の正答率とも差が出なかった（成功は 20 枚中 11 枚と 12 枚）。

### タグ記法

- 全て**小文字・スペース区切り**（アンダースコア不使用）
- 例外: `score_7`, `score_1` 等のスコアタグのみアンダースコア
- アーティストタグは `@` 必須: `@wlop`, `@fkey`（`@` がないと効果が極めて弱い）
- キャラクター名の作品名は括弧: `hatsune miku (vocaloid)`
- `BREAK` タグは Anima では効果なし → 使用しない（検証でも、`BREAK` で区切ったタグ列の成功率は区切りなしと同じ 2% だった）
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

キャラの自然文の外見・服装はこの順に沿わせる（1 人の絵でタグ列を書く場合も同じ順）。

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

複数キャラクターの最大の失敗要因は**属性の混線**（片方の髪色・眼鏡・服の色がもう片方に移るなど）。これを防ぐのは**自然文**である。検証では、タグ列だけで書いた方式は人数こそ合うものの属性がキャラ間で入れ替わり、成功率は 2〜21% にとどまった。自然文でキャラを描写した方式は 71〜81% だった。

- 人数タグを 1 行目に必ず明示する
- **各キャラの外見・服装・動作は、自然文の 1 文に「位置語, 名前, 外見, 服装, 動作」の順でまとめる**。他のキャラの記述を挟まない
- **名前の直後に外見を続けるのは、自然文の中で行う**。公式 README の注意（名前だけを並べると誰がどの外見かを取り違える）は、タグ列の中で `<名前> with <外見タグ>` と書いても効かない（検証で成功率 4%）。自然文の中で名前と外見を隣接させると効く
- 区切り記号では混線を防げない。ラベルとコロン（`the girl on the left: <タグ列>`）、改行、`BREAK` でタグ列を区切っても、属性の正答率は 4〜44% だった
- キャラクターを区別する属性が**対照的**（黒髪×金髪、服の色を分けるなど）な方が安定
- **2人は安定、3人は失敗が増える**。3人では、人数が 4 人に増える失敗が最も多い（検証での成功は最良の書き方でも 20 枚中 13 枚）。4人以上は検証していない
- 特定のキャラだけに小物を付けたい場合は、タグではなく**自然文で所属を書く**（`the girl on the left is wearing glasses`）

**位置語**: 各キャラの文の先頭に置く。人数と構図に応じて選ぶ。

| 構図 | 位置語 |
|---|---|
| 2人 | `On the left,` / `On the right,` |
| 3人 | `On the left,` / `In the center,` / `On the right,` |
| 4人以上 | `On the far left,` / `Second from the left,` / `Second from the right,` / `On the far right,` |
| 上下 | `On top,` / `At the bottom,` |
| 奥行き | `In the foreground,` / `In the background,` |
| 1人 | 位置語は使わない |

**キャラの文の中身**:

```
On the left, kutara natsumi, a girl with black hair tied in a low ponytail, blunt bangs and round glasses, wearing a green turtleneck sweater and a brown long skirt, waves at the viewer with her right hand raised and smiles.
```

- 「位置語 → 名前 → 外見（髪・目など） → 服装 → 動作」の順。名前がないオリジナルキャラは `a girl with ...` から始める
- タグにない語彙（`ash blonde`、素材や質感の説明など）も自由に書いてよい
- 文と文の間は改行しない。**位置語を見出しにして改行・インデントでキャラごとに区切ると、相互作用のない並びで「キャラごとに別のコマ」の分割画像になることがある**（検証の 2 人並びで 4/4）

**持ち物の言い直し（任意）**: キャラごとに違う持ち物があるときは、段落の最後に持ち主を 1 文で言い直す。人物はキャラの文と同じ位置語の呼び名（`the girl on the left`）で指す。

```
The yellow umbrella belongs to the girl on the left, the blue balloon to the girl in the center, and the red book to the girl on the right.
```

- 検証では、3 人がそれぞれ違う物を持つ構図で、言い直しありが 4/4、なしが 2/4 だった
- 人物どうしの関係を言い直す文は、全体では効果が出なかった（言い直しありとなしで成功 35/48 と 36/48）。特に、`the girl with glasses` のような外見の呼び名で人物を言い直すと、別の人物と解釈されて人数が増えることがある（前景・遠景の構図で 4 人出現が 3/4。言い直しなしでは 0/4）。関係は全体シーン文と各キャラの動作で書けば足りる

### カメラ・構図

```
shot size, camera position, camera angle, lens, focus, composition
```

ダイナミック化に便利なタグ:
```
dynamic diagonal composition, extreme dutch angle, dramatic perspective, strong foreshortening, foreground blur, layered depth
```

複数人物の難しい構図でも、キャラを自然文で書けば多くは通る。検証では肩車、逆さまの人物と正立の人物、真上からの俯瞰、極端な煽り、向き合ってのハイタッチが、ほぼ毎回意図どおりになった。

一方、次の構図はプロンプトの書き方だけではほとんど成功しなかった。ユーザーに伝え、seed を多めに回すか、構図を変える・領域指定やポーズ参照（ControlNet など）を使うことを提案する。

- **3人の縦積み**（3 段の肩車タワー）: 段数が 4 段に増える、上下の順序や手の位置がそろわない
- **前景と遠景の極端なサイズ差**（手前に大きな顔、遠くに小さな全身）: 遠景の人物が大きすぎる、遠景に余分な人物が増える

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

2 行目の先頭に置く**必須要素**。「誰が・どこで・何をしているか」を1文で述べ、後続のキャラの文の土台にする:
```
Three characters are studying together at a wooden table inside a quiet library.
```

- **1文に収める**。ここで各キャラの外見を書き込まない（それはキャラの文の仕事）
- 場所・全体の行為・空気感までにとどめる

1 行目のタグと 2 行目の自然文は隣接させ、**間に空行を入れない**（空行が入ると追従性が落ちる）。

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
| 複数キャラ | `duplicate, twins, clone`（3人の構図で 4 人に増える失敗は、これを入れても残る） |
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
何人のキャラクターを描くかを確認する。人数に上限はないが、2人は安定、3人は人数が増えるなどの失敗が増え、4人以上はさらに破綻しやすいことを伝える。

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

2人以上は**このテンプレート**を使う。1 行目にタグ、2 行目に自然文の段落を置く。YAML はリテラルブロック `|` を使い、改行をそのまま保持する。

```yaml
prompt: |
  masterpiece, best quality, score_7, highres, newest, year 2025, <safety_tag>, <count>, <キャラ名>, <@artist>, <style_tags>, <scene_tags>, <camera, composition>, <environment, lighting>.
  <全体シーンを述べる1文> <位置語>, <キャラ1の名前>, <外見>, <服装>, <動作>. <位置語>, <キャラ2の名前>, <外見>, <服装>, <動作>. <持ち物の持ち主を言い直す1文>
negative_prompt: "<negative>"
```

- キャラクター名がある場合は 1 行目に名前だけを並べ、2 行目の各キャラの文で `hatsune miku (vocaloid), a girl with ...` のように名前の直後に外見を書く
- 2 行目は 1 段落。キャラの文の間で改行しない、インデントしない
- 持ち物の言い直しは、キャラごとの持ち物がなければ省く
- **ユーザーが指定しなかった任意項目は省く**。特に `<@artist>, <style_tags>` は指定がなければ丸ごと落とす
- 空行は入れない

**完成例（3人）:**

```yaml
prompt: |
  masterpiece, best quality, score_7, highres, newest, year 2025, 3people, 2girls, 1boy, @wlop, studying, upper body, from side, layered depth, indoors, library, wooden table, bookshelf, warm indoor lighting, depth of field.
  Three characters are studying together at a wooden table inside a quiet library. On the left, a lively girl with short black hair, wearing a red bomber jacket, looks slightly confused at the open notebook. In the center, a gentle woman with long wavy ash blonde hair, wearing a white blouse and a cardigan, points at the notebook and kindly teaches the girl on the left. On the right, an intellectual young man with black-framed glasses, wearing a black turtleneck, is deeply focused on reading a thick textbook. The open notebook belongs to the girl on the left, and the thick textbook belongs to the young man on the right.
negative_prompt: "worst quality, low quality, score_1, score_2, score_3, artist name, blurry, jpeg artifacts, chromatic aberration, duplicate, twins, clone"
```

この例は**ユーザーが `@wlop` を指定した場合**のもの。安全タグと同様、アーティストタグも指定がなければ省く。

**1人の場合:** 複数人の検証の対象外なので、従来の形のまま使う。全体シーン文の直後に、そのキャラの自然文 1 文と Danbooru タグ列をインデントして置く。

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

自然文には `ash blonde` のようにタグに存在しない語も使える。1 行目やタグ列に書くタグは実在する Danbooru タグに落とす。確信がないタグは検索して確認する。

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
