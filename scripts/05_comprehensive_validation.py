"""
完全版Pine Script移植検証スクリプト

全インジケーターの一致率を検証します
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trading_system import TradingSystem, TradingConfig
from src.indicators import Indicators


def load_pine_signals(csv_path: str) -> pd.DataFrame:
    """
    Pine ScriptからエクスポートしたCSVを読み込み

    Args:
        csv_path: CSVファイルパス

    Returns:
        pd.DataFrame: Pine Scriptの出力データ
    """
    df = pd.read_csv(csv_path)

    # タイムスタンプをインデックスに
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

    return df


def calculate_python_indicators(ohlcv_df: pd.DataFrame) -> pd.DataFrame:
    """
    Python実装で全インジケーターを計算

    Args:
        ohlcv_df: OHLCV DataFrame

    Returns:
        pd.DataFrame: 全インジケーター付きDataFrame
    """
    config = TradingConfig(
        ma_fast_length=5,
        ma_mid_length=9,
        ma_slow_length=21,
        ma_flat_threshold=0.03,
        bb_length=20,
        bb_mult=2.0,
        bb_touch_tolerance=0.5,
        consecutive_threshold=4,
        consecutive_5_threshold=5
    )

    system = TradingSystem(config)

    # MAシグナル計算
    result = system.calculate_ma_signals(ohlcv_df)

    # 連続ローソク足検知
    consecutive_buy, consecutive_sell, bull_streak, bear_streak = \
        system.calculate_consecutive_candles(result)

    result['consecutive_buy'] = consecutive_buy
    result['consecutive_sell'] = consecutive_sell
    result['bull_streak'] = bull_streak
    result['bear_streak'] = bear_streak

    # 5連続検知
    is_5_consecutive = system.detect_5_consecutive(result)
    result['is_5_consecutive'] = is_5_consecutive

    # 環境分析
    lookback = 10
    consistency = system.calculate_directional_consistency(result, lookback)
    max_consecutive = system.detect_max_consecutive_pattern(result, lookback)
    bbw = system.calculate_bbw(result)

    result['directional_consistency'] = consistency
    result['max_consecutive_pattern'] = max_consecutive
    result['bbw'] = bbw

    # ローソク足サイズスコア
    candle_size_score = pd.Series(0.0, index=result.index)
    for i in range(lookback, len(result)):
        window = result.iloc[i-lookback+1:i+1]
        total_size = (window['high'] - window['low']).sum()
        total_body = abs(window['close'] - window['open']).sum()
        avg_size = total_size / lookback
        avg_body = total_body / lookback
        if avg_size > 0:
            candle_size_score.iloc[i] = avg_body / avg_size

    result['candle_size_score'] = candle_size_score

    return result


def compare_indicators(pine_df: pd.DataFrame, python_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pine ScriptとPythonのインジケーターを比較

    Args:
        pine_df: Pine Scriptの出力
        python_df: Pythonの計算結果

    Returns:
        pd.DataFrame: 比較結果
    """
    # インジケーター対応表
    # (Pine列名, Python列名, タイプ)
    indicators = [
        ('ma_fast', 'ma_fast', 'float'),
        ('ma_mid', 'ma_mid', 'float'),
        ('ma_slow', 'ma_slow', 'float'),
        ('bb_upper', 'bb_upper', 'float'),
        ('bb_lower', 'bb_lower', 'float'),
        ('bb_basis', 'bb_basis', 'float'),
        ('bbw', 'bbw', 'float'),
        ('ma_slope', 'ma_slope', 'float'),
        ('ma_deviation', 'ma_deviation', 'float'),
        ('is_trending', 'is_trending', 'bool'),
        ('ma_signal_buy', 'ma_signal_buy', 'bool'),
        ('ma_signal_sell', 'ma_signal_sell', 'bool'),
        ('consecutive_buy', 'consecutive_buy', 'bool'),
        ('consecutive_sell', 'consecutive_sell', 'bool'),
        ('bull_streak', 'bull_streak', 'int'),
        ('bear_streak', 'bear_streak', 'int'),
        ('is_5_consecutive', 'is_5_consecutive', 'bool'),
        ('directional_consistency', 'directional_consistency', 'float'),
        ('max_consecutive_pattern', 'max_consecutive_pattern', 'int'),
        ('candle_size_score', 'candle_size_score', 'float'),
    ]

    results = []

    for pine_col, python_col, col_type in indicators:
        if pine_col not in pine_df.columns:
            print(f"⚠️  Pine列 '{pine_col}' が見つかりません")
            continue

        if python_col not in python_df.columns:
            print(f"⚠️  Python列 '{python_col}' が見つかりません")
            continue

        # 共通インデックスで比較
        common_idx = pine_df.index.intersection(python_df.index)

        pine_vals = pine_df.loc[common_idx, pine_col]
        python_vals = python_df.loc[common_idx, python_col]

        # 比較
        if col_type == 'bool':
            # ブール値：完全一致
            pine_vals = pine_vals.astype(bool)
            python_vals = python_vals.astype(bool)
            matches = (pine_vals == python_vals).sum()
            total = len(common_idx)
            match_rate = matches / total * 100 if total > 0 else 0

        elif col_type == 'int':
            # 整数：完全一致
            pine_vals = pine_vals.astype(int)
            python_vals = python_vals.astype(int)
            matches = (pine_vals == python_vals).sum()
            total = len(common_idx)
            match_rate = matches / total * 100 if total > 0 else 0

        else:  # float
            # 浮動小数点：相対誤差1%以内を一致とみなす
            pine_vals = pine_vals.astype(float)
            python_vals = python_vals.astype(float)

            # NaN除外
            valid_mask = ~(np.isnan(pine_vals) | np.isnan(python_vals))
            pine_valid = pine_vals[valid_mask]
            python_valid = python_vals[valid_mask]

            if len(pine_valid) == 0:
                match_rate = 0
                matches = 0
                total = 0
            else:
                # 相対誤差計算
                abs_diff = np.abs(pine_valid - python_valid)
                rel_error = abs_diff / (np.abs(pine_valid) + 1e-10)

                # 1%以内を一致とみなす
                matches = (rel_error < 0.01).sum()
                total = len(pine_valid)
                match_rate = matches / total * 100 if total > 0 else 0

        results.append({
            'Indicator': pine_col,
            'Type': col_type,
            'Matches': matches,
            'Total': total,
            'Match_Rate': match_rate
        })

    return pd.DataFrame(results)


