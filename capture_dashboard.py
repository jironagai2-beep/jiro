"""
ダッシュボードのスクリーンショットを撮影
"""
from playwright.sync_api import sync_playwright
import time

def capture_dashboard():
    with sync_playwright() as p:
        # ブラウザを起動
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})

        # ローカルサーバーのダッシュボードにアクセス
        page.goto('http://localhost:8000/dashboard_static.html')

        # ページが完全に読み込まれるまで待つ
        time.sleep(2)

        # スクリーンショットを保存
        page.screenshot(path='dashboard_screenshot.png', full_page=True)

        browser.close()
        print("✅ スクリーンショットを保存しました: dashboard_screenshot.png")

if __name__ == "__main__":
    capture_dashboard()
