import sys
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QSlider, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from TimelineTrackWidget import TimelineTrackWidget

class TimelineAndTracks(QWidget):
    def __init__(self, SPACING, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING)
        layout.setContentsMargins(SPACING, SPACING, SPACING, SPACING)

        self.timeline_container = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_container)
        self.timeline_layout.setSpacing(SPACING)
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)

        # --- Top bar ---
        self.timeline_topbar = QHBoxLayout()
        self.timeline_topbar.setSpacing(SPACING)

        self.add_tracks_button = self._create_icon_btn("icons/plus.png")
        self.align_tracks_button = self._create_icon_btn("icons/magnet.png")
        self.cut_button = self._create_icon_btn("icons/cut.png")
        self.place_button = self._create_icon_btn("icons/place.png") 
        
        self.timeline_topbar.addWidget(self.add_tracks_button)
        self.timeline_topbar.addWidget(self.align_tracks_button)
        self.timeline_topbar.addWidget(self.cut_button)
        self.timeline_topbar.addWidget(self.place_button)
        
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(10000) 
        # Si sliderul poate avea focus border, il scoatem si pe el
        self.time_slider.setFocusPolicy(Qt.NoFocus)
        self.time_slider.setValue(0)
        
        self.timeline_topbar.addWidget(self.time_slider)
        self.timeline_layout.addLayout(self.timeline_topbar)

        # --- Scroll Area ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFocusPolicy(Qt.NoFocus) # Scoatem focus si de pe scroll area
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.track_widget = TimelineTrackWidget()
        self.scroll_area.setWidget(self.track_widget)
        
        self.timeline_layout.addWidget(self.scroll_area)

        layout.addWidget(self.timeline_container)

    def _create_icon_btn(self, icon_path):
        btn = QPushButton()
        btn.setIcon(QIcon(icon_path))
        btn.setIconSize(QSize(32,32))
        
        # --- FIX: Scoate conturul albastru de focus ---
        btn.setFocusPolicy(Qt.NoFocus)
        
        btn.setStyleSheet("""
            QPushButton { border: none; background: transparent; padding: 0; }
            QPushButton:hover { background: rgba(255,255,255,0.1); }
        """)
        return btn

    def ensure_cursor_visible(self, x_pos):
        viewport_width = self.scroll_area.viewport().width()
        current_scroll = self.scroll_area.horizontalScrollBar().value()
        margin = 100 

        right_boundary = current_scroll + viewport_width - margin
        if x_pos > right_boundary:
            target = x_pos - viewport_width + margin
            self.scroll_area.horizontalScrollBar().setValue(target)
        
        left_boundary = current_scroll + margin
        if x_pos < left_boundary:
            target = x_pos - margin
            if target < 0: target = 0
            self.scroll_area.horizontalScrollBar().setValue(target)