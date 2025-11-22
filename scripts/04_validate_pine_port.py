#!/usr/bin/env python3
"""
Pine Script移植版の検証

Pine Scriptの出力と完全一致を検証します。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
from data_loader import DataLoader
from indicators import validate_against_pine
from trading_system import TradingSystem, TradingConfig
from backtest_engine import BacktestEngine


class PinePortValidator:
    """Pine Script移植版の検証クラス"""

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

        print()

    def validate_ma_calculations(self):
        """MA計算の検証"""
        print("=" * 70)
        print("MA計算の検証")
        print("=" * 70)

        config = TradingConfig()
        system = TradingSystem(config)

        result = system.calculate_ma_signals(self.ohlcv)

        # MA検証
        ma_columns = {
            'ma_fast': 'ma5',    # Pine Scriptのカラム名に合わせる
            'ma_mid': 'ma9',
            'ma_slow': 'ma21'
        }

        for py_col, pine_col in ma_columns.items():
            if pine_col not in self.pine.columns:
                print(f"⊘ {pine_col}: Pine Scriptデータにありません - スキップ")
                continue

            val_result = validate_against_pine(
                result[py_col],
                self.pine[pine_col],
                tolerance=1e-5,
                name=f"MA({pine_col})"
            )

            self.results[py_col] = val_result

            status = "✓" if val_result['is_valid'] else "✗"
            print(f"{status} {pine_col}: {val_result['match_rate']}% "
                  f"({val_result['matched']}/{val_result['total']})")

            if not val_result['is_valid'] and val_result.get('sample_mismatches'):
                print(f"  最大誤差: {val_result['max_diff']:.6f}")

        print()

    def validate_signals(self):
        """シグナルの検証"""
        print("=" * 70)
        print("シグナルの検証")
        print("=" * 70)

        # バックテスト実行
        config = TradingConfig(
            required_wins=3,
            winrate_threshold=70.0,
            stop_signals_below_threshold=False
        )

        engine = BacktestEngine(config)
        result = engine.run(self.ohlcv)

        # シグナル比較
        signal_columns = {
            'final_buy_signal': 'buy_signal',
            'final_sell_signal': 'sell_signal'
        }

        for py_col, pine_col in signal_columns.items():
            if pine_col not in self.pine.columns:
                print(f"⊘ {pine_col}: Pine Scriptデータにありません - スキップ")
                continue

            # bool型に変換
            py_signals = result[py_col].astype(bool)
            pine_signals = self.pine[pine_col].astype(bool)

            # 共通インデックス
            common_index = py_signals.index.intersection(pine_signals.index)
            py_vals = py_signals.loc[common_index]
            pine_vals = pine_signals.loc[common_index]

            matches = (py_vals == pine_vals).sum()
            total = len(py_vals)
            match_rate = matches / total * 100 if total > 0 else 0

            is_valid = match_rate >= 99.0

            self.results[py_col] = {
                'name': py_col,
                'matched': matches,
                'total': total,
                'match_rate': match_rate,
                'is_valid': is_valid,
                'python_detections': py_vals.sum(),
                'pine_detections': pine_vals.sum()
            }

            status = "✓" if is_valid else "✗"
            print(f"{status} {pine_col}: {match_rate:.2f}% ({matches}/{total})")
            print(f"  Python検知: {py_vals.sum()}回")
            print(f"  Pine検知: {pine_vals.sum()}回")

        print()

    def validate_winrate(self):
        """勝率の検証"""
        print("=" * 70)
        print("勝率の検証")
        print("=" * 70)

        # バックテスト実行
        config = TradingConfig()
        engine = BacktestEngine(config)
        result = engine.run(self.ohlcv)

        stats = engine.get_statistics()

        # Pine Scriptの勝率と比較
        if 'buy_winrate' in self.pine.columns:
            pine_buy_winrate = self.pine['buy_winrate'].iloc[-1]
            py_buy_winrate = stats['buy']['winrate']

            diff = abs(py_buy_winrate - pine_buy_winrate)
            is_valid = diff < 5.0  # 5%以内の誤差

            status = "✓" if is_valid else "✗"
            print(f"{status} BUY勝率: Python={py_buy_winrate:.1f}%, Pine={pine_buy_winrate:.1f}%, 差={diff:.1f}%")

        if 'sell_winrate' in self.pine.columns:
            pine_sell_winrate = self.pine['sell_winrate'].iloc[-1]
            py_sell_winrate = stats['sell']['winrate']

            diff = abs(py_sell_winrate - pine_sell_winrate)
            is_valid = diff < 5.0

            status = "✓" if is_valid else "✗"
            print(f"{status} SELL勝率: Python={py_sell_winrate:.1f}%, Pine={pine_sell_winrate:.1f}%, 差={diff:.1f}%")

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
        passed_items = sum(1 for r in self.results.values() if r.get('is_valid', False))

        print(f"\n総検証項目: {total_items}")
        print(f"合格項目（99%以上）: {passed_items}")
        print(f"不合格項目: {total_items - passed_items}")
        print(f"\n全体合格率: {passed_items / total_items * 100:.1f}%")

        # 不合格項目の詳細
        failed = {k: v for k, v in self.results.items() if not v.get('is_valid', False)}
        if failed:
            print(f"\n不合格項目の詳細:")
            for name, result in failed.items():
                print(f"  {name}: {result.get('match_rate', 0)}%")

        # 目標達成判定
        print("\n" + "=" * 70)
        if passed_items == total_items:
            print("🎉 検証成功！すべての項目で99%以上の一致を達成しました！")
        else:
            print(f"⚠️  検証未達成: {total_items - passed_items}項目が99%未満")
            print("   次のステップ:")
            print("   1. Pine Scriptから詳細なデータをエクスポート")
            print("   2. scripts/03_analyze_mismatches.py で不一致を分析")
            print("   3. ロジックを修正して再検証")

        print("=" * 70)

    def run(self):
        """検証実行"""
        print("\n" + "=" * 70)
        print("Pine Script → Python 移植版検証")
        print("目標: 99%以上の一致率")
        print("=" * 70 + "\n")

        self.load_data()
        self.validate_ma_calculations()
        # self.validate_signals()  # シグナルデータがあれば有効化
        # self.validate_winrate()   # 勝率データがあれば有効化
        self.print_summary()


if __name__ == "__main__":
    validator = PinePortValidator()
    validator.run()
