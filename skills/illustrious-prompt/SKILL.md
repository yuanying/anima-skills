---
name: illustrious-prompt
description: |
  Illustrious XL 系モデル（および WAI / illustrij / Raehoshi などの派生）向けに最適化された Danbooru タグ主体のプロンプトを生成するスキル。
  トリガー: "illustrious-prompt", "/illustrious-prompt", "illustriousプロンプト", "イラストリアス", "Illustriousのプロンプト生成", "illustrious prompt", "IL_"
  使用場面: (1) Illustrious 系モデルで画像を生成する前にプロンプトを作りたいとき、(2) 品質タグ・レーティングタグ・年代タグの並べ方がわからないとき、(3) 複数キャラの色移り（属性の混線）を抑えたいとき
---

Illustrious XL 系モデル向けのプロンプトをインタラクティブに組み立てます。

対象モデル: Illustrious XL v0.1 / v1.0 / v1.1 / v2.0 と、その派生（`IL_` プレフィックスのチェックポイント全般。WAI-ILLUSTRIOUS、illustrij、Raehoshi illust XL など）。

## タグ検索エンジンの使い方

Danbooru タグをキーワード（英語・日本語）で検索できます:

```bash
python skills/illustrious-prompt/scripts/tag_search.py "long hair" --limit 5
python skills/illustrious-prompt/scripts/tag_search.py "青い目" --limit 5
python skills/illustrious-prompt/scripts/tag_search.py "セーラー服" --limit 3 --underscore
```

- 出力は JSON 配列。`tag` はスペース区切り（`--underscore` でアンダースコア形式）
- **括弧は自動でエスケープされる**（`artoria pendragon \(fate\)`）。そのままプロンプトに貼れる
- `post_count` はそのタグの学習量の目安。**数百件未満のタグは効きが弱い**と判断する
- タグの確信がない場合はプロンプト組み立て前に必ず検索して確認する

タグデータ（`tags.json`）は `anima-prompt` スキルと共有している。見つからない場合は
`python skills/anima-prompt/scripts/build_data.py` で生成する。

---

## Illustrious プロンプト規則（厳守）

### 大前提: Anima とも Pony とも書き方が違う

同じ「アニメ系モデル」でも作法が正反対の項目がある。**Anima のクセを持ち込まない**。

| 項目 | Anima | **Illustrious** | Pony |
|---|---|---|---|
| 主体 | 自然文 + タグ | **Danbooru タグ主体**（自然文は補助） | タグ |
| `BREAK` | 効果なし | **効く**（チャンク分割） | 効く |
| 重み付け | 1.5〜2.0 が必要 | **1.05〜1.3。1.5 超は破綻** | 1.1〜1.4 |
| 品質タグ | `masterpiece, best quality` | `masterpiece, best quality, amazing quality` | `score_9, score_8_up, ...` |
| `score_*` | `score_7` のみ | **使わない** | 必須 |
| アーティスト | `@wlop` | **`@` を付けない**（Danbooru の artist タグ名そのまま） | `by wlop` 等 |
| CFG | 4〜5 | **4.5〜7（5〜5.5 が中心）** | 7 前後 |
| Clip skip | — | **2 必須** | 2 |

### プロンプト構造（固定順序）

先頭にあるタグほど強く効き、後ろに行くほど薄まる。この順で並べる:

```
<quality>, <aesthetic>, <year>, <rating>,
<artist>,
<count>, <character name \(series\)>,
<外見タグ（上から下へ）>,
<expression>, <pose / action>,
<composition / camera>,
<background / environment>,
<lighting / effects>,
<resolution>
```

- 行分けは可読性のためで、モデルにとってはカンマ区切りの一続きと同じ。**空行は入れない**
- `<>` は指定があるときだけ埋める。埋めるものが無い項目は行ごと省く（空のカンマを残さない）
- **絶対に描きたいもの（キャラ名・決め要素）は前方に置く**。後半に置くと薄まる

### タグ記法

