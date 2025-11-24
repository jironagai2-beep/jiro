import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

# === ここを書き換える ===
my_login = 12345678          # 口座ID（数字なのでクォートなし）
my_password = "password"     # パスワード
my_server = "XMTrading-MT5-2" # サーバー名（メールを確認）
# ========================

print("MT5への接続を試みます...")

# 1. MT5と接続・ログイン
if not mt5.initialize(login=my_login, server=my_server, password=my_password):
    print("❌ 接続失敗")
    print("エラーコード:", mt5.last_error())
    quit()
else:
    print("✅ 接続成功！")

# 2. USDJPYの最新価格を取得してみる
symbol = "USDJPY"

# 気配値に通貨ペアが表示されているか確認・有効化
selected = mt5.symbol_select(symbol, True)
if not selected:
    print(f"{symbol} が見つかりません。気配値に追加してください。")
    mt5.shutdown()
    quit()

# 最新の価格情報（Tick）を取得
last_tick = mt5.symbol_info_tick(symbol)

if last_tick:
    print(f"\n--- {symbol} 現在レート ---")
    print(f"時間: {datetime.fromtimestamp(last_tick.time)}")
    print(f"売値(Bid): {last_tick.bid}")
    print(f"買値(Ask): {last_tick.ask}")
    print("------------------------")
else:
    print("価格取得に失敗しました")

# 3. 過去データ（1分足）を10本取ってみる
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 10)
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s') # 時間を見やすく変換

print("\n--- 直近10本の1分足データ ---")
print(df[['time', 'open', 'high', 'low', 'close', 'tick_volume']])

# 接続終了
mt5.shutdown()
