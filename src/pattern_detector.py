"""
パターン検知

連続ローソク足パターンの検知を実装します。
Pine Scriptと完全一致する挙動を目指します。
"""

import pandas as pd
import numpy as np
from typing import Tuple


class PatternDetector:
    """ローソク足パターン検知クラス"""

    @staticmethod
    def consecutive_candles(
        open_series: pd.Series,
        close_series: pd.Series,
        max_lookback: int = 10
    ) -> Tuple[pd.Series, pd.Series]:
        """
        連続陽線・陰線をカウント

        Pine Scriptロジック:
        - 陽線: close > open
        - 陰線: close < open
        - 同値: カウントしない（連続をリセット）

        Args:
            open_series: 始値
            close_series: 終値
            max_lookback: 最大遡り期間

        Returns:
            Tuple[pd.Series, pd.Series]: (連続陽線数, 連続陰線数)
        """
        bullish_count = pd.Series(0, index=open_series.index)
        bearish_count = pd.Series(0, index=open_series.index)

        for i in range(len(open_series)):
            if i == 0:
                # 最初の足
                if close_series.iloc[i] > open_series.iloc[i]:
                    bullish_count.iloc[i] = 1
                elif close_series.iloc[i] < open_series.iloc[i]:
                    bearish_count.iloc[i] = 1
            else:
                # 前の足の状態を引き継ぐ
                if close_series.iloc[i] > open_series.iloc[i]:
                    # 陽線
                    bullish_count.iloc[i] = bullish_count.iloc[i-1] + 1
                    bearish_count.iloc[i] = 0
                elif close_series.iloc[i] < open_series.iloc[i]:
                    # 陰線
                    bullish_count.iloc[i] = 0
                    bearish_count.iloc[i] = bearish_count.iloc[i-1] + 1
                else:
                    # 同値（十字線）
                    bullish_count.iloc[i] = 0
                    bearish_count.iloc[i] = 0

            # 最大値で打ち切り
            if bullish_count.iloc[i] > max_lookback:
                bullish_count.iloc[i] = max_lookback
            if bearish_count.iloc[i] > max_lookback:
                bearish_count.iloc[i] = max_lookback

        return bullish_count, bearish_count

    @staticmethod
    def is_bullish(open_val: float, close_val: float) -> bool:
        """陽線判定"""
        return close_val > open_val

    @staticmethod
    def is_bearish(open_val: float, close_val: float) -> bool:
        """陰線判定"""
        return close_val < open_val

    @staticmethod
    def is_doji(
        open_val: float,
        close_val: float,
        high_val: float,
        low_val: float,
        threshold: float = 0.1
    ) -> bool:
        """
        十字線（Doji）判定

        Args:
            open_val: 始値
            close_val: 終値
            high_val: 高値
            low_val: 安値
            threshold: 実体の閾値（％）

        Returns:
            bool: 十字線ならTrue
        """
        body = abs(close_val - open_val)
        total_range = high_val - low_val

        if total_range == 0:
            return True

        body_ratio = body / total_range
        return body_ratio < threshold

    @staticmethod
    def detect_engulfing(
        open_series: pd.Series,
        close_series: pd.Series
    ) -> Tuple[pd.Series, pd.Series]:
        """
        包み足（Engulfing）検知

        - 強気の包み足: 前が陰線、今が陽線で前の実体を完全に包む
        - 弱気の包み足: 前が陽線、今が陰線で前の実体を完全に包む

        Args:
            open_series: 始値
            close_series: 終値

        Returns:
            Tuple[pd.Series, pd.Series]: (強気包み足, 弱気包み足)
        """
        bullish_engulfing = pd.Series(False, index=open_series.index)
        bearish_engulfing = pd.Series(False, index=open_series.index)

        for i in range(1, len(open_series)):
            prev_open = open_series.iloc[i-1]
            prev_close = close_series.iloc[i-1]
            curr_open = open_series.iloc[i]
            curr_close = close_series.iloc[i]

            # 強気の包み足
            if (prev_close < prev_open and  # 前が陰線
                curr_close > curr_open and  # 今が陽線
                curr_open < prev_close and  # 前の終値より下で始まる
                curr_close > prev_open):    # 前の始値より上で終わる
                bullish_engulfing.iloc[i] = True

            # 弱気の包み足
            if (prev_close > prev_open and  # 前が陽線
                curr_close < curr_open and  # 今が陰線
                curr_open > prev_close and  # 前の終値より上で始まる
                curr_close < prev_open):    # 前の始値より下で終わる
                bearish_engulfing.iloc[i] = True

        return bullish_engulfing, bearish_engulfing

    @staticmethod
    def detect_hammer(
        open_series: pd.Series,
        high_series: pd.Series,
        low_series: pd.Series,
        close_series: pd.Series,
        body_ratio: float = 0.3,
        lower_shadow_ratio: float = 2.0
    ) -> pd.Series:
        """
        ハンマー（Hammer）検知

        - 下ヒゲが長い
        - 実体が小さい
        - 上ヒゲがほとんどない

        Args:
            open_series: 始値
            high_series: 高値
            low_series: 安値
            close_series: 終値
            body_ratio: 実体の最大比率
            lower_shadow_ratio: 下ヒゲの最小比率

        Returns:
            pd.Series: ハンマー検知
        """
        hammer = pd.Series(False, index=open_series.index)

        for i in range(len(open_series)):
            o = open_series.iloc[i]
            h = high_series.iloc[i]
            l = low_series.iloc[i]
            c = close_series.iloc[i]

            body = abs(c - o)
            total_range = h - l

            if total_range == 0:
                continue

            lower_shadow = min(o, c) - l
            upper_shadow = h - max(o, c)

            # 条件チェック
            if (body / total_range < body_ratio and
                lower_shadow / body > lower_shadow_ratio if body > 0 else False and
                upper_shadow / total_range < 0.1):
                hammer.iloc[i] = True

        return hammer


