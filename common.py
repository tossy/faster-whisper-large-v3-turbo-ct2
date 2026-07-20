#!/usr/bin/env python3
"""
Shared helpers for the download/transcription pipeline.

Used by pipeline.py, mlx_whisper_cli.py, main.py and downloader.py so that
media extensions, timestamp formatting and output writing live in one place.
"""

import json
import os

# Supported media extensions
MEDIA_EXTENSIONS = {
    ".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma",  # Audio
    ".mp4", ".webm", ".mkv", ".avi", ".mov",  # Video
}

OUTPUT_FORMATS = ("txt", "json", "srt", "vtt", "tsv")


def find_media_files(directory: str) -> list:
    """Return sorted list of media filenames (not full paths) in a directory."""
    return sorted(
        f for f in os.listdir(directory)
        if os.path.splitext(f)[1].lower() in MEDIA_EXTENSIONS
    )


def format_timestamp(seconds: float, sep: str = ".") -> str:
    """Format seconds as HH:MM:SS<sep>mmm. VTT uses '.', SRT uses ','."""
    total_millis = round(seconds * 1000)
    hours, rem = divmod(total_millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}{sep}{millis:03}"


def save_output(result: dict, output_path: str, format_type: str) -> None:
    """
    Save a transcription result in the specified format.

    Args:
        result: dict with "text" (full transcript) and "segments"
                (list of dicts with "start", "end", "text")
        output_path: file to write
        format_type: one of OUTPUT_FORMATS (unknown values fall back to txt)
    """
    if format_type == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    elif format_type == "srt":
        with open(output_path, "w", encoding="utf-8") as f:
            write_srt(result["segments"], f)

    elif format_type == "vtt":
        with open(output_path, "w", encoding="utf-8") as f:
            write_vtt(result["segments"], f)

    elif format_type == "tsv":
        with open(output_path, "w", encoding="utf-8") as f:
            write_tsv(result["segments"], f)

    else:  # txt and any unknown format
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["text"])


def write_srt(segments, file) -> None:
    """Write segments in SRT format (comma millisecond separator)."""
    for i, segment in enumerate(segments, 1):
        start = format_timestamp(segment["start"], sep=",")
        end = format_timestamp(segment["end"], sep=",")
        text = segment["text"].strip()

        file.write(f"{i}\n")
        file.write(f"{start} --> {end}\n")
        file.write(f"{text}\n\n")


def write_vtt(segments, file) -> None:
    """Write segments in WebVTT format (dot millisecond separator)."""
    file.write("WEBVTT\n\n")

    for segment in segments:
        start = format_timestamp(segment["start"], sep=".")
        end = format_timestamp(segment["end"], sep=".")
        text = segment["text"].strip()

        file.write(f"{start} --> {end}\n")
        file.write(f"{text}\n\n")


def write_tsv(segments, file) -> None:
    """Write segments in TSV format (millisecond timestamps)."""
    file.write("start\tend\ttext\n")

    for segment in segments:
        start = int(segment["start"] * 1000)
        end = int(segment["end"] * 1000)
        text = segment["text"].strip().replace("\t", " ")

        file.write(f"{start}\t{end}\t{text}\n")
