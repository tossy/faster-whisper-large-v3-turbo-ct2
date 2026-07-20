#!/usr/bin/env python3
"""
Transcribe audio/video files using mlx-whisper (optimized for Apple Silicon).
Supports single files and batch directory processing.
"""

import argparse
import sys
import os
import mlx_whisper

from common import MEDIA_EXTENSIONS, find_media_files, save_output

DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"


def transcribe_file(
    input_file: str,
    output_file: str = None,
    output_format: str = "txt",
    model: str = DEFAULT_MODEL,
    language: str = None,
    word_timestamps: bool = False
) -> str:
    """
    Transcribe a single audio/video file.

    Args:
        input_file: Path to input audio/video file
        output_file: Path to output file (optional, auto-generated if not provided)
        output_format: Output format - txt, json, srt, vtt, tsv
        model: Whisper model to use
        language: Force specific language (None for auto-detect)
        word_timestamps: Include word-level timestamps

    Returns:
        Path to the output file
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' not found.")

    # Determine output file path
    if not output_file:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.{output_format}"

    print(f"Transcribing '{input_file}' using model '{model}'...")

    # Build transcribe options
    transcribe_options = {
        "path_or_hf_repo": model,
        "word_timestamps": word_timestamps
    }

    if language:
        transcribe_options["language"] = language

    result = mlx_whisper.transcribe(input_file, **transcribe_options)

    # Save output based on format
    save_output(result, output_file, output_format)

    print(f"Transcription saved to: {output_file}")
    return output_file


def transcribe_directory(
    input_dir: str,
    output_format: str = "txt",
    model: str = DEFAULT_MODEL,
    language: str = None,
    word_timestamps: bool = False,
    force: bool = False
) -> list:
    """
    Transcribe all audio/video files in a directory.

    Args:
        input_dir: Path to directory containing media files
        output_format: Output format - txt, json, srt, vtt, tsv
        model: Whisper model to use
        language: Force specific language (None for auto-detect)
        word_timestamps: Include word-level timestamps
        force: Re-transcribe even if output file already exists

    Returns:
        Tuple of (list of output file paths, number of failed files)
    """
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"'{input_dir}' is not a valid directory.")

    # Find all media files
    files = find_media_files(input_dir)

    if not files:
        print(f"No media files found in '{input_dir}'")
        return [], 0

    print(f"Found {len(files)} media file(s) in '{input_dir}'")
    print("-" * 50)

    output_files = []
    skipped = 0
    failed = 0
    for i, filename in enumerate(files, 1):
        input_file = os.path.join(input_dir, filename)
        expected_output = f"{os.path.splitext(input_file)[0]}.{output_format}"

        if not force and os.path.exists(expected_output):
            print(f"\n[{i}/{len(files)}] Skipping (transcript exists): {filename}")
            skipped += 1
            continue

        print(f"\n[{i}/{len(files)}] Processing: {filename}")

        try:
            output_file = transcribe_file(
                input_file=input_file,
                output_format=output_format,
                model=model,
                language=language,
                word_timestamps=word_timestamps
            )
            output_files.append(output_file)
        except Exception as e:
            print(f"Error transcribing '{filename}': {e}", file=sys.stderr)
            failed += 1

    print("-" * 50)
    print(f"Transcription complete. Processed: {len(output_files)}/{len(files)} files"
          + (f" (skipped {skipped} existing)" if skipped else "")
          + (f" (failed {failed})" if failed else ""))

    return output_files, failed


def main():
    #   CLI Arguments:
    #   - -i/--input: Input audio file or directory (required)
    #   - -o/--output: Output file path (optional, for single file mode only)
    #   - -f/--format: Output format - txt, json, srt, vtt, tsv (default: txt)
    #   - --model: Whisper model to use (default: mlx-community/whisper-large-v3-turbo)
    #   - --word-timestamps: Include word-level timestamps
    #   - --language: Force specific language
    #
    #   Output Formats:
    #   - txt: Plain text transcription
    #   - json: Full JSON output with segments and metadata
    #   - srt: SubRip subtitle format
    #   - vtt: WebVTT subtitle format
    #   - tsv: Tab-separated values with timestamps
    #
    #   Usage examples:
    #   python mlx_whisper_cli.py -i audio.mp3 -o transcript.txt -f txt
    #   python mlx_whisper_cli.py -i ./videos/ -f vtt
    #   python mlx_whisper_cli.py -i audio.wav -f srt --model mlx-community/whisper-large-v3
    #   python mlx_whisper_cli.py -i speech.m4a -f json --word-timestamps --language en

    parser = argparse.ArgumentParser(
        description="Transcribe audio/video files using mlx-whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input audio/video file path or directory"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output file path (optional, for single file mode only)"
    )

    parser.add_argument(
        "-f", "--format",
        choices=["txt", "json", "srt", "vtt", "tsv"],
        default="txt",
        help="Output format (default: txt)"
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model to use (default: {DEFAULT_MODEL})"
    )

    parser.add_argument(
        "--word-timestamps",
        action="store_true",
        help="Include word-level timestamps"
    )

    parser.add_argument(
        "--language",
        help="Force specific language (e.g., 'en', 'ja')"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-transcribe even if output file already exists (directory mode)"
    )

    args = parser.parse_args()

    # Check if input exists
    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        if os.path.isdir(args.input):
            # Directory mode
            if args.output:
                print("Warning: --output is ignored in directory mode", file=sys.stderr)
            _, failed = transcribe_directory(
                input_dir=args.input,
                output_format=args.format,
                model=args.model,
                language=args.language,
                word_timestamps=args.word_timestamps,
                force=args.force
            )
            if failed:
                sys.exit(1)
        else:
            # Single file mode
            transcribe_file(
                input_file=args.input,
                output_file=args.output,
                output_format=args.format,
                model=args.model,
                language=args.language,
                word_timestamps=args.word_timestamps
            )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
