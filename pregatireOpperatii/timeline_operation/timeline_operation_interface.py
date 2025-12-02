from abc import ABC, abstractmethod
from PySide6.QtCore import QTimeLine

class TimelineOperation(ABC):
    @abstractmethod
    def applyOperation(self, qTimeLine: QTimeLine) -> QTimeLine:
        pass
