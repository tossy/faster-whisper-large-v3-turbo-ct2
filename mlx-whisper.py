#!/usr/bin/env python3

import argparse
import sys
import os
import mlx_whisper
import json

def main():


#   CLI Arguments:
#   - -i/--input: Input audio file (required)
#   - -o/--output: Output file path (optional)
#   - -f/--format: Output format - txt, json, srt, vtt, tsv (default: txt)
#   - --model: Whisper model to use (default: mlx-community/whisper-tiny)
#   - --word-timestamps: Include word-level timestamps
#   - --language: Force specific language

#   Output Formats:
#   - txt: Plain text transcription
#   - json: Full JSON output with segments and metadata
#   - srt: SubRip subtitle format
#   - vtt: WebVTT subtitle format
#   - tsv: Tab-separated values with timestamps

#   Usage examples:
#   python mlx-whisper.py -i audio.mp3 -o transcript.txt -f txt
#   python mlx-whisper.py -i audio.wav -f srt --model mlx-community/whisper-large-v3
#   python mlx-whisper.py -i speech.m4a -f json --word-timestamps --language en

    parser = argparse.ArgumentParser(
        description="Transcribe audio files using mlx-whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input audio file path"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (optional, defaults to input filename with .txt extension)"
    )
    
    parser.add_argument(
        "-f", "--format",
        choices=["txt", "json", "srt", "vtt", "tsv"],
        default="txt",
        help="Output format (default: txt)"
    )
    
    parser.add_argument(
        "--model",
        default="mlx-community/whisper-large-v3-turbo",
        help="Model to use (default: mlx-community/whisper-large-v3-turbo)"
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
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Determine output file path
    if args.output:
        output_path = args.output
    else:
        base_name = os.path.splitext(args.input)[0]
        output_path = f"{base_name}.{args.format}"
    
    print(f"Transcribing '{args.input}' using model '{args.model}'...")
    
    try:
        # Transcribe the audio
        transcribe_options = {
            "path_or_hf_repo": args.model,
            "word_timestamps": args.word_timestamps
        }
        
        if args.language:
            transcribe_options["language"] = args.language
        
        result = mlx_whisper.transcribe(args.input, **transcribe_options)
        
        # Save output based on format
        save_output(result, output_path, args.format)
        
        print(f"Transcription saved to: {output_path}")
        
    except Exception as e:
        print(f"Error during transcription: {e}", file=sys.stderr)
        sys.exit(1)

def save_output(result, output_path, format_type):
    """Save transcription result in specified format"""
    
    if format_type == "txt":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
    
    elif format_type == "json":
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

def format_timestamp(seconds):
    """Format seconds as HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

def format_timestamp_vtt(seconds):
    """Format seconds as HH:MM:SS.mmm for WebVTT"""
    timestamp = format_timestamp(seconds)
    return timestamp.replace(",", ".")

def write_srt(segments, file):
    """Write segments in SRT format"""
    for i, segment in enumerate(segments, 1):
        start = format_timestamp(segment["start"])
        end = format_timestamp(segment["end"])
        text = segment["text"].strip()
        
        file.write(f"{i}\n")
        file.write(f"{start} --> {end}\n")
        file.write(f"{text}\n\n")

def write_vtt(segments, file):
    """Write segments in WebVTT format"""
    file.write("WEBVTT\n\n")
    
    for segment in segments:
        start = format_timestamp_vtt(segment["start"])
        end = format_timestamp_vtt(segment["end"])
        text = segment["text"].strip()
        
        file.write(f"{start} --> {end}\n")
        file.write(f"{text}\n\n")

def write_tsv(segments, file):
    """Write segments in TSV format"""
    file.write("start\tend\ttext\n")
    
    for segment in segments:
        start = int(segment["start"] * 1000)  # Convert to milliseconds
        end = int(segment["end"] * 1000)
        text = segment["text"].strip().replace("\t", " ")
        
        file.write(f"{start}\t{end}\t{text}\n")

if __name__ == "__main__":
    main()