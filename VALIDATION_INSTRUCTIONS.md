# Pine Script → Python 完全移植検証手順

## 📋 概要

このドキュメントでは、Pine Scriptのトレーディングシステムが正しくPythonに移植されているかを検証する手順を説明します。

## ✅ 実装済み機能の確認

以下の機能はすでにPython実装が完了しています：

### 1. **MA改善版シグナル** (`src/trading_system.py`)
- ✅ トレンドフォローシグナル（trend_following_buy/sell）
- ✅ レンジ相場でのMA反発（ma_bounce_buy/sell）
- ✅ ボリンジャーバンド反転（bb_reversal_buy/sell）
- ✅ トレンド/レンジ自動判定（is_trending）

### 2. **連続ローソク足検知** (`src/trading_system.py`)
- ✅ N本連続の検知（consecutive_buy/sell_signal）
- ✅ 連続カウント（bull_streak/bear_streak）
- ✅ 5連続警告（is_5_consecutive）

### 3. **環境分析** (`src/trading_system.py`)
- ✅ 方向性の一貫性（calculate_directional_consistency）
- ✅ 最大連続パターン（detect_max_consecutive_pattern）
- ✅ BBW計算（calculate_bbw）

### 4. **シグナル管理** (`src/signal_manager.py`)
- ✅ シグナル履歴管理（SignalManager）
- ✅ 勝敗判定（judge_signals）
- ✅ 勝率計算（calculate_winrate）
- ✅ クールダウン処理

### 5. **連勝検知システム** (`src/signal_manager.py`)
- ✅ 連勝カウント（StreakDetector）
- ✅ トレーディングモード判定
- ✅ 時間制限チェック（streak_start_max_bars）
- ✅ 2連敗でリセット

### 6. **環境マッチング** (`src/environment_matcher.py`)
- ✅ 環境データ記録（record_environment）
- ✅ 環境統計計算（get_environment_stats）
- ✅ 環境一致判定（check_if_streak_environment）

### 7. **勝敗分析** (`src/win_loss.py`)
- ✅ 統計情報計算（WinLossAnalyzer）
- ✅ 連勝・連敗検知（StreakDetector）
- ✅ プロフィットファクター計算

## 🔧 検証手順

### ステップ1: Pine Scriptのエクスポート

1. **TradingViewを開く**
   - https://www.tradingview.com/ にアクセス
   - チャートを開く

2. **Pine Editorでスクリプトを開く**
   ```
   scripts/02_full_export_pine_signals.pine
   ```
   このファイルの内容をコピーしてPine Editorに貼り付け

3. **チャートに適用**
   - 「チャートに追加」をクリック
   - 対象の通貨ペア（例：BTCUSD）を選択
   - 時間足を選択（例：1分足、5分足など）

4. **ログを確認**
   - Pine Editorの下部にある「コンソール」タブを開く
   - ログが大量に出力されているはず

5. **CSVファイルとして保存**
   - コンソールのログをすべて選択してコピー
   - テキストエディタに貼り付け
   - 1行目にヘッダーを追加：
   ```csv
   timestamp,open,high,low,close,ma_fast,ma_mid,ma_slow,bb_upper,bb_lower,bb_basis,bbw,ma_slope,ma_deviation,is_trending,ma_signal_buy,ma_signal_sell,consecutive_buy,consecutive_sell,bull_streak,bear_streak,is_5_consecutive,directional_consistency,max_consecutive_pattern,candle_size_score,bar_index
   ```
   - `data/pine_signals_full.csv` として保存

### ステップ2: Python側で検証実行

```bash
python scripts/05_comprehensive_validation.py
```

### ステップ3: 結果の確認

スクリプトが以下の情報を表示します：

```
================================================================================
Pine Script → Python 移植検証結果
================================================================================

Indicator                      Type       一致数          一致率
--------------------------------------------------------------------------------
✅ ma_fast                      float      1000/1000       100.00%
✅ ma_mid                       float      1000/1000       100.00%
✅ ma_slow                      float      1000/1000       100.00%
✅ bb_upper                     float      998/1000        99.80%
✅ bb_lower                     float      998/1000        99.80%
...
--------------------------------------------------------------------------------

総合一致率: 99.52% (19904/20000)

🎉 目標達成！ 99%以上の一致率を達成しました！
================================================================================
```

