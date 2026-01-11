import subprocess
import json
from timing.timing_interface import Timing
from PySide6.QtCore import QTimeLine

class FadeInOut(Timing):
    def __init__(self, duration: int = 1, type: str = "both"):
        self.duration = max(0, int(duration))
        self.type = type.lower()

        if self.type not in ["in", "out", "both"]:
            raise ValueError("Type trebuie sa fie 'in', 'out' sau 'both'")

    def _get_video_duration(self, input_file: str) -> float:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            input_file
        ]

        result  = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Eroare ffprobe: {result.stderr}")

        data = json.loads(result.stdout)
        return float(data["format"]["duration"])

    def applyOperation(self, qTimeLine: QTimeLine) -> QTimeLine:
        input_file = qTimeLine.property("input_file")

        if self.type == "in":
            filter_str = f"fade=t=in:st=0:d={self.duration}"

        elif self.type == "out":
            video_duration = self._get_video_duration(input_file)
            start_time = video_duration - self.duration
            filter_str = f"fade=t=out:st={start_time}:d={self.duration}"

        else:
            video_duration = self._get_video_duration(input_file)
            start_time = video_duration - self.duration
            filter_str = f"fade=t=in:st=0:d={self.duration},fade=t=out:st={start_time}:d={self.duration}"

        return self._apply_ffmpeg(qTimeLine, filter_str, "video")