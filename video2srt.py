import whisper
import srt
from pydub import AudioSegment
from moviepy.editor import *
from datetime import timedelta
import sys

class VideoToSRT:
    def __init__(self, video_path, output_path):
        self.video_path = video_path
        self.output_path = output_path

    def _split_audio(self, audio_path, max_duration):
        audio = AudioSegment.from_file(audio_path)
        duration = len(audio)
        chunks = []

        for i in range(0, duration, max_duration):
            chunk = audio[i:i+max_duration]
            chunks.append(chunk)
        
        return chunks

    def _transcribe_chunk(self, chunk):
        with open("temp_chunk.mp3", "wb") as f:
            chunk.export(f, format="mp3")
        
        model = whisper.load_model("medium")
        transcript = model.transcribe("temp_chunk.mp3")
        
        return transcript

    def generate_srt(self):
        # Extract audio from the video
        video = VideoFileClip(self.video_path)
        video.audio.write_audiofile("temp_audio.mp3")

        # Split audio if it's too long
        max_duration = 10 * 60 * 1000  # 10 minutes in milliseconds
        audio_chunks = self._split_audio("temp_audio.mp3", max_duration)

        subs = []
        idx = 0

        for chunk in audio_chunks:
            transcript = self._transcribe_chunk(chunk)
            segments = transcript.get("segments", [])

            for data in segments:
                idx += 1
                start = data["start"]
                end = data["end"]
                text = self._format_text(data["text"])

                sub = srt.Subtitle(index=idx, 
                                   start=timedelta(seconds=start), 
                                   end=timedelta(seconds=end),
                                   content=text)
                
                subs.append(sub)

        # Save to srt
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(srt.compose(subs))

    def _format_text(self, text):
        lines = text.split("\n")
        formatted_lines = [self._add_line(line) for line in lines]
        return "\n".join(formatted_lines)

    def _add_line(self, s):
        new_s = s
        s_count = len(s)
        s_max_count = 15
        if s_count >= s_max_count:
            if (s_count - s_max_count) >= 3:
                new_s = s[:s_max_count] + "\n" + s[s_max_count:]
        return new_s

def print_usage():
    print("Usage:")
    print("python video2srt.py [VIDEO_FILE] [OUTPUT_FILE]")
    print("Example:")
    print("python video2srt.py sample_video.mp4 output.srt")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print_usage()
        sys.exit(1)

    video_path = sys.argv[1]
    output_path = sys.argv[2]
    video_to_srt = VideoToSRT(video_path, output_path)
    video_to_srt.generate_srt()