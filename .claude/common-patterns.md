# よく使用するパターン

## mlx-whisper 基本使用 (メイン)

### シンプルな文字起こし
```bash
uv run mlx-whisper.py -i audio.mp3
```

### フォーマット指定
```bash
# VTT字幕出力
uv run mlx-whisper.py -i audio.mp3 -f vtt

# SRT字幕出力
uv run mlx-whisper.py -i audio.mp3 -f srt

# JSON出力（全メタデータ）
uv run mlx-whisper.py -i audio.mp3 -f json
```

### 言語指定と単語タイムスタンプ
```bash
uv run mlx-whisper.py -i audio.mp3 -f vtt --language ja --word-timestamps
```

### 出力ファイル指定
```bash
uv run mlx-whisper.py -i audio.mp3 -o transcript.txt
```

## faster-whisper 使用 (バッチ処理用)

### 単一ファイル処理
```bash
uv run main.py -i audio.mp3
```

### ディレクトリ一括処理
```bash
uv run main.py -i ./audio_files/
```

### VTT出力付き
```bash
uv run main.py -i audio.mp3 --segmented
```

## Python コード内での使用

### mlx-whisper
```python
import mlx_whisper

result = mlx_whisper.transcribe(
    "audio.mp3",
    path_or_hf_repo="mlx-community/whisper-large-v3-turbo"
)
print(result["text"])
```

### faster-whisper
```python
from faster_whisper import WhisperModel

model = WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2")
segments, info = model.transcribe("audio.mp3")
for segment in segments:
    print(segment.text)
```

## 進捗バー付き処理
```python
from tqdm import tqdm
for item in tqdm(items):
    process(item)
```
