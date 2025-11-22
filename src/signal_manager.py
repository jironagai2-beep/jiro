"""
シグナル管理・勝敗判定システム

Pine Scriptのシグナル履歴管理と完全互換
"""

import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Signal:
    """シグナル情報"""
    bar_index: int
    timestamp: pd.Timestamp
    signal_type: str  # 'BUY' or 'SELL'
    entry_price: float
    is_judged: bool = False
    is_win: Optional[bool] = None
    was_disabled: bool = False
    is_reentry: bool = False
    generation: int = 0
    included_in_winrate: bool = True
    parent_index: int = -1
    in_streak_mode: bool = False

    def judge(self, next_candle_bullish: bool) -> bool:
        """
        勝敗を判定

        Args:
            next_candle_bullish: 次の足が陽線かどうか

        Returns:
            bool: 勝ちならTrue
        """
        self.is_judged = True

        if self.signal_type == 'BUY':
            self.is_win = next_candle_bullish
        else:  # SELL
            self.is_win = not next_candle_bullish

        return self.is_win


class SignalManager:
    """シグナル管理クラス"""

    def __init__(
        self,
        winrate_period: int = 300,
        min_signals: int = 3,
        winrate_threshold: float = 70.0,
        stop_signals_below_threshold: bool = False,
        include_stopped_signals_in_winrate: bool = False
    ):
        self.winrate_period = winrate_period
        self.min_signals = min_signals
        self.winrate_threshold = winrate_threshold
        self.stop_signals_below_threshold = stop_signals_below_threshold
        self.include_stopped_signals_in_winrate = include_stopped_signals_in_winrate

        self.signals: List[Signal] = []

    def add_signal(
        self,
        bar_index: int,
        timestamp: pd.Timestamp,
        signal_type: str,
        entry_price: float,
        was_disabled: bool = False,
        is_reentry: bool = False,
        in_streak_mode: bool = False,
        parent_index: int = -1
    ) -> Signal:
        """
        シグナルを追加

        Args:
            bar_index: バーインデックス
            timestamp: タイムスタンプ
            signal_type: 'BUY' or 'SELL'
            entry_price: エントリー価格
            was_disabled: 停止中のシグナルか
            is_reentry: 再エントリーか
            in_streak_mode: 連勝モード中か
            parent_index: 親シグナルのインデックス（再エントリー用）

        Returns:
            Signal: 追加されたシグナル
        """
        signal = Signal(
            bar_index=bar_index,
            timestamp=timestamp,
            signal_type=signal_type,
            entry_price=entry_price,
            was_disabled=was_disabled,
            is_reentry=is_reentry,
            in_streak_mode=in_streak_mode,
            parent_index=parent_index
        )

        self.signals.append(signal)
        return signal

    def judge_signals(
        self,
        current_bar_index: int,
        candle_is_bullish: bool
    ) -> Tuple[bool, bool]:
        """
        シグナルの勝敗を判定

        Args:
            current_bar_index: 現在のバーインデックス
            candle_is_bullish: 現在の足が陽線か

        Returns:
            (is_win, is_lose): 勝ち、負けのフラグ
        """
        is_win = False
        is_lose = False

        for signal in self.signals:
            if signal.is_judged:
                continue

            # 次の足で判定
            if current_bar_index == signal.bar_index + 1:
                result = signal.judge(candle_is_bullish)

                # 再エントリーで勝った場合、親シグナルを勝率計算から除外
                if signal.is_reentry and result and signal.parent_index >= 0:
                    if signal.parent_index < len(self.signals):
                        self.signals[signal.parent_index].included_in_winrate = False

                # 背景色表示判定
                should_show = not signal.was_disabled or True  # show_disabled_signal_results相当

                if should_show:
                    if result:
                        is_win = True
                    else:
                        is_lose = True

        return is_win, is_lose

    def calculate_winrate(
        self,
        signal_type: str,
        only_streak_mode: bool = False
    ) -> Tuple[bool, int, int]:
        """
        勝率を計算

        Args:
            signal_type: 'BUY' or 'SELL'
            only_streak_mode: 連勝モード中のみカウント

        Returns:
            (has_data, wins, total): データがあるか、勝ち数、総数
        """
        wins = 0
        total = 0

        for signal in self.signals:
            if not signal.is_judged:
                continue

            if signal.signal_type != signal_type:
                continue

            # 連勝モードのみカウント
            if only_streak_mode and not signal.in_streak_mode:
                continue

            # 停止中シグナルの扱い
            should_include = self.include_stopped_signals_in_winrate or \
                           not signal.was_disabled

            if should_include and signal.included_in_winrate:
                total += 1
                if signal.is_win:
                    wins += 1

        has_data = total >= self.min_signals
        return has_data, wins, total

    def check_winrate_ok(self, signal_type: str) -> bool:
        """
        勝率が閾値以上かチェック

        Args:
            signal_type: 'BUY' or 'SELL'

        Returns:
            bool: 勝率OKならTrue
        """
        if not self.stop_signals_below_threshold:
            return True

        has_data, wins, total = self.calculate_winrate(signal_type)

        if not has_data:
            return True

        winrate = wins / total * 100 if total > 0 else 0
        return winrate >= self.winrate_threshold

    def cleanup_old_signals(self, current_bar_index: int):
        """
        古いシグナルを削除

        Args:
            current_bar_index: 現在のバーインデックス
        """
        if not self.signals:
            return

        # 期間外のシグナルを削除
        self.signals = [
            s for s in self.signals
            if current_bar_index - s.bar_index <= self.winrate_period
        ]

    def get_recent_signals(self, count: int = 10) -> List[Signal]:
        """
        最近のシグナルを取得

        Args:
            count: 取得数

        Returns:
            List[Signal]: シグナルリスト
        """
        return self.signals[-count:] if len(self.signals) >= count else self.signals

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
                'bar_index': signal.bar_index,
                'timestamp': signal.timestamp,
                'type': signal.signal_type,
                'entry_price': signal.entry_price,
                'is_judged': signal.is_judged,
                'is_win': signal.is_win,
                'was_disabled': signal.was_disabled,
                'is_reentry': signal.is_reentry,
                'in_streak_mode': signal.in_streak_mode,
                'included_in_winrate': signal.included_in_winrate
            })

        return pd.DataFrame(data)


