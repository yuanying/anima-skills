#!/usr/bin/env python3
"""修正版 anima-prompt スキルの書き方で、再検証用のプロンプトを prompts/ に書き出す。

build_prompts.py と同じ characters.yaml / scenes.yaml から組み立てる。
出力: prompts/<scene_id>/<method_id>.yaml（method_id は METHODS_V2 のキー）
"""
import pathlib
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_prompts import LORA, QUALITY, char_sentence, char_tags  # noqa: E402


def head_tags(s, chars):
    # 1 行目: 品質・人数・キャラ名・シーン・カメラ・背景のタグ。
    names = ", ".join(chars[ch["who"]]["trigger"] for ch in s["chars"])
    return ", ".join([QUALITY, s["count"], names, s["scene_tags"], s["camera_tags"], s["env_tags"]]) + "."


def m_skill_v2(s, chars):
    # 修正版スキル: hybrid-tags-nl の 1 段落に、相互作用・持ち物の言い直し文を末尾に足す。
    sents = [s["scene_nl"]]
    for ch in s["chars"]:
        sents.append(f"{ch['pos']}, {char_sentence(chars[ch['who']], ch)}")
    sents.append(s["relation_nl"])
    return head_tags(s, chars) + "\n" + " ".join(sents)


def m_skill_v2_tags(s, chars):
    # skill-v2 の各キャラの文の直後に、そのキャラのタグ列（1girl から始める）を同じ段落で続ける。
    # 3 人以上でキャラごとのタグ列を残すべきかを確かめるための変種。
    sents = [s["scene_nl"]]
    for ch in s["chars"]:
        c = chars[ch["who"]]
        sents.append(f"{ch['pos']}, {char_sentence(c, ch)} {char_tags(c, ch)}.")
    sents.append(s["relation_nl"])
    return head_tags(s, chars) + "\n" + " ".join(sents)


METHODS_V2 = {
    "skill-v2": m_skill_v2,
    "skill-v2-tags": m_skill_v2_tags,
}


def main():
    chars = yaml.safe_load((HERE / "characters.yaml").read_text())
    scenes = yaml.safe_load((HERE / "scenes.yaml").read_text())
    for s in scenes:
        d = HERE / "prompts" / s["id"]
        d.mkdir(parents=True, exist_ok=True)
        for mid, fn in METHODS_V2.items():
            body = f"{LORA}\n{fn(s, chars)}"
            (d / f"{mid}.yaml").write_text(yaml.safe_dump({"prompt": body}, allow_unicode=True, sort_keys=False, width=10**6))


if __name__ == "__main__":
    main()
