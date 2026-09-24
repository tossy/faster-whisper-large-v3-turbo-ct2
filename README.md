# Whisper Audio Transcription Tool

A Python-based audio transcription tool optimized for Apple Silicon (M3) using MLX-Whisper, with faster-whisper as an alternative for batch processing. Includes a complete YouTube download and transcription pipeline.

## Features

- **YouTube Download Pipeline**: Download videos/playlists from YouTube and automatically transcribe
- **Apple Silicon Optimized**: MLX-Whisper leverages M3 GPU/Neural Engine for fast inference
- **Multiple Output Formats**: txt, json, srt, vtt, tsv
- **Word-Level Timestamps**: Optional detailed timing for each word
- **Batch Processing**: Process entire directories
- **Language Detection**: Automatic detection or manual specification
- **Multi-Format Support**: Various audio and video formats
- **Automatic Cleanup**: Optionally delete media files after transcription

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

3. **Create your local config** (gitignored, keeps your URLs private):
   ```bash
   cp config.example.py config.py
   ```
   Then edit `config.py` with your YouTube URLs and settings.

## Usage

### Pipeline (YouTube Download & Transcription)

The pipeline automatically downloads YouTube videos and transcribes them. Configure settings in `config.py` (created from `config.example.py`, kept out of git).

#### Configuration (config.py)

```python
# YouTube URLs (single videos or playlists)
YOUTUBE_URLS = [
    "https://www.youtube.com/playlist?list=PLxxxxxxxx",
    "https://www.youtube.com/watch?v=VIDEO_ID",
]

# Download directory
DOWNLOAD_DIR = "./downloads"

# Browser to read YouTube cookies from ("brave", "chrome", "firefox", ...).
# Required as of 2026: unauthenticated downloads fail with HTTP 403.
# None = no cookies.
COOKIES_FROM_BROWSER = None

# Audio only mode (smaller files, faster download)
AUDIO_ONLY = False

# Output format: "txt", "vtt", "srt", "json", "tsv"
OUTPUT_FORMAT = "vtt"

# Language (None for auto-detect, or "en", "ja", etc.)
LANGUAGE = None

# Delete media files after transcription
DELETE_AFTER_TRANSCRIPTION = False
```

#### Run Full Pipeline
```bash
# Use URLs and settings from config.py
uv run pipeline.py

# Or override on the command line (no config.py edit needed)
uv run pipeline.py "https://www.youtube.com/watch?v=VIDEO_ID" -d ./MyTalk -f srt
```

#### Download Only (Skip Transcription)
```bash
uv run pipeline.py --download-only
```

#### Transcribe Only (Skip Download)
```bash
uv run pipeline.py --transcribe-only
```

#### Re-transcribe Existing Files
Already-transcribed files are skipped by default (a transcript with the target
format already exists next to the media file). To redo transcription:
```bash
uv run pipeline.py --transcribe-only --force
```

### Avoiding Duplicate Downloads

A project-wide registry at `.registry.json` records every video that has been
downloaded or transcribed, keyed by YouTube video ID. Before each run the
pipeline rebuilds it and generates `.download-archive.txt` at the project root,
which is what yt-dlp reads to skip finished videos.

The registry is **project-wide, not per-directory**. Running the same playlist
into a new `--dir` still skips everything already downloaded elsewhere. (The
archive used to live inside each output directory, so a new `--dir` re-fetched
the whole playlist.)

It is also **rebuildable**. Downloads are named `<title> [<video id>].<ext>`, so
every media file and every transcript carries its own ID. Delete
`.registry.json` and the next run reconstructs it by scanning the project.

A video counts as done when a transcript exists, when its media is still on
disk, or when it appears in an old per-directory archive. A video whose
transcription failed is downloaded again, because cleanup keeps media that has
no transcript.

```bash
# Inspect
uv run registry.py stats            # counts
uv run registry.py list             # every tracked video
uv run registry.py list --pending   # videos still needing a download

# Rescan the project and regenerate the archive
uv run registry.py rebuild

# Force one video back into the download set
uv run registry.py forget VIDEO_ID
uv run pipeline.py --redownload VIDEO_ID
```

