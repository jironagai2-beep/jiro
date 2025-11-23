#!/usr/bin/env python3
"""
不一致分析ツール

Python実装とPine Scriptの不一致を詳細に分析します。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
import numpy as np
from data_loader import DataLoader
from indicators import Indicators


class MismatchAnalyzer:
    """不一致分析クラス"""

    def __init__(self):
        self.loader = DataLoader()

    def analyze_indicator_mismatch(
        self,
        indicator_name: str,
        python_values: pd.Series,
        pine_values: pd.Series,
        max_display: int = 20
    ):
        """
        インジケーターの不一致を分析

        Args:
            indicator_name: インジケーター名
            python_values: Python実装の値
            pine_values: Pine Scriptの値
            max_display: 最大表示件数
        """
        print("=" * 70)
        print(f"{indicator_name} 不一致分析")
        print("=" * 70)

        # 共通インデックス
        common_index = python_values.index.intersection(pine_values.index)
        py_vals = python_values.loc[common_index]
        pine_vals = pine_values.loc[common_index]

        # NaN除外
        valid_mask = ~(py_vals.isna() | pine_vals.isna())
        py_vals_valid = py_vals[valid_mask]
        pine_vals_valid = pine_vals[valid_mask]

        # 誤差計算
        abs_diff = abs(py_vals_valid - pine_vals_valid)
        rel_diff = abs_diff / abs(pine_vals_valid + 1e-10)

        # 統計情報
        print(f"\n統計情報:")
        print(f"  総データ数: {len(py_vals_valid)}")
        print(f"  最大絶対誤差: {abs_diff.max():.10f}")
        print(f"  平均絶対誤差: {abs_diff.mean():.10f}")
        print(f"  最大相対誤差: {rel_diff.max():.10f}")
        print(f"  平均相対誤差: {rel_diff.mean():.10f}")

        # 誤差分布
        print(f"\n誤差分布:")
        percentiles = [50, 75, 90, 95, 99, 99.9]
        for p in percentiles:
            val = np.percentile(abs_diff, p)
            print(f"  {p}パーセンタイル: {val:.10f}")

        # 最大誤差の詳細
        print(f"\n最大誤差の詳細（上位{max_display}件）:")
        top_errors = abs_diff.nlargest(max_display)

        for idx in top_errors.index:
            py_val = py_vals.loc[idx]
            pine_val = pine_vals.loc[idx]
            diff = abs_diff.loc[idx]
            rel = rel_diff.loc[idx]

            print(f"  {idx}")
            print(f"    Python: {py_val:.10f}")
            print(f"    Pine:   {pine_val:.10f}")
            print(f"    絶対誤差: {diff:.10f}")
            print(f"    相対誤差: {rel:.10%}")

        # 時系列パターン分析
        self._analyze_temporal_pattern(abs_diff)

    def _analyze_temporal_pattern(self, diff_series: pd.Series):
        """時系列パターンを分析"""
        print(f"\n時系列パターン分析:")

        # 初期値付近の誤差
        initial_errors = diff_series.head(50)
        print(f"  初期50件の平均誤差: {initial_errors.mean():.10f}")

        # 後半の誤差
        later_errors = diff_series.tail(50)
        print(f"  後半50件の平均誤差: {later_errors.mean():.10f}")

        # 誤差の増加傾向
        if initial_errors.mean() < later_errors.mean():
            ratio = later_errors.mean() / (initial_errors.mean() + 1e-10)
            print(f"  → 誤差が増加傾向（{ratio:.2f}倍）")
            print(f"     原因候補: 浮動小数点の累積誤差、計算順序の違い")
        else:
            print(f"  → 誤差は安定")

    def analyze_signal_mismatch(
        self,
        signal_name: str,
        python_signals: pd.Series,
        pine_signals: pd.Series,
        ohlcv: pd.DataFrame
    ):
        """
        シグナルの不一致を分析

        Args:
            signal_name: シグナル名
            python_signals: Python実装のシグナル
            pine_signals: Pine Scriptのシグナル
            ohlcv: OHLCVデータ
        """
        print("=" * 70)
        print(f"{signal_name} 不一致分析")
        print("=" * 70)

        # 共通インデックス
        common_index = python_signals.index.intersection(pine_signals.index)
        py_sig = python_signals.loc[common_index].astype(bool)
        pine_sig = pine_signals.loc[common_index].astype(bool)

        # 不一致箇所
        mismatches = py_sig != pine_sig

        print(f"\n統計情報:")
        print(f"  総データ数: {len(py_sig)}")
        print(f"  Python検知: {py_sig.sum()}回")
        print(f"  Pine検知: {pine_sig.sum()}回")
        print(f"  不一致数: {mismatches.sum()}件")
        print(f"  一致率: {(~mismatches).sum() / len(py_sig) * 100:.2f}%")

        # 不一致の詳細
        print(f"\n不一致の詳細:")
        mismatch_indices = mismatches[mismatches].index

        for idx in mismatch_indices[:20]:  # 最大20件
            py_val = py_sig.loc[idx]
            pine_val = pine_sig.loc[idx]

            print(f"\n  {idx}")
            print(f"    Python: {py_val} | Pine: {pine_val}")

            # 周辺のOHLCVデータを表示
            if idx in ohlcv.index:
                loc = ohlcv.index.get_loc(idx)
                context_start = max(0, loc - 2)
                context_end = min(len(ohlcv), loc + 3)
                context = ohlcv.iloc[context_start:context_end]

                print(f"    周辺のOHLCV:")
                for ctx_idx, row in context.iterrows():
                    marker = "  →" if ctx_idx == idx else "   "
                    print(f"{marker} {ctx_idx}: "
                          f"O={row['open']:.3f} "
                          f"H={row['high']:.3f} "
                          f"L={row['low']:.3f} "
                          f"C={row['close']:.3f}")

    def run_full_analysis(self):
        """完全な不一致分析を実行"""
        print("\n" + "=" * 70)
        print("不一致分析ツール")
        print("=" * 70 + "\n")

        # データ読み込み
        try:
            ohlcv = self.loader.load_ohlcv()
            pine = self.loader.load_pine_signals()
        except FileNotFoundError as e:
            print(f"エラー: {e}")
            sys.exit(1)

        # MA検証
        ma_periods = [20, 50, 100, 200]
        for period in ma_periods:
            col_name = f'ma{period}'
            if col_name not in pine.columns:
                continue

            python_ma = Indicators.sma(ohlcv['close'], period)
            self.analyze_indicator_mismatch(
                f"SMA({period})",
                python_ma,
                pine[col_name],
                max_display=10
            )
            print("\n")

        # シグナル検証
        if 'long_signal' in pine.columns and 'ma20' in pine.columns and 'ma50' in pine.columns:
            ma20 = Indicators.sma(ohlcv['close'], 20)
            ma50 = Indicators.sma(ohlcv['close'], 50)
            python_long = Indicators.crossover(ma20, ma50)

            self.analyze_signal_mismatch(
                "Long Signal",
                python_long,
                pine['long_signal'],
                ohlcv
            )
            print("\n")


if __name__ == "__main__":
    analyzer = MismatchAnalyzer()
    analyzer.run_full_analysis()
