from filters.filters_interface import Filters
from PySide6.QtCore import QTimeLine

class Volume(Filters):
    def __init__(self, gain_db: float = 0.0):
        self.gain_db = float(gain_db)

        if self.gain_db < -60 or self.gain_db > 60:
            raise ValueError("Gain trebuie sa fie intre -60 si 60 dB")

    def applyFilter(self, qTimeLine: QTimeLine) -> QTimeLine:
        filter_str = f"volume={self.gain_db}dB"
        return self._apply_ffmpeg(qTimeLine, filter_str, "audio")