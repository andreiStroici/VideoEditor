from filters.filters_interface import Filters
from PySide6.QtCore import QTimeLine

class Tempo(Filters):
    def __init__(self, factor: float = 1.0):
        self.factor = float(factor)

        if self.factor < 0.5 or self.factor > 2.0:
            raise ValueError("Tempo trebuie sa fie intre 0.5 si 2.0")

    def applyFilter(self, qTimeLine: QTimeLine) -> QTimeLine:
        filter_parts = []
        remaining_factor = self.factor

        while remaining_factor > 2.0:
            filter_parts.append("atempo=2.0")
            remaining_factor /= 2.0

        while remaining_factor < 0.5:
            filter_parts.append("atempo=0.5")
            remaining_factor /= 0.5

        if 0.5 <= remaining_factor <= 2.0:
            filter_parts.append(f"atempo={remaining_factor}")

        filter_str = ",".join(filter_parts)

        return self._apply_ffmpeg(qTimeLine, filter_str, "audio")
