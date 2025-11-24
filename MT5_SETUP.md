# MT5 接続スクリプト 実行手順

## 概要
このスクリプトは MetaTrader5 (MT5) に接続し、価格データを取得します。

## 必要な環境

### Windows環境の場合（推奨）

1. **MT5のインストール**
   - XMTradingなどのブローカーからMT5をダウンロード・インストール
   - 一度MT5を起動してログインしておく

2. **Pythonパッケージのインストール**
   ```bash
   pip install MetaTrader5 pandas
   ```

3. **スクリプトの設定**
   - `mt5_connection_test.py` を開く
   - 以下の3つの値を自分の口座情報に書き換える：
     ```python
     my_login = 12345678          # あなたの口座番号
     my_password = "password"     # あなたのパスワード
     my_server = "XMTrading-MT5-2" # あなたのサーバー名
     ```

4. **実行**
   ```bash
   python mt5_connection_test.py
   ```

### Linux環境の場合（高度）

Linux環境ではMT5がネイティブで動作しないため、以下の手順が必要です：

1. **Wine のインストール**
   ```bash
   sudo apt update
   sudo apt install wine64 wine32
   ```

2. **MT5 のインストール（Wine経由）**
   ```bash
   # MT5インストーラーをダウンロード
   wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe

   # Wineでインストール
   wine mt5setup.exe
   ```

3. **Pythonパッケージのインストール**
   ```bash
   pip3 install MetaTrader5 pandas
   ```

4. **MT5パスの設定**
   スクリプトを修正して、WineでインストールしたMT5のパスを指定：
   ```python
   # mt5.initialize() の前に追加
   mt5_path = "~/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe"
   if not mt5.initialize(path=mt5_path, login=my_login, server=my_server, password=my_password):
   ```

## トラブルシューティング

### 「❌ 接続失敗」と表示される場合

1. **ログイン情報を確認**
   - 口座番号、パスワード、サーバー名が正しいか
   - サーバー名はブローカーからのメールに記載

2. **MT5が起動しているか確認**
   - MT5アプリが一度も起動していない場合、初回接続が失敗することがある
   - MT5を手動で起動してログインしてから、スクリプトを実行

3. **通貨ペアが見つからない**
   - MT5の「気配値表示」にUSDJPYを追加
   - 右クリック → 「すべて表示」

### エラーコードの意味

- `-2`: 初期化失敗（MT5がインストールされていない、またはパスが間違っている）
- `-10006`: ログイン失敗（認証情報が間違っている）
- その他: [公式ドキュメント](https://www.mql5.com/en/docs/integration/python_metatrader5)参照

## 実行結果の例

成功すると以下のような出力が表示されます：

```
MT5への接続を試みます...
✅ 接続成功！

--- USDJPY 現在レート ---
時間: 2025-11-24 10:30:15
売値(Bid): 149.823
買値(Ask): 149.825
------------------------

--- 直近10本の1分足データ ---
                 time    open    high     low   close  tick_volume
0 2025-11-24 10:21:00 149.820 149.825 149.818 149.823           45
1 2025-11-24 10:22:00 149.823 149.827 149.821 149.825           52
...
```

## 次のステップ

接続が成功したら、以下のような機能を追加できます：

- リアルタイム価格監視
- テクニカル指標の計算
- 自動売買ロジックの実装
- バックテスト用データの取得

## 参考リンク

- [MetaTrader5 Python Documentation](https://www.mql5.com/en/docs/integration/python_metatrader5)
- [XMTrading MT5ダウンロード](https://www.xmtrading.com/jp/mt5)
