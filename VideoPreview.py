import sys
import os
import hashlib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget, QTabBar, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QResizeEvent, QShowEvent, QIcon


from VideoPreviewButtons import VideoPreviewButtons

from VideoTabContent import VideoTabContent


class VideoPreview(QWidget):
    def __init__(self, SPACING, parent=None):
        super().__init__(parent)
       
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING)
        layout.setContentsMargins(SPACING, SPACING, SPACING, SPACING)

        self.buttons = VideoPreviewButtons(SPACING)
        self.preview_tabs = QTabWidget()
        self.preview_tabs.setTabsClosable(True)

        self._current_connected_tab = None
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        timeline_image_path = os.path.join(base_dir, "icons", "black.jpg")
        
        self.main_timeline_tab = VideoTabContent(timeline_image_path)
        
        self.preview_tabs.addTab(self.main_timeline_tab, "Timeline")
        self.preview_tabs.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

        layout.addWidget(self.preview_tabs)
        layout.addWidget(self.buttons)

        self.preview_tabs.tabCloseRequested.connect(self._close_tab)
        self.preview_tabs.currentChanged.connect(self._on_tab_changed)
        self.buttons.play_pause_button.clicked.connect(self._toggle_play_active_tab)

        self.buttons.next_frame_button.clicked.connect(lambda: self._step_video(1))
        self.buttons.prev_frame_button.clicked.connect(lambda: self._step_video(-1))

        self._on_tab_changed(0)


    def _step_video(self, direction):
        """Wrapper care apeleaza step_frame pe tab-ul activ."""
        current_widget = self.preview_tabs.currentWidget()
        
        # Verificam daca widgetul curent este de tip VideoTabContent si are player
        if isinstance(current_widget, VideoTabContent) and current_widget.player:
            current_widget.step_frame(direction)

    def add_media_tab(self, file_path):
        new_tab_content = VideoTabContent(file_path)
        tab_name = os.path.basename(file_path)
        new_index = self.preview_tabs.addTab(new_tab_content, tab_name)
        self.preview_tabs.setCurrentIndex(new_index)

    def _on_tab_changed(self, index):
        if self._current_connected_tab:
            try:
                self._current_connected_tab.player_state_changed.disconnect(self._update_play_button_icon)
            except:
                pass # Ignoram daca nu era conectat
            self._current_connected_tab = None

        current_widget = self.preview_tabs.widget(index)
        controls_enabled = False
        
        if isinstance(current_widget, VideoTabContent):
            if current_widget.player is not None:
                controls_enabled = True

                self._current_connected_tab = current_widget
                current_widget.player_state_changed.connect(self._update_play_button_icon)
                
                # 3. Fortam o actualizare vizuala imediata
                self._update_play_button_icon(current_widget.player.playbackState())
        
        self.buttons.setEnabled(controls_enabled)
        opacity = 1.0 if controls_enabled else 0.3
        self.buttons.setWindowOpacity(opacity) 


    def _update_play_button_icon(self, state):
        play_btn = self.buttons.play_pause_button
        if state == QMediaPlayer.PlayingState:
            play_btn.setIcon(QIcon(play_btn.pause_icon_path))
        else:
            play_btn.setIcon(QIcon(play_btn.play_icon_path))
    

    def _toggle_play_active_tab(self):
        current_widget = self.preview_tabs.currentWidget()
        if isinstance(current_widget, VideoTabContent) and current_widget.player:
            state = current_widget.player.playbackState()
            if state == QMediaPlayer.PlayingState:
                current_widget.player.pause()
            else:
                current_widget.player.play()

    def _close_tab(self, index):
        if index == 0: return

        widget = self.preview_tabs.widget(index)
        if isinstance(widget, VideoTabContent) and widget.player:
            widget.player.stop()
        
        self.preview_tabs.removeTab(index)