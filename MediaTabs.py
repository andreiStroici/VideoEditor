import sys
from PySide6.QtWidgets import (
    QWidget, QTabWidget, QListWidget, QVBoxLayout
    
)
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QIcon


class MediaTabs(QWidget):
    def __init__(self,SPACING,parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self) 
        layout.setContentsMargins(0, 0, 0, 0)
        self.media_tabs = QTabWidget()
        self.media_tabs.setContentsMargins(0, 0, 0, 0)

        self.media_tabs.addTab(QListWidget(), "Show All")
        self.media_tabs.addTab(QListWidget(), "Video")
        self.media_tabs.addTab(QListWidget(), "Audio")

        layout.addWidget(self.media_tabs)