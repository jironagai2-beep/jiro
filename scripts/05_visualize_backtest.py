"""
バックテスト結果のチャート可視化
"""

import sys
sys.path.insert(0, '/home/user/jiro/src')

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from data_loader import DataLoader
from backtest_engine import BacktestEngine
from trading_system import TradingConfig

def visualize_backtest():
    """バックテスト結果をチャート表示"""

    # データ読み込み
    loader = DataLoader()
    df = loader.load_ohlcv('USDJPY_1m.csv')

    print(f'データ読み込み: {len(df)}行')

    # バックテスト実行
    config = TradingConfig()
    engine = BacktestEngine(config)
    result = engine.run(df)

    # チャート作成
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # サブプロット1: 価格とMA
    ax1.plot(result.index, result['close'], label='Close Price', linewidth=1.5, color='black')
    ax1.plot(result.index, result['ma_fast'], label=f'MA{config.ma_fast_length}', linewidth=1, alpha=0.7, color='blue')
    ax1.plot(result.index, result['ma_mid'], label=f'MA{config.ma_mid_length}', linewidth=1, alpha=0.7, color='orange')
    ax1.plot(result.index, result['ma_slow'], label=f'MA{config.ma_slow_length}', linewidth=1, alpha=0.7, color='red')

    # シグナルをプロット
    buy_signals = result[result['final_buy_signal']]
    sell_signals = result[result['final_sell_signal']]

    if len(buy_signals) > 0:
        ax1.scatter(buy_signals.index, buy_signals['close'],
                   marker='^', color='green', s=100, label='Buy Signal', zorder=5)

    if len(sell_signals) > 0:
        ax1.scatter(sell_signals.index, sell_signals['close'],
                   marker='v', color='red', s=100, label='Sell Signal', zorder=5)

    ax1.set_ylabel('Price', fontsize=12)
    ax1.set_title('Pine Script to Python バックテスト結果', fontsize=14, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)

    # サブプロット2: 連続ローソク足
    if 'consecutive_bullish' in result.columns:
        ax2.bar(result.index, result['consecutive_bullish'],
               label='Consecutive Bullish', color='green', alpha=0.6)
        ax2.bar(result.index, result['consecutive_bearish'],
               label='Consecutive Bearish', color='red', alpha=0.6)
        ax2.set_ylabel('Consecutive Candles', fontsize=12)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linewidth=0.5)

    # X軸フォーマット
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)

    plt.tight_layout()

    # 保存
    output_path = '/home/user/jiro/backtest_chart.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f'\nチャート保存: {output_path}')

    # 統計情報
    print(f'\n=== 統計情報 ===')
    print(f'期間: {result.index[0]} ~ {result.index[-1]}')
    print(f'価格範囲: {result["close"].min():.3f} - {result["close"].max():.3f}')
    print(f'Buy シグナル: {len(buy_signals)}回')
    print(f'Sell シグナル: {len(sell_signals)}回')

    if 'consecutive_bullish' in result.columns:
        print(f'最大連続陽線: {result["consecutive_bullish"].max()}')
        print(f'最大連続陰線: {abs(result["consecutive_bearish"].min())}')

    return output_path

if __name__ == '__main__':
    visualize_backtest()
