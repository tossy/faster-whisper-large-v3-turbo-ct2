# プロジェクトコンテキスト

## 概要
- プロジェクト名: faster-whisper-large-v3-turbo-ct2
- 技術スタック: Python, mlx-whisper (メイン), faster-whisper (代替)
- 目標: 高速かつ高精度な音声認識システムの構築

## 制約条件
- Mac (Apple Silicon M3) 環境での動作
- MLX フレームワークによる Apple Silicon 最適化

## 技術選定理由
- **mlx-whisper (メイン)**: Apple Silicon (M3チップ) に最適化されたMLXフレームワークベース。GPU/Neural Engine を活用し高速推論が可能
- faster-whisper + CTranslate2: 代替実装（CPUベース）

## パッケージ管理
- `uv` のみを使用し、 `pip` は使用しない
- インストール方法: `uv add [package_name]`
- ツールの実行: `uv run [tool_name.py]`

## 機能仕様
- 単一ファイル処理
- 対応フォーマット: WAV, MP3, M4A, FLAC, OGG, AAC, WMA, MP4, WebM, MKV, AVI, MOV
- 複数出力フォーマット対応: txt, json, srt, vtt, tsv
- 単語レベルタイムスタンプ対応
- 言語指定機能

## 実行環境
- Python: 3.10+
- **メイン使用モデル**: mlx-community/whisper-large-v3-turbo (MLX最適化版)
- 代替モデル: deepdml/faster-whisper-large-v3-turbo-ct2 (CTranslate2版)
- 依存関係: mlx-whisper, faster-whisper, tqdm

## コマンドライン仕様 (mlx-whisper.py - メイン)
- 基本実行: `uv run mlx-whisper.py -i <input> [-o <output>] [-f <format>]`
- 必須オプション: `-i/--input` (入力ファイルパス)
- オプション:
  - `-o/--output`: 出力ファイルパス
  - `-f/--format`: 出力形式 (txt, json, srt, vtt, tsv) デフォルト: txt
  - `--model`: 使用モデル (デフォルト: mlx-community/whisper-large-v3-turbo)
  - `--word-timestamps`: 単語レベルタイムスタンプ有効化
  - `--language`: 言語指定 (例: 'en', 'ja')

## コマンドライン仕様 (main.py - 代替/バッチ処理用)
- 基本実行: `uv run main.py -i <input> [-o <output>] [--segmented]`
- ディレクトリ一括処理対応

## 出力ファイル仕様
- テキスト出力: UTF-8エンコーディング、.txt拡張子
- JSON出力: 完全なメタデータとセグメント情報
- SRT/VTT出力: 字幕形式（タイムスタンプ付き）
- TSV出力: タブ区切り（ミリ秒タイムスタンプ）
- ファイル命名: 入力ファイル名ベース（拡張子変更）

## プロジェクト構造
- **メインスクリプト: mlx-whisper.py** (Apple Silicon最適化版)
- 代替スクリプト: main.py (faster-whisper/CTranslate2版、バッチ処理対応)
- 設定ファイル: pyproject.toml
- 出力ディレクトリ: target/, done/ (処理済みファイル格納)

