#!/usr/bin/env python3
"""
簡単なパスワードジェネレーター
Simple Password Generator
"""

import random
import string
import argparse


def generate_password(length=12, use_uppercase=True, use_lowercase=True,
                     use_digits=True, use_special=True):
    """
    指定された条件でパスワードを生成します。
    Generate a password with specified conditions.

    Args:
        length (int): パスワードの長さ / Password length
        use_uppercase (bool): 大文字を含める / Include uppercase letters
        use_lowercase (bool): 小文字を含める / Include lowercase letters
        use_digits (bool): 数字を含める / Include digits
        use_special (bool): 特殊文字を含める / Include special characters

    Returns:
        str: 生成されたパスワード / Generated password
    """
    characters = ""

    if use_uppercase:
        characters += string.ascii_uppercase
    if use_lowercase:
        characters += string.ascii_lowercase
    if use_digits:
        characters += string.digits
    if use_special:
        characters += string.punctuation

    if not characters:
        raise ValueError("少なくとも1つの文字タイプを選択してください / At least one character type must be selected")

    # パスワードを生成 / Generate password
    password = ''.join(random.choice(characters) for _ in range(length))

    return password


def generate_memorable_password(num_words=4, separator="-", capitalize=True, add_number=True):
    """
    覚えやすいパスワードを生成します（単語ベース）。
    Generate a memorable password (word-based).

    Args:
        num_words (int): 単語の数 / Number of words
        separator (str): 単語間の区切り文字 / Separator between words
        capitalize (bool): 各単語を大文字で始める / Capitalize each word
        add_number (bool): 末尾に数字を追加 / Add number at the end

    Returns:
        str: 生成されたパスワード / Generated password
    """
    # 簡単な単語リスト / Simple word list
    words = [
        "apple", "banana", "cherry", "dragon", "eagle", "forest",
        "garden", "happy", "island", "jungle", "kitten", "lemon",
        "mountain", "nature", "ocean", "planet", "queen", "river",
        "sunset", "tiger", "umbrella", "valley", "winter", "yellow"
    ]

    selected_words = random.choices(words, k=num_words)

    if capitalize:
        selected_words = [word.capitalize() for word in selected_words]

    password = separator.join(selected_words)

    if add_number:
        password += str(random.randint(10, 99))

    return password


def main():
    """メイン関数 / Main function"""
    parser = argparse.ArgumentParser(
        description='簡単なパスワードジェネレーター / Simple Password Generator'
    )

    parser.add_argument(
        '-l', '--length',
        type=int,
        default=12,
        help='パスワードの長さ（デフォルト: 12）/ Password length (default: 12)'
    )

    parser.add_argument(
        '-n', '--count',
        type=int,
        default=1,
        help='生成するパスワードの数（デフォルト: 1）/ Number of passwords to generate (default: 1)'
    )

    parser.add_argument(
        '--no-uppercase',
        action='store_true',
        help='大文字を除外 / Exclude uppercase letters'
    )

    parser.add_argument(
        '--no-lowercase',
        action='store_true',
        help='小文字を除外 / Exclude lowercase letters'
    )

    parser.add_argument(
        '--no-digits',
        action='store_true',
        help='数字を除外 / Exclude digits'
    )

    parser.add_argument(
        '--no-special',
        action='store_true',
        help='特殊文字を除外 / Exclude special characters'
    )

    parser.add_argument(
        '-m', '--memorable',
        action='store_true',
        help='覚えやすいパスワードを生成 / Generate memorable password'
    )

    parser.add_argument(
        '-w', '--words',
        type=int,
        default=4,
        help='覚えやすいパスワードの単語数（デフォルト: 4）/ Number of words for memorable password (default: 4)'
    )

    args = parser.parse_args()

    print("\n🔐 パスワードジェネレーター / Password Generator\n")
    print("=" * 50)

    for i in range(args.count):
        if args.memorable:
            password = generate_memorable_password(num_words=args.words)
        else:
            password = generate_password(
                length=args.length,
                use_uppercase=not args.no_uppercase,
                use_lowercase=not args.no_lowercase,
                use_digits=not args.no_digits,
                use_special=not args.no_special
            )

        print(f"{i + 1}. {password}")

    print("=" * 50)
    print()


if __name__ == "__main__":
    main()