## 📊 検証項目

以下の20個のインジケーターを検証します：

| # | インジケーター | タイプ | 説明 |
|---|---------------|--------|------|
| 1 | ma_fast | float | 超短期MA（5期間） |
| 2 | ma_mid | float | 短期MA（9期間） |
| 3 | ma_slow | float | 中長期MA（21期間） |
| 4 | bb_upper | float | ボリンジャーバンド上限 |
| 5 | bb_lower | float | ボリンジャーバンド下限 |
| 6 | bb_basis | float | ボリンジャーバンド中心線 |
| 7 | bbw | float | ボリンジャーバンド幅 |
| 8 | ma_slope | float | MA傾き（%） |
| 9 | ma_deviation | float | MA乖離率（%） |
| 10 | is_trending | bool | トレンド判定 |
| 11 | ma_signal_buy | bool | MA買いシグナル |
| 12 | ma_signal_sell | bool | MA売りシグナル |
| 13 | consecutive_buy | bool | 連続買いシグナル |
| 14 | consecutive_sell | bool | 連続売りシグナル |
| 15 | bull_streak | int | 連続陽線カウント |
| 16 | bear_streak | int | 連続陰線カウント |
| 17 | is_5_consecutive | bool | 5連続フラグ |
| 18 | directional_consistency | float | 方向性の一貫性 |
| 19 | max_consecutive_pattern | int | 最大連続パターン |
| 20 | candle_size_score | float | ローソク足サイズスコア |

## 🎯 成功基準

- **総合一致率 99%以上** を目標とします
- 各インジケーターの一致率：
  - ✅ 99%以上: 完璧
  - ⚠️ 95-99%: 許容範囲（微調整が必要な可能性）
  - ❌ 95%未満: 実装に問題あり

## 🔍 トラブルシューティング

### Q1: Pine Scriptのログが表示されない

**A:** Pine Editorのコンソールタブを確認してください。ログが多すぎる場合は、TradingViewのプラン制限により一部しか表示されない可能性があります。

### Q2: 一致率が低い

**A:** 以下を確認してください：
1. Pine Scriptとpythonの設定パラメータが一致しているか
2. タイムスタンプが正しく変換されているか
3. NaN値の扱いが同じか

### Q3: CSVファイルのフォーマットエラー

**A:** 以下を確認してください：
1. ヘッダー行が正しく追加されているか
2. カンマ区切りになっているか
3. 不要な空行がないか

## 📁 ファイル構成

```
jiro/
├── scripts/
│   ├── 01_export_pine_signals.pine      # 旧テンプレート
│   ├── 02_full_export_pine_signals.pine # 完全版エクスポート用（新規作成）
│   ├── 04_validate_pine_port.py         # 旧検証スクリプト（基本MAのみ）
│   └── 05_comprehensive_validation.py    # 完全版検証スクリプト（新規作成）
│
├── src/
│   ├── trading_system.py                # メインシステム
│   ├── signal_manager.py                # シグナル管理
│   ├── environment_matcher.py           # 環境マッチング
│   ├── win_loss.py                      # 勝敗分析
│   ├── signal_history.py                # シグナル履歴
│   └── indicators.py                    # 基本インジケーター
│
└── data/
    ├── pine_signals.csv                 # 旧データ（基本MAのみ）
    └── pine_signals_full.csv            # 完全版データ（手動作成が必要）
```

## 🚀 次のステップ

検証が成功したら：

1. **バックテストの実行**
   ```bash
   python scripts/03_run_backtest.py
   ```

2. **ダッシュボードの起動**
   ```bash
   python server.py
   ```
   ブラウザで `http://localhost:8000` にアクセス（ただし、browser-based Claude Codeでは直接アクセス不可）

3. **リアルタイム監視**
   ```bash
   python terminal_dashboard.py
   ```

## ❓ サポート

問題が発生した場合は、以下の情報を提供してください：
- エラーメッセージ
- Pine Scriptの設定パラメータ
- 使用した通貨ペアと時間足
- サンプルデータ（最初の10行程度）
