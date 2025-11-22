"""
シグナル履歴管理

トレーディングシグナルの履歴を管理し、
勝敗判定、連勝検知などに必要なデータを保持します。
"""

import pandas as pd
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class SignalType(Enum):
    """シグナルタイプ"""
    LONG = "LONG"
    SHORT = "SHORT"


class TradeResult(Enum):
    """トレード結果"""
    WIN = "WIN"
    LOSS = "LOSS"
    PENDING = "PENDING"  # まだ決済されていない


@dataclass
class Signal:
    """シグナル情報"""
    timestamp: pd.Timestamp
    signal_type: SignalType
    entry_price: float
    exit_price: Optional[float] = None
    result: TradeResult = TradeResult.PENDING
    profit: Optional[float] = None

    def close(self, exit_price: float) -> 'Signal':
        """
        シグナルをクローズ（決済）

        Args:
            exit_price: 決済価格

        Returns:
            Signal: 更新されたシグナル
        """
        self.exit_price = exit_price

        # 勝敗判定
        if self.signal_type == SignalType.LONG:
            self.profit = exit_price - self.entry_price
        else:  # SHORT
            self.profit = self.entry_price - exit_price

        self.result = TradeResult.WIN if self.profit > 0 else TradeResult.LOSS

        return self


class SignalHistory:
    """シグナル履歴管理クラス"""

    def __init__(self):
        self.signals: List[Signal] = []

    def add_signal(
        self,
        timestamp: pd.Timestamp,
        signal_type: SignalType,
        entry_price: float
    ) -> Signal:
        """
        新しいシグナルを追加

        Args:
            timestamp: タイムスタンプ
            signal_type: シグナルタイプ（LONG/SHORT）
            entry_price: エントリー価格

        Returns:
            Signal: 追加されたシグナル
        """
        signal = Signal(
            timestamp=timestamp,
            signal_type=signal_type,
            entry_price=entry_price
        )
        self.signals.append(signal)
        return signal

    def close_last_signal(self, exit_price: float) -> Optional[Signal]:
        """
        最後のシグナルをクローズ

        Args:
            exit_price: 決済価格

        Returns:
            Optional[Signal]: クローズされたシグナル（存在しなければNone）
        """
        if not self.signals:
            return None

        # 未決済のシグナルを探す
        for signal in reversed(self.signals):
            if signal.result == TradeResult.PENDING:
                return signal.close(exit_price)

        return None

    def get_closed_signals(self) -> List[Signal]:
        """決済済みシグナルのリストを取得"""
        return [s for s in self.signals if s.result != TradeResult.PENDING]

    def get_pending_signals(self) -> List[Signal]:
        """未決済シグナルのリストを取得"""
        return [s for s in self.signals if s.result == TradeResult.PENDING]

    def get_win_rate(self) -> float:
        """
        勝率を計算

        Returns:
            float: 勝率（0.0-100.0）
        """
        closed = self.get_closed_signals()
        if not closed:
            return 0.0

        wins = sum(1 for s in closed if s.result == TradeResult.WIN)
        return wins / len(closed) * 100

    def get_consecutive_wins(self) -> int:
        """
        現在の連勝数を取得

        Returns:
            int: 連勝数
        """
        closed = self.get_closed_signals()
        if not closed:
            return 0

        count = 0
        for signal in reversed(closed):
            if signal.result == TradeResult.WIN:
                count += 1
            else:
                break

        return count

    def get_consecutive_losses(self) -> int:
        """
        現在の連敗数を取得

        Returns:
            int: 連敗数
        """
        closed = self.get_closed_signals()
        if not closed:
            return 0

        count = 0
        for signal in reversed(closed):
            if signal.result == TradeResult.LOSS:
                count += 1
            else:
                break

        return count

    def to_dataframe(self) -> pd.DataFrame:
        """
        シグナル履歴をDataFrameに変換

        Returns:
            pd.DataFrame: シグナル履歴
        """
        if not self.signals:
            return pd.DataFrame()

        data = []
        for signal in self.signals:
            data.append({
                'timestamp': signal.timestamp,
                'type': signal.signal_type.value,
                'entry_price': signal.entry_price,
                'exit_price': signal.exit_price,
                'result': signal.result.value,
                'profit': signal.profit
            })

        return pd.DataFrame(data)

    def __len__(self) -> int:
        return len(self.signals)


def build_signal_history_from_dataframe(
    df: pd.DataFrame,
    long_col: str = "long_signal",
    short_col: str = "short_signal",
    close_col: str = "close"
) -> SignalHistory:
    """
    DataFrameからシグナル履歴を構築

    Args:
        df: OHLCV + シグナル列を含むDataFrame
        long_col: ロングシグナル列名
        short_col: ショートシグナル列名
        close_col: 終値列名

    Returns:
        SignalHistory: 構築されたシグナル履歴
    """
    history = SignalHistory()

    for idx in df.index:
        row = df.loc[idx]

        # ロングシグナル
        if long_col in df.columns and row[long_col]:
            history.add_signal(
                timestamp=idx,
                signal_type=SignalType.LONG,
                entry_price=row[close_col]
            )

        # ショートシグナル
        if short_col in df.columns and row[short_col]:
            history.add_signal(
                timestamp=idx,
                signal_type=SignalType.SHORT,
                entry_price=row[close_col]
            )

    return history


if __name__ == "__main__":
    # 簡易テスト
    print("シグナル履歴のテスト")
    print("=" * 50)

    history = SignalHistory()

    # シグナル追加
    history.add_signal(
        pd.Timestamp("2024-01-01 10:00"),
        SignalType.LONG,
        100.0
    )
    print("✓ ロングシグナル追加: エントリー=100.0")

    # 決済（勝ち）
    history.close_last_signal(105.0)
    print("✓ 決済: 105.0 (利益=+5.0)")

    # 次のシグナル
    history.add_signal(
        pd.Timestamp("2024-01-01 11:00"),
        SignalType.SHORT,
        105.0
    )
    print("✓ ショートシグナル追加: エントリー=105.0")

    # 決済（勝ち）
    history.close_last_signal(100.0)
    print("✓ 決済: 100.0 (利益=+5.0)")

    # もう一つ
    history.add_signal(
        pd.Timestamp("2024-01-01 12:00"),
        SignalType.LONG,
        100.0
    )
    history.close_last_signal(95.0)
    print("✓ ロングシグナル: 100.0 → 95.0 (損失=-5.0)")

    print(f"\n統計:")
    print(f"  総シグナル数: {len(history)}")
    print(f"  決済済み: {len(history.get_closed_signals())}")
    print(f"  未決済: {len(history.get_pending_signals())}")
    print(f"  勝率: {history.get_win_rate():.1f}%")
    print(f"  連勝: {history.get_consecutive_wins()}")
    print(f"  連敗: {history.get_consecutive_losses()}")

    print(f"\nDataFrame:")
    print(history.to_dataframe())
