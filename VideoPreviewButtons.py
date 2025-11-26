import sys
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon


class VideoPreviewButtons(QWidget):
    def __init__(self, SPACING, parent=None):
        super().__init__(parent)

        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(SPACING)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.btn_style = """
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """

        
        self.to_start_button = self._create_btn("icons/toStart.png", 32)
        self.playback_button = self._create_btn("icons/playback.png", 32)
        self.prev_frame_button = self._create_btn("icons/prevFrame.png", 32)
        
        self.play_pause_button = self._create_btn("icons/play-button.png", 32)

        self.play_pause_button.play_icon_path = "icons/play-button.png"
        self.play_pause_button.pause_icon_path = "icons/pause.png"

        self.next_frame_button = self._create_btn("icons/nextFrame.png", 32)
        self.faster_button = self._create_btn("icons/speedUp.png", 32)
        self.to_end_button = self._create_btn("icons/toEnd.png", 32)


        self.layout.addStretch()
        self.layout.addSpacing(SPACING * 3)
        self.layout.addWidget(self.to_start_button)
        self.layout.addWidget(self.playback_button)
        self.layout.addWidget(self.prev_frame_button)
        self.layout.addWidget(self.play_pause_button)
        self.layout.addWidget(self.next_frame_button)
        self.layout.addWidget(self.faster_button)
        self.layout.addWidget(self.to_end_button)
        self.layout.addStretch()

    def _create_btn(self, icon_path, size):
        btn = QPushButton()
        btn.setIcon(QIcon(icon_path))
        btn.setIconSize(QSize(size, size))
        btn.setStyleSheet(self.btn_style)
        return btn