"""
テクニカルインジケーター

Pine Scriptと完全一致するMA（移動平均）計算を実装します。
"""

import pandas as pd
import numpy as np
from typing import Union


class Indicators:
    """テクニカルインジケーター計算クラス"""

    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        """
        単純移動平均（SMA）を計算

        Pine Scriptの ta.sma() と同じロジック:
        - 過去N期間の終値の平均
        - 最初のN-1期間はNaN

        Args:
            series: 価格データ（通常はclose）
            period: 期間

        Returns:
            pd.Series: SMA値
        """
        return series.rolling(window=period, min_periods=period).mean()

    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        """
        指数移動平均（EMA）を計算

        Pine Scriptの ta.ema() と同じロジック:
        - 指数平滑化された移動平均
        - alpha = 2 / (period + 1)

        Args:
            series: 価格データ
            period: 期間

        Returns:
            pd.Series: EMA値
        """
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """
        RSI（相対力指数）を計算

        Pine Scriptの ta.rsi() と同じロジック

        Args:
            series: 価格データ
            period: 期間（デフォルト14）

        Returns:
            pd.Series: RSI値（0-100）
        """
        delta = series.diff()

        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def crossover(series1: pd.Series, series2: Union[pd.Series, float]) -> pd.Series:
        """
        クロスオーバー検知

        Pine Scriptの ta.crossover() と同じロジック:
        - series1が下からseries2を上抜けたらTrue

        Args:
            series1: 系列1
            series2: 系列2（または定数値）

        Returns:
            pd.Series: クロスオーバー検知（bool）
        """
        if isinstance(series2, (int, float)):
            series2 = pd.Series(series2, index=series1.index)

        prev1 = series1.shift(1)
        prev2 = series2.shift(1) if isinstance(series2, pd.Series) else series2

        crossover = (prev1 <= prev2) & (series1 > series2)
        return crossover

    @staticmethod
    def crossunder(series1: pd.Series, series2: Union[pd.Series, float]) -> pd.Series:
        """
        クロスアンダー検知

        Pine Scriptの ta.crossunder() と同じロジック:
        - series1が上からseries2を下抜けたらTrue

        Args:
            series1: 系列1
            series2: 系列2（または定数値）

        Returns:
            pd.Series: クロスアンダー検知（bool）
        """
        if isinstance(series2, (int, float)):
            series2 = pd.Series(series2, index=series1.index)

        prev1 = series1.shift(1)
        prev2 = series2.shift(1) if isinstance(series2, pd.Series) else series2

        crossunder = (prev1 >= prev2) & (series1 < series2)
        return crossunder

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        ATR（Average True Range）を計算

        Pine Scriptの ta.atr() と同じロジック

        Args:
            high: 高値
            low: 安値
            close: 終値
            period: 期間（デフォルト14）

        Returns:
            pd.Series: ATR値
        """
        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period, min_periods=period).mean()

        return atr


def validate_against_pine(
    python_values: pd.Series,
    pine_values: pd.Series,
    tolerance: float = 1e-6,
    name: str = "indicator"
) -> dict:
    """
    PythonとPine Scriptの計算結果を比較検証

    Args:
        python_values: Python実装の結果
        pine_values: Pine Scriptの結果
        tolerance: 許容誤差
        name: インジケーター名

    Returns:
        dict: 検証結果
    """
    # 共通のインデックスに絞る
    common_index = python_values.index.intersection(pine_values.index)

    if len(common_index) == 0:
        return {
            "name": name,
            "matched": 0,
            "total": 0,
            "match_rate": 0.0,
            "is_valid": False,
            "message": "共通するデータポイントがありません"
        }

    py_vals = python_values.loc[common_index]
    pine_vals = pine_values.loc[common_index]

    # NaNを除外
    valid_mask = ~(py_vals.isna() | pine_vals.isna())
    py_vals_valid = py_vals[valid_mask]
    pine_vals_valid = pine_vals[valid_mask]

    if len(py_vals_valid) == 0:
        return {
            "name": name,
            "matched": 0,
            "total": 0,
            "match_rate": 0.0,
            "is_valid": False,
            "message": "有効なデータポイントがありません（すべてNaN）"
        }

    # 相対誤差で比較
    abs_diff = abs(py_vals_valid - pine_vals_valid)
    rel_diff = abs_diff / abs(pine_vals_valid + 1e-10)  # ゼロ除算回避

    matches = (rel_diff < tolerance).sum()
    total = len(py_vals_valid)
    match_rate = matches / total * 100

    # 不一致のサンプル
    mismatches = rel_diff[rel_diff >= tolerance]
    sample_mismatches = []
    if len(mismatches) > 0:
        for idx in mismatches.head(5).index:
            sample_mismatches.append({
                "timestamp": idx,
                "python": py_vals.loc[idx],
                "pine": pine_vals.loc[idx],
                "diff": abs_diff.loc[idx]
            })

    return {
        "name": name,
        "matched": int(matches),
        "total": int(total),
        "match_rate": round(match_rate, 2),
        "is_valid": match_rate >= 99.0,
        "max_diff": float(abs_diff.max()),
        "mean_diff": float(abs_diff.mean()),
        "sample_mismatches": sample_mismatches[:5]
    }


if __name__ == "__main__":
    # 簡易テスト
    print("インジケーターのテスト")
    print("=" * 50)

    # サンプルデータ
    dates = pd.date_range('2024-01-01', periods=100, freq='1min')
    closes = pd.Series(
        np.random.randn(100).cumsum() + 100,
        index=dates
    )

    # SMAテスト
    sma20 = Indicators.sma(closes, 20)
    print(f"✓ SMA(20) 計算完了: {sma20.notna().sum()}個の有効値")

    # クロスオーバーテスト
    sma50 = Indicators.sma(closes, 50)
    crossover = Indicators.crossover(sma20, sma50)
    print(f"✓ クロスオーバー検知: {crossover.sum()}回")

    print("\n実際のデータでテストするには:")
    print("  1. data/USDJPY_1m.csv を配置")
    print("  2. data/pine_signals.csv を配置（ma20, ma50列を含む）")
    print("  3. tests/test_indicators.py を実行")
