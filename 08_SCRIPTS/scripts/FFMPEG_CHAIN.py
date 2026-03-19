
import subprocess
import json
from pathlib import Path

class FFMPEGChain:
    def __init__(self, ffmpeg_path="ffmpeg", ffprobe_path="ffprobe"):
        self.ffmpeg = ffmpeg_path
        self.ffprobe = ffprobe_path

    def burn_in_timestamp(self, input_video, output_video):
        cmd = [
            self.ffmpeg,
            "-i", input_video,
            "-vf", "drawtext=text='%{pts\:localtime\:%T}':x=8:y=8:fontsize=24:fontcolor=white",
            "-c:a", "copy",
            "-y", output_video
        ]
        return subprocess.run(cmd, capture_output=True, text=True)

    def generate_waveform(self, input_video, output_image):
        cmd = [
            self.ffmpeg,
            "-i", input_video,
            "-filter_complex", "showwavespic=s=640x120",
            "-frames:v", "1",
            "-y", output_image
        ]
        return subprocess.run(cmd, capture_output=True, text=True)

    def extract_metadata(self, input_video):
        cmd = [
            self.ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            input_video
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout) if result.returncode == 0 else result.stderr

    def generate_frame_hashes(self, input_video, output_hash_file):
        cmd = [
            self.ffmpeg,
            "-i", input_video,
            "-f", "framemd5",
            output_hash_file
        ]
        return subprocess.run(cmd, capture_output=True, text=True)

    def reencode_admissible(self, input_video, output_video):
        cmd = [
            self.ffmpeg,
            "-i", input_video,
            "-c:v", "libx264",
            "-preset", "veryslow",
            "-crf", "18",
            "-c:a", "pcm_s16le",
            "-map_metadata", "-1",
            "-movflags", "+faststart",
            "-y", output_video
        ]
        return subprocess.run(cmd, capture_output=True, text=True)
