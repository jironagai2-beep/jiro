"""
静的HTMLダッシュボード用のシンプルなFastAPIサーバー
"""
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="7通貨ペア監視システム")

# 静的ファイルのディレクトリ
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
async def root():
    """ルートパス - ダッシュボードにリダイレクト"""
    return FileResponse(os.path.join(STATIC_DIR, "dashboard_static.html"))

@app.get("/dashboard_static.html")
async def dashboard():
    """ダッシュボードHTML"""
    return FileResponse(os.path.join(STATIC_DIR, "dashboard_static.html"))

@app.get("/backtest_chart.png")
async def chart():
    """チャート画像"""
    chart_path = os.path.join(STATIC_DIR, "backtest_chart.png")
    if os.path.exists(chart_path):
        return FileResponse(chart_path)
    else:
        return {"detail": "Chart not found"}

@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {"status": "ok", "message": "Server is running"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 サーバー起動中...")
    print("📊 ダッシュボード: http://localhost:8000")
    print("📊 直接アクセス: http://localhost:8000/dashboard_static.html")
    uvicorn.run(app, host="0.0.0.0", port=8000)
