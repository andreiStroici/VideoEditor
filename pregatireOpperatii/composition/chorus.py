from composition.composition_interface import Composition
from base import BaseProcessor
from PySide6.QtCore import QTimeLine

class Chorus(Composition, BaseProcessor):
    def __init__(self, delay_ms: int = 40, depth: float = 0.3, mix: float = 0.5):
        self.delay_ms = max(20, min(100, int(delay_ms)))
        self.depth = max(0.0, min(1.0, float(depth)))
        self.mix = max(0.0, min(1.0, float(mix)))

    def applyComposition(self, videoClip: QTimeLine) -> QTimeLine:
        in_gain = 0.4
        out_gain = 0.4
        delays = f"{self.delay_ms}"
        decays = "0.5"
        speeds = "0.25"
        depths = f"{self.depth}"

        filter_str = f"chorus=in_gain={in_gain}:out_gain={out_gain}:delays={delays}:decays={decays}:speeds={speeds}:depths={depths}"

        return self._apply_ffmpeg(videoClip, filter_str, "audio")
