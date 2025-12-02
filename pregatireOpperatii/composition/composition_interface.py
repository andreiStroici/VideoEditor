from abc import ABC, abstractmethod
from PySide6.QtCore import QTimeLine

class Composition(ABC):
    @abstractmethod
    def applyComposition(self, videoClip: QTimeLine) -> QTimeLine:
        pass
