# プロジェクト知見集

## アーキテクチャ決定
- faster-whisper + CTranslate2 構成
- シンプルなCLI/バッチ処理を基本とする

## 実装パターン
- 進捗表示には tqdm を利用
- 設定ファイルは YAML/JSON で管理

## 避けるべきパターン
- Apple Silicon の GPU/NPU 利用は不可
- 長時間音声の一括処理はメモリ消費に注意
