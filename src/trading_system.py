"""
統合トレーディングシステム

Pine Scriptの完全移植版
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
from dataclasses import dataclass
from indicators import Indicators


@dataclass
class TradingConfig:
    """トレーディング設定"""
    # 共通設定
    cooldown_period: int = 5

    # MA設定
    ma_fast_length: int = 5
    ma_mid_length: int = 9
    ma_slow_length: int = 21
    ma_flat_threshold: float = 0.03
    bb_touch_tolerance: float = 0.5
    bb_length: int = 20
    bb_mult: float = 2.0

    # 連続ローソク足設定
    consecutive_threshold: int = 4
    consecutive_5_threshold: int = 4
    warning_period_length: int = 10

    # 勝率設定
    winrate_period: int = 300
    min_signals: int = 3
    win_judge_period: int = 2
    winrate_threshold: float = 70.0
    stop_signals_below_threshold: bool = False

    # 連勝検知設定
    required_wins: int = 3
    exit_on_real_loss: bool = True
    streak_start_max_bars: int = 20

    # 環境分析設定
    environment_match_threshold: int = 4


class TradingSystem:
    """統合トレーディングシステム"""

    def __init__(self, config: TradingConfig = None):
        self.config = config or TradingConfig()

        # 状態管理
        self.signal_history: List[Dict] = []
        self.last_any_signal_bar = 0
        self.last_ma_signal_bar = 0
        self.signals_disabled = False
        self.in_bull_streak = False
        self.in_bear_streak = False

        # 連勝モード
        self.trading_mode_active = False
        self.consecutive_final_wins = 0
        self.previous_bar_was_lose = False
        self.streak_mode_start_bar = 0
        self.first_win_bar = -1

        # 環境データ記録
        self.streak_env_ma_slope: List[float] = []
        self.streak_env_ma_deviation: List[float] = []
        self.streak_env_consistency: List[float] = []
        self.streak_env_max_consecutive: List[int] = []
        self.streak_env_bbw: List[float] = []

        # 5連続背景色履歴
        self.consecutive_bg_history: List[bool] = []
        self.warning_period_start_bar = -1

    def calculate_ma_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        MA改善版シグナル計算

        Args:
            df: OHLCV DataFrame

        Returns:
            pd.DataFrame: シグナル追加されたDataFrame
        """
        result = df.copy()

        # BB計算
        bb_basis = Indicators.sma(df['close'], self.config.bb_length)
        bb_dev = df['close'].rolling(window=self.config.bb_length).std()
        bb_upper = bb_basis + self.config.bb_mult * bb_dev
        bb_lower = bb_basis - self.config.bb_mult * bb_dev

        result['bb_upper'] = bb_upper
        result['bb_lower'] = bb_lower
        result['bb_basis'] = bb_basis

        # MA計算
        ma_fast = Indicators.sma(df['close'], self.config.ma_fast_length)
        ma_mid = Indicators.sma(df['close'], self.config.ma_mid_length)
        ma_slow = Indicators.sma(df['close'], self.config.ma_slow_length)

        result['ma_fast'] = ma_fast
        result['ma_mid'] = ma_mid
        result['ma_slow'] = ma_slow

        # トレンド判定
        uptrend_alignment = (ma_fast > ma_mid) & (ma_mid > ma_slow)
        downtrend_alignment = (ma_fast < ma_mid) & (ma_mid < ma_slow)
        is_trending = uptrend_alignment | downtrend_alignment

        # MA傾き
        ma_slope = (ma_mid - ma_mid.shift(5)) / ma_mid.shift(5) * 100
        is_ma_flat = abs(ma_slope) < self.config.ma_flat_threshold

        # プルバック検知
        small_pullback_up = (df['close'] < ma_fast) & \
                           (df['close'].shift(1) < ma_fast.shift(1)) & \
                           (df['close'] > df['open'])

        small_pullback_down = (df['close'] > ma_fast) & \
                             (df['close'].shift(1) > ma_fast.shift(1)) & \
                             (df['close'] < df['open'])

        # トレンドフォロー
        trend_following_buy = uptrend_alignment & small_pullback_up
        trend_following_sell = downtrend_alignment & small_pullback_down

        # MAタッチ判定
        price_near_ma = abs(df['close'] - ma_mid) / ma_mid * 100 < 0.02
        ma_cross_up = Indicators.crossover(df['close'], ma_mid)
        ma_cross_down = Indicators.crossunder(df['close'], ma_mid)

        ma_touch_from_below = ma_cross_up | (price_near_ma & (df['close'] > ma_mid))
        ma_touch_from_above = ma_cross_down | (price_near_ma & (df['close'] < ma_mid))

        # MA反発
        ma_bounce_buy = ma_touch_from_below & is_ma_flat & (df['close'] > df['open'])
        ma_bounce_sell = ma_touch_from_above & is_ma_flat & (df['close'] < df['open'])

        # BB反転
        bb_lower_touch = df['low'] <= bb_lower * (1 + self.config.bb_touch_tolerance / 100)
        bb_upper_touch = df['high'] >= bb_upper * (1 - self.config.bb_touch_tolerance / 100)

        bb_reversal_buy = bb_lower_touch & (df['close'] > df['open']) & (df['close'] > ma_mid)
        bb_reversal_sell = bb_upper_touch & (df['close'] < df['open']) & (df['close'] < ma_mid)

        # 最終シグナル
        ma_signal_buy = pd.Series(False, index=df.index)
        ma_signal_sell = pd.Series(False, index=df.index)

        # トレンド時はフォロー、レンジ時は反発・反転
        ma_signal_buy.loc[is_trending] = trend_following_buy[is_trending].astype(bool)
        ma_signal_buy.loc[~is_trending] = (ma_bounce_buy | bb_reversal_buy)[~is_trending].astype(bool)

        ma_signal_sell.loc[is_trending] = trend_following_sell[is_trending].astype(bool)
        ma_signal_sell.loc[~is_trending] = (ma_bounce_sell | bb_reversal_sell)[~is_trending].astype(bool)

        result['ma_signal_buy'] = ma_signal_buy
        result['ma_signal_sell'] = ma_signal_sell
        result['ma_slope'] = ma_slope
        result['is_trending'] = is_trending

        return result

    def calculate_consecutive_candles(
        self,
        df: pd.DataFrame
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        連続ローソク足検知

        Returns:
            (consecutive_buy_signal, consecutive_sell_signal, bull_streak, bear_streak)
        """
        consecutive_buy = pd.Series(False, index=df.index)
        consecutive_sell = pd.Series(False, index=df.index)

        bullish = df['close'] > df['open']
        bearish = df['close'] < df['open']

        # 連続カウント
        bull_streak = pd.Series(0, index=df.index)
        bear_streak = pd.Series(0, index=df.index)

        for i in range(len(df)):
            if i == 0:
                if bullish.iloc[i]:
                    bull_streak.iloc[i] = 1
                elif bearish.iloc[i]:
                    bear_streak.iloc[i] = 1
            else:
                if bullish.iloc[i]:
                    bull_streak.iloc[i] = bull_streak.iloc[i-1] + 1 if bullish.iloc[i-1] else 1
                    bear_streak.iloc[i] = 0
                elif bearish.iloc[i]:
                    bear_streak.iloc[i] = bear_streak.iloc[i-1] + 1 if bearish.iloc[i-1] else 1
                    bull_streak.iloc[i] = 0
                else:
                    bull_streak.iloc[i] = 0
                    bear_streak.iloc[i] = 0

        # N本連続でシグナル（逆張り）
        # N本連続陽線 → 売りシグナル
        # N本連続陰線 → 買いシグナル
        for i in range(1, len(df)):
            if bull_streak.iloc[i] >= self.config.consecutive_threshold and \
               bull_streak.iloc[i-1] < self.config.consecutive_threshold:
                consecutive_sell.iloc[i] = True

            if bear_streak.iloc[i] >= self.config.consecutive_threshold and \
               bear_streak.iloc[i-1] < self.config.consecutive_threshold:
                consecutive_buy.iloc[i] = True

        return consecutive_buy, consecutive_sell, bull_streak, bear_streak

    def detect_5_consecutive(self, df: pd.DataFrame) -> pd.Series:
        """
        5連続ローソク足検知（警告用）

        Returns:
            pd.Series: 5連続フラグ
        """
        is_5_consecutive = pd.Series(False, index=df.index)

        bullish = df['close'] > df['open']
        bearish = df['close'] < df['open']

        for i in range(self.config.consecutive_5_threshold - 1, len(df)):
            # 過去N本全て陽線 or 全て陰線
            last_n_bullish = all(bullish.iloc[i-j] for j in range(self.config.consecutive_5_threshold))
            last_n_bearish = all(bearish.iloc[i-j] for j in range(self.config.consecutive_5_threshold))

            if last_n_bullish or last_n_bearish:
                is_5_consecutive.iloc[i] = True

        return is_5_consecutive

    def calculate_directional_consistency(
        self,
        df: pd.DataFrame,
        lookback: int = 10
    ) -> pd.Series:
        """
        方向性の一貫性を計算

        Returns:
            pd.Series: 一貫性スコア（0.5-1.0）
        """
        consistency = pd.Series(0.0, index=df.index)

        for i in range(lookback, len(df)):
            window = df.iloc[i-lookback+1:i+1]
            bullish_count = (window['close'] > window['open']).sum()
            bearish_count = (window['close'] < window['open']).sum()

            max_count = max(bullish_count, bearish_count)
            consistency.iloc[i] = max_count / lookback

        return consistency

    def detect_max_consecutive_pattern(
        self,
        df: pd.DataFrame,
        lookback: int = 10
    ) -> pd.Series:
        """
        期間内の最大連続本数を検知

        Returns:
            pd.Series: 最大連続本数
        """
        max_consecutive = pd.Series(0, index=df.index)

        for i in range(lookback, len(df)):
            window = df.iloc[i-lookback+1:i+1]

            max_bull = 0
            max_bear = 0
            current_bull = 0
            current_bear = 0

            for idx in window.index:
                if window.loc[idx, 'close'] > window.loc[idx, 'open']:
                    current_bull += 1
                    current_bear = 0
                else:
                    current_bear += 1
                    current_bull = 0

                max_bull = max(max_bull, current_bull)
                max_bear = max(max_bear, current_bear)

            max_consecutive.iloc[i] = max(max_bull, max_bear)

        return max_consecutive

    def calculate_bbw(self, df: pd.DataFrame) -> pd.Series:
        """
        ボリンジャーバンド幅（BBW）を計算

        Returns:
            pd.Series: BBW (%)
        """
        if 'bb_upper' not in df.columns:
            df = self.calculate_ma_signals(df)

        bbw = (df['bb_upper'] - df['bb_lower']) / df['bb_basis'] * 100
        return bbw


if __name__ == "__main__":
    # 簡易テスト
    print("統合トレーディングシステムのテスト")
    print("=" * 70)

    # サンプルデータ
    dates = pd.date_range('2024-01-01', periods=200, freq='1min')
    np.random.seed(42)

    trend = np.linspace(100, 110, 200)
    noise = np.random.randn(200) * 0.5
    close_prices = trend + noise

    df = pd.DataFrame({
        'open': close_prices + np.random.randn(200) * 0.1,
        'high': close_prices + abs(np.random.randn(200) * 0.3),
        'low': close_prices - abs(np.random.randn(200) * 0.3),
        'close': close_prices
    }, index=dates)

    # システム初期化
    config = TradingConfig()
    system = TradingSystem(config)

    # MAシグナル計算
    result = system.calculate_ma_signals(df)

    print(f"✓ MAシグナル計算完了")
    print(f"  買いシグナル: {result['ma_signal_buy'].sum()}回")
    print(f"  売りシグナル: {result['ma_signal_sell'].sum()}回")

    # 連続ローソク足検知
    consec_buy, consec_sell, bull_streak, bear_streak = \
        system.calculate_consecutive_candles(df)

    print(f"\n✓ 連続ローソク足検知完了")
    print(f"  連続買いシグナル: {consec_buy.sum()}回")
    print(f"  連続売りシグナル: {consec_sell.sum()}回")
    print(f"  最大連続陽線: {bull_streak.max()}本")
    print(f"  最大連続陰線: {bear_streak.max()}本")

    # 5連続検知
    is_5_consec = system.detect_5_consecutive(df)
    print(f"\n✓ 5連続検知: {is_5_consec.sum()}回")

    # 環境分析
    consistency = system.calculate_directional_consistency(df)
    max_consec = system.detect_max_consecutive_pattern(df)
    bbw = system.calculate_bbw(result)

    print(f"\n✓ 環境分析完了")
    print(f"  平均一貫性: {consistency[consistency > 0].mean():.2%}")
    print(f"  平均最大連続: {max_consec[max_consec > 0].mean():.1f}本")
    print(f"  平均BBW: {bbw[bbw > 0].mean():.2f}%")
