from abc import abstractmethod
from PySide6.QtCore import QTimeLine
from base import BaseProcessor

class Filters(BaseProcessor):
    @abstractmethod
    def applyFilter(self, qTimeLine: QTimeLine) -> QTimeLine:
        pass

