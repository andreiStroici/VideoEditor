from abc import ABC, abstractmethod
from PySide6.QtCore import QTimeLine

class TextOperation(ABC):
    @abstractmethod
    def applyText(self, videoClip: QTimeLine) -> QTimeLine:
        pass
