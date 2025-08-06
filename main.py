import argparse
from faster_whisper import WhisperModel
from tqdm import tqdm

def format_timestamp(seconds: float) -> str:
    # Format seconds to VTT timestamp (hh:mm:ss.mmm)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Transcribe audio files using faster-whisper')
    parser.add_argument('-i', '--input', required=True, help='Input audio file path')
    parser.add_argument('-o', '--output', required=True, help='Output text file path')
    parser.add_argument('--segmented', action='store_true', help='Save segmented output as VTT file')
    
    # Parse arguments
    args = parser.parse_args()
    
    input_file = args.input
    output_file = args.output
    segmented = args.segmented

    print(f"Transcribing {input_file}...")
    print(f"Output will be saved to {output_file}\n")
    
    # Load the model
    model = WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2")
    
    # Transcribe the audio file
    segments, info = model.transcribe(input_file)
    
    transcript_text = []
    vtt_segments = []
    print("Processing audio segments...")
    
    with tqdm(desc="Processing segments", unit="segment") as pbar:
        for i, segment in enumerate(segments, 1):
            text = segment.text.strip()
            transcript_text.append(text)
            if segmented:
                start = format_timestamp(segment.start)
                end = format_timestamp(segment.end)
                vtt_segments.append(f"{i}\n{start} --> {end}\n{text}\n\n")
            pbar.update(1)
            pbar.set_postfix_str(f"Current: {text[:50]}...")
    
    # Join all text segments with spaces
    full_transcript = " ".join(transcript_text)
    
    # Write to output file (plain text)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_transcript)
    
    # Optionally write segmented output as VTT
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

if __name__ == "__main__":
    main()