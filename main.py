import argparse
from faster_whisper import WhisperModel
from tqdm import tqdm

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Transcribe audio files using faster-whisper')
    parser.add_argument('-i', '--input', required=True, help='Input audio file path')
    parser.add_argument('-o', '--output', required=True, help='Output text file path')
    
    # Parse arguments
    args = parser.parse_args()
    
    input_file = args.input
    output_file = args.output
    
    print(f"Transcribing {input_file}...")
    print(f"Output will be saved to {output_file}\n")
    
    # Load the model
    model = WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2")
    
    # Transcribe the audio file
    segments, info = model.transcribe(input_file)
    
    # Collect all text segments with progress bar
    # Since segments is a generator, we'll process them one by one
    transcript_text = []
    print("Processing audio segments...")
    
    # Use tqdm without total count since we don't know ahead of time
    with tqdm(desc="Processing segments", unit="segment") as pbar:
        for segment in segments:
            transcript_text.append(segment.text.strip())
            pbar.update(1)
            # Optional: show current segment text (truncated)
            pbar.set_postfix_str(f"Current: {segment.text[:50]}...")
    
    # Join all text segments with spaces
    full_transcript = " ".join(transcript_text)
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_transcript)
    
    print(f"Transcription completed!")
    print(f"Text saved to: {output_file}")
    print(f"Language detected: {info.language}")
    print(f"Language probability: {info.language_probability:.2f}")

if __name__ == "__main__":
    main()