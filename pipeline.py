#!/usr/bin/env python3
"""
Main pipeline for downloading YouTube videos and transcribing them.
Automatically selects the appropriate transcription engine based on platform:
- Apple Silicon (M1/M2/M3): mlx-whisper
- Windows/Other: faster-whisper

URLs and settings come from config.py but can be overridden on the command
line, e.g.:

    python pipeline.py "https://www.youtube.com/watch?v=..." -d ./MyTalk -f srt
"""

import argparse
import os
import platform
import sys

try:
    import config
except ImportError:
    print(
        "config.py not found. Copy the template first:\n"
        "    cp config.example.py config.py",
        file=sys.stderr,
    )
    sys.exit(1)

from common import MEDIA_EXTENSIONS, OUTPUT_FORMATS, find_media_files, save_output
from downloader import download_videos, get_downloaded_files


def detect_platform() -> str:
    """
    Detect the current platform and return the appropriate transcription engine.

    Returns:
        'mlx' for Apple Silicon Mac, 'faster' for Windows/other
    """
    system = platform.system()
    machine = platform.machine()

    if system == "Darwin" and machine == "arm64":
        return "mlx"
    else:
        return "faster"


def transcribe_with_mlx(input_dir: str, output_format: str, language: str = None, force: bool = False) -> tuple:
    """Transcribe using mlx-whisper (Apple Silicon). Returns (output_files, failed)."""
    import mlx_whisper_cli

    return mlx_whisper_cli.transcribe_directory(
        input_dir=input_dir,
        output_format=output_format,
        language=language,
        force=force
    )


def transcribe_with_faster_whisper(input_dir: str, output_format: str, language: str = None, force: bool = False) -> tuple:
    """Transcribe using faster-whisper (Windows/CPU). Returns (output_files, failed)."""
    from faster_whisper import WhisperModel
    from tqdm import tqdm

    files = find_media_files(input_dir)

    if not files:
        print(f"No media files found in '{input_dir}'")
        return [], 0

    print(f"Found {len(files)} media file(s) in '{input_dir}'")
    print("-" * 50)

    # Skip files that already have a transcript (unless force)
    ext = output_format if output_format in OUTPUT_FORMATS else "txt"
    pending = []
    skipped = 0
    for filename in files:
        base_name = os.path.splitext(os.path.join(input_dir, filename))[0]
        if not force and os.path.exists(f"{base_name}.{ext}"):
            print(f"Skipping (transcript exists): {filename}")
            skipped += 1
        else:
            pending.append(filename)

    if not pending:
        print(f"All {len(files)} file(s) already transcribed. Use --force to re-transcribe.")
        return [], 0

    model = WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2")

    output_files = []
    failed = 0

    for i, filename in enumerate(pending, 1):
        input_file = os.path.join(input_dir, filename)
        base_name = os.path.splitext(input_file)[0]

        print(f"\n[{i}/{len(pending)}] Processing: {filename}")
        print(f"Transcribing '{input_file}'...")

        try:
            transcribe_options = {"vad_filter": True}
            if language:
                transcribe_options["language"] = language

            segments, info = model.transcribe(input_file, **transcribe_options)

            transcript_text = []
            segment_dicts = []

            with tqdm(desc="Processing segments", unit="segment") as pbar:
                for segment in segments:
                    text = segment.text.strip()
                    transcript_text.append(text)
                    segment_dicts.append({
                        "start": segment.start,
                        "end": segment.end,
                        "text": text
                    })

                    pbar.update(1)
                    pbar.set_postfix_str(f"Current: {text[:50]}...")

            result = {
                "text": " ".join(transcript_text),
                "segments": segment_dicts,
                "language": info.language,
            }
            output_file = f"{base_name}.{ext}"
            save_output(result, output_file, ext)

            print(f"Transcription saved to: {output_file}")
            print(f"Language detected: {info.language} (probability: {info.language_probability:.2f})")
            output_files.append(output_file)

        except Exception as e:
            print(f"Error transcribing '{filename}': {e}", file=sys.stderr)
            failed += 1

    print("-" * 50)
    print(f"Transcription complete. Processed: {len(output_files)}/{len(pending)} files"
          + (f" (skipped {skipped} existing)" if skipped else "")
          + (f" (failed {failed})" if failed else ""))

    return output_files, failed


def cleanup_media_files(directory: str) -> int:
    """Delete media files after successful transcription."""
    deleted = 0
    for filename in find_media_files(directory):
        filepath = os.path.join(directory, filename)
        try:
            os.remove(filepath)
            print(f"Deleted: {filename}")
            deleted += 1
        except Exception as e:
            print(f"Failed to delete {filename}: {e}", file=sys.stderr)

    return deleted


