from transformations.transformations_interface import Transformations
from PySide6.QtCore import QTimeLine

class ScaleTransform(Transformations):
    def __init__(self, scale_x: float = 1.0, scale_y: float = 1.0):
        self.scale_x = max(0.1, min(10.0, float(scale_x)))
        self.scale_y = max(0.1, min(10.0, float(scale_y)))

    def applyTransformation(self, qTimeLine: QTimeLine) -> QTimeLine:
        width_expr = f"iw*{self.scale_x}"
        height_expr = f"ih*{self.scale_y}"

        filter_str = f"scale={width_expr}:{height_expr}"

        return self._apply_ffmpeg(qTimeLine, filter_str, "video")