- 全て**小文字・カンマ区切り**
- 単語の区切りは**スペース推奨**（`long hair`）。アンダースコア（`long_hair`）でも通るが、**一つのプロンプト内では必ずどちらかに統一する**
- **括弧は必ずバックスラッシュでエスケープする**: `hatsune miku \(vocaloid\)`
  - エスケープしないと `(vocaloid)` が**重み付け構文として解釈され**、キャラ指定が壊れる
  - 検索スクリプトの出力はエスケープ済み
- アーティストタグに `@` を付けない（`@` は Anima の記法）
- `score_9` などのスコアタグは**使わない**（Pony 用。Illustrious では品質が下がる）
- 人物は `woman` / `man` ではなく **`1girl` / `1boy`** を使う（学習タグそのもの）
- 自然文は v1.1 以降で 5 割程度しか効かない。**タグで書けるものはタグで書く**。自然文はタグの隙間を埋める補助（`leaning against wall`、`glowing eyes under hair` のような短い句）に留める

### 品質タグ・aesthetic・年代・レーティング

プロンプト**先頭**にこのブロックを置く。

**品質タグ**（強→弱）: `masterpiece`, `best quality`, `amazing quality`, `good quality`, `normal quality`, `bad quality`, `worst quality`

既定は上位3つ:
```
masterpiece, best quality, amazing quality
```

**aesthetic タグ**（学習時の美的スコア帯に対応。任意）:

| タグ | スコア帯 |
|---|---|
| `very aesthetic` | 0.71 超 |
| `aesthetic` | 0.45〜0.71 |
| `displeasing` | 0.27〜0.45 |
| `very displeasing` | 0.27 以下 |

`very aesthetic` を足すと整った絵になるが、構図が無難になりやすい。既定では入れず、絵が荒れるときに足す。

**年代タグ**（絵柄の年代を決める。学習データの投稿年に対応）:

| タグ | 年代 |
|---|---|
| `newest` | 2021〜2024 |
| `recent` | 2018〜2020 |
| `mid` | 2015〜2017 |
| `early` | 2011〜2014 |
| `oldest` | 2005〜2010 |

既定は `newest`（現代的な絵柄）。レトロな絵柄が欲しいときだけ `early` / `oldest` を指定する。
**`early` / `oldest` を狙う場合は、ネガティブから `oldest, early` を必ず外す**（標準ネガティブに含まれているため打ち消し合う）。

**レーティングタグ**: **勝手に決めず、必ずユーザーに確認する**（フェーズ1 ステップ5）。既定値は設けない。

| タグ | 用途 |
|---|---|
| `safe` | 全年齢向け |
| `sensitive` | 軽い色気・肌見せ・水着 |
| `nsfw` | 成人向け方向 |
| `explicit` | 強い成人向け方向 |
| （指定なし） | レーティングタグを入れない。モデルの既定挙動に任せる |

- Danbooru 由来の `general` / `questionable` も部分的に反応するが、Illustrious 系では上の4語がよく通る
- レーティングタグはポジティブ側にのみ置く。**対になるタグをネガティブに入れない**
- **未成年風の出力を確実に避けたい場合**は、ポジティブに `mature female` / `adult` を足し、ネガティブに `loli, shota, child, aged down` を足す（完全ではない）

**解像度タグ**（プロンプト末尾。任意）: `absurdres`, `highres`

### 重み付け

SDXL 標準の括弧記法が使える。**Illustrious は重みに敏感で、盛ると即破綻する**。

```
(blue eyes:1.2)          効かせたいとき
(background:0.8)         弱めたいとき
```

- 実用域は **1.05〜1.3**。**1.5 を超えると色が焼けて崩れる**
- Anima の感覚（1.5〜2.0）を持ち込まない
- `(bad)` = 1.1倍、`[abstract]` = 0.9倍 の略記も使える
- 重みで殴る前に、**タグを前方に移動する**方が安全で効果が高い

### トークンと BREAK

CLIP は 75 トークン単位のチャンクで処理される。`BREAK` は**そこまでを1チャンクとして埋め、次のチャンクを開始する**キーワードで、Illustrious（A1111 / Forge）では正しく機能する。

