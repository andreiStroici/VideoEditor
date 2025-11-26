import sys
import os

from PySide6.QtWidgets import QGridLayout, QWidget, QApplication, QListWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtMultimedia import QMediaPlayer

from Toolbar import Toolbar
from MediaTabs import MediaTabs
from VideoPreview import VideoPreview
from EnchancementsTabs import EnchancementsTabs
from TimelineAndTracks  import TimelineAndTracks
from VideoTabContent import VideoTabContent
from ImagePlayer import ImagePlayer

class VideoEditorUI(QWidget):
    
    IMG_EXT = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
    VID_EXT = {'.mp4', '.mov', '.avi', '.mkv'}
    AUD_EXT = {'.mp3', '.wav', '.flac'}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Editor")
        self.showMaximized()

        SPACING = 8

        main = QGridLayout(self)
        main.setSpacing(SPACING*2)
        main.setContentsMargins(SPACING, SPACING, SPACING, SPACING)

        self.toolbar = Toolbar(SPACING)
        self.media_tabs = MediaTabs(SPACING)
        self.video_preview = VideoPreview(SPACING) 
        self.enchancements_tabs = EnchancementsTabs(SPACING)
        self.timeline_container = TimelineAndTracks(SPACING)

        main.addWidget(self.toolbar, 0, 0, 1, 2)
        main.addWidget(self.media_tabs, 1, 0)
        main.addWidget(self.video_preview, 1, 1)
        main.addWidget(self.enchancements_tabs, 2, 0)
        main.addWidget(self.timeline_container, 2, 1)
        
        main.setRowStretch(1, 2)
        main.setRowStretch(2, 1)
        main.setColumnStretch(0, 2)
        main.setColumnStretch(1, 5)

        self._connected_timeline_player = None
        self.auto_scroll_active = True 

        self.toolbar.files_selected.connect(self.media_tabs.add_files)
        self.toolbar.folder_selected.connect(self.media_tabs.add_folder)
        self.media_tabs.file_double_clicked.connect(self.video_preview.add_media_tab)

        self.timeline_container.place_button.clicked.connect(self._on_place_clicked)
        self.video_preview.preview_tabs.currentChanged.connect(self._sync_timeline_connection)
        self.timeline_container.track_widget.seek_request.connect(self._on_timeline_seek)
        self.timeline_container.time_slider.sliderMoved.connect(self._on_slider_user_moved)

        h_scrollbar = self.timeline_container.scroll_area.horizontalScrollBar()
        h_scrollbar.sliderPressed.connect(self._on_user_scroll_start)
        h_scrollbar.sliderMoved.connect(self._on_user_scroll_start)

        self._sync_timeline_connection(0)

    def closeEvent(self, event):
        count = self.video_preview.preview_tabs.count()
        for i in range(count):
            widget = self.video_preview.preview_tabs.widget(i)
            if isinstance(widget, VideoTabContent):
                widget.cleanup()
        super().closeEvent(event)

    def _on_user_scroll_start(self):
        self.auto_scroll_active = False

    def _on_place_clicked(self):
        current_list_widget = self.media_tabs.media_tabs.currentWidget()
        if not isinstance(current_list_widget, QListWidget): return

        selected_items = current_list_widget.selectedItems()
        if not selected_items: return
            
        item = selected_items[0]
        file_path = item.data(Qt.UserRole)
        
        if not file_path or not os.path.exists(file_path): return

        print(f"Placing: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        color = "#3a6ea5" 
        if ext in self.VID_EXT: color = "#800080" 
        elif ext in self.AUD_EXT: color = "#FFA500" 

        new_tab_content = self.video_preview.load_into_timeline_tab(file_path)

        if new_tab_content.player:
            new_tab_content.player.durationChanged.connect(
                lambda d: self._add_visual_clip_and_update_slider(file_path, d, color)
            )

        self._sync_timeline_connection(0)

    def _add_visual_clip_and_update_slider(self, path, duration, color):
        if duration > 0:
            track_widget = self.timeline_container.track_widget
            track_widget.add_clip(path, duration, color)
            
            content_end = track_widget.get_content_end_ms()
            
            final_slider_max = content_end 
            self.timeline_container.time_slider.setMaximum(final_slider_max)
            
            try:
                self.sender().durationChanged.disconnect()
            except:
                pass

    def _sync_timeline_connection(self, index):
        if self._connected_timeline_player:
            try:
                self._connected_timeline_player.positionChanged.disconnect(self._update_timeline_ui)
                self._connected_timeline_player.playbackStateChanged.disconnect(self._on_playback_state_changed)
            except Exception:
                pass
            self._connected_timeline_player = None

        current_widget = self.video_preview.preview_tabs.widget(index)
        track_widget = self.timeline_container.track_widget
        slider = self.timeline_container.time_slider

        if index == 0:
            if isinstance(current_widget, VideoTabContent) and current_widget.player:
                self._connected_timeline_player = current_widget.player
                self._connected_timeline_player.positionChanged.connect(self._update_timeline_ui)
                self._connected_timeline_player.playbackStateChanged.connect(self._on_playback_state_changed)

                pos = current_widget.player.position()
                slider.setValue(pos)
                track_widget.set_playhead(pos)
            
            content_end = track_widget.get_content_end_ms()
            slider_max = max(content_end, 100) 
            slider.setMaximum(slider_max)

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.auto_scroll_active = True

    def _update_timeline_ui(self, ms):
        slider = self.timeline_container.time_slider
        slider.blockSignals(True)
        slider.setValue(ms)
        slider.blockSignals(False)

        track_widget = self.timeline_container.track_widget
        track_widget.set_playhead(ms)
        
        if self.auto_scroll_active:
            cursor_x = track_widget.ms_to_px(ms)
            self.timeline_container.ensure_cursor_visible(cursor_x)

    def _on_slider_user_moved(self, val):
        if self.video_preview.preview_tabs.currentIndex() != 0: return 
        current_widget = self.video_preview.preview_tabs.currentWidget()
        
        track_widget = self.timeline_container.track_widget
        content_end = track_widget.get_content_end_ms()
        
        if val > content_end: val = content_end
        if val < 0: val = 0 
        
        if val != self.timeline_container.time_slider.value():
            self.timeline_container.time_slider.setValue(val)

        if isinstance(current_widget, VideoTabContent) and current_widget.player:
            current_widget.player.setPosition(val)
            
        track_widget.set_playhead(val)

        self.auto_scroll_active = True
        cursor_x = track_widget.ms_to_px(val)
        self.timeline_container.ensure_cursor_visible(cursor_x)

    def _on_timeline_seek(self, ms):
        if self.video_preview.preview_tabs.currentIndex() != 0: return 
        current_widget = self.video_preview.preview_tabs.currentWidget()
        
        track_widget = self.timeline_container.track_widget
        content_end = track_widget.get_content_end_ms()
        
        if ms > content_end: ms = content_end
        if ms < 0: ms = 0 
        
        if isinstance(current_widget, VideoTabContent) and current_widget.player:
             current_widget.player.setPosition(ms)
             
        self.timeline_container.time_slider.setValue(ms)
        self.auto_scroll_active = True
        cursor_x = track_widget.ms_to_px(ms)
        self.timeline_container.ensure_cursor_visible(cursor_x)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = VideoEditorUI()
    editor.show()
    sys.exit(app.exec())