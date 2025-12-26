# プロジェクト知見集

## アーキテクチャ決定
- **mlx-whisper (メイン)**: Apple Silicon M3 に最適化、MLXフレームワーク活用
- faster-whisper + CTranslate2: 代替構成（バッチ処理用）
- シンプルなCLI処理を基本とする

## 実装パターン

### mlx-whisper での文字起こし
```python
import mlx_whisper

result = mlx_whisper.transcribe(
    "audio.mp3",
    path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
    word_timestamps=True,  # オプション
    language="ja"  # オプション
)
# result["text"] - 全文テキスト
# result["segments"] - セグメント配列 (start, end, text)
```

### 出力フォーマット変換
- txt: `result["text"]` をそのまま出力
- json: `json.dump(result, ...)` で全データ保存
- srt/vtt: segments をタイムスタンプ付きで整形
- tsv: ミリ秒タイムスタンプでタブ区切り

### タイムスタンプフォーマット
```python
def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
```

## 避けるべきパターン
- 長時間音声の一括処理はメモリ消費に注意
- faster-whisper は CPU のみ使用（M3 の性能を活かせない）

## MLX vs faster-whisper 選択基準
| 用途 | 推奨 |
|------|------|
| 単一ファイル処理 | mlx-whisper.py |
| バッチ/ディレクトリ処理 | main.py (faster-whisper) |
| 最速処理 (M3) | mlx-whisper.py |
| 言語検出確信度が必要 | main.py (faster-whisper)
