from filters.filters_interface import Filters
from PySide6.QtCore import QTimeLine

class NoiseReduction(Filters):
    def __init__(self, strength: float = 1.0, method: str = "hqdn3d"):
        self.strength = max(0.0, min(10.0, float(strength)))
        self.method = method.lower()

        valid_methods = ["hqdn3d", "nlmeans", "atadenoise", "removegrain"]
        if self.method not in valid_methods:
            raise ValueError(f"Metoda invalida. Foloseste: {valid_methods}")

    def applyFilter(self, qTimeLine: QTimeLine) -> QTimeLine:
        if self.method == "hqdn3d":
            luma_spatial = self.strength * 4
            chroma_spatial = luma_spatial * 0.75
            luma_tmp = luma_spatial * 1.5
            chroma_tmp = chroma_spatial * 1.5
            filter_str = f"hqdn3d={luma_spatial}:{chroma_spatial}:{luma_tmp}:{chroma_tmp}"

        elif self.method == "nlmeans":
            filter_str = f"nlmeans=s={self.strength}:p=7:r=15"

        elif self.method == "atadenoise":
            filter_str = f"atadenoise=0a={self.strength}:0b={self.strength}:1a={self.strength}:1b={self.strength}:2a={self.strength}:2b={self.strength}"

        elif self.method == "removegrain":
            mode = min(24, max(1, int(self.strength * 2)))
            filter_str = f"removegrain=mode={mode}"

        return self._apply_ffmpeg(qTimeLine, filter_str, "video")
