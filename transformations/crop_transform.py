from transformations.transformations_interface import Transformations
from PySide6.QtCore import QTimeLine

class CropTransform(Transformations):
    def __init__(self, x: int = 0, y: int = 0, width: int = 0, height: int = 0):
        self.x = max(0, int(x))
        self.y = max(0, int(y))
        self.width = max(1, int(width))
        self.height = max(1, int(height))

    def applyTransformation(self, qTimeLine: QTimeLine) -> QTimeLine:
        filter_str = f"crop={self.width}:{self.height}:{self.x}:{self.y}"
        return self._apply_ffmpeg(qTimeLine, filter_str, "video")
