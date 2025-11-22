"""
環境マッチングシステム

連勝モード時の環境を記録し、同様の環境でのみ取引を許可
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict


class EnvironmentMatcher:
    """環境マッチングクラス"""

    def __init__(
        self,
        environment_match_threshold: int = 4,
        max_samples: int = 500
    ):
        self.environment_match_threshold = environment_match_threshold
        self.max_samples = max_samples

        # 連勝モード時の環境データ
        self.streak_env_ma_slope: List[float] = []
        self.streak_env_ma_deviation: List[float] = []
        self.streak_env_consistency: List[float] = []
        self.streak_env_max_consecutive: List[int] = []
        self.streak_env_bbw: List[float] = []

    def record_environment(
        self,
        ma_slope: float,
        ma_deviation: float,
        consistency: float,
        max_consecutive: int,
        bbw: float
    ):
        """
        環境データを記録

        Args:
            ma_slope: MA傾き (%)
            ma_deviation: MA乖離率 (%)
            consistency: 方向性の一貫性 (0-1)
            max_consecutive: 最大連続本数
            bbw: ボリンジャーバンド幅 (%)
        """
        self.streak_env_ma_slope.append(ma_slope)
        self.streak_env_ma_deviation.append(ma_deviation)
        self.streak_env_consistency.append(consistency)
        self.streak_env_max_consecutive.append(max_consecutive)
        self.streak_env_bbw.append(bbw)

        # 最大サンプル数を超えたら古いデータを削除
        if len(self.streak_env_ma_slope) > self.max_samples:
            self.streak_env_ma_slope.pop(0)
            self.streak_env_ma_deviation.pop(0)
            self.streak_env_consistency.pop(0)
            self.streak_env_max_consecutive.pop(0)
            self.streak_env_bbw.pop(0)

    def get_environment_stats(self) -> Dict:
        """
        記録された環境の統計情報を取得

        Returns:
            dict: 統計情報
        """
        sample_count = len(self.streak_env_ma_slope)

        if sample_count < 20:
            return {
                'has_data': False,
                'sample_count': sample_count
            }

        return {
            'has_data': True,
            'sample_count': sample_count,
            'ma_slope': {
                'avg': np.mean(self.streak_env_ma_slope),
                'min': np.min(self.streak_env_ma_slope),
                'max': np.max(self.streak_env_ma_slope)
            },
            'ma_deviation': {
                'avg': np.mean(self.streak_env_ma_deviation),
                'min': np.min(self.streak_env_ma_deviation),
                'max': np.max(self.streak_env_ma_deviation)
            },
            'consistency': {
                'avg': np.mean(self.streak_env_consistency),
                'min': np.min(self.streak_env_consistency),
                'max': np.max(self.streak_env_consistency)
            },
            'max_consecutive': {
                'avg': np.mean(self.streak_env_max_consecutive),
                'min': np.min(self.streak_env_max_consecutive),
                'max': np.max(self.streak_env_max_consecutive)
            },
            'bbw': {
                'avg': np.mean(self.streak_env_bbw),
                'min': np.min(self.streak_env_bbw),
                'max': np.max(self.streak_env_bbw)
            }
        }

    def check_if_streak_environment(
        self,
        current_ma_slope: float,
        current_ma_deviation: float,
        current_consistency: float,
        current_max_consecutive: int,
        current_bbw: float
    ) -> Tuple[bool, int, str]:
        """
        現在の環境が連勝モード環境と一致するかチェック

        Args:
            current_ma_slope: 現在のMA傾き
            current_ma_deviation: 現在のMA乖離率
            current_consistency: 現在の一貫性
            current_max_consecutive: 現在の最大連続本数
            current_bbw: 現在のBBW

        Returns:
            (is_match, match_count, quality): 一致判定、一致数、品質評価
        """
        stats = self.get_environment_stats()

        if not stats['has_data']:
            return False, 0, "データ不足"

        match_count = 0

        # MA傾き
        if stats['ma_slope']['min'] <= current_ma_slope <= stats['ma_slope']['max']:
            match_count += 1

        # MA乖離率
        if stats['ma_deviation']['min'] <= current_ma_deviation <= stats['ma_deviation']['max']:
            match_count += 1

        # 一貫性
        if stats['consistency']['min'] <= current_consistency <= stats['consistency']['max']:
            match_count += 1

        # 最大連続本数
        if stats['max_consecutive']['min'] <= current_max_consecutive <= stats['max_consecutive']['max']:
            match_count += 1

        # BBW
        if stats['bbw']['min'] <= current_bbw <= stats['bbw']['max']:
            match_count += 1

        # 品質評価
        if match_count == 5:
            quality = "⭐⭐⭐完全一致"
        elif match_count == 4:
            quality = "⭐⭐高一致"
        elif match_count == 3:
            quality = "⭐部分一致"
        else:
            quality = "範囲外"

        is_match = match_count >= self.environment_match_threshold

        return is_match, match_count, quality

    def clear(self):
        """記録をクリア"""
        self.streak_env_ma_slope.clear()
        self.streak_env_ma_deviation.clear()
        self.streak_env_consistency.clear()
        self.streak_env_max_consecutive.clear()
        self.streak_env_bbw.clear()


if __name__ == "__main__":
    # 簡易テスト
    print("環境マッチングシステムのテスト")
    print("=" * 70)

    matcher = EnvironmentMatcher(environment_match_threshold=4)

    # 連勝モード時の環境を記録
    print("連勝モード時の環境を記録中...")
    for i in range(30):
        matcher.record_environment(
            ma_slope=0.05 + np.random.randn() * 0.01,
            ma_deviation=0.02 + np.random.randn() * 0.005,
            consistency=0.7 + np.random.randn() * 0.05,
            max_consecutive=3 + int(np.random.randn()),
            bbw=2.5 + np.random.randn() * 0.5
        )

    # 統計情報取得
    stats = matcher.get_environment_stats()
    print(f"\n✓ サンプル数: {stats['sample_count']}")
    print(f"\nMA傾き範囲: {stats['ma_slope']['min']:.4f} - {stats['ma_slope']['max']:.4f}")
    print(f"MA乖離範囲: {stats['ma_deviation']['min']:.4f} - {stats['ma_deviation']['max']:.4f}")
    print(f"一貫性範囲: {stats['consistency']['min']:.2%} - {stats['consistency']['max']:.2%}")
    print(f"最大連続範囲: {stats['max_consecutive']['min']:.0f} - {stats['max_consecutive']['max']:.0f}")
    print(f"BBW範囲: {stats['bbw']['min']:.2f} - {stats['bbw']['max']:.2f}")

    # 環境チェック
    print(f"\n環境チェック:")
    print("=" * 70)

    # ケース1: 範囲内
    is_match, match_count, quality = matcher.check_if_streak_environment(
        current_ma_slope=0.05,
        current_ma_deviation=0.02,
        current_consistency=0.7,
        current_max_consecutive=3,
        current_bbw=2.5
    )
    print(f"ケース1（範囲内）: 一致={is_match}, 一致数={match_count}/5, 品質={quality}")

    # ケース2: 範囲外
    is_match, match_count, quality = matcher.check_if_streak_environment(
        current_ma_slope=0.5,  # 大きく外れる
        current_ma_deviation=0.5,
        current_consistency=0.3,
        current_max_consecutive=10,
        current_bbw=10.0
    )
    print(f"ケース2（範囲外）: 一致={is_match}, 一致数={match_count}/5, 品質={quality}")