- **タグの塊どうしを干渉させたくないとき**に `BREAK` を挟む（複数キャラが主用途）
- `BREAK` の前後に空行を入れない
- チャンクを増やせばトークン制限は事実上回避できるが、**チャンクをまたぐと関連付けが弱まる**。1キャラ = 1チャンクに収める
- `BREAK` は**領域を指定しない**。「左のキャラ」を確実に左に置きたい場合は Forge Couple / Regional Prompter などの拡張が要る

### 複数キャラクターの描き分け

Illustrious の最大の失敗要因は**属性の混線（色移り）**。プロンプトだけで完全には防げないことを前提に、確率を上げる。

**方式A: BREAK ブロック（既定・2〜3人向け）**

```
masterpiece, best quality, amazing quality, newest, safe,
2girls, sitting on a bench, park, daytime,
BREAK
1girl, blonde hair, twintails, blue eyes, white dress, smile, sitting,
BREAK
1girl, black hair, short hair, red eyes, black hoodie, expressionless, sitting
```

- 共通ブロックに**総人数**（`2girls`）、各ブロックに**`1girl`** を置く
- 共通ブロックには全体の場所・行為・構図だけを書き、外見は書かない
- 各ブロックの中で `1girl` を先頭に置き、その直後にそのキャラの外見を並べる
- 各ブロックに**分身が出る**場合は、各ブロックを `1girl, solo,` で始めるか、背景タグの重みを下げる

**方式B: エスケープ括弧グルーピング（1チャンクに収めたいとき）**

```
2girls, 1girl \(blonde hair, blue eyes, white dress\), 1girl \(black hair, red eyes, black hoodie\), park, daytime
```

- 主体タグと `\(` の間に**カンマを入れない**
- 完全一致率は 2〜3割程度。**要素を増やすほど崩れる**ので各キャラ3〜4タグまで
- 同性2人のときはキャラ名を主体タグ代わりに使える（`hatsune miku \(...\), kagamine rin \(...\)`）

**共通の混線対策**:

- キャラを区別する属性を**対照的**にする（金髪×黒髪、白×黒。似た色同士は必ず混ざる）
- 各キャラの記述量を**揃える**（片方だけ長いと、長い方の属性が全体に染み出す）
- ネガティブに `feature bleeding, mixed hair colors, swapped outfits, duplicate, clone, twins` を足す
- **4人以上をプロンプトだけで描き分けるのは非現実的**。Regional Prompter / Forge Couple、または生成後の inpaint を案内する

### キャラクター外見の記述（上から下へ）

各キャラのタグはこの順に並べる:

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

### 既存キャラクターの再現

Illustrious は Danbooru のキャラクター名を直接知っている。**キャラ名タグが使えるなら、外見タグを並べるより圧倒的に強い**。

- 判定基準: **Danbooru の post_count が 100 以上**なら名前だけで出る見込みが高い。数十件なら外見タグの補強が要る。数件なら LoRA が必要
- 書式は `character name \(series\)`。検索スクリプトの出力をそのまま使う
- 知識のカットオフに注意: **v0.1 は 2023年末まで / v1.0 以降は 2024年6月まで**。それ以降のキャラ・タグは知らない
- キャラ名を使う場合、その**キャラ本来の髪色・目の色のタグは書かない**（衣装違いなど、意図的に変える場合のみ書く）

### 構図・カメラ

```
shot size, camera position, camera angle, focus, composition
```

公式は**強い構図タグの多用を避けるよう明記している**。`close-up` / `upside-down` / `cowboy shot` を重ねると互いに衝突して品質が落ちる。

- 迷ったら `portrait` / `upper body` / `full body` のいずれか**1つだけ**使う
- 角度は `from above` / `from below` / `from side` から1つ
- ダイナミックにしたいとき: `dynamic angle, dutch angle, foreshortening, depth of field`

### 背景・光・エフェクト

