"""
勝敗判定

トレードの勝敗を判定し、統計情報を計算します。
"""

import pandas as pd
from typing import Dict, List
from signal_history import SignalHistory, SignalType, TradeResult


class WinLossAnalyzer:
    """勝敗分析クラス"""

    @staticmethod
    def calculate_stats(history: SignalHistory) -> Dict:
        """
        シグナル履歴から統計情報を計算

        Args:
            history: シグナル履歴

        Returns:
            dict: 統計情報
        """
        closed = history.get_closed_signals()

        if not closed:
            return {
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "total_profit": 0.0,
                "avg_profit": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "max_consecutive_wins": 0,
                "max_consecutive_losses": 0,
                "profit_factor": 0.0
            }

        wins = [s for s in closed if s.result == TradeResult.WIN]
        losses = [s for s in closed if s.result == TradeResult.LOSS]

        total_profit = sum(s.profit for s in closed if s.profit)
        total_win_profit = sum(s.profit for s in wins if s.profit)
        total_loss_profit = sum(s.profit for s in losses if s.profit)

        # 連勝・連敗の最大値を計算
        max_consec_wins = 0
        max_consec_losses = 0
        current_wins = 0
        current_losses = 0

        for signal in closed:
            if signal.result == TradeResult.WIN:
                current_wins += 1
                current_losses = 0
                max_consec_wins = max(max_consec_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consec_losses = max(max_consec_losses, current_losses)

        # プロフィットファクター
        profit_factor = 0.0
        if total_loss_profit != 0:
            profit_factor = abs(total_win_profit / total_loss_profit)

        return {
            "total_trades": len(closed),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": len(wins) / len(closed) * 100 if closed else 0.0,
            "total_profit": total_profit,
            "avg_profit": total_profit / len(closed) if closed else 0.0,
            "avg_win": total_win_profit / len(wins) if wins else 0.0,
            "avg_loss": total_loss_profit / len(losses) if losses else 0.0,
            "max_consecutive_wins": max_consec_wins,
            "max_consecutive_losses": max_consec_losses,
            "profit_factor": profit_factor
        }

    @staticmethod
    def print_stats(stats: Dict):
        """統計情報を見やすく表示"""
        print("トレード統計")
        print("=" * 50)
        print(f"総トレード数: {stats['total_trades']}")
        print(f"勝ち: {stats['wins']} | 負け: {stats['losses']}")
        print(f"勝率: {stats['win_rate']:.2f}%")
        print(f"\n損益:")
        print(f"  合計損益: {stats['total_profit']:+.2f}")
        print(f"  平均損益: {stats['avg_profit']:+.2f}")
        print(f"  平均勝ち: {stats['avg_win']:+.2f}")
        print(f"  平均負け: {stats['avg_loss']:+.2f}")
        print(f"\n連勝・連敗:")
        print(f"  最大連勝: {stats['max_consecutive_wins']}")
        print(f"  最大連敗: {stats['max_consecutive_losses']}")
        print(f"  プロフィットファクター: {stats['profit_factor']:.2f}")


class StreakDetector:
    """連勝・連敗検知クラス"""

    @staticmethod
    def detect_streaks(history: SignalHistory, threshold: int = 3) -> Dict:
        """
        連勝・連敗を検知

        Args:
            history: シグナル履歴
            threshold: 連勝/連敗とみなす閾値

        Returns:
            dict: 連勝・連敗情報
        """
        closed = history.get_closed_signals()

        if not closed:
            return {
                "current_streak_type": None,
                "current_streak_count": 0,
                "is_hot_streak": False,
                "is_cold_streak": False
            }

        current_wins = history.get_consecutive_wins()
        current_losses = history.get_consecutive_losses()

        streak_type = None
        streak_count = 0

        if current_wins > 0:
            streak_type = "WIN"
            streak_count = current_wins
        elif current_losses > 0:
            streak_type = "LOSS"
            streak_count = current_losses

        return {
            "current_streak_type": streak_type,
            "current_streak_count": streak_count,
            "is_hot_streak": current_wins >= threshold,
            "is_cold_streak": current_losses >= threshold
        }


if __name__ == "__main__":
    # 簡易テスト
    print("勝敗判定のテスト")
    print("=" * 50)

    from signal_history import SignalHistory, SignalType

    history = SignalHistory()

    # テストシグナルを追加
    test_signals = [
        (SignalType.LONG, 100.0, 105.0),   # 勝ち +5
        (SignalType.SHORT, 105.0, 100.0),  # 勝ち +5
        (SignalType.LONG, 100.0, 95.0),    # 負け -5
        (SignalType.LONG, 95.0, 100.0),    # 勝ち +5
        (SignalType.SHORT, 100.0, 105.0),  # 負け -5
    ]

    for i, (sig_type, entry, exit) in enumerate(test_signals):
        timestamp = pd.Timestamp(f"2024-01-01 {10+i}:00")
        history.add_signal(timestamp, sig_type, entry)
        history.close_last_signal(exit)

    # 統計計算
    stats = WinLossAnalyzer.calculate_stats(history)
    WinLossAnalyzer.print_stats(stats)

    # 連勝・連敗検知
    print("\n連勝・連敗検知")
    print("=" * 50)
    streak = StreakDetector.detect_streaks(history, threshold=2)
    print(f"現在のストリーク: {streak['current_streak_type']} x{streak['current_streak_count']}")
    print(f"ホットストリーク: {streak['is_hot_streak']}")
    print(f"コールドストリーク: {streak['is_cold_streak']}")
