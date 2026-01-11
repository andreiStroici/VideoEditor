from abc import abstractmethod
from PySide6.QtCore import QTimeLine
from base import BaseProcessor

class Transformations(BaseProcessor):
    @abstractmethod
    def applyTransformation(self, qTimeLine: QTimeLine) -> QTimeLine:
        pass