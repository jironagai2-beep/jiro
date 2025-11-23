"""
インジケーターのユニットテスト

Pine Scriptとの一致率を検証します。
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from indicators import Indicators, validate_against_pine
from data_loader import DataLoader


class TestIndicators:
    """インジケーターのテストクラス"""

    def test_sma_basic(self):
        """SMA基本動作テスト"""
        # 簡単なケース: [1,2,3,4,5,6,7,8,9,10]
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        sma3 = Indicators.sma(data, 3)

        # 最初の2つはNaN
        assert pd.isna(sma3.iloc[0])
        assert pd.isna(sma3.iloc[1])

        # 3番目以降は計算される
        assert sma3.iloc[2] == 2.0  # (1+2+3)/3
        assert sma3.iloc[3] == 3.0  # (2+3+4)/3
        assert sma3.iloc[4] == 4.0  # (3+4+5)/3

    def test_ema_basic(self):
        """EMA基本動作テスト"""
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        ema3 = Indicators.ema(data, 3)

        # EMAは最初から計算される
        assert not pd.isna(ema3.iloc[0])
        assert len(ema3) == len(data)

    def test_crossover(self):
        """クロスオーバー検知テスト"""
        series1 = pd.Series([1, 2, 3, 4, 5])
        series2 = pd.Series([3, 3, 3, 3, 3])

        crossover = Indicators.crossover(series1, series2)

        # インデックス3でクロスオーバー: 2→4 (3を跨ぐ)
        assert crossover.iloc[0] == False  # 1 < 3
        assert crossover.iloc[1] == False  # 2 < 3
        assert crossover.iloc[2] == False  # 3 = 3（まだ下）
        assert crossover.iloc[3] == True   # 3 → 4（上抜け）
        assert crossover.iloc[4] == False  # 4 > 3（継続）

    def test_crossunder(self):
        """クロスアンダー検知テスト"""
        series1 = pd.Series([5, 4, 3, 2, 1])
        series2 = pd.Series([3, 3, 3, 3, 3])

        crossunder = Indicators.crossunder(series1, series2)

        # インデックス3でクロスアンダー: 4→2
        assert crossunder.iloc[0] == False  # 5 > 3
        assert crossunder.iloc[1] == False  # 4 > 3
        assert crossunder.iloc[2] == False  # 3 = 3（まだ上）
        assert crossunder.iloc[3] == True   # 3 → 2（下抜け）
        assert crossunder.iloc[4] == False  # 1 < 3（継続）

    def test_validate_against_pine(self):
        """検証関数のテスト"""
        # 完全一致のケース
        python_vals = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        pine_vals = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])

        result = validate_against_pine(python_vals, pine_vals, name="test")

        assert result["match_rate"] == 100.0
        assert result["is_valid"] == True
        assert result["matched"] == 5
        assert result["total"] == 5

    def test_validate_with_tolerance(self):
        """許容誤差内の検証テスト"""
        python_vals = pd.Series([1.0000001, 2.0000002, 3.0000001])
        pine_vals = pd.Series([1.0, 2.0, 3.0])

        # 許容誤差 1e-6
        result = validate_against_pine(python_vals, pine_vals, tolerance=1e-6, name="test")

        # わずかな誤差は許容される
        assert result["match_rate"] == 100.0


class TestWithRealData:
    """実データを使った検証テスト"""

    @pytest.fixture
    def loader(self):
        """データローダーのフィクスチャ"""
        return DataLoader()

    def test_sma_against_pine(self, loader):
        """実データでSMAを検証"""
        try:
            # データ読み込み
            ohlcv = loader.load_ohlcv()
            pine = loader.load_pine_signals()

            # SMA20を計算
            python_sma20 = Indicators.sma(ohlcv['close'], 20)

            # Pine Scriptの結果と比較
            if 'ma20' in pine.columns:
                result = validate_against_pine(
                    python_sma20,
                    pine['ma20'],
                    tolerance=1e-5,
                    name="SMA(20)"
                )

                print(f"\nSMA(20) 検証結果:")
                print(f"  一致率: {result['match_rate']}%")
                print(f"  一致数: {result['matched']}/{result['total']}")
                print(f"  最大誤差: {result['max_diff']}")

                # 99%以上一致を要求
                assert result['match_rate'] >= 99.0, \
                    f"SMA(20)の一致率が99%未満: {result['match_rate']}%"

            else:
                pytest.skip("pine_signals.csvにma20列がありません")

        except FileNotFoundError:
            pytest.skip("テストデータが配置されていません")

    def test_sma50_against_pine(self, loader):
        """実データでSMA50を検証"""
        try:
            ohlcv = loader.load_ohlcv()
            pine = loader.load_pine_signals()

            python_sma50 = Indicators.sma(ohlcv['close'], 50)

            if 'ma50' in pine.columns:
                result = validate_against_pine(
                    python_sma50,
                    pine['ma50'],
                    tolerance=1e-5,
                    name="SMA(50)"
                )

                print(f"\nSMA(50) 検証結果:")
                print(f"  一致率: {result['match_rate']}%")
                print(f"  一致数: {result['matched']}/{result['total']}")

                assert result['match_rate'] >= 99.0, \
                    f"SMA(50)の一致率が99%未満: {result['match_rate']}%"

            else:
                pytest.skip("pine_signals.csvにma50列がありません")

        except FileNotFoundError:
            pytest.skip("テストデータが配置されていません")


if __name__ == "__main__":
    # pytestを直接実行
    pytest.main([__file__, "-v", "-s"])