def validate_pattern_against_pine(
    python_pattern: pd.Series,
    pine_pattern: pd.Series,
    name: str = "pattern"
) -> dict:
    """
    パターン検知結果をPine Scriptと比較

    Args:
        python_pattern: Python実装の結果（bool）
        pine_pattern: Pine Scriptの結果（bool or 0/1）
        name: パターン名

    Returns:
        dict: 検証結果
    """
    # 共通のインデックス
    common_index = python_pattern.index.intersection(pine_pattern.index)

    if len(common_index) == 0:
        return {
            "name": name,
            "matched": 0,
            "total": 0,
            "match_rate": 0.0,
            "is_valid": False,
            "message": "共通するデータポイントがありません"
        }

    py_vals = python_pattern.loc[common_index].astype(bool)
    pine_vals = pine_pattern.loc[common_index].astype(bool)

    matches = (py_vals == pine_vals).sum()
    total = len(py_vals)
    match_rate = matches / total * 100

    # 不一致のサンプル
    mismatches = py_vals[py_vals != pine_vals]
    sample_mismatches = []
    if len(mismatches) > 0:
        for idx in mismatches.head(5).index:
            sample_mismatches.append({
                "timestamp": idx,
                "python": py_vals.loc[idx],
                "pine": pine_vals.loc[idx]
            })

    return {
        "name": name,
        "matched": int(matches),
        "total": int(total),
        "match_rate": round(match_rate, 2),
        "is_valid": match_rate >= 99.0,
        "python_detections": int(py_vals.sum()),
        "pine_detections": int(pine_vals.sum()),
        "sample_mismatches": sample_mismatches[:5]
    }


if __name__ == "__main__":
    # 簡易テスト
    print("パターン検知のテスト")
    print("=" * 50)

    # サンプルデータ: 陽線→陽線→陰線→陰線→陰線
    opens = pd.Series([100, 101, 103, 102, 101])
    closes = pd.Series([101, 103, 102, 101, 100])

    bullish, bearish = PatternDetector.consecutive_candles(opens, closes)

    print("連続ローソク足カウント:")
    for i in range(len(opens)):
        print(f"  [{i}] O:{opens.iloc[i]:.0f} C:{closes.iloc[i]:.0f} "
              f"-> 陽:{bullish.iloc[i]} 陰:{bearish.iloc[i]}")

    # 期待値:
    # [0] 陽線: 陽=1, 陰=0
    # [1] 陽線: 陽=2, 陰=0
    # [2] 陰線: 陽=0, 陰=1
    # [3] 陰線: 陽=0, 陰=2
    # [4] 陰線: 陽=0, 陰=3
