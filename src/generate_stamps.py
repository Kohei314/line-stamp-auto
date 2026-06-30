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
    {"bg": (74, 112, 48), "inner": (255, 255, 255), "text": (30, 60, 20)},
    {"bg": (74, 112, 48), "inner": (255, 255, 255), "text": (30, 60, 20)},
    {"bg": (74, 112, 48), "inner": (255, 255, 255), "text": (30, 60, 20)},
    {"bg": (74, 112, 48), "inner": (255, 255, 255), "text": (30, 60, 20)},
    {"bg": (74, 112, 48), "inner": (255, 255, 255), "text": (30, 60, 20)},
    {"bg": (74, 112, 48), "inner": (255, 255, 255), "text": (30, 60, 20)},
    {"bg": (74, 112, 48), "inner": (255, 255, 255), "text": (30, 60, 20)},
    {"bg": (74, 112, 48), "inner": (255, 255, 255), "text": (30, 60, 20)},
]


def generate_haiku(theme, api_key):
    import google.generativeai as genai
    import time
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
LINEスタンプ用の川柳（5・7・5）を8句考えてください。

テーマ: {theme["target"]}向け・{theme["style"]}
条件:
- p1は5文字程度（4～6文字なら可）
- p2は7文字程度（6～8文字なら可）
- p3は5文字程度（4～6文字なら可）
- シュールで思わず笑えるもの、または日常でLINEで使えるもの
- 重複なし

以下のJSON形式のみで返してください。説明文は不要です。
{{"haiku": [
  {{"p1": "5文字", "p2": "7文字", "p3": "5文字"}}
]}}
"""
    response = model.generate_content(prompt)
    text = response.text.strip().replace("```json", "").replace("```", "").strip()
    data = json.loads(text)
    
    # バリデーション：4・6・4をチェック
    valid_haiku = []
    for haiku in data["haiku"]:
        p1_len = len(haiku["p1"])
        p2_len = len(haiku["p2"])
        p3_len = len(haiku["p3"])
        
        if 4 <= p1_len <= 6 and 6 <= p2_len <= 8 and 4 <= p3_len <= 6:
            valid_haiku.append(haiku)
        else:
            print(f"スキップ（フォーマット不正）: {haiku['p1']}({p1_len})/{haiku['p2']}({p2_len})/{haiku['p3']}({p3_len})")
    
    # 不足分はダミーで埋める
    while len(valid_haiku) < 8:
        valid_haiku.append({"p1": "dummy", "p2": "dummy01", "p3": "test!"})
    
    time.sleep(15)
    return valid_haiku[:8]


def create_shikishi_stamp(haiku, output_path, design):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = 10
    border = 8
    radius = 30

    draw.rounded_rectangle(
        [margin, margin, WIDTH - margin, HEIGHT - margin],
        radius=radius,
        fill=(*design["bg"], 255)
    )
    draw.rounded_rectangle(
        [margin + border, margin + border,
         WIDTH - margin - border, HEIGHT - margin - border],
        radius=max(radius - border, 0),
        fill=(*design["inner"], 255)
    )

    p1 = haiku["p1"]
    p2 = haiku["p2"]
    p3 = haiku["p3"]

    # フォントサイズを最大文字数に応じて自動調整
    max_chars = max(len(p1), len(p2), len(p3))
    usable_height = HEIGHT - 90
    font_size = max(20, int(usable_height / max_chars) - 2)
    font_size = min(32, font_size)

    font = ImageFont.truetype(FONT_PATH, font_size)

    char_h = font_size + 3
    char_w = font_size + 2

    total_w = char_w * 3 + 10 * 2
    start_x = (WIDTH - total_w) // 2 + total_w - char_w

    inner_top = margin + border + 12

    x1 = start_x
    x2 = start_x - char_w - 10
    x3 = start_x - (char_w + 10) * 2

    y1 = inner_top
    y2 = inner_top + char_h * 0.2
    y3 = inner_top + char_h * 0.4

    for char in p1:
        draw.text((x1, y1), char, font=font, fill=(*design["text"], 255))
        y1 += char_h

    for char in p2:
        draw.text((x2, y2), char, font=font, fill=(*design["text"], 255))
        y2 += char_h

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
        output_path = os.path.join(set_dir, f"{i+1:02d}.png")
        create_shikishi_stamp(haiku, output_path, design)
        image_paths.append(output_path)

    # メイン画像・タブ画像を同じフォルダに生成
    first_stamp = os.path.join(set_dir, "01.png")
    main_path = os.path.join(set_dir, "main.png")
    tab_path = os.path.join(set_dir, "tab.png")
    
    if os.path.exists(first_stamp):
        main_img = Image.open(first_stamp).convert("RGBA")
        main_img = main_img.resize((240, 240), Image.Resampling.LANCZOS)
        main_img.save(main_path)
        image_paths.insert(0, main_path)
        
        tab_img = Image.open(first_stamp).convert("RGBA")
        tab_img = tab_img.resize((96, 74), Image.Resampling.LANCZOS)
        tab_img.save(tab_path)
        image_paths.insert(1, tab_path)

    # ZIP化（main、tab、stamp_01～08を全部含める）
    zip_path = os.path.join(OUTPUT_DIR, f"{set_id}.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        for path in image_paths:
            zf.write(path, arcname=os.path.basename(path))
    print(f"ZIP作成: {zip_path}")


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(THEMES_PATH, "r", encoding="utf-8") as f:
        themes = json.load(f)
    
    run_number = int(os.environ.get("GITHUB_RUN_NUMBER", "0"))
    stamp_sets = themes["stamp_sets"]
    selected = stamp_sets[run_number % len(stamp_sets)]
    
    print(f"今回のテーマ: {selected['target']}（{selected['id']}）")
    create_stamp_set(selected, api_key)

    print("完了！")


if __name__ == "__main__":
    main()
