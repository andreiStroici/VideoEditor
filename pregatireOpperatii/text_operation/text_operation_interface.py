from abc import abstractmethod
from PySide6.QtCore import QTimeLine
from base import BaseProcessor

class TextOperation(BaseProcessor):
    @abstractmethod
    def applyText(self, videoClip: QTimeLine) -> QTimeLine:
        pass
