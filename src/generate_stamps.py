import json
import os
import zipfile
from PIL import Image, ImageDraw, ImageFont

# パス設定
THEMES_PATH = "themes/stamp_themes.json"
FONT_PATH = "fonts/NotoSansJP-Bold.ttf"
OUTPUT_DIR = "output"

# LINE規格
WIDTH = 370
HEIGHT = 320
FONT_SIZE = 48


def create_stamp(phrase, output_path, bg_color, text_color):
    """1枚のスタンプ画像を生成"""
    # 透過PNG作成
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
    phrases = stamp_set["phrases"]

    # 出力フォルダ作成
    set_dir = os.path.join(OUTPUT_DIR, set_id)
    os.makedirs(set_dir, exist_ok=True)

    # カラーパターン（フレーズごとに色を変える）
    colors = [
        {"bg": (255, 220, 100, 255), "text": (80, 50, 0, 255)},    # 黄
        {"bg": (100, 200, 255, 255), "text": (0, 50, 120, 255)},    # 青
        {"bg": (255, 150, 150, 255), "text": (120, 0, 0, 255)},     # 赤
        {"bg": (150, 230, 150, 255), "text": (0, 80, 0, 255)},      # 緑
        {"bg": (200, 150, 255, 255), "text": (60, 0, 120, 255)},    # 紫
        {"bg": (255, 180, 100, 255), "text": (100, 40, 0, 255)},    # オレンジ
        {"bg": (150, 230, 230, 255), "text": (0, 80, 80, 255)},     # シアン
        {"bg": (255, 200, 220, 255), "text": (120, 0, 60, 255)},    # ピンク
    ]

    image_paths = []
    for i, phrase in enumerate(phrases[:8]):  # 最大8枚
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
