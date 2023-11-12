import whisper
import srt
from pydub import AudioSegment
from moviepy.editor import *
from datetime import timedelta
import sys
import torch

class VideoToSRT:
    def __init__(self, video_path, output_path, max_line_length=40):
        self.video_path = video_path
        self.output_path = output_path
        self.chunkNo = 0
        self.max_line_length = max_line_length

    def _split_audio(self, audio_path, max_duration):
        audio = AudioSegment.from_file(audio_path)
        duration = len(audio)
        chunks = []

        for i in range(0, duration, max_duration):
            chunk = audio[i:i+max_duration]
            chunks.append(chunk)
        
        return chunks

    def _transcribe_chunk(self, chunk):
        temp_chunk_path = f"./tmp/temp_chunk_{self.chunkNo}.mp3"
        with open(temp_chunk_path, "wb") as f:
            chunk.export(f, format="mp3")
        
        if torch.cuda.is_available() :
            model = whisper.load_model("large", device="cuda")
        else :
            model = whisper.load_model("large", device="cpu")
        transcript = model.transcribe(temp_chunk_path)
        
        self.chunkNo += 1
        
        return transcript

    def generate_srt(self):
        # create tmp directory
        if not os.path.exists("./tmp"):
            os.makedirs("./tmp")
        
        # Determine if the provided file is a video or an audio
        audio_extensions = ['.mp3', '.wav', '.flac']
        if any(self.video_path.lower().endswith(ext) for ext in audio_extensions):
            # If it's an audio, use it directly
            temp_audio_path = self.video_path
        else:
            # If it's a video, extract audio from it
            video = VideoFileClip(self.video_path)
            temp_audio_path = "./tmp/temp_audio.mp3"
            video.audio.write_audiofile(temp_audio_path)

        # Split audio if it's too long
        max_duration = 10 * 60 * 1000  # 10 minutes in milliseconds
        audio_chunks = self._split_audio(temp_audio_path, max_duration)

        subs = []
        idx = 0
        elapsed_time = 0  # ここで経過時間を追跡するための変数を初期化します

        for chunk in audio_chunks:
            transcript = self._transcribe_chunk(chunk)
            segments = transcript.get("segments", [])

            for data in segments:
                idx += 1
                start = data["start"] + elapsed_time  # 経過時間を加算
                end = data["end"] + elapsed_time      # 経過時間を加算
                text = self._format_text(data["text"])

                sub = srt.Subtitle(index=idx, 
                                   start=timedelta(seconds=start), 
                                   end=timedelta(seconds=end),
                                   content=text)
                # print number of subs
                subs.append(sub)
                print(f"number of subs : {len(subs)}")

            elapsed_time += len(chunk) / 1000  # このチャンクの長さを経過時間に加算 (pydubはミリ秒単位での長さを返しますので、秒単位に変換)

        # Save to srt
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(srt.compose(subs))

    def _format_text(self, text):
        lines = text.split("\n")
        # 「。」を削除
        lines = [line.replace("。", "") for line in lines]
        formatted_lines = [self._add_line(line) for line in lines]
        return "\n".join(formatted_lines)

    def _add_line(self, s):
        if len(s) <= self.max_line_length:
            return s
        # 文字列を指定された長さで分割
        return '\n'.join([s[i:i+self.max_line_length] for i in range(0, len(s), self.max_line_length)])

def print_usage():
    print("Usage:")
    print("python video2srt.py [VIDEO_FILE] [OUTPUT_FILE]")
    print("Example:")
    print("python video2srt.py sample_video.mp4 output.srt max_line_length")

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print_usage()
        sys.exit(1)

    video_path = sys.argv[1]
    output_path = sys.argv[2]
    max_line_length = int(sys.argv[3]) if len(sys.argv) == 4 else 40

    video_to_srt = VideoToSRT(video_path, output_path, max_line_length)
    video_to_srt.generate_srt()