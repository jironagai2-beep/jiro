"""
環境分析

市場環境（トレンド、ボラティリティなど）を分析します。
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple

try:
    from .indicators import Indicators
except ImportError:
    from indicators import Indicators


class EnvironmentAnalyzer:
    """市場環境分析クラス"""

    @staticmethod
    def detect_trend(
        close: pd.Series,
        ma_short: int = 20,
        ma_long: int = 50
    ) -> pd.Series:
        """
        トレンド検知

        Args:
            close: 終値
            ma_short: 短期MA期間
            ma_long: 長期MA期間

        Returns:
            pd.Series: トレンド方向 (1=上昇, -1=下降, 0=レンジ)
        """
        ma_s = Indicators.sma(close, ma_short)
        ma_l = Indicators.sma(close, ma_long)

        trend = pd.Series(0, index=close.index)
        trend[ma_s > ma_l] = 1   # 上昇トレンド
        trend[ma_s < ma_l] = -1  # 下降トレンド

        return trend

    @staticmethod
    def calculate_volatility(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        ボラティリティ計算（ATRベース）

        Args:
            high: 高値
            low: 安値
            close: 終値
            period: 期間

        Returns:
            pd.Series: ボラティリティ
        """
        return Indicators.atr(high, low, close, period)

    @staticmethod
    def classify_volatility(
        atr: pd.Series,
        threshold_low: float = 0.001,
        threshold_high: float = 0.003
    ) -> pd.Series:
        """
        ボラティリティ分類

        Args:
            atr: ATR値
            threshold_low: 低ボラ閾値
            threshold_high: 高ボラ閾値

        Returns:
            pd.Series: ボラティリティ分類 ("LOW", "MEDIUM", "HIGH")
        """
        volatility = pd.Series("MEDIUM", index=atr.index)
        volatility[atr < threshold_low] = "LOW"
        volatility[atr > threshold_high] = "HIGH"

        return volatility

    @staticmethod
    def detect_range_market(
        high: pd.Series,
        low: pd.Series,
        period: int = 20,
        threshold: float = 0.02
    ) -> pd.Series:
        """
        レンジ相場検知

        Args:
            high: 高値
            low: 安値
            period: 期間
            threshold: レンジ判定閾値（％）

        Returns:
            pd.Series: レンジ相場フラグ
        """
        # 期間内の最高値・最安値
        rolling_high = high.rolling(window=period).max()
        rolling_low = low.rolling(window=period).min()

        # レンジ幅
        range_width = (rolling_high - rolling_low) / rolling_low

        # レンジが狭い場合はTrue
        is_range = range_width < threshold

        return is_range

    @staticmethod
    def analyze_environment(
        df: pd.DataFrame,
        ma_short: int = 20,
        ma_long: int = 50,
        atr_period: int = 14
    ) -> pd.DataFrame:
        """
        総合的な環境分析

        Args:
            df: OHLCVデータ
            ma_short: 短期MA期間
            ma_long: 長期MA期間
            atr_period: ATR期間

        Returns:
            pd.DataFrame: 環境分析結果を追加したDataFrame
        """
        result = df.copy()

        # トレンド検知
        result['trend'] = EnvironmentAnalyzer.detect_trend(
            df['close'],
            ma_short,
            ma_long
        )

        # ATR計算
        result['atr'] = EnvironmentAnalyzer.calculate_volatility(
            df['high'],
            df['low'],
            df['close'],
            atr_period
        )

        # ボラティリティ分類
        # USDJPYの場合の閾値（要調整）
        result['volatility'] = EnvironmentAnalyzer.classify_volatility(
            result['atr'],
            threshold_low=0.05,
            threshold_high=0.15
        )

        # レンジ相場検知
        result['is_range'] = EnvironmentAnalyzer.detect_range_market(
            df['high'],
            df['low'],
            period=20,
            threshold=0.02
        )

        # 環境スコア（トレードに有利な環境かどうか）
        result['env_score'] = EnvironmentAnalyzer._calculate_env_score(result)

        return result

    @staticmethod
    def _calculate_env_score(df: pd.DataFrame) -> pd.Series:
        """
        環境スコアを計算（0-100）

        良い環境:
        - 明確なトレンドがある
        - 適度なボラティリティ
        - レンジ相場でない

        Args:
            df: 環境分析データ

        Returns:
            pd.Series: 環境スコア
        """
        score = pd.Series(50.0, index=df.index)  # ベーススコア

        # トレンドがある: +20
        if 'trend' in df.columns:
            score[df['trend'] != 0] += 20

        # 適度なボラティリティ: +20
        if 'volatility' in df.columns:
            score[df['volatility'] == 'MEDIUM'] += 20

        # レンジでない: +10
        if 'is_range' in df.columns:
            score[~df['is_range']] += 10

        # 高ボラティリティ: -10
        if 'volatility' in df.columns:
            score[df['volatility'] == 'HIGH'] -= 10

        # レンジ相場: -20
        if 'is_range' in df.columns:
            score[df['is_range']] -= 20

        # 0-100に制限
        score = score.clip(0, 100)

        return score


if __name__ == "__main__":
    # 簡易テスト
    print("環境分析のテスト")
    print("=" * 50)

    # サンプルデータ生成
    dates = pd.date_range('2024-01-01', periods=100, freq='1min')

    # トレンド + ノイズ
    trend = np.linspace(100, 110, 100)
    noise = np.random.randn(100) * 0.5

    close = trend + noise
    high = close + abs(np.random.randn(100) * 0.2)
    low = close - abs(np.random.randn(100) * 0.2)
    open_ = close + np.random.randn(100) * 0.1

    df = pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close
    }, index=dates)

    # 環境分析実行
    result = EnvironmentAnalyzer.analyze_environment(df)

    print(f"✓ 環境分析完了: {len(result)}行")
    print(f"\nトレンド分布:")
    print(result['trend'].value_counts())
    print(f"\nボラティリティ分布:")
    print(result['volatility'].value_counts())
    print(f"\nレンジ相場: {result['is_range'].sum()}行")
    print(f"\n環境スコア統計:")
    print(f"  平均: {result['env_score'].mean():.1f}")
    print(f"  最小: {result['env_score'].min():.1f}")
    print(f"  最大: {result['env_score'].max():.1f}")

    print(f"\nサンプル（最新5行）:")
    print(result[['close', 'trend', 'atr', 'volatility', 'is_range', 'env_score']].tail())
