import json
import os
import zipfile
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# パス設定
THEMES_PATH = "themes/stamp_themes.json"
FONT_PATH = "fonts/NotoSansJP-Bold.ttf"
OUTPUT_DIR = "output"

# LINE規格
WIDTH = 370
HEIGHT = 320

# テーマごとのデザイン設定
THEME_DESIGNS = {
    "working_adult": {
        "colors": [
            {"bg": (70, 130, 180, 255), "text": (255, 255, 255, 255), "border": (40, 80, 130, 255)},
            {"bg": (95, 158, 160, 255), "text": (255, 255, 255, 255), "border": (60, 110, 112, 255)},
            {"bg": (112, 128, 144, 255), "text": (255, 255, 255, 255), "border": (70, 85, 100, 255)},
            {"bg": (176, 196, 222, 255), "text": (40, 60, 100, 255), "border": (120, 145, 175, 255)},
            {"bg": (230, 230, 250, 255), "text": (60, 60, 120, 255), "border": (170, 170, 210, 255)},
            {"bg": (245, 245, 245, 255), "text": (50, 50, 50, 255), "border": (180, 180, 180, 255)},
            {"bg": (255, 250, 240, 255), "text": (80, 60, 20, 255), "border": (200, 180, 140, 255)},
            {"bg": (240, 248, 255, 255), "text": (30, 60, 100, 255), "border": (150, 190, 220, 255)},
        ],
        "font_size": 44,
        "border_width": 4,
        "radius": 20,
        "shadow": True,
    },
    "college_student": {
        "colors": [
            {"bg": (255, 105, 180, 255), "text": (255, 255, 255, 255), "border": (220, 50, 140, 255)},
            {"bg": (255, 165, 0, 255),   "text": (255, 255, 255, 255), "border": (210, 120, 0, 255)},
            {"bg": (50, 205, 50, 255),   "text": (255, 255, 255, 255), "border": (30, 160, 30, 255)},
            {"bg": (30, 144, 255, 255),  "text": (255, 255, 255, 255), "border": (10, 100, 210, 255)},
            {"bg": (255, 69, 0, 255),    "text": (255, 255, 255, 255), "border": (200, 40, 0, 255)},
            {"bg": (148, 0, 211, 255),   "text": (255, 255, 255, 255), "border": (100, 0, 160, 255)},
            {"bg": (255, 215, 0, 255),   "text": (100, 70, 0, 255),   "border": (200, 160, 0, 255)},
            {"bg": (0, 206, 209, 255),   "text": (255, 255, 255, 255), "border": (0, 150, 160, 255)},
        ],
        "font_size": 46,
        "border_width": 5,
        "radius": 50,
        "shadow": True,
    },
    "housewife": {
        "colors": [
            {"bg": (255, 228, 225, 255), "text": (180, 80, 100, 255), "border": (240, 180, 190, 255)},
            {"bg": (255, 240, 200, 255), "text": (160, 100, 30, 255), "border": (230, 200, 140, 255)},
            {"bg": (220, 245, 220, 255), "text": (60, 130, 60, 255),  "border": (170, 220, 170, 255)},
            {"bg": (220, 235, 255, 255), "text": (60, 90, 170, 255),  "border": (170, 200, 240, 255)},
            {"bg": (250, 220, 250, 255), "text": (130, 50, 150, 255), "border": (210, 170, 220, 255)},
            {"bg": (255, 245, 220, 255), "text": (150, 100, 30, 255), "border": (230, 210, 160, 255)},
            {"bg": (225, 245, 240, 255), "text": (40, 120, 100, 255), "border": (170, 220, 210, 255)},
            {"bg": (255, 235, 240, 255), "text": (170, 60, 90, 255),  "border": (230, 190, 200, 255)},
        ],
        "font_size": 44,
        "border_width": 3,
        "radius": 60,
        "shadow": False,
    },
    "teenager": {
        "colors": [
            {"bg": (255, 182, 193, 255), "text": (180, 0, 80, 255),   "border": (255, 100, 150, 255)},
            {"bg": (173, 216, 230, 255), "text": (0, 80, 160, 255),   "border": (100, 180, 220, 255)},
            {"bg": (144, 238, 144, 255), "text": (0, 100, 0, 255),    "border": (80, 200, 80, 255)},
            {"bg": (255, 255, 153, 255), "text": (130, 100, 0, 255),  "border": (220, 210, 0, 255)},
            {"bg": (216, 191, 216, 255), "text": (100, 0, 130, 255),  "border": (180, 140, 200, 255)},
            {"bg": (255, 200, 150, 255), "text": (160, 60, 0, 255),   "border": (230, 150, 80, 255)},
            {"bg": (150, 230, 230, 255), "text": (0, 100, 110, 255),  "border": (80, 190, 200, 255)},
            {"bg": (255, 160, 180, 255), "text": (150, 0, 60, 255),   "border": (220, 100, 130, 255)},
        ],
        "font_size": 48,
        "border_width": 4,
        "radius": 70,
        "shadow": True,
    },
}

