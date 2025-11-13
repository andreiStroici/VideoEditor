from composition.composition_interface import Composition
from base import BaseProcessor
from PySide6.QtCore import QTimeLine

class Delay(Composition, BaseProcessor):
    def __init__(self, delay_ms: int = 500, mix: float = 0.5):
        self.delay_ms = max(0, int(delay_ms))
        self.mix = max(0.0, min(1.0, float(mix)))

    def applyComposition(self, videoClip: QTimeLine) -> QTimeLine:
        in_gain = 1.0 - self.mix
        out_gain = self.mix
        delays = str(self.delay_ms)
        decays = "1.0"

        filter_str = f"aecho=in_gain={in_gain}:out_gain={out_gain}:delays={delays}:decays={decays}"

        return self._apply_ffmpeg(videoClip, filter_str, "audio")
