import subprocess
import tempfile
import os
from composition.composition_interface import Composition
from PySide6.QtCore import QTimeLine

class BlendVideos(Composition):
    def __init__(self, otherClip: QTimeLine, alpha: float = 0.5, mode: str = "overlay"):
        self.otherClip = otherClip
        self.alpha = max(0.0, min(1.0, float(alpha)))
        self.mode = mode.lower()

        valid_modes = ["overlay", "multiply", "screen", "addition", "subtract", "difference"]
        if self.mode not in valid_modes:
            raise ValueError(f"Mod invalid. Foloseste: {valid_modes}")

    def applyComposition(self, videoClip: QTimeLine) -> QTimeLine:
        input_file1 = videoClip.property("input_file")
        input_file2 = self.otherClip.property("input_file")
        original_file = videoClip.property("original_file")

        if not input_file1 or not os.path.exists(input_file1):
            raise ValueError("Primul videoclip nu exista")
        if not input_file2 or not os.path.exists(input_file2):
            raise ValueError("Al doilea videoclip nu exista")

        if original_file is None:
            videoClip.setProperty("original_file", input_file1)
            original_file = input_file1

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(input_file1)[1]).name

        filter_complex = f"[0:v][1:v]blend=all_mode={self.mode}:all_opacity={self.alpha}[v]"

        cmd = [
            "ffmpeg",
            "-i", input_file1,
            "-i", input_file2,
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "0:a",
            "-c:a", "copy",
            "-shortest",
            "-y",
            output_file
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            if os.path.exists(output_file):
                os.unlink(output_file)
            raise RuntimeError(f"Eroare FFmpeg: {result.stderr}")

        if input_file1 != original_file and os.path.exists(input_file1):
            os.unlink(input_file1)

        videoClip.setProperty("input_file", output_file)
        return videoClip