"""
データローダー

TradingViewからエクスポートしたOHLCVデータと
Pine Scriptから出力したシグナルデータを読み込みます。
"""

import pandas as pd
from pathlib import Path
from typing import Optional


class DataLoader:
    """OHLCVデータとPineシグナルを読み込むクラス"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

    def load_ohlcv(self, filename: str = "USDJPY_1m.csv") -> pd.DataFrame:
        """
        OHLCVデータを読み込む

        Args:
            filename: CSVファイル名

        Returns:
            pd.DataFrame: timestamp, open, high, low, close, volume
        """
        filepath = self.data_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(
                f"{filepath} が見つかりません。\n"
                f"TradingViewからOHLCVデータをエクスポートして配置してください。\n"
                f"詳細: data/README.md を参照"
            )

        df = pd.read_csv(filepath)

        # タイムスタンプをdatetime型に変換
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        elif 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
            df = df.rename(columns={'time': 'timestamp'})
            df = df.set_index('timestamp')

        # 必要なカラムの存在確認
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"必要なカラムが不足しています: {missing_cols}")

        # ソート（念のため）
        df = df.sort_index()

        return df

    def load_pine_signals(self, filename: str = "pine_signals.csv") -> pd.DataFrame:
        """
        Pine Scriptから出力したシグナルデータを読み込む

        Args:
            filename: CSVファイル名

        Returns:
            pd.DataFrame: Pine Scriptの出力データ
        """
        filepath = self.data_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(
                f"{filepath} が見つかりません。\n"
                f"Pine Scriptでシグナルを出力して配置してください。\n"
                f"詳細: scripts/01_export_pine_signals.pine を参照"
            )

        df = pd.read_csv(filepath)

        # タイムスタンプをdatetime型に変換
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        elif 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
            df = df.rename(columns={'time': 'timestamp'})
            df = df.set_index('timestamp')

        # ソート
        df = df.sort_index()

        return df

    def validate_data_alignment(
        self,
        ohlcv: pd.DataFrame,
        pine_signals: pd.DataFrame,
        tolerance_seconds: int = 60
    ) -> dict:
        """
        OHLCVデータとPineシグナルデータのアライメントを検証

        Args:
            ohlcv: OHLCVデータ
            pine_signals: Pineシグナルデータ
            tolerance_seconds: 許容する時刻ずれ（秒）

        Returns:
            dict: 検証結果
        """
        result = {
            "is_aligned": True,
            "ohlcv_rows": len(ohlcv),
            "pine_rows": len(pine_signals),
            "common_rows": 0,
            "ohlcv_only": 0,
            "pine_only": 0,
            "messages": []
        }

        # インデックスの共通部分を確認
        ohlcv_index_set = set(ohlcv.index)
        pine_index_set = set(pine_signals.index)

        common = ohlcv_index_set & pine_index_set
        ohlcv_only = ohlcv_index_set - pine_index_set
        pine_only = pine_index_set - ohlcv_index_set

        result["common_rows"] = len(common)
        result["ohlcv_only"] = len(ohlcv_only)
        result["pine_only"] = len(pine_only)

        # 行数が大きく異なる場合は警告
        if abs(len(ohlcv) - len(pine_signals)) > 10:
            result["is_aligned"] = False
            result["messages"].append(
                f"行数に大きな差があります: OHLCV={len(ohlcv)}, Pine={len(pine_signals)}"
            )

        # 共通データが少ない場合は警告
        if len(common) < min(len(ohlcv), len(pine_signals)) * 0.9:
            result["is_aligned"] = False
            result["messages"].append(
                f"共通する時刻が少なすぎます: {len(common)}/{min(len(ohlcv), len(pine_signals))}"
            )

        # OHLCVの値が一致しているか確認（サンプル）
        if len(common) > 0:
            sample_indices = list(common)[:min(100, len(common))]
            mismatches = []

            for idx in sample_indices:
                if 'close' in pine_signals.columns:
                    ohlcv_close = ohlcv.loc[idx, 'close']
                    pine_close = pine_signals.loc[idx, 'close']

                    # 浮動小数点の比較（相対誤差）
                    if abs(ohlcv_close - pine_close) / ohlcv_close > 0.0001:
                        mismatches.append((idx, ohlcv_close, pine_close))

            if mismatches:
                result["is_aligned"] = False
                result["messages"].append(
                    f"OHLCV値の不一致を検出: {len(mismatches)}件"
                )

        return result


if __name__ == "__main__":
    # 簡易テスト
    loader = DataLoader()

    print("データローダーのテスト")
    print("=" * 50)

    try:
        ohlcv = loader.load_ohlcv()
        print(f"✓ OHLCV読み込み成功: {len(ohlcv)}行")
        print(ohlcv.head())
    except FileNotFoundError as e:
        print(f"✗ OHLCV読み込み失敗:\n{e}")

    print()

    try:
        pine = loader.load_pine_signals()
        print(f"✓ Pineシグナル読み込み成功: {len(pine)}行")
        print(pine.head())

        # アライメント検証
        if 'ohlcv' in locals():
            validation = loader.validate_data_alignment(ohlcv, pine)
            print("\nデータアライメント検証:")
            for key, value in validation.items():
                print(f"  {key}: {value}")

    except FileNotFoundError as e:
        print(f"✗ Pineシグナル読み込み失敗:\n{e}")
