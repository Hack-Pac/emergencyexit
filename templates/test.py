import os
from pydub import AudioSegment

def convert_mp3_to_wav(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".mp3"):
            mp3_path = os.path.join(directory, filename)
            wav_path = os.path.join(directory, os.path.splitext(filename)[0] + ".wav")
            audio = AudioSegment.from_mp3(mp3_path)
            audio.export(wav_path, format="wav")
            print(f"Converted {mp3_path} to {wav_path}")

if __name__ == "__main__":
    directory = input("Enter the directory containing .mp3 files: ")
    convert_mp3_to_wav(directory)