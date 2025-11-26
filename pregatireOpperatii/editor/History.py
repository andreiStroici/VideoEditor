from PyQt5.QtCore import QTimeLine


class History:
    _instance = None
    _locked = False

    def __init__(self):
        self._undo = []
        self._redo = []

    def __new__(cls, *args, **kwargs):
        if not cls._locked:
            cls._locked = True
            cls._instance = super().__new__(cls)
        return cls._instance

    def undo(self) -> QTimeLine:
        pass

    def redo(self) -> QTimeLine:
        q = self._redo.pop()
        self._undo.append(q)
        return q

    def clear_history(self):
        self._undo.clear()
        self._redo.clear()

    def save(self, q: QTimeLine):
        self._undo.append(q)
