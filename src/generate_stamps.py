import json
import os
import zipfile
from PIL import Image, ImageDraw, ImageFont

THEMES_PATH = "themes/stamp_themes.json"
FONT_PATH = "fonts/NotoSansJP-Bold.ttf"
OUTPUT_DIR = "output"

WIDTH = 370
HEIGHT = 320

TANZAKU_DESIGNS = [
    {"bg": (123, 160, 91),  "inner": (242, 249, 236), "border": (74, 112, 48),  "deco": "line"},
    {"bg": (232, 213, 160), "inner": (253, 248, 236), "border": (184, 148, 26), "deco": "line"},
    {"bg": (160, 200, 232), "inner": (238, 246, 255), "border": (42, 106, 154), "deco": "circle"},
    {"bg": (232, 160, 184), "inner": (255, 240, 244), "border": (160, 48, 96),  "deco": "heart"},
    {"bg": (180, 140, 210), "inner": (248, 240, 255), "border": (100, 50, 160), "deco": "line"},
    {"bg": (210, 140, 100), "inner": (255, 245, 235), "border": (150, 80, 30),  "deco": "line"},
    {"bg": (140, 200, 200), "inner": (235, 252, 252), "border": (40, 130, 130), "deco": "circle"},
    {"bg": (200, 200, 140), "inner": (252, 252, 235), "border": (120, 120, 40), "deco": "line"},
]


def generate_haiku(theme, api_key):
    """Gemini APIで川柳を自動生成"""
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


def draw_deco(draw, design, width, height):
    """上下の飾りを描画"""
    margin = 10
    border = 4
    deco = design["deco"]
    color = design["border"]

    if deco == "circle":
        cx = width // 2
        draw.ellipse([cx - 6, margin + border + 6, cx + 6, margin + border + 18], fill=color)
        draw.ellipse([cx - 18, margin + border + 10, cx - 8, margin + border + 20], fill=(*color, 160))
        draw.ellipse([cx + 8, margin + border + 10, cx + 18, margin + border + 20], fill=(*color, 160))
        draw.ellipse([cx - 6, height - margin - border - 18, cx + 6, height - margin - border - 6], fill=color)
    elif deco == "heart":
        cx = width // 2
        for ox in [-20, 0, 20]:
            x = cx + ox
            draw.ellipse([x - 5, margin + border + 6, x + 5, margin + border + 14], fill=color)
            draw.ellipse([x, margin + border + 6, x + 10, margin + border + 14], fill=color)
            draw.polygon([(x - 5, margin + border + 12), (x + 5, margin + border + 20), (x + 10, margin + border + 12)], fill=color)
        for ox in [-20, 0, 20]:
            x = cx + ox
            draw.ellipse([x - 5, height - margin - border - 20, x + 5, height - margin - border - 12], fill=color)
            draw.ellipse([x, height - margin - border - 20, x + 10, height - margin - border - 12], fill=color)
            draw.polygon([(x - 5, height - margin - border - 14), (x + 5, height - margin - border - 6), (x + 10, height - margin - border - 14)], fill=color)


def create_tanzaku_stamp(haiku, output_path, design):
    """短冊風スタンプを1枚生成"""
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = 10
    border = 4
    radius = 20

    # 外枠（短冊の色）
    draw.rounded_rectangle(
        [margin, margin, WIDTH - margin, HEIGHT - margin],
        radius=radius, fill=(*design["bg"], 255)
    )

    # 内側（和紙色）
    draw.rounded_rectangle(
        [margin + border, margin + border, WIDTH - margin - border, HEIGHT - margin - border],
        radius=max(radius - border, 0), fill=(*design["inner"], 255)
    )

    # 上下の飾り線（2本）
    line_y_top1 = margin + border + 22
    line_y_top2 = line_y_top1 + 4
    line_y_bot1 = HEIGHT - margin - border - 22
    line_y_bot2 = line_y_bot1 + 4
    for y in [line_y_top1, line_y_top2, line_y_bot1, line_y_bot2]:
        draw.line([margin + border + 10, y, WIDTH - margin - border - 10, y],
                  fill=design["border"], width=1)

    # 飾り
    draw_deco(draw, design, WIDTH, HEIGHT)

    # 川柳テキスト（縦書き・段々下がり）
    p1, p2, p3 = haiku["p1"], haiku["p2"], haiku["p3"]

    font_large = ImageFont.truetype(FONT_PATH, 30)

    # 右列（p1・5文字）→ 上から
    x1 = WIDTH - margin - border - 30
    y1_start = line_y_top2 + 20

    # 中列（p2・7文字）→ 少し下から
    x2 = x1 - 38
    y2_start = y1_start + 18

    # 左列（p3・5文字）→ さらに下から
    x3 = x2 - 38
    y3_start = y2_start + 18

    # 縦書き描画
    for char in p1:
        draw.text((x1, y1_start), char, font=font_large, fill=design["border"])
        y1_start += 34

    for char in p2:
        draw.text((x2, y2_start), char, font=font_large, fill=design["border"])
        y2_start += 34

    for char in p3:
        draw.text((x3, y3_start), char, font=font_large, fill=design["border"])
        y3_start += 34

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
        design = TANZAKU_DESIGNS[i % len(TANZAKU_DESIGNS)]
        output_path = os.path.join(set_dir, f"stamp_{i+1:02d}.png")
        create_tanzaku_stamp(haiku, output_path, design)
        image_paths.append(output_path)

    zip_path = os.path.join(OUTPUT_DIR, f"{set_id}.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        for path in image_paths:
            zf.write(path, os.path.basename(path))
    print(f"ZIP作成: {zip_path}")


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(THEMES_PATH, "r", encoding="utf-8") as f:
        themes = json.load(f)

    for stamp_set in themes["stamp_sets"]:
        create_stamp_set(stamp_set, api_key)

    print("完了！")


if __name__ == "__main__":
    main()
