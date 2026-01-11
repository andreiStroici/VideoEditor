from composition.composition_interface import Composition
from base import BaseProcessor
from PySide6.QtCore import QTimeLine
import subprocess
import tempfile
import os

class Delay(Composition, BaseProcessor):
    def __init__(self, delay_ms: int = 500, mix: float = 0.5):
        self.delay_ms = max(0, int(delay_ms))
        self.mix = max(0.0, min(1.0, float(mix)))

    def applyComposition(self, videoClip: QTimeLine) -> QTimeLine:
        input_file = videoClip.property("input_file")
        original_file = videoClip.property("original_file")

        if not input_file or not os.path.exists(input_file):
            raise ValueError("Fisier inexistent")

        if original_file is None:
            videoClip.setProperty("original_file", input_file)
            original_file = input_file

        in_gain = 1.0 - self.mix
        out_gain = self.mix
        delays = str(self.delay_ms)
        decays = "1.0"
        
        audio_filter = f"aecho=in_gain={in_gain}:out_gain={out_gain}:delays={delays}:decays={decays}"
        filter_complex = f"[0:a]{audio_filter}[aout]"

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name

        cmd = [
            "ffmpeg", "-y",
            "-i", input_file,
            "-filter_complex", filter_complex,
            "-map", "0:v",     
            "-map", "[aout]",   
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-shortest",       
            output_file
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            if os.path.exists(output_file): os.unlink(output_file)
            raise RuntimeError(f"Eroare FFmpeg Delay: {result.stderr}")

        if input_file != original_file and os.path.exists(input_file):
            os.unlink(input_file)

        videoClip.setProperty("input_file", output_file)
        return videoClip