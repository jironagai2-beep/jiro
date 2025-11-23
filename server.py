"""
静的HTMLダッシュボード用のシンプルなFastAPIサーバー
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import os
import asyncio
import random
import json

app = FastAPI(title="7通貨ペア監視システム")

# --- WebSocket connections ---
clients = set()


async def price_generator_task():
    """Background task that simulates price ticks and broadcasts to connected clients."""
    # initial prices (match dashboard_static.html defaults)
    pairs = {
        "BTC/USD": 84186.040,
        "USD/JPY": 150.433,
        "EUR/USD": 1.498,
        "GBP/JPY": 150.229,
        "AUD/USD": 1.499,
        "AUD/JPY": 150.389,
        "EUR/JPY": 150.411,
    }

    # build 1-minute OHLC candles for BTC/USD (keep last 120 minutes)
    import time as _time
    btc_price = pairs["BTC/USD"]
    btc_candles = []  # list of dicts: {t, o, h, l, c}

    # start current candle aligned to minute
    now = int(_time.time())
    current_minute = now - (now % 60)
    current_candle = {"t": current_minute, "o": btc_price, "h": btc_price, "l": btc_price, "c": btc_price}

    while True:
        # simulate ticks each second and update pair prices
        for k in pairs:
            change = pairs[k] * (random.uniform(-0.0008, 0.0008))
            if pairs[k] < 10:
                change = random.uniform(-0.001, 0.001)
            pairs[k] = round(pairs[k] + change, 6)

        # update BTC current candle with latest price
        btc_price = pairs["BTC/USD"]
        sec = int(_time.time())
        minute = sec - (sec % 60)

        if minute != current_candle["t"]:
            # push finished candle
            btc_candles.append(current_candle.copy())
            if len(btc_candles) > 120:
                btc_candles.pop(0)
            # start new candle
            current_candle = {"t": minute, "o": btc_price, "h": btc_price, "l": btc_price, "c": btc_price}
        else:
            # update OHLC
            current_candle["c"] = btc_price
            if btc_price > current_candle["h"]:
                current_candle["h"] = btc_price
            if btc_price < current_candle["l"]:
                current_candle["l"] = btc_price

        payload = {
            "timestamp": asyncio.get_event_loop().time(),
            "pairs": [{"name": k, "price": pairs[k]} for k in pairs],
            "btc_candles": btc_candles + [current_candle],
        }

        # broadcast
        to_remove = []
        for ws in list(clients):
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                to_remove.append(ws)

        for ws in to_remove:
            clients.discard(ws)

        await asyncio.sleep(1)


async def coinbase_ws_task():
    """Connect to Coinbase websocket and build 1-minute candles for BTC-USD."""
    import websockets as _ws
    import time as _time

    product = "BTC-USD"
    pairs["BTC/USD"] = pairs.get("BTC/USD", 0.0)

    # candle storage
    btc_candles = []
    now = int(_time.time())
    current_minute = now - (now % 60)
    current_candle = {"t": current_minute, "o": pairs["BTC/USD"], "h": pairs["BTC/USD"], "l": pairs["BTC/USD"], "c": pairs["BTC/USD"]}

    url = "wss://ws-feed.pro.coinbase.com"
    while True:
        try:
            async with _ws.connect(url) as ws:
                sub = {"type": "subscribe", "channels": [{"name": "ticker", "product_ids": [product]}]}
                await ws.send(json.dumps(sub))

                async for msg in ws:
                    try:
                        data = json.loads(msg)
                        if data.get('type') in ('ticker', 'snapshot') and data.get('product_id') == product:
                            price = float(data.get('price') or data.get('last_trade_price') or 0)
                            pairs["BTC/USD"] = price

                            sec = int(_time.time())
                            minute = sec - (sec % 60)

                            if minute != current_candle['t']:
                                btc_candles.append(current_candle.copy())
                                if len(btc_candles) > 120:
                                    btc_candles.pop(0)
                                current_candle = {"t": minute, "o": price, "h": price, "l": price, "c": price}
                            else:
                                current_candle['c'] = price
                                if price > current_candle['h']:
                                    current_candle['h'] = price
                                if price < current_candle['l']:
                                    current_candle['l'] = price

                            payload = {
                                "timestamp": asyncio.get_event_loop().time(),
                                "pairs": [{"name": k, "price": pairs[k]} for k in pairs],
                                "btc_candles": btc_candles + [current_candle],
                            }

                            to_remove = []
                            for ws_client in list(clients):
                                try:
                                    await ws_client.send_text(json.dumps(payload))
                                except Exception:
                                    to_remove.append(ws_client)
                            for ws_client in to_remove:
                                clients.discard(ws_client)
                    except Exception:
                        continue
        except Exception:
            # reconnect after short delay
            await asyncio.sleep(5)



@app.on_event("startup")
async def startup_event():
    # start background price generator or Coinbase feed depending on env
    use_coinbase = os.environ.get('USE_COINBASE', '').lower() in ('1', 'true', 'yes')
    if use_coinbase:
        asyncio.create_task(coinbase_ws_task())
    else:
        asyncio.create_task(price_generator_task())


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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            # keep connection open; generator pushes updates
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.discard(websocket)
    except Exception:
        clients.discard(websocket)

@app.get("/validation_result.html")
async def validation_result():
    """検証結果HTML"""
    return FileResponse(os.path.join(STATIC_DIR, "validation_result.html"))

@app.get("/backtest_interactive.html")
async def backtest_interactive():
    """インタラクティブバックテストダッシュボード"""
    return FileResponse(os.path.join(STATIC_DIR, "backtest_interactive.html"))

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
