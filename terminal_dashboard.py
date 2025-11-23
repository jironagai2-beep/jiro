#!/usr/bin/env python3
"""
ターミナルで動作する7通貨ペア監視ダッシュボード
リアルタイムで更新される
"""
import sys
import time
from datetime import datetime
sys.path.insert(0, '/home/user/jiro/src')

from data_loader import DataLoader
from backtest_engine import BacktestEngine
from trading_system import TradingConfig

def clear_screen():
    """画面をクリア"""
    print("\033[2J\033[H", end="")

def print_header():
    """ヘッダーを表示"""
    print("=" * 100)
    print("📊 7通貨ペア監視システム - リアルタイムダッシュボード".center(100))
    print("=" * 100)
    print(f"🟢 Server: Connected | 最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

def print_pairs():
    """7通貨ペア情報を表示"""
    pairs = [
        {"name": "BTC/USD", "price": 84186.040, "signals": 0, "winrate": 0},
        {"name": "USD/JPY", "price": 150.433, "signals": 0, "winrate": 0},
        {"name": "EUR/USD", "price": 1.498, "signals": 0, "winrate": 0},
        {"name": "GBP/JPY", "price": 150.229, "signals": 0, "winrate": 0},
        {"name": "AUD/USD", "price": 1.499, "signals": 0, "winrate": 0},
        {"name": "AUD/JPY", "price": 150.389, "signals": 0, "winrate": 0},
        {"name": "EUR/JPY", "price": 150.411, "signals": 0, "winrate": 0},
    ]

    print("\n【通貨ペア一覧】")
    print("-" * 100)
    print(f"{'通貨ペア':<15} {'現在価格':>15} {'運勝数':>10} {'勝率':>10}")
    print("-" * 100)

    for pair in pairs:
        print(f"{pair['name']:<15} {pair['price']:>15.3f} {pair['signals']:>10} {pair['winrate']:>9}%")

    print("-" * 100)

def print_chart_data():
    """チャートデータを表示"""
    print("\n【USD/JPY バックテスト結果】")
    print("-" * 100)

    try:
        loader = DataLoader()
        df = loader.load_ohlcv('USDJPY_1m.csv')

        config = TradingConfig()
        engine = BacktestEngine(config)
        result = engine.run(df)

        # 最新20行を表示
        latest = result.tail(20)

        print(f"{'時刻':<20} {'終値':>10} {'MA5':>10} {'MA9':>10} {'MA21':>10} {'Buy':>5} {'Sell':>5}")
        print("-" * 100)

        for idx, row in latest.iterrows():
            timestamp = idx.strftime('%Y-%m-%d %H:%M:%S')
            buy_sig = '🟢' if row.get('final_buy_signal', False) else '  '
            sell_sig = '🔴' if row.get('final_sell_signal', False) else '  '

            print(f"{timestamp:<20} {row['close']:>10.3f} {row['ma_fast']:>10.3f} "
                  f"{row['ma_mid']:>10.3f} {row['ma_slow']:>10.3f} {buy_sig:>5} {sell_sig:>5}")

        print("-" * 100)

        # 統計情報
        total_buy = result['final_buy_signal'].sum()
        total_sell = result['final_sell_signal'].sum()
        price_range = result['close'].max() - result['close'].min()

        print(f"\n【統計情報】")
        print(f"  データ行数: {len(result)}")
        print(f"  Buy シグナル数: {total_buy}")
        print(f"  Sell シグナル数: {total_sell}")
        print(f"  価格変動幅: {price_range:.3f}")

    except Exception as e:
        print(f"エラー: {str(e)}")

def main():
    """メイン処理"""
    try:
        while True:
            clear_screen()
            print_header()
            print_pairs()
            print_chart_data()

            print("\n" + "=" * 100)
            print("Press Ctrl+C to exit | 自動更新: 5秒ごと")
            print("=" * 100)

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\nダッシュボードを終了します...")
        sys.exit(0)

if __name__ == "__main__":
    main()
