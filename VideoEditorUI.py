import sys
import os
import hashlib
import subprocess 

from PySide6.QtWidgets import QGridLayout, QWidget, QApplication, QListWidget, QMessageBox
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
        self.setWindowTitle("Video Editor Professional")
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
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.tracks_cache_dir = os.path.join(base_dir, "filesFromTracks")
        os.makedirs(self.tracks_cache_dir, exist_ok=True)

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
                self._synchronize_preview_with_timeline(current_pos)

    def _on_user_scroll_start(self):
        self.auto_scroll_active = False

    def _create_track_file(self, source_path, duration_ms):
        import time
        import shutil
        base_name = os.path.basename(source_path)
        name, ext = os.path.splitext(base_name)
        unique_hash = hashlib.md5(f"{source_path}_{time.time()}".encode()).hexdigest()[:8]
        new_filename = f"{name}_clip_{unique_hash}{ext}"
        output_path = os.path.join(self.tracks_cache_dir, new_filename)
        
        duration_sec = duration_ms / 1000.0
        
        if ext.lower() in self.IMG_EXT:
            shutil.copy2(source_path, output_path)
            return output_path
        
        cmd = f'ffmpeg -y -i "{source_path}" -t {duration_sec} "{output_path}"'
        try:
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(output_path):
                return output_path
        except:
            pass
            
        shutil.copy2(source_path, output_path)
        return output_path

    def _on_place_clicked(self):
        current_list_widget = self.media_tabs.media_tabs.currentWidget()
        if not isinstance(current_list_widget, QListWidget): return

        selected_items = current_list_widget.selectedItems()
        if not selected_items: return
            
        item = selected_items[0]
        file_path = item.data(Qt.UserRole)
        
        if not file_path or not os.path.exists(file_path): return

        duration = 5000
        if file_path.endswith(tuple(self.IMG_EXT)):
            duration = 5000
        else:
            try:
                cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
                res = subprocess.check_output(cmd, shell=True)
                duration = float(res) * 1000
            except:
                duration = 5000 

        cached_path = self._create_track_file(file_path, duration)
        
        _, ext = os.path.splitext(cached_path)
        ext = ext.lower()
        color = "#3a6ea5" 
        if ext in self.VID_EXT: color = "#800080" 
        elif ext in self.AUD_EXT: color = "#FFA500" 
        
        track_widget = self.timeline_container.track_widget
        playhead_pos = self.timeline_container.time_slider.value()

        track_widget.trim_clip_at(playhead_pos)
        track_widget.add_clip_at_pos(cached_path, playhead_pos, int(duration), color)

        content_end = track_widget.get_content_end_ms()
        slider_max = max(content_end, playhead_pos + int(duration) + 1000)
        self.timeline_container.time_slider.setMaximum(slider_max)
        
        self._synchronize_preview_with_timeline(playhead_pos)


    def _synchronize_preview_with_timeline(self, global_ms):
        track_widget = self.timeline_container.track_widget
        clip_data = track_widget.get_clip_at_ms(global_ms)
        current_widget = self.video_preview.preview_tabs.widget(0)
        
        # State capture
        was_playing = False
        if self._connected_timeline_player:
            if self._connected_timeline_player.playbackState() == QMediaPlayer.PlayingState:
                was_playing = True

        if clip_data is None:
            if isinstance(current_widget, VideoTabContent):

                if "blackCat.jpg" in current_widget.file_path:
                    pass
                else:
                    if self._connected_timeline_player:
                        try:
                            self._connected_timeline_player.positionChanged.disconnect(self._update_timeline_ui)
                        except: pass
                        self._connected_timeline_player = None
                    new_tab = self.video_preview.reset_timeline_to_black()
                    self._sync_timeline_connection(0)
            return

        file_path = clip_data['path']
        clip_start = clip_data['start']
        clip_duration = clip_data['duration']
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

            new_tab = self.video_preview.load_into_timeline_tab(file_path)
            self._sync_timeline_connection(0)
            
            new_tab.set_explicit_duration(clip_duration)
            
            current_widget = self.video_preview.preview_tabs.widget(0)
            
            if new_tab.player:
                new_tab.player.setPosition(local_pos)
                if was_playing:
                    new_tab.player.play()
                else:
                    new_tab.player.pause() 
        
        if isinstance(current_widget, VideoTabContent) and current_widget.player:
            if abs(current_widget.player.position() - local_pos) > 100:
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
            slider.setEnabled(True)
            
            if isinstance(current_widget, VideoTabContent) and current_widget.player:
                self._connected_timeline_player = current_widget.player
                self._connected_timeline_player.positionChanged.connect(self._update_timeline_ui)
                self._connected_timeline_player.playbackStateChanged.connect(self._on_playback_state_changed)

            content_end = track_widget.get_content_end_ms()
            current_max = slider.maximum()
            slider.setMaximum(max(current_max, content_end, 100))
        else:
            slider.setEnabled(False)

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.auto_scroll_active = True

    def _update_timeline_ui(self, ms):
        slider = self.timeline_container.time_slider
        track_widget = self.timeline_container.track_widget
        
        current_widget = self.video_preview.preview_tabs.widget(0)
        if not isinstance(current_widget, VideoTabContent): return

        approx_global_pos = slider.value()
        active_clip = track_widget.get_clip_at_ms(approx_global_pos)
        
        content_end = track_widget.get_content_end_ms()
        if approx_global_pos >= content_end:
             if self._connected_timeline_player and self._connected_timeline_player.playbackState() == QMediaPlayer.PlayingState:
                  self._connected_timeline_player.pause()
                  slider.setValue(content_end)
                  track_widget.set_playhead(content_end)
                  return

        if active_clip and os.path.abspath(active_clip['path']) == os.path.abspath(current_widget.file_path):
             global_pos = active_clip['start'] + ms
             
             clip_end_time = active_clip['start'] + active_clip['duration']
             if global_pos >= clip_end_time:
                 next_pos = clip_end_time + 1 
                 slider.blockSignals(True)
                 slider.setValue(next_pos)
                 slider.blockSignals(False)
                 track_widget.set_playhead(next_pos)
                 self._synchronize_preview_with_timeline(next_pos)
             else:
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
        
        if val >= self.timeline_container.time_slider.maximum() - 1000:
             self.timeline_container.time_slider.setMaximum(val + 5000)

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
        
        if ms >= self.timeline_container.time_slider.maximum() - 1000:
             self.timeline_container.time_slider.setMaximum(ms + 5000)
             
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