def run_pipeline(
    urls: list = None,
    download_dir: str = None,
    output_format: str = None,
    language: str = None,
    audio_only: bool = None,
    download_only: bool = False,
    transcribe_only: bool = False,
    force: bool = False,
) -> int:
    """
    Run the full pipeline: download -> transcribe -> cleanup.

    Args default to the values in config.py when None.

    Args:
        urls: YouTube URLs to download (videos or playlists)
        download_dir: Directory for downloads and transcripts
        output_format: Transcript format (txt, json, srt, vtt, tsv)
        language: Transcription language (None for auto-detect)
        audio_only: Download audio only instead of full video
        download_only: Only download, skip transcription
        transcribe_only: Only transcribe existing files, skip download
        force: Re-transcribe files that already have a transcript

    Returns:
        Number of failed transcriptions (0 on full success)
    """
    urls = urls if urls else config.YOUTUBE_URLS
    download_dir = download_dir if download_dir is not None else config.DOWNLOAD_DIR
    output_format = output_format if output_format is not None else config.OUTPUT_FORMAT
    language = language if language is not None else config.LANGUAGE
    audio_only = audio_only if audio_only is not None else config.AUDIO_ONLY

    print("=" * 60)
    print("YouTube Download & Transcription Pipeline")
    print("=" * 60)

    # Detect platform
    engine = detect_platform()
    engine_name = "mlx-whisper (Apple Silicon)" if engine == "mlx" else "faster-whisper"
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Transcription engine: {engine_name}")
    print(f"Output format: {output_format}")
    print(f"Language: {language if language else 'auto-detect'}")
    print(f"Download directory: {os.path.abspath(download_dir)}")
    print("=" * 60)

    # Phase 1: Download
    if not transcribe_only:
        print("\n[Phase 1] Downloading videos...")
        print("-" * 50)
        downloaded = download_videos(urls, download_dir, audio_only)
        if not downloaded:
            print("No videos downloaded.")
    else:
        print("\n[Phase 1] Skipped (--transcribe-only)")

    if download_only:
        print("\n[Phase 2] Skipped (--download-only)")
        print("\nPipeline complete (download only).")
        return 0

    # Phase 2: Transcribe
    print("\n[Phase 2] Transcribing files...")
    print("-" * 50)

    # Check if there are files to transcribe
    files = get_downloaded_files(download_dir)
    if not files:
        print(f"No media files found in '{download_dir}'")
        print("\nPipeline complete (no files to transcribe).")
        return 0

    if engine == "mlx":
        output_files, failed = transcribe_with_mlx(download_dir, output_format, language, force)
    else:
        output_files, failed = transcribe_with_faster_whisper(download_dir, output_format, language, force)

    # Phase 3: Cleanup
    if config.DELETE_AFTER_TRANSCRIPTION and output_files:
        print("\n[Phase 3] Cleaning up media files...")
        print("-" * 50)
        deleted = cleanup_media_files(download_dir)
        print(f"Deleted {deleted} media file(s)")
    else:
        print("\n[Phase 3] Cleanup skipped (DELETE_AFTER_TRANSCRIPTION=False)")

    # Summary
    print("\n" + "=" * 60)
    print("Pipeline complete!" if not failed else f"Pipeline finished with {failed} failure(s).")
    print(f"Transcribed files: {len(output_files)}")
    if output_files:
        print(f"Output directory: {os.path.abspath(download_dir)}")
    print("=" * 60)

    return failed


def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube videos and transcribe them"
    )

    parser.add_argument(
        "urls",
        nargs="*",
        help="YouTube URLs (videos or playlists). Defaults to YOUTUBE_URLS in config.py"
    )

    parser.add_argument(
        "-d", "--dir",
        help="Download/transcript directory. Defaults to DOWNLOAD_DIR in config.py"
    )

    parser.add_argument(
        "-f", "--format",
        choices=OUTPUT_FORMATS,
        help="Transcript format. Defaults to OUTPUT_FORMAT in config.py"
    )

    parser.add_argument(
        "-l", "--language",
        help="Transcription language (e.g. 'en', 'ja'). Defaults to LANGUAGE in config.py"
    )

    media_group = parser.add_mutually_exclusive_group()
    media_group.add_argument(
        "--audio-only",
        action="store_true",
        default=None,
        help="Download audio only (overrides AUDIO_ONLY in config.py)"
    )
    media_group.add_argument(
        "--video",
        action="store_true",
        help="Download full video (overrides AUDIO_ONLY in config.py)"
    )

    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download videos, skip transcription"
    )

    parser.add_argument(
        "--transcribe-only",
        action="store_true",
        help="Only transcribe existing files, skip download"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-transcribe files that already have a transcript"
    )

    args = parser.parse_args()

    if args.download_only and args.transcribe_only:
        print("Error: Cannot use both --download-only and --transcribe-only", file=sys.stderr)
        sys.exit(1)

    audio_only = None
    if args.audio_only:
        audio_only = True
    elif args.video:
        audio_only = False

    failed = run_pipeline(
        urls=args.urls,
        download_dir=args.dir,
        output_format=args.format,
        language=args.language,
        audio_only=audio_only,
        download_only=args.download_only,
        transcribe_only=args.transcribe_only,
        force=args.force,
    )

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
