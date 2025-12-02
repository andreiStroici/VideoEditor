from typing import Optional

from PyQt5.QtCore import QTimeLine

from editor.History import History


class VideoEditor:
    def __init__(self):
        self.history = History()
        self.video_clip: Optional[QTimeLine] = None

    def apply_filter(self, data: dict):
        operation_type = data["type"]
        match operation_type:
            case "blend videos":
                pass
            case "chorus":
                pass
            case "delay":
                pass
            case "echo":
                pass
            case "overlay":
                pass
            case "blur":
                pass
            case "edge detect":
                pass
            case "kernel filtering":
                pass
            case "noise reduction":
                pass
            case "tempo filter":
                pass
            case "volume filter":
                pass
            case "draw text":
                pass
            case "concat":
                pass
            case "cut":
                pass
            case "fade in/out":
                pass
            case "change fps":
                pass
            case "crop":
                pass
            case "padding":
                pass
            case "playback speed":
                pass
            case "rotate":
                pass
            case "scale":
                pass
            case "transpose":
                pass
            case _:
                pass
        pass

    def show_results(self):
        return self.video_clip

    def set_video(self, video_clip: QTimeLine):
        self.video_clip = video_clip
        self.history.clear_history()
