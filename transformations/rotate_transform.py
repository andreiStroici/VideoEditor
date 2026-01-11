import math
from transformations.transformations_interface import Transformations
from PySide6.QtCore import QTimeLine

class Rotate(Transformations):
    def __init__(self, angle: float = 0.0):
        self.angle = float(angle)

    def applyTransformation(self, qTimeLine: QTimeLine) -> QTimeLine:
        angle_rad = math.radians(self.angle)
        filter_str = f"rotate={angle_rad}:c=black:ow='trunc(hypot(iw,ih)/2)*2':oh=ow"
        return self._apply_ffmpeg(qTimeLine, filter_str, "video")