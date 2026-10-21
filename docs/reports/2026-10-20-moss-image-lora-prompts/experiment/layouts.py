"""Write MOSS-Image layout prompts (abs_centralized / yxyx) from top-left xyxy pixel drafts."""
import json, math, sys

AKI = "kutara aki, femboy, short black bob cut with blunt bangs, black eyes"
NAT = "kutara natsumi, 1girl, dark brown hair in a low ponytail with blunt bangs, glasses, grey eyes, large breasts"

DRAFTS = {
    "01_cafe_table": (1216, 832, 301, {
        "meta": ["illustration"],
        "caption": "Anime illustration of two friends sitting face to face at a small round table by the window of a cozy cafe, warm afternoon light, coffee cups and a slice of cake on the table.",
        "items": [
            ("object", f"{AKI}, wearing a pink oversized hoodie, sitting on the left, laughing with open mouth, holding a fork", None, [40, 120, 560, 832]),
            ("object", f"{NAT}, wearing a grey ribbed turtleneck sweater, sitting on the right, gentle smile, holding a coffee cup with both hands", None, [640, 100, 1180, 832]),
            ("object", "small round wooden table with two coffee cups and a strawberry shortcake", None, [380, 560, 840, 832]),
        ]}),
    "02_poster": (832, 1216, 302, {
        "meta": ["poster"],
        "caption": "Anime-style movie poster with a pastel sunset sky background, two characters standing back to back, title text at the top and a tagline at the bottom.",
        "items": [
            ("text", "Large bold white title with a dark outline, centered at the top.", "KUTARA DAYS", [80, 40, 752, 200]),
            ("object", f"{AKI}, wearing a white shirt and black pants school uniform, standing on the left, arms crossed, smug smile", None, [40, 240, 440, 1060]),
            ("object", f"{NAT}, wearing a black business suit and white shirt, standing on the right, back to back with the other, looking at viewer", None, [400, 220, 800, 1060]),
            ("text", "Small white italic tagline centered at the bottom.", "Two lives, one summer.", [160, 1090, 672, 1170]),
        ]}),
    "03_park_bench": (1216, 832, 303, {
        "meta": ["illustration"],
        "caption": "Anime illustration of a park in autumn, orange and yellow leaves falling, a wooden bench in the center, soft evening light.",
        "items": [
            ("object", f"{NAT}, wearing a beige trench coat and a red scarf, sitting on the bench on the left, reading a paperback book", None, [200, 160, 600, 800]),
            ("object", f"{AKI}, wearing a navy duffle coat, sitting on the bench on the right, leaning on her shoulder, sleeping, eyes closed", None, [560, 200, 980, 800]),
            ("object", "wooden park bench", None, [160, 520, 1060, 800]),
        ]}),
    "04_classroom_board": (1216, 832, 304, {
        "meta": ["illustration"],
        "caption": "Anime illustration of an empty classroom after school, sunlight through the windows, a green chalkboard with handwritten chalk text.",
        "items": [
            ("text", "White chalk handwriting on the green chalkboard, two lines.", "Today's lesson:\nMOSS-Image LoRA", [220, 60, 900, 300]),
            ("object", f"{NAT}, as a teacher, wearing a white blouse and a long navy skirt, standing in front of the chalkboard on the left, holding a piece of chalk, pointing at the text", None, [60, 160, 460, 832]),
            ("object", f"{AKI}, as a student, wearing a school uniform with a sweater vest, sitting at a desk on the right, raising one hand, smiling", None, [700, 340, 1160, 832]),
        ]}),
}

def compile_layout(w, h, d):
    items = []
    for label, caption, text, (x0, y0, x1, y1) in d["items"]:
        assert 0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h, (caption, w, h)
        bb = [math.floor(y0) - h // 2, math.floor(x0) - w // 2, math.ceil(y1) - h // 2, math.ceil(x1) - w // 2]
        it = {"label": label, "caption": caption}
        if text is not None:
            it["text"] = text
        it["bbox"] = bb
        items.append(it)
    return json.dumps({"summary": {"meta": d["meta"], "canvas": "single", "caption": d["caption"]}, "items": items,
                       "bbox_coord_space": "abs_centralized", "bbox_format": "yxyx"}, ensure_ascii=False)

for name, (w, h, seed, d) in DRAFTS.items():
    print(f"{name}\t{w}\t{h}\t{seed}\t{compile_layout(w, h, d)}")
