# Whisper Audio Transcription Tool

A Python-based audio transcription tool optimized for Apple Silicon (M3) using MLX-Whisper, with faster-whisper as an alternative for batch processing.

## Features

- **Apple Silicon Optimized**: MLX-Whisper leverages M3 GPU/Neural Engine for fast inference
- **Multiple Output Formats**: txt, json, srt, vtt, tsv
- **Word-Level Timestamps**: Optional detailed timing for each word
- **Batch Processing**: Process entire directories (via faster-whisper)
- **Language Detection**: Automatic detection or manual specification
- **Multi-Format Support**: Various audio and video formats

## Supported Formats

- **Audio**: WAV, MP3, M4A, FLAC, OGG, AAC, WMA
- **Video**: MP4, WebM, MKV, AVI, MOV

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd faster-whisper-large-v3-turbo-ct2
   ```

2. **Install dependencies** (using uv):
   ```bash
   uv sync
   ```

## Usage

### MLX-Whisper (Recommended for Apple Silicon)

#### Basic Transcription
```bash
uv run mlx-whisper.py -i audio.mp3
```

#### Specify Output Format
```bash
# VTT subtitles
uv run mlx-whisper.py -i audio.mp3 -f vtt

# SRT subtitles
uv run mlx-whisper.py -i audio.mp3 -f srt

# JSON with full metadata
uv run mlx-whisper.py -i audio.mp3 -f json

# TSV (tab-separated with timestamps)
uv run mlx-whisper.py -i audio.mp3 -f tsv
```

#### With Language and Word Timestamps
```bash
uv run mlx-whisper.py -i audio.mp3 -f vtt --language ja --word-timestamps
```

#### Custom Output Path
```bash
uv run mlx-whisper.py -i audio.mp3 -o transcript.txt
```

### Faster-Whisper (Batch Processing)

#### Single File
```bash
uv run main.py -i audio.mp3
```

#### Directory Batch Processing
```bash
uv run main.py -i /path/to/audio/directory
```

#### With VTT Subtitles
```bash
uv run main.py -i audio.mp3 --segmented
```

## Command Line Options

### mlx-whisper.py (Main)

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--input` | `-i` | Input audio file path | Required |
| `--output` | `-o` | Output file path | Auto-generated |
| `--format` | `-f` | Output format (txt, json, srt, vtt, tsv) | txt |
| `--model` | | Whisper model to use | mlx-community/whisper-large-v3-turbo |
| `--word-timestamps` | | Include word-level timestamps | Off |
| `--language` | | Force specific language (e.g., 'en', 'ja') | Auto-detect |

### main.py (Batch Processing)

| Option | Short | Description | Required |
|--------|-------|-------------|----------|
| `--input` | `-i` | Input audio file or directory path | Yes |
| `--output` | `-o` | Output text file path (single file mode) | No |
| `--segmented` | | Generate timestamped VTT subtitle file | No |

## Output Formats

### Text (.txt)
Plain text transcription of the entire audio.

### JSON (.json)
Full output with segments and metadata:
```json
{
  "text": "Full transcription...",
  "segments": [
    {"start": 0.0, "end": 5.2, "text": "First segment..."}
  ]
}
```

### SRT (.srt)
SubRip subtitle format:
```
1
00:00:00,000 --> 00:00:05,230
First segment of transcribed text.

2
00:00:05,230 --> 00:00:10,450
Second segment of transcribed text.
```

### VTT (.vtt)
WebVTT subtitle format:
```
WEBVTT

00:00:00.000 --> 00:00:05.230
First segment of transcribed text.

00:00:05.230 --> 00:00:10.450
Second segment of transcribed text.
```

### TSV (.tsv)
Tab-separated values with millisecond timestamps:
```
start	end	text
0	5230	First segment of transcribed text.
5230	10450	Second segment of transcribed text.
```

## Dependencies

- **mlx-whisper**: Apple Silicon optimized Whisper (main)
- **faster-whisper**: CPU-based Whisper implementation (batch processing)
- **tqdm**: Progress bar visualization
- **Python 3.10+**: Required Python version

## Models

| Script | Model | Optimization |
|--------|-------|--------------|
| mlx-whisper.py | mlx-community/whisper-large-v3-turbo | Apple Silicon (MLX) |
| main.py | deepdml/faster-whisper-large-v3-turbo-ct2 | CTranslate2 (CPU) |

## When to Use Which Script

| Use Case | Recommended Script |
|----------|-------------------|
| Single file, fastest speed (M3) | mlx-whisper.py |
| Multiple output formats needed | mlx-whisper.py |
| Word-level timestamps | mlx-whisper.py |
| Batch/directory processing | main.py |
| Language detection confidence | main.py |

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool!
