import sys
import os
import hashlib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget, QTabBar, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, QSize, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QResizeEvent, QShowEvent, QIcon

from VideoPreviewButtons import VideoPreviewButtons
from VideoTabContent import VideoTabContent

class VideoPreview(QWidget):
    # actiuni: 'start', 'end', 'step', 'speed', 'toggle_play'
    timeline_action = Signal(str, float)

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
        self.main_timeline_tab = VideoTabContent(timeline_image_path, is_timeline=True)
        
        self.preview_tabs.addTab(self.main_timeline_tab, "Timeline")
        self.preview_tabs.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

        layout.addWidget(self.preview_tabs)
        layout.addWidget(self.buttons)

        self.preview_tabs.tabCloseRequested.connect(self._close_tab)
        self.preview_tabs.currentChanged.connect(self._on_tab_changed)
        self.buttons.play_pause_button.clicked.connect(self._toggle_play_active_tab)

        self.buttons.next_frame_button.clicked.connect(lambda: self._step_video(1))
        self.buttons.prev_frame_button.clicked.connect(lambda: self._step_video(-1))

        self.buttons.to_start_button.clicked.connect(self._on_go_to_start)
        self.buttons.to_end_button.clicked.connect(self._on_go_to_end)

        self.buttons.faster_button.clicked.connect(lambda: self._on_change_speed_directional("forward"))
        self.buttons.playback_button.clicked.connect(lambda: self._on_change_speed_directional("backward"))

        self._on_tab_changed(0)

    def _on_change_speed_directional(self, direction):
        if self.preview_tabs.currentIndex() == 0:
            val = 1.0 if direction == "forward" else -1.0
            self.timeline_action.emit('speed', val)
        else:
            current_widget = self.preview_tabs.currentWidget()
            if isinstance(current_widget, VideoTabContent) and current_widget.player:
                current_widget.change_speed_mode(direction)
                self._update_play_button_icon(current_widget.player.playbackState())
    
    def _on_go_to_start(self):
        if self.preview_tabs.currentIndex() == 0:
            self.timeline_action.emit('start', 0)
        else:
            current_widget = self.preview_tabs.currentWidget()
            if isinstance(current_widget, VideoTabContent) and current_widget.player:
                current_widget.go_to_start()

    def _on_go_to_end(self):
        if self.preview_tabs.currentIndex() == 0:
            self.timeline_action.emit('end', 0)
        else:
            current_widget = self.preview_tabs.currentWidget()
            if isinstance(current_widget, VideoTabContent) and current_widget.player:
                current_widget.go_to_end()

    def _step_video(self, direction):
        if self.preview_tabs.currentIndex() == 0:
            self.timeline_action.emit('step', float(direction))
        else:
            current_widget = self.preview_tabs.currentWidget()
            if isinstance(current_widget, VideoTabContent) and current_widget.player:
                current_widget.step_frame(direction)

    def add_media_tab(self, file_path):
        target_path = os.path.abspath(file_path)
        for i in range(1, self.preview_tabs.count()):
            widget = self.preview_tabs.widget(i)
            if isinstance(widget, VideoTabContent):
                if widget.file_path == target_path:
                    self.preview_tabs.setCurrentIndex(i)
                    return
        
        new_tab_content = VideoTabContent(file_path)
        tab_name = os.path.basename(file_path)
        new_index = self.preview_tabs.addTab(new_tab_content, tab_name)
        self.preview_tabs.setCurrentIndex(new_index)

    def _on_tab_changed(self, index):
        if self._current_connected_tab:
            try:
                self._current_connected_tab.player_state_changed.disconnect(self._update_play_button_icon)
            except:
                pass
            self._current_connected_tab = None

        current_widget = self.preview_tabs.widget(index)
        controls_enabled = False
        
        if isinstance(current_widget, VideoTabContent):
            if current_widget.player is not None or index == 0:
                controls_enabled = True
                
                if controls_enabled:
                    self._current_connected_tab = current_widget
                    current_widget.player_state_changed.connect(self._update_play_button_icon)
                    if index != 0 and current_widget.player:
                        self._update_play_button_icon(current_widget.player.playbackState())
        
        self.buttons.setEnabled(controls_enabled)
        opacity = 1.0 if controls_enabled else 0.3
        self.buttons.setWindowOpacity(opacity) 

    def _toggle_play_active_tab(self):
        if self.preview_tabs.currentIndex() == 0:
            self.timeline_action.emit('toggle_play', 0)
        else:
            current_widget = self.preview_tabs.currentWidget()
            if isinstance(current_widget, VideoTabContent) and current_widget.player:
                current_widget.toggle_play_safe()
            
    def _update_play_button_icon(self, state):
        play_btn = self.buttons.play_pause_button
        if state == QMediaPlayer.PlayingState:
            play_btn.setIcon(QIcon(play_btn.pause_icon_path))
        else:
            play_btn.setIcon(QIcon(play_btn.play_icon_path))

    def _close_tab(self, index):
        if index == 0: return
        widget = self.preview_tabs.widget(index)
        if isinstance(widget, VideoTabContent):
            widget.cleanup()
        self.preview_tabs.removeTab(index)

    def load_into_timeline_tab(self, file_path):
        old_widget = self.preview_tabs.widget(0)
        if isinstance(old_widget, VideoTabContent):
            old_widget.cleanup()
        
        self.preview_tabs.removeTab(0)
        new_content = VideoTabContent(file_path, is_timeline=True)
        self.preview_tabs.insertTab(0, new_content, "Timeline")
        self.preview_tabs.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)
        self.main_timeline_tab = new_content 
        self.preview_tabs.setCurrentIndex(0)
        return new_content

    def reset_timeline_to_black(self):
        old_widget = self.preview_tabs.widget(0)
        if isinstance(old_widget, VideoTabContent):
            old_widget.cleanup()
        self.preview_tabs.removeTab(0)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        timeline_image_path = os.path.join(base_dir, "icons", "black.jpg")
        new_content = VideoTabContent(timeline_image_path, is_timeline=True)
        self.preview_tabs.insertTab(0, new_content, "Timeline")
        self.preview_tabs.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)
        self.preview_tabs.setCurrentIndex(0)
        self.main_timeline_tab = new_content
        return new_content