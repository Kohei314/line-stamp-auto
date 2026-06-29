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
FONT_SIZE = 48


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

    # JSONを抽出
    text = text.replace("```json", "").replace("```", "").strip()
    data = json.loads(text)
    return data["phrases"]


def create_stamp(phrase, output_path, bg_color, text_color):
    """1枚のスタンプ画像を生成"""
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 背景の角丸四角形
    margin = 10
    draw.rounded_rectangle(
        [margin, margin, WIDTH - margin, HEIGHT - margin],
        radius=40,
        fill=bg_color
    )

    # フォント読み込み
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    # テキストを中央に配置
    bbox = draw.textbbox((0, 0), phrase, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (WIDTH - text_w) / 2
    y = (HEIGHT - text_h) / 2

    draw.text((x, y), phrase, font=font, fill=text_color)

    img.save(output_path, "PNG")
    print(f"生成: {phrase} → {output_path}")


def create_stamp_set(stamp_set):
    """1セット分のスタンプを生成してZIP化"""
    set_id = stamp_set["id"]

    # Gemini APIでフレーズ自動生成
    print(f"フレーズ生成中: {stamp_set['target']}")
    phrases = generate_phrases(stamp_set)
    print(f"生成されたフレーズ: {phrases}")

    # 出力フォルダ作成
    set_dir = os.path.join(OUTPUT_DIR, set_id)
    os.makedirs(set_dir, exist_ok=True)

    # カラーパターン
    colors = [
        {"bg": (255, 220, 100, 255), "text": (80, 50, 0, 255)},
        {"bg": (100, 200, 255, 255), "text": (0, 50, 120, 255)},
        {"bg": (255, 150, 150, 255), "text": (120, 0, 0, 255)},
        {"bg": (150, 230, 150, 255), "text": (0, 80, 0, 255)},
        {"bg": (200, 150, 255, 255), "text": (60, 0, 120, 255)},
        {"bg": (255, 180, 100, 255), "text": (100, 40, 0, 255)},
        {"bg": (150, 230, 230, 255), "text": (0, 80, 80, 255)},
        {"bg": (255, 200, 220, 255), "text": (120, 0, 60, 255)},
    ]

    image_paths = []
    for i, phrase in enumerate(phrases[:8]):
        color = colors[i % len(colors)]
        output_path = os.path.join(set_dir, f"stamp_{i+1:02d}.png")
        create_stamp(
            phrase,
            output_path,
            bg_color=color["bg"],
            text_color=color["text"]
        )
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
