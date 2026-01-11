from filters.filters_interface import Filters
from PySide6.QtCore import QTimeLine

class EdgeDetect(Filters):
    def __init__(self, method: str = "sobel", threshold: float = 0.1):
        self.method = method.lower()
        self.threshold = max(0.0, min(1.0, float(threshold)))

        valid_methods = ["sobel", "roberts", "prewitt", "canny"]
        if self.method not in valid_methods:
            raise ValueError(f"Metoda invalida. Foloseste: {valid_methods}")

    def applyFilter(self, qTimeLine: QTimeLine) -> QTimeLine:
        if self.method == "sobel":
            filter_str = f"edgedetect=mode=colormix:high={self.threshold}"
        elif self.method == "canny":
            low = self.threshold * 0.5
            filter_str = f"edgedetect=mode=canny:low={low}:high={self.threshold}"
        elif self.method == "roberts":
            filter_str = f"edgedetect=mode=colormix:high={self.threshold},convolution='0 1 0 -1 0 0 0 0 0:0 0 1 0 -1 0 0 0 0:0 0 0 0 0 0 0 0 0:0 0 0 0 0 0 0 0 0'"
        else:
            filter_str = f"edgedetect=mode=colormix:high={self.threshold}"

        return self._apply_ffmpeg(qTimeLine, filter_str, "video")