#!/usr/bin/env python3
"""characters.yaml と scenes.yaml から、指示方法ごとのプロンプトを組み立てて prompts/ に書き出す。

出力: prompts/<scene_id>/<method_id>.yaml（sdctl --prompt で読める形式）
"""
import pathlib

import yaml

HERE = pathlib.Path(__file__).resolve().parent
LORA = "<lora:kutara_anima.v12:1>"
QUALITY = "masterpiece, best quality, score_7, highres, newest, year 2025, safe"


def char_tags(c, ch, with_gender=True):
    parts = [c["gender_tag"]] if with_gender else []
    parts += [c["trigger"], c["appearance_tags"], c["outfit_tags"], ch["pose_tags"]]
    return ", ".join(parts)


def char_sentence(c, ch):
    # 名前の直後に外見を続ける（公式モデルカードの注意点）。代名詞は避ける。
    return f"{c['trigger']}, {c['appearance_nl']}, {c['outfit_nl']}, {ch['pose_nl']}."


def tail_tags(s):
    return f"{s['camera_tags']},\n{s['env_tags']}"


def cap(t):
    return t[0].upper() + t[1:]


def setting_sentence(s):
    # 自然文系の方式でもカメラ・背景の情報量を揃えるための 1 文。
    return f"The picture is a {s['camera_tags']} view, set in {s['env_tags']}."


def image_pos(ch):
    pos = ch["pos"].replace(" of the frame", "")
    return f"{pos} is" if pos.startswith("The ") else f"{pos} of the image is"


def m_tags_only(s, chars):
    # 1. Danbooru タグのみ。キャラごとのタグを順に並べるだけ（区切りなし）。
    parts = [QUALITY, s["count"]]
    for ch in s["chars"]:
        parts.append(char_tags(chars[ch["who"]], ch, with_gender=False))
    parts += [s["scene_tags"], s["camera_tags"], s["env_tags"]]
    return ", ".join(parts)


def m_tags_break(s, chars):
    # 8. タグのみ + キャラ間を BREAK で区切る（SD1.5/SDXL の慣習。対照群）。
    head = f"{QUALITY}, {s['count']}, {s['scene_tags']}"
    blocks = [char_tags(chars[ch["who"]], ch) for ch in s["chars"]]
    return " BREAK ".join([head] + blocks + [f"{s['camera_tags']}, {s['env_tags']}"])


def m_name_then_appearance(s, chars):
    # 2. 公式モデルカードの注意「名前の直後に外見」をタグ列の中で行う。位置は各キャラの末尾に添える。
    parts = [QUALITY, s["count"]]
    for ch in s["chars"]:
        c = chars[ch["who"]]
        parts.append(f"{c['trigger']} with {c['appearance_tags']} wearing {c['outfit_tags']}, {ch['pose_tags']}, {ch['pos'].lower()}")
    parts += [s["scene_tags"], s["camera_tags"], s["env_tags"]]
    return ", ".join(parts)


def m_nl_sentences(s, chars):
    # 3. 自然文のみ。キャラごとに文を分け、位置付きの呼び名を主語として毎文繰り返す。
    sents = [s["scene_nl"]]
    for ch in s["chars"]:
        c = chars[ch["who"]]
        lab = cap(ch["label"])
        sents.append(f"{lab} is {c['trigger']}, {c['appearance_nl']}, {c['outfit_nl']}.")
        sents.append(f"{lab} {ch['pose_nl']}.")
    sents.append(setting_sentence(s))
    return f"{QUALITY}.\n" + " ".join(sents)


def m_hybrid_tags_nl(s, chars):
    # 4. タグ（品質・人数・キャラ名・カメラ・背景）を先頭に置き、続けて自然文で各キャラを記述。
    names = ", ".join(chars[ch["who"]]["trigger"] for ch in s["chars"])
    tags = ", ".join([QUALITY, s["count"], names, s["scene_tags"], s["camera_tags"], s["env_tags"]])
    sents = [s["scene_nl"]]
    for ch in s["chars"]:
        sents.append(f"{ch['pos']}, {char_sentence(chars[ch['who']], ch)}")
    return tags + ".\n" + " ".join(sents)


def m_skill_position_blocks(s, chars):
    # 5a. 現行 anima-prompt スキルの「位置ブロック」構造（インデント付き、自然文 + タグ列）。
    lines = [f"{QUALITY},", f"{s['count']},", s["scene_nl"]]
    for ch in s["chars"]:
        c = chars[ch["who"]]
        lines.append(f"{ch['pos']},")
        lines.append(f"    {char_sentence(c, ch)}")
        lines.append(f"    {char_tags(c, ch)},")
    lines.append(tail_tags(s))
    return "\n".join(lines)


def m_image_side_blocks(s, chars):
    # 5b. HF Discussions 型: 画面構成を宣言し「Left side of the image is <名前>, <タグ>」で区切る。
    n = len(s["chars"])
    parts = [f"{QUALITY}, {s['count']}, the image depicts {n} characters. {s['scene_nl']}"]
    for ch in s["chars"]:
        c = chars[ch["who"]]
        parts.append(f"{image_pos(ch)} {c['trigger']}, {c['gender_tag']}, {c['appearance_tags']}, {c['outfit_tags']}, {ch['pose_tags']}.")
    parts.append(f"{s['scene_tags']}, {s['camera_tags']}, {s['env_tags']}")
    return " ".join(parts)


def m_labeled_groups(s, chars):
    # 6. キャラごとにラベル + コロンを付け、改行でグループを分ける。
    lines = [f"{QUALITY}, {s['count']}, {s['scene_tags']}"]
    for ch in s["chars"]:
        lines.append(f"{ch['label']}: {char_tags(chars[ch['who']], ch)}")
    lines.append(f"{s['camera_tags']}, {s['env_tags']}")
    return "\n".join(lines)


def m_interaction_relations(s, chars):
    # 7. 各キャラを別の文で定義した後、相互作用を言い直し、最後に役割を再掲する。
    sents = [s["scene_nl"]]
    for ch in s["chars"]:
        c = chars[ch["who"]]
        sents.append(f"{cap(ch['label'])} is {c['trigger']}, {c['appearance_nl']}, {c['outfit_nl']}, and {ch['pose_nl']}.")
    sents.append(s["relation_nl"])
    recap = ", ".join(f"{chars[ch['who']]['trigger']} is {ch['label']}" for ch in s["chars"])
    sents.append(f"To be clear, {recap}.")
    return f"{QUALITY}, {s['count']}.\n" + " ".join(sents) + f"\n{s['camera_tags']}, {s['env_tags']}"


METHODS = {
    "tags-only": m_tags_only,
    "name-then-appearance": m_name_then_appearance,
    "nl-sentences": m_nl_sentences,
    "hybrid-tags-nl": m_hybrid_tags_nl,
    "skill-position-blocks": m_skill_position_blocks,
    "image-side-blocks": m_image_side_blocks,
    "labeled-groups": m_labeled_groups,
    "interaction-relations": m_interaction_relations,
    "tags-break": m_tags_break,
}


def main():
    chars = yaml.safe_load((HERE / "characters.yaml").read_text())
    scenes = yaml.safe_load((HERE / "scenes.yaml").read_text())
    out = HERE / "prompts"
    for s in scenes:
        d = out / s["id"]
        d.mkdir(parents=True, exist_ok=True)
        for mid, fn in METHODS.items():
            body = f"{LORA}\n{fn(s, chars)}"
            (d / f"{mid}.yaml").write_text(yaml.safe_dump({"prompt": body}, allow_unicode=True, sort_keys=False, width=10**6))


if __name__ == "__main__":
    main()
