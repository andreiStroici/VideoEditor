import sys
from PySide6.QtWidgets import (
    QWidget, QTabWidget, QListWidget, QVBoxLayout
    
)
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QIcon


class EnchancementsTabs(QWidget):
    def __init__(self,SPACING,parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.enhanced_tab = QTabWidget()
        self.enhanced_tab.setContentsMargins(0, 0, 0, 0)
        self.enhanced_tab.addTab(QListWidget(), "Filters")
        self.enhanced_tab.addTab(QListWidget(), "Transitions")
        self.enhanced_tab.addTab(QListWidget(), "Effects")

        layout.addWidget(self.enhanced_tab) 