背景は場所だけでなく時間・天候・小物も入れる（弱い例 → 強い例）:
```
beach, sunset
→
beach, ocean, palm tree, sunset, orange sky, cloud, wet sand
```

光・エフェクトはプロンプト後半にまとめる:
```
backlighting, rim light, lens flare, depth of field, bokeh, volumetric lighting, cinematic lighting
```

### アーティストタグ

- **Danbooru の artist タグ名をそのまま**書く（`@` や `by` を付けない）
- 置き場所は品質ブロックの直後か、プロンプト末尾。**先頭に近いほど画風が強く出る**
- **Danbooru の投稿数が少ない絵師（〜20件程度）は画風が乗らない**。その場合は LoRA が必要
- 効きが強すぎるときは `(artist name:0.8)` で弱める
- **ユーザーが指定しなかった場合はアーティストタグを入れない**。勝手に絵師名を補わない
- 複数混ぜると画風が中和されて不安定になる。混ぜるなら 2 名までで、重みで比率を調整する

### ネガティブプロンプト

Illustrious は**ネガティブがポジティブと同じくらい効く**。短すぎると品質が出ない。

**標準（既定はこちら。公式ガイド由来）**:
```
lowres, (bad), text, error, fewer, extra, missing, worst quality, jpeg artifacts, low quality, watermark, unfinished, displeasing, oldest, early, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract]
```

**短縮版（プロンプトを軽くしたいとき）**:
```
lowres, bad quality, worst quality, jpeg artifacts, signature, watermark, username, text, bad hands, extra digits
```

**状況別の追加**:

| 状況 | 追加するタグ |
|---|---|
| 手足が崩れる | `bad hands, bad anatomy, extra digits, fewer digits, missing fingers, anatomical nonsense` |
| 複数キャラの色移り | `feature bleeding, mixed hair colors, swapped outfits, duplicate, clone, twins` |
| コマ割り・複数カットが出る | `multiple views, comic, 2koma, 4koma, panel layout` |
| 白黒・線画になる | `monochrome, greyscale, sketch, lineart` |
| 検閲・ロゴが乗る | `censored, mosaic censoring, bar censor, patreon logo, artist name` |
| 意図せず幼く見える | `loli, shota, child, aged down` |

**注意**: レトロな絵柄を狙うとき（`early` / `oldest` をポジティブに入れたとき）は、標準ネガティブから `oldest, early` を必ず外す。

### 解像度

| アスペクト比 | width × height |
|---|---|
| 1:1 | 1024 × 1024 |
| 3:4 | 896 × 1152 |
| 4:3 | 1152 × 896 |
| 2:3 | 832 × 1216 |
| 3:2 | 1216 × 832 |
| 9:16 | 768 × 1344 |
| 16:9 | 1344 × 768 |

- 幅・高さとも **64 の倍数**にする（SDXL の学習バケットに合わせる）
- **既定は総画素 約1MP（1024×1024 相当）**。派生モデルの大半は 1024 系で学習されているため、いきなり 1536 を指定すると**キャラが二重に出る**
- 1536 級（`1536×1536` / `1248×1824` / `1824×1248`）を狙えるのは **本家 v1.0 以降**。派生モデルで高解像度が欲しい場合は 1MP で生成して **Hires. fix** で上げる

### モデルの限界（プロンプトで解決できないもの）

- **写実は苦手**。アニメ・イラスト特化。`photorealistic` を積んでも効果は薄い（realistic 系のマージモデルを使う）
- **文字描画は短い単語まで**。長文の看板・本文は破綻する
- **複数キャラの完全な描き分けは不可能**。プロンプトは確率を上げるだけで、最終的には inpaint か領域指定拡張が要る
- 知識カットオフ以降のキャラ・作品・絵師は知らない（v0.1: 2023年末 / v1.0以降: 2024年6月）

---

$ARGUMENTS

## フェーズ1: 情報収集（1問ずつ確認）

`$ARGUMENTS` と会話の文脈からすでに判明している項目はスキップする。

