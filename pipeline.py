#!/usr/bin/env python3
"""
Main pipeline for downloading YouTube videos and transcribing them.
Automatically selects the appropriate transcription engine based on platform:
- Apple Silicon (M1/M2/M3): mlx-whisper
- Windows/Other: faster-whisper
"""

import argparse
import os
import platform
import sys

from config import (
    DOWNLOAD_DIR,
    OUTPUT_FORMAT,
    LANGUAGE,
    DELETE_AFTER_TRANSCRIPTION,
)
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


def transcribe_with_mlx(input_dir: str, output_format: str, language: str = None) -> list:
    """Transcribe using mlx-whisper (Apple Silicon)."""
    # Import the mlx-whisper module (hyphen in filename requires special handling)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "mlx_whisper_cli",
        os.path.join(os.path.dirname(__file__), "mlx-whisper.py")
    )
    mlx_whisper_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mlx_whisper_module)

    return mlx_whisper_module.transcribe_directory(
        input_dir=input_dir,
        output_format=output_format,
        language=language
    )


def transcribe_with_faster_whisper(input_dir: str, output_format: str, language: str = None) -> list:
    """Transcribe using faster-whisper (Windows/CPU)."""
    from faster_whisper import WhisperModel
    from tqdm import tqdm

    model = WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2")

    media_extensions = {
        ".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma",
        ".mp4", ".webm", ".mkv", ".avi", ".mov"
    }

    files = [
        f for f in os.listdir(input_dir)
        if os.path.splitext(f)[1].lower() in media_extensions
    ]

    if not files:
        print(f"No media files found in '{input_dir}'")
        return []

    print(f"Found {len(files)} media file(s) in '{input_dir}'")
    print("-" * 50)

    output_files = []

    for i, filename in enumerate(files, 1):
        input_file = os.path.join(input_dir, filename)
        base_name = os.path.splitext(input_file)[0]

        print(f"\n[{i}/{len(files)}] Processing: {filename}")
        print(f"Transcribing '{input_file}'...")

        try:
            transcribe_options = {}
            if language:
                transcribe_options["language"] = language

            segments, info = model.transcribe(input_file, **transcribe_options)

            transcript_text = []
            vtt_segments = []

            with tqdm(desc=f"Processing segments", unit="segment") as pbar:
                for seg_i, segment in enumerate(segments, 1):
                    text = segment.text.strip()
                    transcript_text.append(text)

                    if output_format in ("vtt", "srt"):
                        start = format_timestamp(segment.start)
                        end = format_timestamp(segment.end)
                        vtt_segments.append({
                            "index": seg_i,
                            "start": start,
                            "end": end,
                            "text": text
                        })

                    pbar.update(1)
                    pbar.set_postfix_str(f"Current: {text[:50]}...")

            # Save output
            if output_format == "txt":
                output_file = f"{base_name}.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(" ".join(transcript_text))

            elif output_format == "vtt":
                output_file = f"{base_name}.vtt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write("WEBVTT\n\n")
                    for seg in vtt_segments:
                        f.write(f"{seg['start']} --> {seg['end']}\n")
                        f.write(f"{seg['text']}\n\n")

            elif output_format == "srt":
                output_file = f"{base_name}.srt"
                with open(output_file, "w", encoding="utf-8") as f:
                    for seg in vtt_segments:
                        f.write(f"{seg['index']}\n")
                        f.write(f"{seg['start']} --> {seg['end']}\n")
                        f.write(f"{seg['text']}\n\n")

            else:
                # Default to txt
                output_file = f"{base_name}.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(" ".join(transcript_text))

            print(f"Transcription saved to: {output_file}")
            print(f"Language detected: {info.language} (probability: {info.language_probability:.2f})")
            output_files.append(output_file)

        except Exception as e:
            print(f"Error transcribing '{filename}': {e}", file=sys.stderr)

    print("-" * 50)
    print(f"Transcription complete. Processed: {len(output_files)}/{len(files)} files")

    return output_files


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm for VTT/SRT."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"


def cleanup_media_files(directory: str) -> int:
    """Delete media files after successful transcription."""
    media_extensions = {
        ".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma",
        ".mp4", ".webm", ".mkv", ".avi", ".mov"
    }

    deleted = 0
    for filename in os.listdir(directory):
        ext = os.path.splitext(filename)[1].lower()
        if ext in media_extensions:
            filepath = os.path.join(directory, filename)
            try:
                os.remove(filepath)
                print(f"Deleted: {filename}")
                deleted += 1
            except Exception as e:
                print(f"Failed to delete {filename}: {e}", file=sys.stderr)

    return deleted


def run_pipeline(download_only: bool = False, transcribe_only: bool = False):
    """
    Run the full pipeline: download -> transcribe -> cleanup.

    Args:
        download_only: Only download, skip transcription
        transcribe_only: Only transcribe existing files, skip download
    """
    print("=" * 60)
    print("YouTube Download & Transcription Pipeline")
    print("=" * 60)

    # Detect platform
    engine = detect_platform()
    engine_name = "mlx-whisper (Apple Silicon)" if engine == "mlx" else "faster-whisper"
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Transcription engine: {engine_name}")
    print(f"Output format: {OUTPUT_FORMAT}")
    print(f"Language: {LANGUAGE if LANGUAGE else 'auto-detect'}")
    print(f"Download directory: {os.path.abspath(DOWNLOAD_DIR)}")
    print("=" * 60)

    # Phase 1: Download
    if not transcribe_only:
        print("\n[Phase 1] Downloading videos...")
        print("-" * 50)
        downloaded = download_videos()
        if not downloaded and not transcribe_only:
            print("No videos downloaded.")
    else:
        print("\n[Phase 1] Skipped (--transcribe-only)")

    if download_only:
        print("\n[Phase 2] Skipped (--download-only)")
        print("\nPipeline complete (download only).")
        return

    # Phase 2: Transcribe
    print("\n[Phase 2] Transcribing files...")
    print("-" * 50)

    # Check if there are files to transcribe
    files = get_downloaded_files(DOWNLOAD_DIR)
    if not files:
        print(f"No media files found in '{DOWNLOAD_DIR}'")
        print("\nPipeline complete (no files to transcribe).")
        return

    if engine == "mlx":
        output_files = transcribe_with_mlx(DOWNLOAD_DIR, OUTPUT_FORMAT, LANGUAGE)
    else:
        output_files = transcribe_with_faster_whisper(DOWNLOAD_DIR, OUTPUT_FORMAT, LANGUAGE)

    # Phase 3: Cleanup
    if DELETE_AFTER_TRANSCRIPTION and output_files:
        print("\n[Phase 3] Cleaning up media files...")
        print("-" * 50)
        deleted = cleanup_media_files(DOWNLOAD_DIR)
        print(f"Deleted {deleted} media file(s)")
    else:
        print("\n[Phase 3] Cleanup skipped (DELETE_AFTER_TRANSCRIPTION=False)")

    # Summary
    print("\n" + "=" * 60)
    print("Pipeline complete!")
    print(f"Transcribed files: {len(output_files)}")
    if output_files:
        print(f"Output directory: {os.path.abspath(DOWNLOAD_DIR)}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube videos and transcribe them"
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

    args = parser.parse_args()

    if args.download_only and args.transcribe_only:
        print("Error: Cannot use both --download-only and --transcribe-only", file=sys.stderr)
        sys.exit(1)

    run_pipeline(
        download_only=args.download_only,
        transcribe_only=args.transcribe_only
    )


if __name__ == "__main__":
    main()