def print_validation_report(results_df: pd.DataFrame):
    """
    検証結果レポートを表示

    Args:
        results_df: 比較結果DataFrame
    """
    print("\n" + "=" * 80)
    print("Pine Script → Python 移植検証結果")
    print("=" * 80)
    print()

    # インジケーターごとの結果
    print(f"{'Indicator':<30} {'Type':<10} {'一致数':<15} {'一致率':<10}")
    print("-" * 80)

    for _, row in results_df.iterrows():
        indicator = row['Indicator']
        ind_type = row['Type']
        matches = row['Matches']
        total = row['Total']
        match_rate = row['Match_Rate']

        # 一致率による色分け
        if match_rate >= 99.0:
            status = "✅"
        elif match_rate >= 95.0:
            status = "⚠️ "
        else:
            status = "❌"

        print(f"{status} {indicator:<28} {ind_type:<10} {matches}/{total:<12} {match_rate:>6.2f}%")

    print("-" * 80)

    # 総合結果
    total_matches = results_df['Matches'].sum()
    total_comparisons = results_df['Total'].sum()
    overall_rate = total_matches / total_comparisons * 100 if total_comparisons > 0 else 0

    print(f"\n総合一致率: {overall_rate:.2f}% ({total_matches}/{total_comparisons})")

    # 目標達成判定
    if overall_rate >= 99.0:
        print("\n🎉 目標達成！ 99%以上の一致率を達成しました！")
    elif overall_rate >= 95.0:
        print("\n⚠️  惜しい！ 95%以上ですが、99%には届きませんでした。")
    else:
        print("\n❌ 一致率が低すぎます。実装を見直してください。")

    print("=" * 80)


def main():
    """メイン処理"""
    # Pine Scriptの出力CSVを読み込み
    pine_csv = "data/pine_signals_full.csv"

    if not Path(pine_csv).exists():
        print(f"❌ Pine Scriptの出力ファイルが見つかりません: {pine_csv}")
        print()
        print("手順:")
        print("1. TradingViewで scripts/02_full_export_pine_signals.pine を開く")
        print("2. チャートに適用してインジケーターを実行")
        print("3. Pine Editorのコンソールからログをコピー")
        print("4. 以下のフォーマットで保存: data/pine_signals_full.csv")
        print()
        print("CSVヘッダー:")
        print("timestamp,open,high,low,close,ma_fast,ma_mid,ma_slow,bb_upper,bb_lower,bb_basis,bbw,ma_slope,ma_deviation,is_trending,ma_signal_buy,ma_signal_sell,consecutive_buy,consecutive_sell,bull_streak,bear_streak,is_5_consecutive,directional_consistency,max_consecutive_pattern,candle_size_score,bar_index")
        return

    print("📊 Pine Script出力を読み込み中...")
    pine_df = load_pine_signals(pine_csv)
    print(f"✓ {len(pine_df)}行のデータを読み込みました")

    # OHLCV抽出
    ohlcv = pine_df[['open', 'high', 'low', 'close']].copy()

    print("\n🐍 Python側でインジケーターを計算中...")
    python_df = calculate_python_indicators(ohlcv)
    print(f"✓ {len(python_df)}行の計算が完了しました")

    print("\n🔍 インジケーターを比較中...")
    results = compare_indicators(pine_df, python_df)

    # レポート表示
    print_validation_report(results)

    # 結果をCSVに保存
    output_path = "validation_results_full.csv"
    results.to_csv(output_path, index=False)
    print(f"\n💾 詳細結果を保存しました: {output_path}")


if __name__ == "__main__":
    main()
