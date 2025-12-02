from transformations.transformations_interface import Transformations
from PySide6.QtCore import QTimeLine

class Transpose(Transformations):
    def __init__(self, mode: str = "clock"):
        self.mode = mode.lower()

        mode_map = {
            "clock": "1",
            "cclock": "2",
            "clock_flip": "3",
            "cclock_flip": "0",
            "hflip": "hflip",
            "vflip": "vflip"
        }

        if self.mode not in mode_map:
            raise ValueError(f"Mode invalid. Foloseste: {list(mode_map.keys())}")

        self.ffmpeg_mode = mode_map[self.mode]

    def applyTransformation(self, qTimeLine: QTimeLine) -> QTimeLine:
        if self.ffmpeg_mode in ["hflip", "vflip"]:
            filter_str = self.ffmpeg_mode
        else:
            filter_str = f"transpose={self.ffmpeg_mode}"

        return self._apply_ffmpeg(qTimeLine, filter_str, "video")