### MLX-Whisper (Recommended for Apple Silicon)

#### Basic Transcription
```bash
uv run mlx_whisper_cli.py -i audio.mp3
```

#### Specify Output Format
```bash
# VTT subtitles
uv run mlx_whisper_cli.py -i audio.mp3 -f vtt

# SRT subtitles
uv run mlx_whisper_cli.py -i audio.mp3 -f srt

# JSON with full metadata
uv run mlx_whisper_cli.py -i audio.mp3 -f json

# TSV (tab-separated with timestamps)
uv run mlx_whisper_cli.py -i audio.mp3 -f tsv
```

#### With Language and Word Timestamps
```bash
uv run mlx_whisper_cli.py -i audio.mp3 -f vtt --language ja --word-timestamps
```

#### Custom Output Path
```bash
uv run mlx_whisper_cli.py -i audio.mp3 -o transcript.txt
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

### pipeline.py (YouTube Download & Transcription)

| Option | Short | Description |
|--------|-------|-------------|
| `urls` (positional) | | YouTube URLs (videos or playlists), overrides `YOUTUBE_URLS` |
| `--dir` | `-d` | Download/transcript directory, overrides `DOWNLOAD_DIR` |
| `--format` | `-f` | Transcript format (txt, json, srt, vtt, tsv), overrides `OUTPUT_FORMAT` |
| `--language` | `-l` | Language (e.g. 'en', 'ja'), overrides `LANGUAGE` |
| `--audio-only` / `--video` | | Override `AUDIO_ONLY` |
| `--download-only` | | Only download videos, skip transcription |
| `--transcribe-only` | | Only transcribe existing files in download directory |
| `--force` | | Re-transcribe files that already have a transcript |
| `--cookies-from-browser` | | Browser to read YouTube cookies from, overrides `COOKIES_FROM_BROWSER` |
| `--redownload` | | Video ID to drop from the registry so it downloads again (repeatable) |
| `--no-registry` | | Ignore the registry (may re-download finished videos) |

Defaults come from `config.py` (see Configuration section above). Exit code is
non-zero if any transcription fails.

### mlx_whisper_cli.py (Main)

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--input` | `-i` | Input audio file path | Required |
| `--output` | `-o` | Output file path | Auto-generated |
| `--format` | `-f` | Output format (txt, json, srt, vtt, tsv) | txt |
| `--model` | | Whisper model to use | mlx-community/whisper-large-v3-turbo |
| `--word-timestamps` | | Include word-level timestamps | Off |
| `--language` | | Force specific language (e.g., 'en', 'ja') | Auto-detect |
| `--force` | | Re-transcribe even if output exists (directory mode) | Off |

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

- **yt-dlp**: YouTube video downloader (pipeline)
- **mlx-whisper**: Apple Silicon optimized Whisper (main)
- **faster-whisper**: CPU-based Whisper implementation (batch processing)
- **tqdm**: Progress bar visualization
- **Python 3.10+**: Required Python version

## Models

| Script | Model | Optimization |
|--------|-------|--------------|
| pipeline.py | Auto-selects based on platform | Apple Silicon or CPU |
| mlx_whisper_cli.py | mlx-community/whisper-large-v3-turbo | Apple Silicon (MLX) |
| main.py | deepdml/faster-whisper-large-v3-turbo-ct2 | CTranslate2 (CPU) |

## When to Use Which Script

| Use Case | Recommended Script |
|----------|-------------------|
| YouTube video/playlist transcription | pipeline.py |
| Automated download + transcribe workflow | pipeline.py |
| Single file, fastest speed (M3) | mlx_whisper_cli.py |
| Multiple output formats needed | mlx_whisper_cli.py |
| Word-level timestamps | mlx_whisper_cli.py |
| Batch/directory processing | main.py |
| Language detection confidence | main.py |

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool!
