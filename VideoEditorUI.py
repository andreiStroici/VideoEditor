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
        self.timeline_container.delete_button.clicked.connect(self._on_delete_clicked)

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
    
    def _on_delete_clicked(self):
        if self._connected_timeline_player:
            if self._connected_timeline_player.playbackState() == QMediaPlayer.PlayingState:
                self._connected_timeline_player.pause()
        
        deleted = self.timeline_container.track_widget.delete_selected_clip()
        
        if deleted:
            track_widget = self.timeline_container.track_widget
            content_end = track_widget.get_content_end_ms()
            current_pos = self.timeline_container.time_slider.value()

            if content_end == 0:
                self.timeline_container.time_slider.setMaximum(100)
                self.timeline_container.time_slider.setValue(0)
                track_widget.set_playhead(0)
                self._synchronize_preview_with_timeline(0)
            else:
                self.timeline_container.time_slider.setMaximum(content_end)
                clip_under_cursor = track_widget.get_clip_at_ms(current_pos)
                
                if clip_under_cursor is None:
                    new_pos = track_widget.get_end_of_clip_before(current_pos)
                    self.timeline_container.time_slider.setValue(new_pos)
                    track_widget.set_playhead(new_pos)
                    self._synchronize_preview_with_timeline(new_pos)
                else:
                    self._synchronize_preview_with_timeline(current_pos)

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

        print(f"Placing (Replacing): {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        color = "#3a6ea5" 
        if ext in self.VID_EXT: color = "#800080" 
        elif ext in self.AUD_EXT: color = "#FFA500" 

        if self._connected_timeline_player:
            try:
                self._connected_timeline_player.stop() # Stop explicit
                self._connected_timeline_player.positionChanged.disconnect(self._update_timeline_ui)
                self._connected_timeline_player.playbackStateChanged.disconnect(self._on_playback_state_changed)
            except:
                pass
            self._connected_timeline_player = None
        self.timeline_container.track_widget.clear_tracks()
        self.timeline_container.time_slider.setValue(0)
        self.video_preview.reset_timeline_to_black()
        
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

            self.timeline_container.time_slider.setValue(0)
            track_widget.set_playhead(0)
            self._synchronize_preview_with_timeline(0)

    def _synchronize_preview_with_timeline(self, global_ms):
        track_widget = self.timeline_container.track_widget
        clip_data = track_widget.get_clip_at_ms(global_ms)
        current_widget = self.video_preview.preview_tabs.widget(0)

        if clip_data is None:
            is_black = False
            if isinstance(current_widget, VideoTabContent):
                if "black.jpg" in current_widget.file_path:
                    is_black = True
            
            if not is_black:
                if self._connected_timeline_player:
                    try:
                        self._connected_timeline_player.positionChanged.disconnect(self._update_timeline_ui)
                    except: pass
                    self._connected_timeline_player = None

                self.video_preview.reset_timeline_to_black()
                self._sync_timeline_connection(0)
            return

        file_path = clip_data['path']
        clip_start = clip_data['start']
        local_pos = global_ms - clip_start
        
        need_reload = True
        if isinstance(current_widget, VideoTabContent):
            if os.path.abspath(current_widget.file_path) == os.path.abspath(file_path):
                need_reload = False
        
        if need_reload:
            if self._connected_timeline_player:
                try:
                    self._connected_timeline_player.positionChanged.disconnect(self._update_timeline_ui)
                except: pass
                self._connected_timeline_player = None

            self.video_preview.load_into_timeline_tab(file_path)
            self._sync_timeline_connection(0)
            current_widget = self.video_preview.preview_tabs.widget(0)
        
        if isinstance(current_widget, VideoTabContent) and current_widget.player:
            if abs(current_widget.player.position() - local_pos) > 50:
                current_widget.player.setPosition(local_pos)

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
            has_content = track_widget.get_content_end_ms() > 0
            slider.setEnabled(has_content)
            
            if isinstance(current_widget, VideoTabContent) and current_widget.player:
                self._connected_timeline_player = current_widget.player
                self._connected_timeline_player.positionChanged.connect(self._update_timeline_ui)
                self._connected_timeline_player.playbackStateChanged.connect(self._on_playback_state_changed)

            content_end = track_widget.get_content_end_ms()
            slider_max = max(content_end, 100) 
            slider.setMaximum(slider_max)
        else:
            slider.setEnabled(False)

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.auto_scroll_active = True

    def _update_timeline_ui(self, ms):
        slider = self.timeline_container.time_slider
        track_widget = self.timeline_container.track_widget
        
        current_slider_val = slider.value()
        clip = track_widget.get_clip_at_ms(current_slider_val)
        
        if clip:
            global_pos = clip['start'] + ms
            slider.blockSignals(True)
            slider.setValue(global_pos)
            slider.blockSignals(False)
            track_widget.set_playhead(global_pos)
            
            if self.auto_scroll_active:
                cursor_x = track_widget.ms_to_px(global_pos)
                self.timeline_container.ensure_cursor_visible(cursor_x)

    def _on_slider_user_moved(self, val):
        if self.video_preview.preview_tabs.currentIndex() != 0: return 
        
        track_widget = self.timeline_container.track_widget
        content_end = track_widget.get_content_end_ms()
        
        if val > content_end: val = content_end
        if val < 0: val = 0 
        
        if val != self.timeline_container.time_slider.value():
            self.timeline_container.time_slider.setValue(val)

        track_widget.set_playhead(val)
        self.auto_scroll_active = True
        cursor_x = track_widget.ms_to_px(val)
        self.timeline_container.ensure_cursor_visible(cursor_x)
        self._synchronize_preview_with_timeline(val)

    def _on_timeline_seek(self, ms):
        if self.video_preview.preview_tabs.currentIndex() != 0: return 
        
        track_widget = self.timeline_container.track_widget
        content_end = track_widget.get_content_end_ms()
        
        if ms > content_end: ms = content_end
        if ms < 0: ms = 0 
        
        self.timeline_container.time_slider.setValue(ms)
        track_widget.set_playhead(ms)
        
        self.auto_scroll_active = True
        cursor_x = track_widget.ms_to_px(ms)
        self.timeline_container.ensure_cursor_visible(cursor_x)
        self._synchronize_preview_with_timeline(ms)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = VideoEditorUI()
    editor.show()
    sys.exit(app.exec())