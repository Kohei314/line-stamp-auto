import json
import os
import zipfile
from PIL import Image, ImageDraw, ImageFont

THEMES_PATH = "themes/stamp_themes.json"
FONT_PATH = "fonts/NotoSansJP-Bold.ttf"
OUTPUT_DIR = "output"

WIDTH = 370
HEIGHT = 320

SHIKISHI_DESIGNS = [
    {"bg": (74, 112, 48),   "inner": (242, 249, 236), "text": (30, 60, 20)},   # 緑
    {"bg": (184, 148, 26),  "inner": (253, 248, 236), "text": (80, 50, 0)},    # 金
    {"bg": (42, 106, 154),  "inner": (238, 246, 255), "text": (0, 40, 100)},   # 青
    {"bg": (160, 48, 96),   "inner": (255, 240, 244), "text": (100, 0, 50)},   # ピンク
    {"bg": (100, 50, 160),  "inner": (248, 240, 255), "text": (60, 0, 120)},   # 紫
    {"bg": (150, 80, 30),   "inner": (255, 245, 235), "text": (100, 40, 0)},   # 茶
    {"bg": (40, 130, 130),  "inner": (235, 252, 252), "text": (0, 70, 70)},    # シアン
    {"bg": (120, 120, 40),  "inner": (252, 252, 235), "text": (60, 60, 0)},    # 抹茶
]


def generate_haiku(theme, api_key):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
LINEスタンプ用の川柳（5・7・5）を8句考えてください。

テーマ: {theme["target"]}向け・{theme["style"]}
条件:
- 必ず5文字・7文字・5文字の3フレーズに分ける
- シュールで思わず笑えるもの、または日常でLINEで使えるもの
- 重複なし

以下のJSON形式のみで返してください。説明文は不要です。
{{"haiku": [
  {{"p1": "5文字", "p2": "7文字", "p3": "5文字"}},
  {{"p1": "5文字", "p2": "7文字", "p3": "5文字"}}
]}}
"""
    response = model.generate_content(prompt)
    text = response.text.strip().replace("```json", "").replace("```", "").strip()
    data = json.loads(text)
    return data["haiku"]


def create_shikishi_stamp(haiku, output_path, design):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 外枠（色紙の縁色）
    margin = 10
    border = 8
    radius = 30

    draw.rounded_rectangle(
        [margin, margin, WIDTH - margin, HEIGHT - margin],
        radius=radius,
        fill=(*design["bg"], 255)
    )

    # 内側（和紙色）
    draw.rounded_rectangle(
        [margin + border, margin + border,
         WIDTH - margin - border, HEIGHT - margin - border],
        radius=max(radius - border, 0),
        fill=(*design["inner"], 255)
    )

    # フォントサイズを最大文字数に応じて自動調整
    p1 = haiku["p1"]  # 5文字 右列
    p2 = haiku["p2"]  # 7文字 中列
    p3 = haiku["p3"]  # 5文字 左列

    # フォントサイズを最大文字数に応じて自動調整
    max_chars = max(len(p1), len(p2), len(p3))
    inner_height = HEIGHT - (margin + border) * 2 - 32
    font_size = min(34, int(inner_height / max_chars))
    font = ImageFont.truetype(FONT_PATH, font_size)
    char_h = font_size + 4
    char_w = font_size + 2


    # 3列を中央に配置
    total_w = char_w * 3 + 10 * 2  # 3列 + 列間隔
    start_x = (WIDTH - total_w) // 2 + total_w - char_w  # 右列のX

    # 段々下がりのY開始位置
    inner_top = margin + border + 16

    x1 = start_x           # 右列
    x2 = start_x - char_w - 10   # 中列
    x3 = start_x - (char_w + 10) * 2  # 左列

    y1 = inner_top          # 右列（一番上）
    y2 = inner_top + 18     # 中列（少し下）
    y3 = inner_top + 36     # 左列（さらに下）

    # 右列（p1・5文字）
    for char in p1:
        draw.text((x1, y1), char, font=font, fill=(*design["text"], 255))
        y1 += char_h

    # 中列（p2・7文字）
    for char in p2:
        draw.text((x2, y2), char, font=font, fill=(*design["text"], 255))
        y2 += char_h

    # 左列（p3・5文字）
    for char in p3:
        draw.text((x3, y3), char, font=font, fill=(*design["text"], 255))
        y3 += char_h

    img.save(output_path, "PNG")
    print(f"生成: {p1}/{p2}/{p3} → {output_path}")


def create_stamp_set(stamp_set, api_key):
    set_id = stamp_set["id"]
    print(f"川柳生成中: {stamp_set['target']}")

    haiku_list = generate_haiku(stamp_set, api_key)

    set_dir = os.path.join(OUTPUT_DIR, set_id)
    os.makedirs(set_dir, exist_ok=True)

    image_paths = []
    for i, haiku in enumerate(haiku_list[:8]):
        design = SHIKISHI_DESIGNS[i % len(SHIKISHI_DESIGNS)]
        output_path = os.path.join(set_dir, f"stamp_{i+1:02d}.png")
        create_shikishi_stamp(haiku, output_path, design)
        image_paths.append(output_path)

    zip_path = os.path.join(OUTPUT_DIR, f"{set_id}.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        for path in image_paths:
            zf.write(path, os.path.basename(path))
    print(f"ZIP作成: {zip_path}")


def main():
    import random
    api_key = os.environ.get("GEMINI_API_KEY")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(THEMES_PATH, "r", encoding="utf-8") as f:
        themes = json.load(f)

    # 実行回数をもとに順番にテーマを選ぶ
    run_number = int(os.environ.get("GITHUB_RUN_NUMBER", "0"))
    stamp_sets = themes["stamp_sets"]
    selected = stamp_sets[run_number % len(stamp_sets)]

    print(f"今回のテーマ: {selected['target']}（{selected['id']}）")
    create_stamp_set(selected, api_key)

    print("完了！")


if __name__ == "__main__":
    main()
