import os
from PySide6.QtWidgets import QWidget, QTabWidget, QListWidget, QVBoxLayout, QListWidgetItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QPixmap


class ClickableListWidget(QListWidget):
    def mousePressEvent(self, event):
        if not self.itemAt(event.pos()):
            self.clearSelection()
            self.clearFocus()
        super().mousePressEvent(event)