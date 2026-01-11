from transformations.transformations_interface import Transformations
from PySide6.QtCore import QTimeLine

class ChangeFPS(Transformations):
    def __init__(self, fps: int = 30):
        self.fps = max(1, min(120, int(fps)))

    def applyTransformation(self, qTimeLine: QTimeLine) -> QTimeLine:
        filter_str = f"fps={self.fps}"
        return self._apply_ffmpeg(qTimeLine, filter_str, "video")