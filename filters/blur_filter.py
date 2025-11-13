from filters.filters_interface import Filters
from PySide6.QtCore import QTimeLine

class BlurFilter(Filters):
    def __init__(self, radius: int = 10):
        self.radius = max(1, int(radius))

    def applyFilter(self, qTimeLine: QTimeLine) -> QTimeLine:
        filter_str = f"boxblur={self.radius}:{self.radius}"
        return self._apply_ffmpeg(qTimeLine, filter_str, "video")