import argparse
import os
from faster_whisper import WhisperModel
from tqdm import tqdm

def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"

def transcribe_file(input_file, output_file, model, segmented):
    print(f"Transcribing {input_file}...")
    print(f"Output will be saved to {output_file}\n")
    segments, info = model.transcribe(input_file)
    transcript_text = []
    vtt_segments = []
    with tqdm(desc=f"Processing segments ({os.path.basename(input_file)})", unit="segment") as pbar:
        for i, segment in enumerate(segments, 1):
            text = segment.text.strip()
            transcript_text.append(text)
            if segmented:
                start = format_timestamp(segment.start)
                end = format_timestamp(segment.end)
                vtt_segments.append(f"{i}\n{start} --> {end}\n{text}\n\n")
            pbar.update(1)
            pbar.set_postfix_str(f"Current: {text[:50]}...")
    full_transcript = " ".join(transcript_text)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_transcript)
    if segmented:
        vtt_file = output_file.rsplit('.', 1)[0] + ".vtt"
        with open(vtt_file, 'w', encoding='utf-8') as vtt:
            vtt.write("WEBVTT\n\n")
            vtt.writelines(vtt_segments)
        print(f"Segmented VTT output saved to: {vtt_file}")
    print(f"Transcription completed!")
    print(f"Text saved to: {output_file}")
    print(f"Language detected: {info.language}")
    print(f"Language probability: {info.language_probability:.2f}")

def main():
    parser = argparse.ArgumentParser(description='Transcribe audio files or all files in a directory using faster-whisper')
    parser.add_argument('-i', '--input', required=True, help='Input audio file path or directory')
    parser.add_argument('-o', '--output', help='Output text file path (used only for single file mode)')
    parser.add_argument('--segmented', action='store_true', help='Save segmented output as VTT file')
    args = parser.parse_args()
    input_path = args.input
    output_file = args.output
    segmented = args.segmented

    model = WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2")

    audio_exts = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac', '.wma', '.mp4', '.webm', '.mkv', '.avi', '.mov'}

    if os.path.isdir(input_path):
        files = [f for f in os.listdir(input_path) if os.path.splitext(f)[1].lower() in audio_exts]
        if not files:
            print("No audio files found in the specified directory.")
            return
        for filename in files:
            input_file = os.path.join(input_path, filename)
            output_txt = os.path.splitext(input_file)[0] + ".txt"
            transcribe_file(input_file, output_txt, model, segmented)
    elif os.path.isfile(input_path):
        if not output_file:
            output_file = os.path.splitext(input_path)[0] + ".txt"
        transcribe_file(input_path, output_file, model, segmented)
    else:
        print(f"Error: {input_path} is not a valid file or directory.")

if __name__ == "__main__":
    main()