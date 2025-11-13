import sys
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout,QPushButton, QLabel, QVBoxLayout
)
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSlider


class TimelineAndTracks(QWidget):
    def __init__(self,SPACING,parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING)
        layout.setContentsMargins(SPACING, SPACING, SPACING, SPACING)


        self.timeline_container = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_container)
        self.timeline_layout.setSpacing(SPACING)
        self.timeline_layout.setContentsMargins(SPACING, SPACING, SPACING, SPACING)

        # Top bar inside timeline
        self.timeline_topbar = QHBoxLayout()
        self.timeline_topbar.setSpacing(SPACING)

        #timeline buttons
        #add tracks
        self.add_tracks_button=QPushButton()
        add_tracks_button_icon=QIcon("icons/plus.png")
        self.add_tracks_button.setIcon(add_tracks_button_icon)
        self.add_tracks_button.setIconSize(QSize(32,32))
        self.add_tracks_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        #align tracks
        self.align_tracks_button=QPushButton()
        align_tracks_button_icon=QIcon("icons/magnet.png")
        self.align_tracks_button.setIcon(align_tracks_button_icon)
        self.align_tracks_button.setIconSize(QSize(32,32))
        self.align_tracks_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        #cut
        self.cut_button=QPushButton()
        cut_button_icon=QIcon("icons/cut.png")
        self.cut_button.setIcon(cut_button_icon)
        self.cut_button.setIconSize(QSize(32,32))
        self.cut_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        #place
        self.place_button=QPushButton()
        place_button_icon=QIcon("icons/place.png")
        self.place_button.setIcon(place_button_icon)
        self.place_button.setIconSize(QSize(32,32))
        self.place_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)

       
        self.timeline_topbar.addWidget(self.add_tracks_button)
        self.timeline_topbar.addWidget(self.align_tracks_button)
        self.timeline_topbar.addWidget(self.cut_button)
        self.timeline_topbar.addWidget(self.place_button)
        


        # Timeline slider
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(600)  # example 10 min (600 sec)
        self.time_slider.setValue(0)

        self.timeline_topbar.addWidget(self.time_slider)

        # Add top bar to timeline layout
        self.timeline_layout.addLayout(self.timeline_topbar)

        # Timeline display area
        self.timeline_area = QLabel("Timeline Area")
        self.timeline_area.setAlignment(Qt.AlignCenter)
        self.timeline_area.setStyleSheet("background:#222; color:white; border:1px solid #444;")

        self.timeline_layout.addWidget(self.timeline_area)

        layout.addWidget(self.timeline_container)