### ステップ1: キャラクター数と構成
何人描くかを確認する。**4人以上はプロンプトだけでは描き分けられない**ことをこの時点で伝え、Regional Prompter / inpaint の併用を案内する。

### ステップ2: キャラクター情報

各キャラクターについて以下を確認する。**2人以上の場合は1人ずつ順に聞き、まとめて聞かない**（属性が混ざるため）。

- キャラクター名（作品名）: 例「初音ミク（ボーカロイド）」「オリジナルキャラ」
- 外見: 髪型・髪色・目の色など（服装は含めない）
- 服装・小物（省略可）
- そのキャラの動作・表情

既存キャラの名前が挙がった場合は、**先にタグ検索で post_count を確認する**。100 未満なら「名前だけでは出にくいので外見タグで補強する」と伝える。

複数人の場合は、**区別する属性が対照的かを確認する**。似た髪色・似た服装を指定されたら、混線しやすい旨を伝えたうえでユーザーの判断を仰ぐ。

### ステップ3: シーン・構図
どこで何をしている場面か、どんな構図（引き/寄り、カメラ角度）かを確認する。

### ステップ4: 画風（アーティストタグ・年代）
好みの絵師名か絵柄の年代を確認する（省略可）。

- **ユーザーが指定しなかった場合はアーティストタグを入れない**
- 年代の指定がなければ `newest` を既定にする

### ステップ5: レーティングタグ
`safe` / `sensitive` / `nsfw` / `explicit` / 指定なし のどれにするかを**必ずユーザーに確認する**。
勝手に `safe` を補わない。「指定なし」を選ばれた場合はレーティングタグ自体を省く。

### ステップ6: 背景・ライティング
背景や光源の要望を確認する（省略可）。

### ステップ7: アスペクト比
「解像度」の表から選ぶ（省略時は `1:1` = 1024×1024）。

---

## フェーズ2: タグ検索（必要に応じて）

収集した情報をタグに変換する際、確信がないタグは検索して確認する。
必要最小限にとどめ、全タグを検索する必要はない。

```bash
# キャラクター名の存在と学習量を確認（複数キャラ時は必須）
python skills/illustrious-prompt/scripts/tag_search.py "初音ミク" --limit 3
# 服装タグを確認
python skills/illustrious-prompt/scripts/tag_search.py "セーラー服" --limit 3
```

---

## フェーズ3: プロンプト組み立て

### ヘッダブロックの構成

```
masterpiece, best quality, amazing quality, <aesthetic>, <year>, <rating>
```

- `<aesthetic>` は既定では入れない（荒れるときだけ `very aesthetic`）
- `<year>` の既定は `newest`
- `<rating>` はステップ5 の回答。「指定なし」なら省き、末尾のカンマも残さない

### count の決定

| 人数 | タグ |
|---|---|
| 1人 | `1girl, solo` / `1boy, solo` |
| 2人 | `2girls` / `2boys` / `1girl, 1boy` |
| 3人以上 | `<N>girls` / `<N>boys`（混合なら多い方から並べる。例: `2girls, 1boy`） |

1人のときは `solo` を必ず添える（背後に人影が出るのを防ぐ）。

### 最終チェック

組み立て後、出力前に以下を確認する:

- [ ] 括弧が全て `\(` `\)` にエスケープされているか
- [ ] `score_*` タグが混ざっていないか
- [ ] アーティストタグに `@` が付いていないか
- [ ] 重みが 1.3 を超えていないか
- [ ] 複数キャラのとき、共通ブロックに総人数・各ブロックに `1girl` があるか
- [ ] ポジティブに `early` / `oldest` を入れたなら、ネガティブから同じ語を外したか
- [ ] スペース区切りとアンダースコアが混在していないか

---

## フェーズ4: 出力

### 出力1: prompt.yaml

YAML はリテラルブロック `|` を使い、改行をそのまま保持する（改行はカンマ区切りと等価で、可読性のためだけに入れる）。

