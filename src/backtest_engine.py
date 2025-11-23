"""
統合バックテストエンジン

Pine Scriptのロジックを完全再現
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple

try:
    from .trading_system import TradingSystem, TradingConfig
    from .signal_manager import SignalManager, StreakDetector
    from .environment_matcher import EnvironmentMatcher
except ImportError:
    from trading_system import TradingSystem, TradingConfig
    from signal_manager import SignalManager, StreakDetector
    from environment_matcher import EnvironmentMatcher


class BacktestEngine:
    """バックテストエンジン"""

    def __init__(self, config: TradingConfig = None):
        self.config = config or TradingConfig()

        # サブシステム
        self.trading_system = TradingSystem(self.config)
        self.signal_manager = SignalManager(
            winrate_period=self.config.winrate_period,
            min_signals=self.config.min_signals,
            winrate_threshold=self.config.winrate_threshold,
            stop_signals_below_threshold=self.config.stop_signals_below_threshold
        )
        self.streak_detector = StreakDetector(
            required_wins=self.config.required_wins,
            exit_on_real_loss=self.config.exit_on_real_loss,
            streak_start_max_bars=self.config.streak_start_max_bars
        )
        self.env_matcher = EnvironmentMatcher(
            environment_match_threshold=self.config.environment_match_threshold
        )

        # 状態
        self.signals_disabled = False
        self.last_signal_bar = -1
        self.last_signal_type = ""
        self.normal_signal_fired = False
        self.reentry_used = False

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        バックテスト実行

        Args:
            df: OHLCV DataFrame

        Returns:
            pd.DataFrame: シグナル・勝敗・環境情報を含むDataFrame
        """
        # MAシグナル計算
        result = self.trading_system.calculate_ma_signals(df)

        # 連続ローソク足検知
        consec_buy, consec_sell, bull_streak, bear_streak = \
            self.trading_system.calculate_consecutive_candles(df)

        result['consecutive_buy_signal'] = consec_buy
        result['consecutive_sell_signal'] = consec_sell
        result['bull_streak'] = bull_streak
        result['bear_streak'] = bear_streak

        # 5連続検知
        is_5_consecutive = self.trading_system.detect_5_consecutive(df)
        result['is_5_consecutive'] = is_5_consecutive

        # 環境分析
        result['consistency'] = self.trading_system.calculate_directional_consistency(df)
        result['max_consecutive'] = self.trading_system.detect_max_consecutive_pattern(df)
        result['bbw'] = self.trading_system.calculate_bbw(result)

        # シグナル統合・勝敗判定
        result = self._process_signals(result)

        return result

    def _process_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        シグナル処理・勝敗判定

        Args:
            df: データ

        Returns:
            pd.DataFrame: 処理済みデータ
        """
        result = df.copy()

        # 出力カラム初期化
        result['final_buy_signal'] = False
        result['final_sell_signal'] = False
        result['reentry_buy_signal'] = False
        result['reentry_sell_signal'] = False
        result['current_is_win'] = False
        result['current_is_lose'] = False
        result['trading_mode_active'] = False
        result['signals_disabled'] = False
        result['is_streak_environment'] = False

        for i in range(len(df)):
            bar_index = i
            current_row = df.iloc[i]

            # クールダウンチェック
            ma_cooldown_ok = bar_index - self.trading_system.last_ma_signal_bar >= \
                           self.config.cooldown_period
            unified_cooldown_ok = bar_index - self.last_signal_bar >= \
                                self.config.cooldown_period

            # シグナル優先順位: 連続 > MA
            consecutive_buy = result.loc[result.index[i], 'consecutive_buy_signal']
            consecutive_sell = result.loc[result.index[i], 'consecutive_sell_signal']
            ma_buy = result.loc[result.index[i], 'ma_signal_buy'] if ma_cooldown_ok else False
            ma_sell = result.loc[result.index[i], 'ma_signal_sell'] if ma_cooldown_ok else False

            raw_buy = (consecutive_buy or ma_buy) and unified_cooldown_ok
            raw_sell = (consecutive_sell or ma_sell) and unified_cooldown_ok

            # 5連続・勝率チェック
            is_5_consec = result.loc[result.index[i], 'is_5_consecutive']
            buy_winrate_ok = self.signal_manager.check_winrate_ok('BUY')
            sell_winrate_ok = self.signal_manager.check_winrate_ok('SELL')

            signal_stopped_by_5consec = is_5_consec
            signal_stopped_by_winrate_buy = not buy_winrate_ok
            signal_stopped_by_winrate_sell = not sell_winrate_ok

            # 環境チェック
            is_streak_env = False
            if i >= 10:  # 最低限のデータが必要
                ma_slope_abs = abs(result.loc[result.index[i], 'ma_slope'])
                ma_deviation = abs(
                    (current_row['close'] - result.loc[result.index[i], 'ma_mid']) /
                    result.loc[result.index[i], 'ma_mid'] * 100
                )
                consistency = result.loc[result.index[i], 'consistency']
                max_consec = result.loc[result.index[i], 'max_consecutive']
                bbw = result.loc[result.index[i], 'bbw']

                is_streak_env, _, _ = self.env_matcher.check_if_streak_environment(
                    ma_slope_abs, ma_deviation, consistency, int(max_consec), bbw
                )

            result.loc[result.index[i], 'is_streak_environment'] = is_streak_env

            # 取引許可判定
            trading_allowed = self.streak_detector.trading_mode_active or is_streak_env

            # 最終シグナル
            final_buy = raw_buy and not self.signals_disabled and \
                       buy_winrate_ok and not signal_stopped_by_5consec and \
                       trading_allowed
            final_sell = raw_sell and not self.signals_disabled and \
                        sell_winrate_ok and not signal_stopped_by_5consec and \
                        trading_allowed

            result.loc[result.index[i], 'final_buy_signal'] = final_buy
            result.loc[result.index[i], 'final_sell_signal'] = final_sell

            # シグナル記録
            if final_buy:
                self.signal_manager.add_signal(
                    bar_index=bar_index,
                    timestamp=result.index[i],
                    signal_type='BUY',
                    entry_price=current_row['close'],
                    was_disabled=self.signals_disabled or signal_stopped_by_5consec or signal_stopped_by_winrate_buy,
                    in_streak_mode=self.streak_detector.trading_mode_active
                )
                self.last_signal_bar = bar_index
                self.last_signal_type = 'BUY'
                self.normal_signal_fired = True
                self.reentry_used = False

            if final_sell:
                self.signal_manager.add_signal(
                    bar_index=bar_index,
                    timestamp=result.index[i],
                    signal_type='SELL',
                    entry_price=current_row['close'],
                    was_disabled=self.signals_disabled or signal_stopped_by_5consec or signal_stopped_by_winrate_sell,
                    in_streak_mode=self.streak_detector.trading_mode_active
                )
                self.last_signal_bar = bar_index
                self.last_signal_type = 'SELL'
                self.normal_signal_fired = True
                self.reentry_used = False

            # 勝敗判定（次の足で）
            if i > 0:
                current_is_bullish = current_row['close'] > current_row['open']
                is_win, is_lose = self.signal_manager.judge_signals(
                    bar_index, current_is_bullish
                )

                result.loc[result.index[i], 'current_is_win'] = is_win
                result.loc[result.index[i], 'current_is_lose'] = is_lose

                # 連勝検知更新
                self.streak_detector.update(bar_index, is_win, is_lose)

                # 環境記録（連勝モード中のシグナル時）
                if self.streak_detector.trading_mode_active and (final_buy or final_sell):
                    if i >= 10:
                        self.env_matcher.record_environment(
                            ma_slope=ma_slope_abs,
                            ma_deviation=ma_deviation,
                            consistency=consistency,
                            max_consecutive=int(max_consec),
                            bbw=bbw
                        )

                # 敗北時の処理
                if is_lose:
                    self.signals_disabled = True

                # 勝利時の処理
                if is_win:
                    self.signals_disabled = False

            # 状態記録
            result.loc[result.index[i], 'trading_mode_active'] = \
                self.streak_detector.trading_mode_active
            result.loc[result.index[i], 'signals_disabled'] = self.signals_disabled

            # 古いシグナル削除
            self.signal_manager.cleanup_old_signals(bar_index)

        return result

    def get_statistics(self) -> Dict:
        """
        統計情報を取得

        Returns:
            dict: 統計情報
        """
        # BUY勝率
        buy_has_data, buy_wins, buy_total = self.signal_manager.calculate_winrate('BUY')
        buy_winrate = buy_wins / buy_total * 100 if buy_total > 0 else 0

        # SELL勝率
        sell_has_data, sell_wins, sell_total = self.signal_manager.calculate_winrate('SELL')
        sell_winrate = sell_wins / sell_total * 100 if sell_total > 0 else 0

        # 連勝モード中の勝率
        streak_buy_has_data, streak_buy_wins, streak_buy_total = \
            self.signal_manager.calculate_winrate('BUY', only_streak_mode=True)
        streak_buy_winrate = streak_buy_wins / streak_buy_total * 100 if streak_buy_total > 0 else 0

        streak_sell_has_data, streak_sell_wins, streak_sell_total = \
            self.signal_manager.calculate_winrate('SELL', only_streak_mode=True)
        streak_sell_winrate = streak_sell_wins / streak_sell_total * 100 if streak_sell_total > 0 else 0

        return {
            'buy': {
                'wins': buy_wins,
                'total': buy_total,
                'winrate': buy_winrate,
                'has_data': buy_has_data
            },
            'sell': {
                'wins': sell_wins,
                'total': sell_total,
                'winrate': sell_winrate,
                'has_data': sell_has_data
            },
            'streak_buy': {
                'wins': streak_buy_wins,
                'total': streak_buy_total,
                'winrate': streak_buy_winrate,
                'has_data': streak_buy_has_data
            },
            'streak_sell': {
                'wins': streak_sell_wins,
                'total': streak_sell_total,
                'winrate': streak_sell_winrate,
                'has_data': streak_sell_has_data
            },
            'total_signals': len(self.signal_manager.signals),
            'consecutive_wins': self.streak_detector.consecutive_wins,
            'trading_mode_active': self.streak_detector.trading_mode_active,
            'environment_samples': len(self.env_matcher.streak_env_ma_slope)
        }


if __name__ == "__main__":
    # 簡易テスト
    print("統合バックテストエンジンのテスト")
    print("=" * 70)

    # サンプルデータ生成
    dates = pd.date_range('2024-01-01', periods=500, freq='1min')
    np.random.seed(42)

    # トレンド + ノイズ
    trend = np.linspace(100, 110, 500)
    noise = np.random.randn(500) * 0.3

    close_prices = trend + noise
    df = pd.DataFrame({
        'open': close_prices + np.random.randn(500) * 0.1,
        'high': close_prices + abs(np.random.randn(500) * 0.2),
        'low': close_prices - abs(np.random.randn(500) * 0.2),
        'close': close_prices
    }, index=dates)

    # バックテスト実行
    config = TradingConfig(
        required_wins=3,
        winrate_threshold=60.0,
        stop_signals_below_threshold=False
    )

    engine = BacktestEngine(config)
    result = engine.run(df)

    print(f"✓ バックテスト完了: {len(result)}本")

    # 統計情報
    stats = engine.get_statistics()

    print(f"\n統計情報:")
    print("=" * 70)
    print(f"総シグナル数: {stats['total_signals']}")
    print(f"\nBUY:")
    print(f"  勝率: {stats['buy']['winrate']:.1f}% ({stats['buy']['wins']}/{stats['buy']['total']})")
    print(f"SELL:")
    print(f"  勝率: {stats['sell']['winrate']:.1f}% ({stats['sell']['wins']}/{stats['sell']['total']})")
    print(f"\n連勝モード中:")
    print(f"  BUY勝率: {stats['streak_buy']['winrate']:.1f}% ({stats['streak_buy']['wins']}/{stats['streak_buy']['total']})")
    print(f"  SELL勝率: {stats['streak_sell']['winrate']:.1f}% ({stats['streak_sell']['wins']}/{stats['streak_sell']['total']})")
    print(f"\n現在の連勝数: {stats['consecutive_wins']}")
    print(f"連勝モードアクティブ: {stats['trading_mode_active']}")
    print(f"環境サンプル数: {stats['environment_samples']}")

    # シグナル数
    buy_signals = result['final_buy_signal'].sum()
    sell_signals = result['final_sell_signal'].sum()
    print(f"\nシグナル発生数:")
    print(f"  BUY: {buy_signals}回")
    print(f"  SELL: {sell_signals}回")
    print(f"  合計: {buy_signals + sell_signals}回")

    # 連勝モード期間
    streak_periods = result['trading_mode_active'].sum()
    print(f"\n連勝モード期間: {streak_periods}本 ({streak_periods/len(result)*100:.1f}%)")

    # 環境一致期間
    env_match_periods = result['is_streak_environment'].sum()
    print(f"環境一致期間: {env_match_periods}本 ({env_match_periods/len(result)*100:.1f}%)")
