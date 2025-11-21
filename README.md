# 簡単なパスワードジェネレーター / Simple Password Generator

Pythonで作成されたシンプルで使いやすいパスワードジェネレーターです。

A simple and easy-to-use password generator written in Python.

## 特徴 / Features

- **ランダムパスワード生成**: 大文字、小文字、数字、特殊文字を組み合わせた強力なパスワードを生成
- **覚えやすいパスワード**: 単語ベースの覚えやすいパスワードを生成
- **カスタマイズ可能**: 長さや文字タイプを自由に設定
- **複数生成**: 一度に複数のパスワードを生成可能

- **Random Password Generation**: Generate strong passwords with uppercase, lowercase, digits, and special characters
- **Memorable Passwords**: Generate word-based memorable passwords
- **Customizable**: Freely configure length and character types
- **Batch Generation**: Generate multiple passwords at once

## 必要要件 / Requirements

- Python 3.6 以上 / Python 3.6 or higher

## 使い方 / Usage

### 基本的な使い方 / Basic Usage

```bash
# デフォルト設定（12文字、すべての文字タイプ使用）
# Default settings (12 characters, all character types)
python3 password_generator.py
```

### オプション / Options

```bash
# 16文字のパスワードを生成
# Generate 16-character password
python3 password_generator.py -l 16

# 5個のパスワードを生成
# Generate 5 passwords
python3 password_generator.py -n 5

# 特殊文字を除外
# Exclude special characters
python3 password_generator.py --no-special

# 数字と特殊文字を除外（英字のみ）
# Exclude digits and special characters (letters only)
python3 password_generator.py --no-digits --no-special

# 覚えやすいパスワードを生成
# Generate memorable password
python3 password_generator.py -m

# 5単語の覚えやすいパスワードを生成
# Generate memorable password with 5 words
python3 password_generator.py -m -w 5
```

### すべてのオプション / All Options

```
-l, --length LENGTH         パスワードの長さ（デフォルト: 12）
                           Password length (default: 12)

-n, --count COUNT          生成するパスワードの数（デフォルト: 1）
                           Number of passwords to generate (default: 1)

--no-uppercase             大文字を除外
                           Exclude uppercase letters

--no-lowercase             小文字を除外
                           Exclude lowercase letters

--no-digits                数字を除外
                           Exclude digits

--no-special               特殊文字を除外
                           Exclude special characters

-m, --memorable            覚えやすいパスワードを生成
                           Generate memorable password

-w, --words WORDS          覚えやすいパスワードの単語数（デフォルト: 4）
                           Number of words for memorable password (default: 4)
```

## 使用例 / Examples

### 例1: 強力な20文字パスワード / Example 1: Strong 20-character password

```bash
python3 password_generator.py -l 20
```

出力例 / Sample output:
```
🔐 パスワードジェネレーター / Password Generator

==================================================
1. K9#mP$xL2@qR7&vN4!t
==================================================
```

### 例2: 3個のパスワードを生成 / Example 2: Generate 3 passwords

```bash
python3 password_generator.py -n 3 -l 14
```

出力例 / Sample output:
```
🔐 パスワードジェネレーター / Password Generator

==================================================
1. aB3$dE6#gH9!k
2. Lm2&Pq5*Rs8@v
3. Wx1^Yz4%Bc7!f
==================================================
```

### 例3: 覚えやすいパスワード / Example 3: Memorable password

```bash
python3 password_generator.py -m
```

出力例 / Sample output:
```
🔐 パスワードジェネレーター / Password Generator

==================================================
1. Dragon-Forest-Happy-Ocean42
==================================================
```

### 例4: 英数字のみ（特殊文字なし）/ Example 4: Alphanumeric only (no special characters)

```bash
python3 password_generator.py -l 16 --no-special
```

出力例 / Sample output:
```
🔐 パスワードジェネレーター / Password Generator

==================================================
1. aB3dE6gH9kLm2Pq
==================================================
```

## セキュリティに関する注意 / Security Notes

- 生成されたパスワードは、安全なパスワードマネージャーに保存してください
- パスワードを他人と共有しないでください
- 定期的にパスワードを変更してください
- 複数のサービスで同じパスワードを使用しないでください

- Store generated passwords in a secure password manager
- Do not share passwords with others
- Change passwords regularly
- Do not use the same password for multiple services

## ライセンス / License

このプロジェクトはMITライセンスの下で公開されています。

This project is released under the MIT License.