# デフォルトデザイン（themes.jsonに新テーマ追加した時のフォールバック）
DEFAULT_DESIGN = {
    "colors": [
        {"bg": (255, 220, 100, 255), "text": (80, 50, 0, 255), "border": (200, 160, 50, 255)},
        {"bg": (100, 200, 255, 255), "text": (0, 50, 120, 255), "border": (50, 150, 220, 255)},
        {"bg": (255, 150, 150, 255), "text": (120, 0, 0, 255), "border": (210, 80, 80, 255)},
        {"bg": (150, 230, 150, 255), "text": (0, 80, 0, 255), "border": (80, 180, 80, 255)},
        {"bg": (200, 150, 255, 255), "text": (60, 0, 120, 255), "border": (150, 90, 220, 255)},
        {"bg": (255, 180, 100, 255), "text": (100, 40, 0, 255), "border": (210, 130, 40, 255)},
        {"bg": (150, 230, 230, 255), "text": (0, 80, 80, 255), "border": (80, 180, 180, 255)},
        {"bg": (255, 200, 220, 255), "text": (120, 0, 60, 255), "border": (210, 140, 170, 255)},
    ],
    "font_size": 48,
    "border_width": 4,
    "radius": 40,
    "shadow": False,
}


def generate_phrases(theme):
    """Gemini APIでフレーズを自動生成"""
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
LINEスタンプ用のフレーズを8個考えてください。

テーマ: {theme["target"]}向け・{theme["style"]}
条件:
- 日本語で短いフレーズ（10文字以内）
- LINEで実際に使いやすいもの
- 重複なし

以下のJSON形式のみで返してください。説明文は不要です。
{{"phrases": ["フレーズ1", "フレーズ2", "フレーズ3", "フレーズ4", "フレーズ5", "フレーズ6", "フレーズ7", "フレーズ8"]}}
"""

    response = model.generate_content(prompt)
    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    data = json.loads(text)
    return data["phrases"]


def create_stamp(phrase, output_path, color, design):
    """1枚のスタンプ画像を生成"""
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = 10
    radius = design["radius"]
    border_width = design["border_width"]

    # 影
    if design["shadow"]:
        shadow_offset = 4
        draw.rounded_rectangle(
            [margin + shadow_offset, margin + shadow_offset,
             WIDTH - margin + shadow_offset, HEIGHT - margin + shadow_offset],
            radius=radius,
            fill=(0, 0, 0, 60)
        )

    # 枠線
    draw.rounded_rectangle(
        [margin, margin, WIDTH - margin, HEIGHT - margin],
        radius=radius,
        fill=color["border"]
    )

    # 背景
    draw.rounded_rectangle(
        [margin + border_width, margin + border_width,
         WIDTH - margin - border_width, HEIGHT - margin - border_width],
        radius=max(radius - border_width, 0),
        fill=color["bg"]
    )

    # フォント
    font = ImageFont.truetype(FONT_PATH, design["font_size"])

    # テキスト中央配置
    bbox = draw.textbbox((0, 0), phrase, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (WIDTH - text_w) / 2
    y = (HEIGHT - text_h) / 2

    draw.text((x, y), phrase, font=font, fill=color["text"])

    img.save(output_path, "PNG")
    print(f"生成: {phrase} → {output_path}")


def create_stamp_set(stamp_set):
    """1セット分のスタンプを生成してZIP化"""
    set_id = stamp_set["id"]

    print(f"フレーズ生成中: {stamp_set['target']}")
    phrases = generate_phrases(stamp_set)
    print(f"生成されたフレーズ: {phrases}")

    # デザイン設定を取得（なければデフォルト）
    design = THEME_DESIGNS.get(set_id, DEFAULT_DESIGN)

    set_dir = os.path.join(OUTPUT_DIR, set_id)
    os.makedirs(set_dir, exist_ok=True)

    image_paths = []
    for i, phrase in enumerate(phrases[:8]):
        color = design["colors"][i % len(design["colors"])]
        output_path = os.path.join(set_dir, f"stamp_{i+1:02d}.png")
        create_stamp(phrase, output_path, color, design)
        image_paths.append(output_path)

    # ZIP化
    zip_path = os.path.join(OUTPUT_DIR, f"{set_id}.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        for path in image_paths:
            zf.write(path, os.path.basename(path))
    print(f"ZIP作成: {zip_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(THEMES_PATH, "r", encoding="utf-8") as f:
        themes = json.load(f)

    for stamp_set in themes["stamp_sets"]:
        create_stamp_set(stamp_set)

    print("完了！")


if __name__ == "__main__":
    main()
