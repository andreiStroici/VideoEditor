from transformations.transformations_interface import Transformations
from PySide6.QtCore import QTimeLine

class PaddingTransform(Transformations):
    def __init__(self, top: int = 0, bottom: int = 0, left: int = 0, right: int = 0, color: str = "black"):
        self.top = max(0, int(top))
        self.bottom = max(0, int(bottom))
        self.left = max(0, int(left))
        self.right = max(0, int(right))
        self.color = color

    def applyTransformation(self, qTimeLine: QTimeLine) -> QTimeLine:
        width_expr = f"iw+{self.left}+{self.right}"
        height_expr = f"ih+{self.top}+{self.bottom}"
        x_expr = str(self.left)
        y_expr = str(self.top)

        filter_str = f"pad={width_expr}:{height_expr}:{x_expr}:{y_expr}:{self.color}"

        return self._apply_ffmpeg(qTimeLine, filter_str, "video")