class StreakDetector:
    """連勝検知システム"""

    def __init__(
        self,
        required_wins: int = 3,
        exit_on_real_loss: bool = True,
        streak_start_max_bars: int = 20
    ):
        self.required_wins = required_wins
        self.exit_on_real_loss = exit_on_real_loss
        self.streak_start_max_bars = streak_start_max_bars

        self.consecutive_wins = 0
        self.previous_was_lose = False
        self.trading_mode_active = False
        self.first_win_bar = -1

    def update(
        self,
        current_bar_index: int,
        is_win: bool,
        is_lose: bool
    ) -> bool:
        """
        連勝状態を更新

        Args:
            current_bar_index: 現在のバーインデックス
            is_win: 勝ちフラグ
            is_lose: 負けフラグ

        Returns:
            bool: 連勝モードがアクティブか
        """
        if is_win:
            # 初勝利
            if self.consecutive_wins == 0:
                self.first_win_bar = current_bar_index

            self.consecutive_wins += 1
            self.previous_was_lose = False

            # 必要な連勝数に達したか
            if self.consecutive_wins >= self.required_wins:
                # 開始時間制限チェック
                bars_since_first = current_bar_index - self.first_win_bar \
                    if self.first_win_bar >= 0 else 0

                if bars_since_first <= self.streak_start_max_bars:
                    self.trading_mode_active = True
                else:
                    # 時間制限オーバー → リセット
                    self.consecutive_wins = 0
                    self.first_win_bar = -1

        elif is_lose:
            if self.previous_was_lose:
                # 2連敗 → リセット
                self.consecutive_wins = 0
                self.first_win_bar = -1

                if self.exit_on_real_loss:
                    self.trading_mode_active = False

            self.previous_was_lose = True
        else:
            # 勝敗なし
            self.previous_was_lose = False

        return self.trading_mode_active

    def reset(self):
        """連勝モードをリセット"""
        self.trading_mode_active = False
        self.consecutive_wins = 0
        self.previous_was_lose = False
        self.first_win_bar = -1


if __name__ == "__main__":
    # 簡易テスト
    print("シグナル管理システムのテスト")
    print("=" * 70)

    manager = SignalManager(
        winrate_period=100,
        min_signals=3,
        winrate_threshold=70.0
    )

    # シグナル追加
    dates = pd.date_range('2024-01-01', periods=10, freq='1min')

    for i, ts in enumerate(dates[:5]):
        signal_type = 'BUY' if i % 2 == 0 else 'SELL'
        manager.add_signal(
            bar_index=i,
            timestamp=ts,
            signal_type=signal_type,
            entry_price=100.0 + i
        )

    print(f"✓ シグナル追加: {len(manager.signals)}件")

    # 勝敗判定
    for i in range(1, 6):
        is_bullish = i % 2 == 0  # 交互に陽線・陰線
        is_win, is_lose = manager.judge_signals(i, is_bullish)
        print(f"  Bar {i}: 勝ち={is_win}, 負け={is_lose}")

    # 勝率計算
    has_data, wins, total = manager.calculate_winrate('BUY')
    print(f"\n✓ BUY勝率: {wins}/{total} = {wins/total*100:.1f}%" if total > 0 else "データ不足")

    has_data, wins, total = manager.calculate_winrate('SELL')
    print(f"✓ SELL勝率: {wins}/{total} = {wins/total*100:.1f}%" if total > 0 else "データ不足")

    # 連勝検知
    print(f"\n連勝検知のテスト")
    print("=" * 70)

    streak = StreakDetector(required_wins=3)

    test_results = [True, True, False, True, True, True]
    for i, is_win in enumerate(test_results):
        active = streak.update(i, is_win, not is_win)
        print(f"  Bar {i}: 勝ち={is_win} → 連勝={streak.consecutive_wins}, モード={active}")
