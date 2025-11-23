#!/usr/bin/env python3
"""
バックテスト検証スクリプト

PythonとPine Scriptの計算結果を比較し、
99%以上の一致率を達成することを目標とします。
"""

import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
from data_loader import DataLoader
from indicators import Indicators, validate_against_pine
from pattern_detector import PatternDetector, validate_pattern_against_pine
from environment import EnvironmentAnalyzer


class ValidationRunner:
    """検証実行クラス"""

    def __init__(self):
        self.loader = DataLoader()
        self.results = {}

    def load_data(self):
        """データ読み込み"""
        print("=" * 70)
        print("データ読み込み")
        print("=" * 70)

        try:
            self.ohlcv = self.loader.load_ohlcv()
            print(f"✓ OHLCV読み込み成功: {len(self.ohlcv)}行")
        except FileNotFoundError as e:
            print(f"✗ エラー: {e}")
            sys.exit(1)

        try:
            self.pine = self.loader.load_pine_signals()
            print(f"✓ Pineシグナル読み込み成功: {len(self.pine)}行")
        except FileNotFoundError as e:
            print(f"✗ エラー: {e}")
            sys.exit(1)

        # データアライメント検証
        validation = self.loader.validate_data_alignment(self.ohlcv, self.pine)
        print(f"\nデータアライメント:")
        print(f"  共通行数: {validation['common_rows']}")
        print(f"  OHLCV専用: {validation['ohlcv_only']}")
        print(f"  Pine専用: {validation['pine_only']}")

        if not validation['is_aligned']:
            print(f"  警告: {validation['messages']}")

        print()

    def validate_indicators(self):
        """インジケーター検証"""
        print("=" * 70)
        print("インジケーター検証")
        print("=" * 70)

        close = self.ohlcv['close']

        # 検証対象のMA期間（Pine Scriptに合わせて調整）
        ma_periods = [20, 50, 100, 200]

        for period in ma_periods:
            col_name = f'ma{period}'

            if col_name not in self.pine.columns:
                print(f"⊘ SMA({period}): Pine Scriptデータに{col_name}列がありません - スキップ")
                continue

            # Python実装で計算
            python_ma = Indicators.sma(close, period)

            # Pine Scriptの結果と比較
            result = validate_against_pine(
                python_ma,
                self.pine[col_name],
                tolerance=1e-5,
                name=f"SMA({period})"
            )

            self.results[f"sma{period}"] = result

            # 結果表示
            status = "✓" if result['is_valid'] else "✗"
            print(f"{status} SMA({period}): {result['match_rate']}% "
                  f"({result['matched']}/{result['total']})")

            if not result['is_valid'] and result.get('sample_mismatches'):
                print(f"  不一致サンプル（最大誤差: {result['max_diff']:.6f}）:")
                for mismatch in result['sample_mismatches'][:3]:
                    print(f"    {mismatch['timestamp']}: "
                          f"Python={mismatch['python']:.5f}, "
                          f"Pine={mismatch['pine']:.5f}, "
                          f"差={mismatch['diff']:.6f}")

        print()

    def validate_patterns(self):
        """パターン検証"""
        print("=" * 70)
        print("パターン検証")
        print("=" * 70)

        # 連続ローソク足
        if 'bullish_count' in self.pine.columns or 'bearish_count' in self.pine.columns:
            python_bullish, python_bearish = PatternDetector.consecutive_candles(
                self.ohlcv['open'],
                self.ohlcv['close']
            )

            if 'bullish_count' in self.pine.columns:
                result = validate_pattern_against_pine(
                    python_bullish,
                    self.pine['bullish_count'],
                    name="Bullish Consecutive"
                )
                self.results['bullish_consecutive'] = result
                status = "✓" if result['is_valid'] else "✗"
                print(f"{status} 連続陽線: {result['match_rate']}% "
                      f"({result['matched']}/{result['total']})")

            if 'bearish_count' in self.pine.columns:
                result = validate_pattern_against_pine(
                    python_bearish,
                    self.pine['bearish_count'],
                    name="Bearish Consecutive"
                )
                self.results['bearish_consecutive'] = result
                status = "✓" if result['is_valid'] else "✗"
                print(f"{status} 連続陰線: {result['match_rate']}% "
                      f"({result['matched']}/{result['total']})")
        else:
            print("⊘ 連続ローソク足: Pine Scriptデータにカウント列がありません - スキップ")

        print()

    def validate_signals(self):
        """シグナル検証"""
        print("=" * 70)
        print("シグナル検証")
        print("=" * 70)

        # ロングシグナル
        if 'long_signal' in self.pine.columns:
            # ここでPython実装のシグナル生成ロジックを実装
            # 例: MA クロスオーバー
            if 'ma20' in self.pine.columns and 'ma50' in self.pine.columns:
                ma20 = Indicators.sma(self.ohlcv['close'], 20)
                ma50 = Indicators.sma(self.ohlcv['close'], 50)
                python_long = Indicators.crossover(ma20, ma50)

                result = validate_pattern_against_pine(
                    python_long,
                    self.pine['long_signal'],
                    name="Long Signal"
                )
                self.results['long_signal'] = result
                status = "✓" if result['is_valid'] else "✗"
                print(f"{status} ロングシグナル: {result['match_rate']}% "
                      f"({result['matched']}/{result['total']})")
                print(f"  Python検知: {result['python_detections']}回")
                print(f"  Pine検知: {result['pine_detections']}回")

        # ショートシグナル
        if 'short_signal' in self.pine.columns:
            if 'ma20' in self.pine.columns and 'ma50' in self.pine.columns:
                ma20 = Indicators.sma(self.ohlcv['close'], 20)
                ma50 = Indicators.sma(self.ohlcv['close'], 50)
                python_short = Indicators.crossunder(ma20, ma50)

                result = validate_pattern_against_pine(
                    python_short,
                    self.pine['short_signal'],
                    name="Short Signal"
                )
                self.results['short_signal'] = result
                status = "✓" if result['is_valid'] else "✗"
                print(f"{status} ショートシグナル: {result['match_rate']}% "
                      f"({result['matched']}/{result['total']})")
                print(f"  Python検知: {result['python_detections']}回")
                print(f"  Pine検知: {result['pine_detections']}回")

        print()

    def print_summary(self):
        """検証結果サマリー"""
        print("=" * 70)
        print("検証結果サマリー")
        print("=" * 70)

        if not self.results:
            print("検証結果がありません")
            return

        total_items = len(self.results)
        passed_items = sum(1 for r in self.results.values() if r['is_valid'])

        print(f"\n総検証項目: {total_items}")
        print(f"合格項目（99%以上）: {passed_items}")
        print(f"不合格項目: {total_items - passed_items}")
        print(f"\n全体合格率: {passed_items / total_items * 100:.1f}%")

        # 不合格項目の詳細
        failed = {k: v for k, v in self.results.items() if not v['is_valid']}
        if failed:
            print(f"\n不合格項目の詳細:")
            for name, result in failed.items():
                print(f"  {name}: {result['match_rate']}%")

        # 目標達成判定
        print("\n" + "=" * 70)
        if passed_items == total_items:
            print("🎉 検証成功！すべての項目で99%以上の一致を達成しました！")
        else:
            print(f"⚠️  検証未達成: {total_items - passed_items}項目が99%未満")
            print("   scripts/03_analyze_mismatches.py で不一致を分析してください")

        print("=" * 70)

    def run(self):
        """検証実行"""
        print("\n" + "=" * 70)
        print("Pine Script → Python バックテスト検証")
        print("目標: 99%以上の一致率")
        print("=" * 70 + "\n")

        self.load_data()
        self.validate_indicators()
        self.validate_patterns()
        self.validate_signals()
        self.print_summary()


if __name__ == "__main__":
    runner = ValidationRunner()
    runner.run()
