"""
7通貨ペア監視ダッシュボードの画像を生成
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_dashboard():
    # キャンバスサイズ
    width = 1920
    height = 1200

    # 背景色
    bg_color = (14, 17, 23)  # #0e1117
    card_color = (30, 33, 48)  # #1e2130
    text_color = (255, 255, 255)
    title_color = (77, 166, 255)  # #4da6ff
    green_color = (0, 255, 0)

    # 画像を作成
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # フォント設定（デフォルトフォント）
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        normal_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        title_font = header_font = normal_font = small_font = ImageFont.load_default()

    # ヘッダー
    draw.text((40, 30), "📊 7通貨ペア監視システム", fill=title_color, font=title_font)
    draw.text((1650, 40), "🟢 Server: Connected", fill=green_color, font=normal_font)

    # 通貨ペアデータ
    pairs = [
        {"name": "BTC/USD", "price": "84186.040", "signals": "0", "winrate": "0%"},
        {"name": "USD/JPY", "price": "150.433", "signals": "0", "winrate": "0%"},
        {"name": "EUR/USD", "price": "1.498", "signals": "0", "winrate": "0%"},
        {"name": "GBP/JPY", "price": "150.229", "signals": "0", "winrate": "0%"},
        {"name": "AUD/USD", "price": "1.499", "signals": "0", "winrate": "0%"},
        {"name": "AUD/JPY", "price": "150.389", "signals": "0", "winrate": "0%"},
        {"name": "EUR/JPY", "price": "150.411", "signals": "0", "winrate": "0%"},
    ]

    # 左側: 通貨ペアカード (2列x4行)
    card_width = 280
    card_height = 180
    start_x = 40
    start_y = 100
    gap = 20

    for i, pair in enumerate(pairs):
        row = i // 2
        col = i % 2

        x = start_x + col * (card_width + gap)
        y = start_y + row * (card_height + gap)

        # カード背景
        draw.rectangle([x, y, x + card_width, y + card_height], fill=card_color, outline=(45, 49, 66), width=1)

        # 通貨ペア名
        draw.text((x + 15, y + 15), pair['name'], fill=title_color, font=header_font)

        # 価格
        draw.text((x + 15, y + 55), pair['price'], fill=text_color, font=title_font)

        # 運勝数と勝率
        draw.text((x + 15, y + 110), "運勝数", fill=(136, 136, 136), font=small_font)
        draw.text((x + 15, y + 130), pair['signals'], fill=text_color, font=normal_font)

        draw.text((x + 150, y + 110), "勝率", fill=(136, 136, 136), font=small_font)
        draw.text((x + 150, y + 130), pair['winrate'], fill=text_color, font=normal_font)

    # 右側: チャートエリア
    chart_x = 640
    chart_y = 100
    chart_width = 1240
    chart_height = 900

    # チャート背景
    draw.rectangle([chart_x, chart_y, chart_x + chart_width, chart_y + chart_height],
                   fill=card_color, outline=(45, 49, 66), width=1)

    # チャートタイトル
    draw.text((chart_x + 20, chart_y + 20), "📈 チャート (BTC/USD)", fill=title_color, font=header_font)

    # バックテストチャートを読み込んで配置 (ワークスペース相対パス)
    try:
        chart_path = os.path.join(os.path.dirname(__file__), 'backtest_chart.png')
        chart_img = Image.open(chart_path)
        # チャート画像をリサイズ
        try:
            resample_method = Image.Resampling.LANCZOS
        except AttributeError:
            resample_method = Image.LANCZOS
        chart_img = chart_img.resize((1200, 800), resample_method)
        # チャートを貼り付け
        img.paste(chart_img, (chart_x + 20, chart_y + 60))
    except Exception:
        draw.text((chart_x + 500, chart_y + 400), "チャート読み込みエラー", fill=text_color, font=normal_font)

    # 凡例
    legend_y = chart_y + 880
    draw.text((chart_x + 20, legend_y), "● MA Fast", fill=(255, 235, 59), font=small_font)
    draw.text((chart_x + 150, legend_y), "● MA Mid", fill=(255, 152, 0), font=small_font)
    draw.text((chart_x + 280, legend_y), "● MA Slow", fill=(244, 67, 54), font=small_font)

    # フッター
    from datetime import datetime
    footer_text = f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    draw.text((width // 2 - 150, height - 50), footer_text, fill=(136, 136, 136), font=small_font)

    # 保存
    img.save('dashboard_complete.png')
    print("✅ ダッシュボード画像を生成しました: dashboard_complete.png")

if __name__ == "__main__":
    create_dashboard()
