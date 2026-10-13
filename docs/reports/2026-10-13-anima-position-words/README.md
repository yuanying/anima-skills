# Anima の複数人プロンプトで「On the left,」を外すと何が変わるか

- 調査・生成日: 2026-10-13
- 対象モデル: [circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima) ベース版（`anima-base-v1.0`）
- キャラクター LoRA: `kutara_anima.v12`（3 キャラを 1 つの LoRA に学習させたもの）
- 前回の記事: [Anima で 2〜3 人を描き分けるプロンプトの書き方を 9 通り比べた](../2026-10-09-anima-multi-character/README.md)

## 要約

- 「`On the left,` のような位置語をキャラの文に付けると画面が分割されやすく、外したほうがカメラワークが柔軟になり、動作にも正確に従う」という仮説を検証した。位置語の書き方だけを変えた 4 通りのプロンプトを 13 シーン × 4 seed で生成し、計 208 枚を、書き方を伏せた 2 人の評価者で判定した。
- **仮説は全体としては支持されなかった。** 成功率は位置語あり（`pos-words`）54%、位置語なし（`no-pos`）50%、相対表現（`relational`）52%、全体シーン文にだけ位置を書く形（`scene-pos`）48% で、差は誤差の範囲だった。動作が主役の 4 シーンとカメラ指定のある 5 シーンでは、動作の正確さにもカメラへの従い方にも差が出なかった。同じ seed なら、書き方が違ってもほぼ同じ構図の絵になる。
- **分割コマについては、条件付きで支持された。** 相互作用のない 2 人が机に並んで別々のことをするシーンでは、位置語ありで 12 枚中 8 枚が左右 2 コマに分かれた。位置語を外すと 12 枚中 0 枚だった。ただし同じ型の別の 3 シーンでは、位置語ありでも分割は 1 枚も出なかった。
- **位置語を外すと悪くなる点もあった。** 3 人が絡むシーンでは服の色の混線が増えた（属性の正解は位置語ありで 8/8、なしで 3/8）。3 人がそれぞれ違う物を持つシーンでは、持ち物の持ち主が入れ替わった（成功 4/4 → 1/4）。
- 位置語を外しても、相互作用のない並びでは、文に書いた順に左から並んだ（48 枚中 47 枚）。
- この結果から、スキル `anima-prompt` では位置語を既定で残すことにした。そのうえで「相互作用のない並びで分割コマが出たら、位置語を外して左から順に書く」という対処を加えた。分割が出たシーンを新しい 8 seed で生成し直すと、修正前の形は 8 枚中 5 枚が分割され、書き直した形は 0 枚だった（[スキルへの反映と検証](#スキルへの反映と検証)）。

## 背景と目的

前回の記事では、2〜3 人を描き分けるプロンプトの書き方を 9 通り比べた。最も成功率が高かったのは、1 行目にタグ、2 行目に全体シーン文と各キャラの自然文を 1 段落で続ける形である。各キャラの文は「位置語, 名前, 外見, 服装, 動作.」の順にする。

```
On the left, kutara natsumi, a girl with black hair tied in a low ponytail, ..., waves at the viewer with her right hand raised and smiles.
```

前回の検証では、位置語を見出しにして改行で区切ると分割コマが出ることは確かめた。一方で、**位置語そのものの有無は比べていなかった。**

筆者は使っているうちに、次のような感触を持った。人物に何かをさせたいとき、`On the left,` を付けると画面が左右に分割されやすい。付けないほうがカメラワークが柔軟になり、指定した動作に正確に従う。本記事では、この感触が実験で裏付けられるかを確かめる。

問いは次の 3 つである。

1. 位置語を外すと、動作・相互作用の正確さやカメラの柔軟さは上がるか
2. 位置語を外すと、分割コマは減るか
3. 位置語を外すと、何が悪くなるか（左右の入れ替わり、属性の混線）

## 実験の方法

### 比べた書き方

4 通りとも、1 行目のタグ（品質・人数・キャラ名・シーン・カメラ・背景）と、各キャラの「名前, 外見, 服装, 動作.」の文は共通である。違うのは位置の書き方だけにした。

| 識別子 | 書き方 | 相互作用の相手の指し方 |
|---|---|---|
| `pos-words` | 現行スキルの形。各キャラの文の先頭に `On the left,` などの位置語を付ける | 位置付きの呼び名（`the girl on the right`） |
| `no-pos` | `pos-words` から位置語だけを外す | 名前（`kutara sayaka`） |
| `relational` | `no-pos` の後に、人物どうしの相対関係を書いた 1 文を足す。左・右・中央の絶対位置は使わない（例 `kutara natsumi stands directly behind kutara sayaka`） | 名前 |
| `scene-pos` | 位置は全体シーン文にだけ書き、キャラの文には位置語を付けない（例 `In a bedroom, kutara natsumi on the left is tying the long hair of kutara sayaka on the right into a ponytail.`） | 名前 |

`relational` で左右を指定する必要があるシーンでは、`kutara natsumi stands to the left of kutara sayaka` のように人物どうしの相対で書いた。持ち物の言い直し（後述の p03）も、`pos-words` では位置付きの呼び名、それ以外では名前で書いた。

髪を結うシーン（a02）での 2 行目は次のとおりである。1 行目はどの書き方でも同じで、`masterpiece, best quality, score_7, highres, newest, year 2025, safe, 2girls, kutara natsumi, kutara sayaka, tying hair, hair tie, sitting, standing, upper body, from side, indoors, bedroom, dresser, mirror, warm lighting.` とした。

**pos-words**

```
In a bedroom, one girl is tying the other girl's long hair into a ponytail. On the left, kutara natsumi, a girl with black hair tied in a low ponytail, blunt bangs and round glasses, wearing a green turtleneck sweater and a brown long skirt, stands behind the girl on the right and gathers the long blonde hair of the girl on the right in her hands, tying it with a hair tie. On the right, kutara sayaka, a girl with long straight blonde hair and a bare forehead, wearing a red hoodie and a black pleated skirt, sits on a stool in front of the girl on the left with her eyes closed and a relaxed smile.
```

**no-pos**

```
In a bedroom, one girl is tying the other girl's long hair into a ponytail. kutara natsumi, a girl with black hair tied in a low ponytail, blunt bangs and round glasses, wearing a green turtleneck sweater and a brown long skirt, stands behind kutara sayaka and gathers the long blonde hair of kutara sayaka in her hands, tying it with a hair tie. kutara sayaka, a girl with long straight blonde hair and a bare forehead, wearing a red hoodie and a black pleated skirt, sits on a stool in front of kutara natsumi with her eyes closed and a relaxed smile.
```

**relational**（`no-pos` の末尾に 1 文を足す）

```
... sits on a stool in front of kutara natsumi with her eyes closed and a relaxed smile. kutara natsumi stands directly behind kutara sayaka, and kutara sayaka sits in front of kutara natsumi.
```

**scene-pos**（全体シーン文だけを差し替える）

```
In a bedroom, kutara natsumi on the left is tying the long hair of kutara sayaka on the right into a ponytail. kutara natsumi, a girl with ... (以下 no-pos と同じ)
```

全シーン・全書き方のプロンプトは [`experiment/prompts/`](experiment/prompts/) にある。

### キャラクター

前回と同じ 3 人を使った。服の色をキャラごとに緑・赤・青に固定し、属性の混線を見分けやすくしている。

![3 人のキャラクター（左からなつみ、さやか、あき）](images/characters.jpg)

| キャラ | トリガー | 外見 | 服装（全シーン共通） |
|---|---|---|---|
| なつみ | `kutara natsumi` | 黒髪の低いポニーテール、ぱっつん前髪、丸眼鏡 | 緑のタートルネックセーター、茶色のロングスカート |
| さやか | `kutara sayaka` | 金髪ストレートのロングヘア、おでこ | 赤いパーカー、黒のプリーツスカート |
| あき | `kutara aki` | 黒髪ボブ、ぱっつん前髪、そばかす、平らな胸（タグは `futanari, flat chest`） | 青い T シャツ、カーキのカーゴパンツ |

### 構図シーン

仮説の両面を確かめられるよう、13 シーンを 3 つのグループに分けて用意した。2 人のシーンが 9、3 人のシーンが 4 である。

| ID | グループ | シーン | 人数 | カメラ（タグ） | 成功の条件（要約） |
|---|---|---|---|---|---|
| a01 | 動作 | 本を手渡す | 2 | cowboy shot, from side | なつみが本を差し出し、さやかが受け取る |
| a02 | 動作 | 髪を結ってあげる | 2 | upper body, from side | 立ったなつみが、座ったさやかの髪を背後から結う |
| a03 | 動作 | 浜辺で追いかける | 2 | full body, from side | あきが手を伸ばしてなつみを追い、なつみが振り返る |
| a04 | 動作 | 長縄跳び | 3 | full body, wide shot | なつみとあきが 1 本の縄を回し、さやかが跳ぶ |
| c01 | カメラ | 後ろ姿で夕日を見る | 2 | wide shot, from behind | 2 人とも後ろ姿。なつみがさやかの肩に頭を乗せ、さやかが腕を回す |
| c02 | カメラ | 斜め俯瞰でトランプ | 3 | from above, high angle | 俯瞰で、3 人がテーブルを囲む（横一列ではない） |
| c03 | カメラ | オーバーショルダー | 2 | over-the-shoulder shot | 手前にあきの後ろ姿、奥でなつみがこちらを向いて話す |
| c04 | カメラ | ダッチアングルで駆け寄る | 2 | dutch angle, from below | 画面が傾き、手をつないだ 2 人がこちらへ走る |
| c05 | カメラ | 頬を寄せて自撮り | 2 | close-up, portrait | 顔の接写。なつみがウインク、さやかがスマホを持つ |
| p01 | 位置 | 2 人並び・左右で違う動作 | 2 | cowboy shot, straight-on | 左のなつみが手を振り、右のさやかが腰に手 |
| p02 | 位置 | 3 人並び・別々のポーズ | 3 | cowboy shot, straight-on | 左なつみがピース、中央さやかが腕組み、右あきが片手を腰 |
| p03 | 位置 | 3 人の持ち物 | 3 | full body, straight-on | 左なつみが黄色い傘、中央さやかが青い風船、右あきが赤い本 |
| p04 | 位置 | 机に並んで別々のことをする | 2 | upper body, straight-on | 左のあきがノートに書き、右のさやかが突っ伏して寝る |

- **動作グループ**（a01〜a04）: 動作・相互作用が主役のシーン。仮説が正しければ、位置語を外したほうが動作が正確になるはずである
- **カメラグループ**（c01〜c05）: 横一列の正面並びではなく、カメラを自由に動かしたほうが自然なシーン。仮説が正しければ、位置語ありは正面並びに引き寄せられるはずである
- **位置グループ**（p01〜p04）: 左右・中央を守る必要があるシーン。仮説の反対側として、位置語を外したときに左右や属性が入れ替わるかを見る。p01〜p03 は前回の記事と同じシーンである

シーンの定義は [`experiment/scenes.yaml`](experiment/scenes.yaml) にある。

### 生成条件

| 項目 | 値 |
|---|---|
| モデル | `anima_anima-base-v1.0` |
| VAE / テキストエンコーダ | `qwen_image_vae.safetensors` / `qwen_3_06b_base.safetensors` |
| LoRA | `<lora:kutara_anima.v12:1>`（全プロンプトの先頭） |
| サンプラー / スケジューラ | ER SDE / simple |
| ステップ / CFG | 30 / 4.5 |
| 解像度 | シーンごとに固定（1344×768 または 1024×1024） |
| seed | 101、202、303、404（全書き方・全シーン共通） |
| ネガティブ | `worst quality, low quality, score_1, score_2, score_3, artist name, blurry, jpeg artifacts, chromatic aberration, duplicate, twins, clone, nsfw, nude, nipples, penis, bulge` |
| 生成ツール | [sdctl](https://github.com/yuanying/sdctl)（Stable Diffusion WebUI Forge の API クライアント） |

条件は前回の記事と同じである。全キャラに服装を明示し、安全タグは `safe` にした。4 書き方 × 13 シーン × 4 seed で、計 208 枚を生成した。

### 評価方法

生成画像を 1 枚ずつ目視し、次の 6 項目を 0 / 1 で判定した。

| 項目 | 1 にする条件 |
|---|---|
| 1 枚の絵 | 左右・上下に別のコマ（枠線や背景の断絶で区切られた別の場面）に分かれていない |
| 人数 | 指定した人数ちょうど |
| 属性 | 全員が指定どおりの外見・服装で、他キャラの髪色・眼鏡・服の色・持ち物が移っていない |
| 動作 | シーンの動作・相互作用が成立し、指定したキャラが行っている（役割の入れ替わりは 0） |
| カメラ | 指定したカメラ・構図に従っている。人物が横一列でカメラを向く絵に引き寄せられていたら 0 |
| 位置 | 位置グループだけ判定する。画面に向かって左・中央・右に、指定どおりのキャラがいる |

判定した項目がすべて 1 の画像を「成功」とした。評価のぶれを抑えるため、次のようにした。

- **書き方を伏せた。** 評価者には、4 seed を 2×2 に並べた画像を、シーンごとにランダムに割り当てたコード（X1〜X4）で渡した。シーンごとに割り当てを変えたので、あるシーンの X1 が別のシーンの X1 と同じ書き方とは限らない。評価者には仮説も伝えていない
- **全画像を 2 人が独立に判定した。** 評価者は Claude のサブエージェントで、A 組と B 組がそれぞれ 13 シーン全部を判定した。同じシーンを両方の組で同じエージェントが見ることはない
- **2 人の判定を項目ごとに AND で統合した。** どちらかが 0 を付けた項目は 0 にした。迷ったら厳しい側に倒すという評価基準に合わせた形である

評価者 B 組の 1 人は、自分の判定を書き終えた後に、同じ組の別の評価者の CSV を読んでいた（本人の申告による）。判定を終えた後なので結果は変えていない。

判定基準の全文は [`experiment/eval_rubric.md`](experiment/eval_rubric.md)、全画像の判定は [`experiment/results.csv`](experiment/results.csv)（統合後）と [`experiment/results_raters.csv`](experiment/results_raters.csv)（評価者ごと）にある。

## 結果

### 書き方別の成績

| 書き方 | 成功 | 成功率（95% CI） | 動作 G | カメラ G | 位置 G | 2 人 | 3 人 |
|---|---|---|---|---|---|---|---|
| `pos-words` | 28/52 | 54%（41〜67%） | 11/16 | 4/20 | 13/16 | 20/36 | 8/16 |
| `no-pos` | 26/52 | 50%（37〜63%） | 10/16 | 4/20 | 12/16 | 21/36 | 5/16 |
| `relational` | 27/52 | 52%（39〜65%） | 11/16 | 4/20 | 12/16 | 22/36 | 5/16 |
| `scene-pos` | 25/52 | 48%（35〜61%） | 11/16 | 5/20 | 9/16 | 21/36 | 4/16 |

項目別の正答率:

| 書き方 | 1 枚の絵 | 人数 | 属性 | 動作 | カメラ | 位置 |
|---|---|---|---|---|---|---|
| `pos-words` | 94% | 100% | 98% | 60% | 88% | 100% |
| `no-pos` | 100% | 94% | 85% | 58% | 94% | 94% |
| `relational` | 100% | 98% | 88% | 60% | 94% | 100% |
| `scene-pos` | 94% | 100% | 90% | 56% | 92% | 100% |

4 通りの成功率は 48〜54% に収まり、信頼区間も大きく重なる。同じシーン・seed で片方だけが成功した組を数えても、`pos-words` と `no-pos` で 4 組対 2 組と、偏りは小さい。

評価者ごとに見ても順位はほぼ同じだった。評価者 A 組の成功は 28 / 26 / 27 / 25（`pos-words` / `no-pos` / `relational` / `scene-pos`）、B 組は 35 / 31 / 33 / 31 である。成功・失敗の判定の一致率は 88% で、ずれのほとんどは「動作」の項目に集中した。たとえば c05 の自撮りでは 2 人ともウインクしている絵が多く、A 組は「ウインクがさやかにも移った」として 0、B 組は条件違反ではないとして 1 を付けた。

### シーン別の成功数（4 枚中）

| 書き方 | a01 | a02 | a03 | a04 | c01 | c02 | c03 | c04 | c05 | p01 | p02 | p03 | p04 | 計 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `pos-words` | 4 | 4 | 3 | 0 | 0 | 0 | 3 | 1 | 0 | 4 | 4 | 4 | 1 | 28 |
| `no-pos` | 4 | 4 | 2 | 0 | 0 | 0 | 3 | 1 | 0 | 4 | 4 | 1 | 3 | 26 |
| `relational` | 4 | 4 | 3 | 0 | 0 | 0 | 3 | 1 | 0 | 4 | 4 | 1 | 3 | 27 |
| `scene-pos` | 4 | 4 | 3 | 0 | 0 | 0 | 3 | 1 | 1 | 4 | 3 | 1 | 1 | 25 |

書き方による差がはっきり出たのは p03（持ち物）と p04（机に並ぶ）の 2 シーンだけである。それ以外のシーンでは、成功数はほぼ揃っている。

### 観察 1: 位置語は動作とカメラワークの妨げにならない

動作グループとカメラグループの 9 シーン（各書き方 36 枚）で、「動作」の正答は `pos-words` 18、`no-pos` 18、`relational` 19、`scene-pos` 20 だった。「カメラ」の正答は 16 / 17 / 17 / 17（カメラグループの 20 枚中）である。位置語を外しても、動作が正確になることも、カメラ指定に従いやすくなることもなかった。カメラ指定のあるシーンで、人物が横一列でカメラを向く絵に引き寄せられた例は、どの書き方でも 1 枚もなかった。

オーバーショルダー（c03）の seed 202 を並べると、位置語あり・なしでほぼ同じ絵になっている。

| `pos-words`（`In the foreground,` / `In the background,`） | `no-pos` |
|---|---|
| ![c03 pos-words seed 202](images/pick_c03_pos-words_202.webp) | ![c03 no-pos seed 202](images/pick_c03_no-pos_202.webp) |

これは c03 に限らない。画像を 64×64 の濃淡に縮めて画素の差を測ると、同じ seed で書き方だけが違う組の平均差は 0.13、同じ書き方で seed が違う組は 0.19 だった。このモデルでは、位置語の有無よりも seed のほうが構図を大きく左右する。

一方、どの書き方でも失敗したシーンがある。長縄跳び（a04）は、縄が 1 本につながらず、跳ぶさやかも縄を持ってしまう。後ろ姿（c01）は、頭を乗せる側と腕を回す側がしばしば逆になる。ダッチアングル（c04）は、seed 303 と 404 でほとんど傾かない。これらは位置語の問題ではなく、プロンプトの書き方の外にある限界である。

### 観察 2: 分割コマは「机に並ぶ」シーンでだけ、位置語ありに出た

本実験の 208 枚で分割コマになったのは 6 枚で、すべて p04（机に並んで別々のことをする）だった。内訳は `pos-words` が 3 枚、`scene-pos` が 3 枚で、`no-pos` と `relational` は 0 枚である。位置語をキャラの文に付けても全体シーン文に書いても、分割が起きた。

| `pos-words`（左右 2 コマに分割） | `no-pos`（1 枚の絵） |
|---|---|
| ![p04 pos-words seed 101](images/pick_p04_pos-words_101.webp) | ![p04 no-pos seed 101](images/pick_p04_no-pos_101.webp) |

ただし、ほかの相互作用のない並び（p01〜p03）では、位置語ありでも分割は 1 枚も出なかった。そこで、p04 と同じ型のシーンを 3 つ足して追試した（[追試](#追試-相互作用のない並びで分割コマは再現するか)）。

### 観察 3: 位置語は画面上の左右を決める

位置語を外すと、左右はモデル任せになる。相互作用のない並び（p01〜p04）では、`no-pos` でも文に書いた順に左から並んだ（左右・中央の正解は 16 枚中 15 枚。外れた 1 枚は 4 人出現）。

相互作用のある構図では、位置語が左右を入れ替えた。髪を結うシーン（a02）では、`pos-words` と `scene-pos` はなつみを左に置き、`no-pos` と `relational` は 8 枚とも右に置いた。どちらも動作としては成功している。左右を指定したいなら位置語が要る、ということである。

| `pos-words`（なつみが左） | `no-pos`（なつみが右） |
|---|---|
| ![a02 pos-words seed 101](images/pick_a02_pos-words_101.webp) | ![a02 no-pos seed 101](images/pick_a02_no-pos_101.webp) |

### 観察 4: 3 人では、位置語を外すと混線が増える

3 人が絡むシーン（a04 長縄跳び、c02 俯瞰のトランプ）では、「属性」の正答が `pos-words` 8/8、`scene-pos` 8/8 に対し、`no-pos` 3/8、`relational` 6/8 だった。`no-pos` では、あきが赤いパーカーを着る、さやかの服が水色になる、といった服の取り違えが出た。a04 では、さやかが 2 人になって 4 人に増えた絵もあった（`no-pos` と `relational` で各 1 枚）。

| `pos-words`（服の色が正しい） | `no-pos`（あきが赤いパーカー） |
|---|---|
| ![c02 pos-words seed 404](images/pick_c02_pos-words_404.webp) | ![c02 no-pos seed 404](images/pick_c02_no-pos_404.webp) |

持ち物のシーン（p03）では差がさらに大きかった。成功は `pos-words` が 4/4 で、ほかの 3 通りは 1/4 である。位置語を外した 3 通りでは、なつみの黄色い傘をさやかが持つ、風船が 2 つになる、といった持ち物の入れ替わりが起きた。持ち物の言い直し文（`The yellow umbrella belongs to ...`）の呼び方も、`pos-words` は位置付きの呼び名、ほかは名前である。どちらの違いが効いたのかは、この実験では切り分けていない。

| `pos-words`（傘・風船・本が正しい持ち主に） | `no-pos`（傘をさやかが持ち、なつみは手ぶら） |
|---|---|
| ![p03 pos-words seed 202](images/pick_p03_pos-words_202.webp) | ![p03 no-pos seed 202](images/pick_p03_no-pos_202.webp) |

### コンタクトシート

各シーンの全 16 枚。行が書き方、列が seed で、緑枠が成功、赤枠が失敗である。

<details>
<summary>13 シーンのコンタクトシートを開く</summary>

#### a01 本を手渡す
![a01](images/sheet_a01.webp)

#### a02 髪を結ってあげる
![a02](images/sheet_a02.webp)

#### a03 浜辺で追いかける
![a03](images/sheet_a03.webp)

#### a04 3人で長縄跳び
![a04](images/sheet_a04.webp)

#### c01 後ろ姿で夕日を見る
![c01](images/sheet_c01.webp)

#### c02 斜め俯瞰でトランプ
![c02](images/sheet_c02.webp)

#### c03 オーバーショルダー
![c03](images/sheet_c03.webp)

#### c04 ダッチアングルで駆け寄る
![c04](images/sheet_c04.webp)

#### c05 頬を寄せて自撮り（顔の接写）
![c05](images/sheet_c05.webp)

#### p01 2人並び・左右で違う動作
![p01](images/sheet_p01.webp)

#### p02 3人並び・別々のポーズ
![p02](images/sheet_p02.webp)

#### p03 3人の持ち物
![p03](images/sheet_p03.webp)

#### p04 机に並んで別々のことをする
![p04](images/sheet_p04.webp)

</details>

## 追試: 相互作用のない並びで分割コマは再現するか

本実験で分割コマが出たのは p04 だけだった。偶然か、構図の型によるものかを確かめるため、追試をした。

- p04 に seed 505 / 606 / 707 / 808 を足し、8 seed にした
- p04 と同じ「相互作用のない人物が並んで別々のことをする」型のシーンを 3 つ足した（各 8 seed）
  - q01 ソファで別々のことをする（2 人。なつみが漫画を読み、あきが携帯ゲーム機で遊ぶ）
  - q02 キッチンで料理と皿洗い（2 人。さやかが人参を切り、なつみが皿を洗う）
  - q03 バス停で 3 人が別々のことをする（3 人。あきがメロンパンを食べ、なつみがスマホを見て、さやかがヘッドホンで音楽を聴く）
- 書き方は `pos-words` と `no-pos` の 2 通りに絞った。計 64 枚を、本実験と同じ手順（書き方を伏せ、2 人が独立に判定し、AND で統合）で評価した

シーン定義は [`experiment/scenes_followup.yaml`](experiment/scenes_followup.yaml)、判定は [`experiment/results_followup.csv`](experiment/results_followup.csv) にある。

| 書き方 | p04 | q01 | q02 | q03 | 計 | 分割コマ |
|---|---|---|---|---|---|---|
| `pos-words` | 3/8 | 8/8 | 8/8 | 6/8 | 25/32 | 5/32（すべて p04） |
| `no-pos` | 7/8 | 8/8 | 4/8 | 8/8 | 27/32 | 0/32 |

- **分割コマは p04 でだけ再現した。** `pos-words` は p04 の 8 枚中 5 枚が分割され、本実験と合わせると 12 枚中 8 枚になる。`no-pos` は 12 枚中 0 枚だった
- **同じ型でも、q01〜q03 では位置語ありで分割は出なかった。** 何が p04 を分割しやすくしているのかは、この実験からは分からない。p04 で分割された絵では、あきが真横を向いてノートに書き、さやかが別の机で突っ伏すという、それぞれ独立した 2 つの場面になっていた
- **位置語を外しても、左右は 32 枚すべて正しかった。** どのシーンでも、文に書いた順に左から並んだ
- 分割以外の失敗は、どちらの書き方にも少しずつ出た。q02 では `no-pos` の動作が 4/8 に落ちた（皿を洗うはずのなつみが人参を扱うなど、動作が人物間で混ざった）。q03 では `pos-words` が 6/8 だった（背景のバス停が描かれない、さやかがヘッドホンをしていない）。成功数の合計は 25/32 と 27/32 で、差は小さい

![追試 p04 のコンタクトシート](images/fu_sheet_p04.webp)

<details>
<summary>q01〜q03 のコンタクトシートを開く</summary>

#### q01 ソファで別々のことをする
![q01](images/fu_sheet_q01.webp)

#### q02 キッチンで料理と皿洗い
![q02](images/fu_sheet_q02.webp)

#### q03 バス停で3人が別々のことをする
![q03](images/fu_sheet_q03.webp)

</details>

## 結論

問いごとの答えは次のとおりである。

1. **位置語を外しても、動作の正確さとカメラの柔軟さは上がらなかった。** 動作が主役の 4 シーン、カメラ指定のある 5 シーンのどちらでも、位置語あり・なし・相対表現・全体シーン文だけの 4 通りで差が出なかった。同じ seed なら、書き方が違ってもほぼ同じ構図の絵になる
2. **分割コマは、位置語を外すと減る。ただし起きる構図は限られる。** 分割は「机に並んで別々のことをする」シーンだけで、位置語ありで 12 枚中 8 枚起きた。位置語を外すと 0 枚になった（後の検証を合わせると 20 枚中 13 枚と 0 枚）。同じ型の他の 3 シーンでは起きなかった
3. **位置語を外すと、3 人の構図で服の色の混線が増え、持ち物の持ち主が入れ替わる。** 相互作用のある構図では、左右がモデル任せになる

仮説は「位置語を付けると分割コマが出ることがある」という部分だけが、特定の構図で支持された。「位置語を外せばカメラワークが柔軟になり、動作に正確に従う」という部分は支持されなかった。差が出なかった、というのが結果である。

推奨は次のとおりである。

- 位置語は既定で付ける。動作やカメラワークを理由に外す必要はない
- 3 人の構図と、持ち物を言い直す構図では、特に位置語を残す
- 相互作用のない並びで分割コマが出たら、位置語を外し、左に置きたいキャラから順に文を書く

## スキルへの反映と検証

`skills/anima-prompt/SKILL.md` に次の内容を反映した。

| 変更 | 根拠 |
|---|---|
| 位置語は既定で付ける、と明記した（構造の説明、出力テンプレートの注記） | 観察 1・3・4。外しても良くならず、3 人と持ち物では悪くなった |
| 「位置語を付けるかどうかの判断」を位置語の表の後に追加した | 観察 1〜4、追試 |
| 分割コマが出たら位置語を外し、左から順に書く、という対処と書き直し例を追加した | 観察 2、追試（p04 で 12 枚中 8 枚 → 0 枚） |
| 位置語を外すときは、相互作用の相手を名前で指す | 本実験の `no-pos` の書き方。相手の指し方による動作の差は出なかった |
| 持ち物の言い直しは位置語の呼び名で書く、という既存の記述に今回の結果を補った | 観察 4（p03 で 4/4 と 1/4） |

既定の書き方は変えていないので、スキルの変更で新しく生まれた書き方は「分割コマが出たときの書き直し」だけである。これを、本実験・追試で使っていない seed で確かめた。

- 対象: p04（机に並んで勉強と居眠り）。今回分割コマが出た唯一の構図である
- 比較: 修正前の形（`pos-words`）と、スキルの書き直し例どおりに位置語を外し、左に置くあきから順に書いた形（本実験の `no-pos` と同じ文）
- seed: 909、1010、1111、1212、1313、1414、1515、1616（本実験・追試で使っていないもの）
- 評価: 本実験と同じ手順（書き方を伏せ、2 人が独立に判定し、AND で統合）

| 書き方 | 成功 | 1 枚の絵 | 動作 | 位置 |
|---|---|---|---|---|
| 修正前（`pos-words`） | 3/8 | 3/8 | 3/8 | 8/8 |
| 書き直し（位置語なし） | 7/8 | 8/8 | 8/8 | 7/8 |

書き直した形では、8 枚とも 1 枚の絵になった。修正前の形は 8 枚中 5 枚が左右 2 コマに分割された。書き直した形の失敗は seed 1313 の 1 枚で、あきとさやかの左右が逆になった。位置語を外した代わりに、左右がモデル任せになったぶんの失敗である。

本実験・追試・検証を合わせると、p04 での分割コマは位置語ありで 20 枚中 13 枚、位置語なしで 20 枚中 0 枚になる。位置語なしの左右の入れ替わりは 20 枚中 1 枚だった。

| 修正前（`pos-words`、seed 1010） | 書き直し（位置語なし、seed 1010） |
|---|---|
| ![p04 pos-words seed 1010](images/v_pick_p04_pos-words_1010.webp) | ![p04 no-pos seed 1010](images/v_pick_p04_no-pos_1010.webp) |

![検証のコンタクトシート](images/v_sheet_p04.webp)

判定は [`experiment/results_verify.csv`](experiment/results_verify.csv) にある。

## この実験の限界

- **シーンごとの枚数が少ない。** 1 条件 4 枚（追試は 8 枚）で、シーン単位の差は 1〜2 枚の違いで入れ替わる。全体の成功率の差（48〜54%）は誤差の範囲である
- **分割コマが出たのは 1 シーンだけである。** 位置語が分割を招く構図の条件は特定できていない。今回の 7 つの並びのシーンのうち 1 つでしか起きていない
- **評価者は Claude のサブエージェントである。** 2 人の判定を AND で統合したが、「動作」の項目では判断が割れた（一致率 86%）。あきのそばかすは、評価用の縮小画像では見分けにくかった
- **キャラクターは LoRA で学習済みの 3 人に限られる。** トリガーワードで呼べないオリジナルキャラでは、位置語を外したときに人物を指す手段が外見の呼び名しかない。前回の記事では、外見の呼び名での言い直しで人数が増える失敗が出ている
- **`no-pos` と `pos-words` では、相互作用の相手の指し方も違う**（名前と位置付きの呼び名）。位置語そのものの効果と、呼び方の効果は切り分けていない

## 再現方法

[`experiment/`](experiment/) に、条件の定義と生成・評価の手順をすべて置いた。

| ファイル | 内容 |
|---|---|
| `characters.yaml` / `params.yaml` | キャラクターの定義と生成パラメータ（前回の記事と同じ） |
| `scenes.yaml` | 本実験の 13 シーンの定義 |
| `scenes_followup.yaml` | 追試で足した 3 シーンの定義 |
| `build_prompts.py` | 4 通りの書き方でプロンプトを組み立てる（引数でシーン定義と出力先を変えられる） |
| `prompts/` / `prompts_followup/` | 実際に使った全プロンプト |
| `generate.py` | sdctl で生成する（`--seeds` で seed を変えられる） |
| `eval_rubric.md` | 評価基準 |
| `evaluate.py` | 書き方を伏せた評価用グリッドの作成（`prepare`）、2 人の判定の統合と集計（`aggregate`）、コンタクトシートの作成（`figures`） |
| `results.csv` / `results_raters.csv` / `results.md` | 本実験の判定（統合後・評価者ごと）と集計 |
| `results_followup*.csv` / `results_followup.md` | 追試の判定と集計 |
| `results_verify*.csv` / `results_verify.md` | スキル修正後の検証の判定と集計 |

追試は `generate.py <出力先> --scenes-file scenes_followup.yaml --prompts prompts_followup --methods pos-words,no-pos --seeds 101,202,303,404,505,606,707,808` で生成した。p04 の追加 seed は `--scenes p04 --methods pos-words,no-pos --seeds 505,606,707,808`、検証は `--seeds 909,1010,1111,1212,1313,1414,1515,1616` である。