```yaml
prompt: |
  masterpiece, best quality, amazing quality, <year>, <rating>,
  <artist>,
  <count>, <character name \(series\)>,
  <外見タグ>,
  <expression>, <pose / action>,
  <composition / camera>,
  <background / environment>,
  <lighting / effects>,
  absurdres
negative_prompt: "<negative>"
```

**完成例（1人・既存キャラ）:**

```yaml
prompt: |
  masterpiece, best quality, amazing quality, newest, safe,
  1girl, solo, hatsune miku \(vocaloid\),
  white shirt, black pleated skirt, cardigan,
  smile, looking at viewer, sitting, holding book,
  upper body, from side, depth of field,
  indoors, classroom, window, afternoon sunlight,
  absurdres
negative_prompt: "lowres, (bad), text, error, fewer, extra, missing, worst quality, jpeg artifacts, low quality, watermark, unfinished, displeasing, oldest, early, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract]"
```

キャラ名タグを使っているので、髪色・目の色は書いていない（`hatsune miku \(vocaloid\)` に含まれる）。制服も原作と違うものを指定しているので明示している。

**完成例（2人・BREAK 方式）:**

```yaml
prompt: |
  masterpiece, best quality, amazing quality, newest, safe,
  2girls, studying together, wooden table, indoors, library, bookshelf, warm lighting,
  upper body, depth of field,
  BREAK
  1girl, blonde hair, long hair, wavy hair, blue eyes, white blouse, cardigan, smile, pointing,
  BREAK
  1girl, black hair, short hair, red eyes, red jacket, confused, holding notebook,
  absurdres
negative_prompt: "lowres, (bad), text, error, fewer, extra, missing, worst quality, jpeg artifacts, low quality, watermark, unfinished, displeasing, oldest, early, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract], feature bleeding, mixed hair colors, swapped outfits, duplicate, clone, twins"
```

共通ブロックに場所・行為・構図、各 `BREAK` ブロックに1人分だけを書いている。金髪×黒髪、白系×赤系と対照的にして混線を抑えている。

出力時に**混線・二重生成が起きやすい構成であること**と、その場合の対処（各ブロックを `1girl, solo` で始める / inpaint する）を必ず添える。

### 出力2: sdctl コマンド

Illustrious 系は `IL_` プレフィックスのモデル。**VAE / text encoder は付けない**。

```bash
sdctl txt2img --prompt prompt.yaml \
  --model IL_<model_name> \
  --width <w> --height <h> \
  --steps 28 \
  --cfg-scale 5.5 \
  --sampler "Euler a" \
  --scheduler "karras" \
  -o <output>.png
```

**生成パラメータの推奨範囲**:

| パラメータ | 推奨 |
|---|---|
| steps | 20〜28（複雑な構図は 40 まで） |
| CFG scale | 4.5〜7（**5〜5.5 が中心。7.5 超は色が焼ける**） |
| sampler | `Euler a`（既定） |
| scheduler | `karras` |
| Clip skip | **2**（下記参照） |

**Clip skip 2 の設定**: `sdctl` に専用フラグはないため、`params.yaml` の `override_settings` で指定する。**Anima 系から切り替える場合は `forge_additional_modules: []` で残留モジュールをクリアする**（クリアし忘れると真っ黒な画像が出る）。

```yaml
override_settings:
  sd_model_checkpoint: "IL_<model_name>"
  forge_additional_modules: []
  CLIP_stop_at_last_layers: 2
```

**サンプラーの選び分け**:

| サンプラー | 特性 |
|---|---|
| `Euler a` | 既定。Illustrious 系で最も安定。線が柔らかい |
| `DPM++ 2M` | 線がシャープ。ディテール寄り |
| `DPM++ 2M SDE` | 変化に富むがブレやすい。バリエーション探索向け |

**高解像度化**: 1MP で生成したあと Hires. fix で上げる。`--hires-fix --hr-scale 1.5 --hr-upscaler "Latent (nearest)" --hr-denoise 0.35` を目安にする（詳細は `sd-generate` スキル）。

`params.yaml` がある場合は `--params params.yaml` を追加するよう案内する。
