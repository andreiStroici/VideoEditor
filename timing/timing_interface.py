from abc import ABC, abstractmethod
from PySide6.QtCore import QTimeLine
from base import BaseProcessor

class Timing(BaseProcessor):
    @abstractmethod
    def applyOperation(self, qTimeLine: QTimeLine) -> QTimeLine:
        pass