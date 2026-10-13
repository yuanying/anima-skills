#!/usr/bin/env python3
"""characters.yaml と scenes.yaml から、書き方ごとのプロンプトを組み立てて prompts/ に書き出す。

4 つの書き方は 1 行目のタグと、各キャラの「名前, 外見, 服装, 動作.」の文を共有し、位置の書き方だけが違う。
出力: prompts/<scene_id>/<method_id>.yaml（sdctl --prompt で読める形式）
"""
import pathlib
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent
LORA = "<lora:kutara_anima.v12:1>"
QUALITY = "masterpiece, best quality, score_7, highres, newest, year 2025, safe"


def head_tags(s, chars):
    # 1 行目: 品質・人数・キャラ名・シーン・カメラ・背景のタグ（フェーズ 1 の skill-v2 と同じ）。
    names = ", ".join(chars[ch["who"]]["trigger"] for ch in s["chars"])
    return ", ".join([QUALITY, s["count"], names, s["scene_tags"], s["camera_tags"], s["env_tags"]]) + "."


def refs(s, chars, by_label):
    # pose_nl / belongings_nl の {natsumi} などを、位置付きの呼び名かトリガーワードに置き換える表。
    return {ch["who"]: (ch["label"] if by_label else chars[ch["who"]]["trigger"]) for ch in s["chars"]}


def char_sentence(c, ch, ref):
    return f"{c['trigger']}, {c['appearance_nl']}, {c['outfit_nl']}, {ch['pose_nl'].format(**ref)}."


def body(s, chars, scene, by_label, pos_prefix, extra=None):
    ref = refs(s, chars, by_label)
    sents = [scene]
    for ch in s["chars"]:
        sent = char_sentence(chars[ch["who"]], ch, ref)
        sents.append(f"{ch['pos']}, {sent}" if pos_prefix else sent)
    if extra:
        sents.append(extra)
    if s.get("belongings_nl"):
        sents.append(s["belongings_nl"].format(**ref))
    return head_tags(s, chars) + "\n" + " ".join(sents)


def m_pos_words(s, chars):
    # 現行スキル（skill-v2）の形: 各キャラの文の先頭に位置語。相手は位置付きの呼び名で指す。
    return body(s, chars, s["scene_nl"], by_label=True, pos_prefix=True)


def m_no_pos(s, chars):
    # pos-words から位置語だけを外す。相手はトリガーワードで指す。
    return body(s, chars, s["scene_nl"], by_label=False, pos_prefix=False)


def m_relational(s, chars):
    # 位置語なし + 人物どうしの相対関係を名前で書いた 1 文を、キャラの文の後に足す。
    return body(s, chars, s["scene_nl"], by_label=False, pos_prefix=False, extra=s["relation_nl"])


def m_scene_pos(s, chars):
    # 位置は全体シーン文にだけ書き、キャラの文には位置語を付けない。
    return body(s, chars, s["scene_pos_nl"], by_label=False, pos_prefix=False)


METHODS = {
    "pos-words": m_pos_words,
    "no-pos": m_no_pos,
    "relational": m_relational,
    "scene-pos": m_scene_pos,
}


def main():
    # 引数: [<シーン定義 YAML> [<出力ディレクトリ>]]。既定は scenes.yaml と prompts/
    args = sys.argv[1:]
    scenes_file = pathlib.Path(args[0]) if args else HERE / "scenes.yaml"
    out = pathlib.Path(args[1]) if len(args) > 1 else HERE / "prompts"
    chars = yaml.safe_load((HERE / "characters.yaml").read_text())
    scenes = yaml.safe_load(scenes_file.read_text())
    for s in scenes:
        d = out / s["id"]
        d.mkdir(parents=True, exist_ok=True)
        for mid, fn in METHODS.items():
            text = f"{LORA}\n{fn(s, chars)}"
            (d / f"{mid}.yaml").write_text(yaml.safe_dump({"prompt": text}, allow_unicode=True, sort_keys=False, width=10**6))


if __name__ == "__main__":
    main()
