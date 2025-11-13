import sys
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout,
    QPushButton, QLabel, QVBoxLayout
    
)
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QIcon


class VideoPreview(QWidget):
    def __init__(self,SPACING,parent=None):
        super().__init__(parent)
       
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING)
        layout.setContentsMargins(SPACING, SPACING, SPACING, SPACING)

        self.video_preview = QLabel("Video Preview (16:9)")
        self.video_preview.setAlignment(Qt.AlignCenter)
        self.video_preview.setStyleSheet("background:#333; color:white; border:1px solid #555;")

        self.video_controls = QHBoxLayout()
        self.video_controls.setSpacing(SPACING)

        # Video COntrol buttons
        self.export_project_button=QPushButton()
        export_project_icon=QIcon("icons/export_project.png")
        self.export_project_button.setIcon(export_project_icon)
        self.export_project_button.setIconSize(QSize(32,32))
        self.export_project_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)

        # To Start Button
        self.to_start_button=QPushButton()
        to_start_button_icon=QIcon("icons/toStart.png")
        self.to_start_button.setIcon(to_start_button_icon)
        self.to_start_button.setIconSize(QSize(32,32))
        self.to_start_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        # PlayBack Button
        self.playback_button=QPushButton()
        playback_button_icon=QIcon("icons/playback.png")
        self.playback_button.setIcon(playback_button_icon)
        self.playback_button.setIconSize(QSize(32,32))
        self.playback_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        # Preview Frame Button
        self.prev_frame_button=QPushButton()
        prev_frame_button_icon=QIcon("icons/prevFrame.png")
        self.prev_frame_button.setIcon(prev_frame_button_icon)
        self.prev_frame_button.setIconSize(QSize(32,32))
        self.prev_frame_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        # PLay/Pause Button
        self.play_pause_button=QPushButton()
        play_pause_button_icon=QIcon("icons/play-button.png")
        self.play_pause_button.setIcon(play_pause_button_icon)
        self.play_pause_button.setIconSize(QSize(32,32))
        self.play_pause_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        # NextFrame Button
        self.next_frame_button=QPushButton()
        next_frame_button_icon=QIcon("icons/nextFrame.png")
        self.next_frame_button.setIcon(next_frame_button_icon)
        self.next_frame_button.setIconSize(QSize(32,32))
        self.next_frame_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        # Faster Button
        self.faster_button=QPushButton()
        faster_button_icon=QIcon("icons/speedUp.png")
        self.faster_button.setIcon(faster_button_icon)
        self.faster_button.setIconSize(QSize(32,32))
        self.faster_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        # ToEnd Button
        self.to_end_button=QPushButton()
        to_end_button_icon=QIcon("icons/toEnd.png")
        self.to_end_button.setIcon(to_end_button_icon)
        self.to_end_button.setIconSize(QSize(32,32))
        self.to_end_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)


        self.video_controls.addStretch()
        self.video_controls.addSpacing(SPACING * 3)
        self.video_controls.addWidget(self.to_start_button)
        self.video_controls.addWidget(self.playback_button)
        self.video_controls.addWidget(self.prev_frame_button)
        self.video_controls.addWidget(self.play_pause_button)
        self.video_controls.addWidget(self.next_frame_button)
        self.video_controls.addWidget(self.faster_button)
        self.video_controls.addWidget(self.to_end_button)

        self.video_controls.addStretch()
        layout.addWidget(self.video_preview, stretch=5)
        layout.addLayout(self.video_controls, stretch=1)