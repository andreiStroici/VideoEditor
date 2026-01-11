from transformations.transformations_interface import Transformations
from PySide6.QtCore import QTimeLine

class PlaybackSpeed(Transformations):
    def __init__(self, factor: float = 1.0):
        self.factor = max(0.5, min(4.0, float(factor)))

    def applyTransformation(self, qTimeLine: QTimeLine) -> QTimeLine:
        video_pts = 1.0 / self.factor
        video_filter = f"setpts={video_pts}*PTS"
        qTimeLine = self._apply_ffmpeg(qTimeLine, video_filter, "video")

        audio_parts = []
        remaining = self.factor
        while remaining > 2.0:
            audio_parts.append("atempo=2.0")
            remaining /= 2.0
        while remaining < 0.5:
            audio_parts.append("atempo=0.5")
            remaining /= 0.5
        if 0.5 <= remaining <= 2.0:
            audio_parts.append(f"atempo={remaining}")

        audio_filter = ",".join(audio_parts) if audio_parts else "atempo=1.0"
        qTimeLine = self._apply_ffmpeg(qTimeLine, audio_filter, "audio")

        return qTimeLine