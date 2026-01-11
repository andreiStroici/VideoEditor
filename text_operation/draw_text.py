from typing import Tuple
from text_operation.text_operation_interface import TextOperation
from base import BaseProcessor
from PySide6.QtCore import QTimeLine

class DrawText(TextOperation):
    def __init__(self, text: str = "", position: Tuple[int, int] = (10, 10),
                 font: str = "Arial", size: int = 24, color: str = "white", opacity: float = 1.0):
        self.text = text.replace("'", "\\'").replace(":", "\\:")
        self.position = position
        self.font = font
        self.size = max(1, int(size))
        self.color = color
        self.opacity = max(0.0, min(1.0, float(opacity)))

    def applyText(self, videoClip: QTimeLine) -> QTimeLine:
        x, y = self.position

        filter_parts = [
            f"text='{self.text}'",
            f"x={x}",
            f"y={y}",
            f"fontsize={self.size}",
            f"fontcolor={self.color}@{self.opacity}"
        ]

        if self.font:
            filter_parts.append(f"font={self.font}")

        filter_str = "drawtext=" + ":".join(filter_parts)

        return self._apply_ffmpeg(videoClip, filter_str, "video")