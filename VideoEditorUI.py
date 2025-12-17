import sys
import os
import hashlib
import subprocess 
import time

from PySide6.QtWidgets import QGridLayout, QWidget, QApplication, QListWidget, QMessageBox, QProgressDialog
from PySide6.QtCore import Qt, QSize, QTimer
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
        self.setWindowTitle("Video Editor Professional - Final")
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
            self._refresh_slider()
            self._synchronize_preview_with_timeline(self.timeline_container.track_widget.playhead_pos_ms)

    def _on_user_scroll_start(self):
        self.auto_scroll_active = False

    def _split_video_file(self, source_path, start_sec, end_sec, part_suffix):
        base_name = os.path.basename(source_path)
        name, ext = os.path.splitext(base_name)
        unique = hashlib.md5(f"{source_path}_{start_sec}_{end_sec}_{time.time()}".encode()).hexdigest()[:6]
        
        out_name = f"{name}_{part_suffix}_{unique}{ext}"
        out_path = os.path.join(self.tracks_cache_dir, out_name)
        
        duration = end_sec - start_sec
        cmd = f'ffmpeg -y -ss {start_sec} -i "{source_path}" -t {duration} -c:v libx264 -preset ultrafast -c:a copy "{out_path}"'
        
        try:
            print(f"[FFMPEG] Processing split: {out_name}...")
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(out_path):
                return out_path
        except Exception as e:
            print(f"[FFMPEG] Error: {e}")
            
        return None

    def _on_place_clicked(self):
        current_list_widget = self.media_tabs.media_tabs.currentWidget()
        if not isinstance(current_list_widget, QListWidget): return
        selected_items = current_list_widget.selectedItems()
        if not selected_items: return
        
        item = selected_items[0]
        insert_file_path = item.data(Qt.UserRole)
        if not insert_file_path or not os.path.exists(insert_file_path): return

        insert_duration_ms = 5000
        if insert_file_path.endswith(tuple(self.IMG_EXT)):
            insert_duration_ms = 5000
        else:
            try:
                cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{insert_file_path}"'
                res = subprocess.check_output(cmd, shell=True)
                insert_duration_ms = float(res) * 1000
            except:
                insert_duration_ms = 5000

        track_widget = self.timeline_container.track_widget
        playhead_pos = track_widget.playhead_pos_ms

        clip_under_cursor = track_widget.get_clip_at_ms(playhead_pos)
        if not clip_under_cursor or clip_under_cursor.get('is_auto_gap', False):
            track_widget.shift_clips_after(playhead_pos, insert_duration_ms)
            self._add_single_clip_to_track(insert_file_path, playhead_pos, insert_duration_ms)

        else:
            original_path = clip_under_cursor['path']
            original_start = clip_under_cursor['start']
            original_dur = clip_under_cursor['duration']
            split_point_local_ms = playhead_pos - original_start

            if split_point_local_ms < 100: 
                 track_widget.shift_clips_after(original_start, insert_duration_ms)
                 self._add_single_clip_to_track(insert_file_path, original_start, insert_duration_ms)
                 self._refresh_slider()
                 self.timeline_container.time_slider.setValue(original_start)
                 return
                 
            if abs(original_dur - split_point_local_ms) < 100:
                 end_pos = original_start + original_dur
                 track_widget.shift_clips_after(end_pos, insert_duration_ms)
                 self._add_single_clip_to_track(insert_file_path, end_pos, insert_duration_ms)
                 self._refresh_slider()
                 self.timeline_container.time_slider.setValue(end_pos)
                 return
            
            _, ext = os.path.splitext(original_path)
            is_image = ext.lower() in self.IMG_EXT
            
            part1_path = None
            part2_path = None
            
            if is_image:
                print("[EDITOR] Splitting IMAGE (Virtual Split)...")
                part1_path = original_path
                part2_path = original_path
            else:
                print("[EDITOR] Splitting VIDEO/AUDIO (Physical Split)...")
                split_sec = split_point_local_ms / 1000.0
                total_sec = original_dur / 1000.0
                
                part1_path = self._split_video_file(original_path, 0, split_sec, "part1")
                part2_path = self._split_video_file(original_path, split_sec, total_sec, "part2")
                
                if not part1_path or not part2_path:
                    print("[EDITOR] Error creating split files via FFmpeg.")
                    return

            track_widget.remove_clip_by_path_and_start(original_path, original_start)
            old_clip_end = original_start + original_dur
            track_widget.shift_clips_after(old_clip_end, insert_duration_ms)
            
            self._add_single_clip_to_track(part1_path, original_start, split_point_local_ms)
            
            insert_pos = original_start + split_point_local_ms
            self._add_single_clip_to_track(insert_file_path, insert_pos, insert_duration_ms)

            part2_pos = insert_pos + insert_duration_ms
            part2_dur = original_dur - split_point_local_ms
            self._add_single_clip_to_track(part2_path, part2_pos, part2_dur)

        self._refresh_slider()
        self.timeline_container.time_slider.setValue(playhead_pos)

        self._synchronize_preview_with_timeline(playhead_pos)

    def _add_single_clip_to_track(self, path, start_ms, duration_ms):
        _, ext = os.path.splitext(path)
        ext = ext.lower()
        color = "#3a6ea5"
        if ext in self.VID_EXT: color = "#800080"
        elif ext in self.AUD_EXT: color = "#FFA500"
        
        clip_data = {
            'path': path,
            'start': int(start_ms),
            'duration': int(duration_ms),
            'name': os.path.basename(path),
            'color': color,
            'is_auto_gap': False
        }
        self.timeline_container.track_widget.insert_clip_physically(clip_data)

    def _refresh_slider(self):
        track_widget = self.timeline_container.track_widget
        content_end = track_widget.get_content_end_ms()
            slider_max = content_end
        else:
            slider_max = 100 

        self.timeline_container.time_slider.setMaximum(slider_max)
        track_widget.set_duration(content_end + 120000)


    def _synchronize_preview_with_timeline(self, global_ms, force_play=False):
        global_ms = int(global_ms)
        
        track_widget = self.timeline_container.track_widget
        clip_data = track_widget.get_clip_at_ms(global_ms)
        current_widget = self.video_preview.preview_tabs.widget(0)
        
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
        clip_start = int(clip_data['start'])
        clip_duration = int(clip_data['duration'])

        local_pos = global_ms - clip_start
        actual_file_pos = int(max(0, local_pos))         
        
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
            
            if new_tab.player:
                new_tab.player.setPosition(actual_file_pos)

                if was_playing or force_play:
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(0, new_tab.player.play)
                else:
                    new_tab.player.pause() 
        
        if isinstance(current_widget, VideoTabContent) and current_widget.player:
            if abs(current_widget.player.position() - actual_file_pos) > 150:
                current_widget.player.setPosition(actual_file_pos)



    def _on_media_status_changed_ui(self, status):
        if status == QMediaPlayer.EndOfMedia:
            print("[UI] EndOfMedia received. Forcing transition...")
            
            slider = self.timeline_container.time_slider
            track_widget = self.timeline_container.track_widget
            
            current_pos = slider.value()
            active_clip = track_widget.get_clip_at_ms(current_pos)
            
            if active_clip:
                clip_end_time = int(active_clip['start'] + active_clip['duration'])
                next_pos = clip_end_time + 5
                
                slider.blockSignals(True)
                slider.setValue(next_pos)
                slider.blockSignals(False)
                
                track_widget.set_playhead(next_pos)
                self._synchronize_preview_with_timeline(next_pos, force_play=True)


    def _sync_timeline_connection(self, index):
        if self._connected_timeline_player:
            try:
                self._connected_timeline_player.positionChanged.disconnect(self._update_timeline_ui)
                self._connected_timeline_player.playbackStateChanged.disconnect(self._on_playback_state_changed)
                self._connected_timeline_player.mediaStatusChanged.disconnect(self._on_media_status_changed_ui)
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
                self._connected_timeline_player.mediaStatusChanged.connect(self._on_media_status_changed_ui)
            
            self._refresh_slider()
        else:
            slider.setEnabled(False)

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.auto_scroll_active = True

    def _update_timeline_ui(self, ms):
        ms = int(ms)
        if self.timeline_container.time_slider.isSliderDown():
            return

        slider = self.timeline_container.time_slider
        track_widget = self.timeline_container.track_widget
        
        current_widget = self.video_preview.preview_tabs.widget(0)
        if not isinstance(current_widget, VideoTabContent): return

        approx_global_pos = track_widget.playhead_pos_ms
        active_clip = track_widget.get_clip_at_ms(approx_global_pos)
        
        content_end = track_widget.get_content_end_ms()
        if approx_global_pos >= content_end:
             if self._connected_timeline_player and self._connected_timeline_player.playbackState() == QMediaPlayer.PlayingState:
                  self._connected_timeline_player.pause()
                  return
        
        if active_clip and os.path.abspath(active_clip['path']) == os.path.abspath(current_widget.file_path):
             global_pos = int(active_clip['start'] + ms)
             clip_end_time = int(active_clip['start'] + active_clip['duration'])
             if global_pos >= clip_end_time - 40: 
                 print(f"[TRANSITION] Clip finished at {global_pos}. Jump to next.")
                 next_pos = int(clip_end_time + 5)
                 
                 slider.blockSignals(True)
                 slider.setValue(next_pos)
                 slider.blockSignals(False)
                 
                 track_widget.set_playhead(next_pos)
                 self._synchronize_preview_with_timeline(next_pos, force_play=True)
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
        if val < 0: val = 0 
        
        track_widget.set_playhead(val)
        self.auto_scroll_active = True
        cursor_x = track_widget.ms_to_px(val)
        self.timeline_container.ensure_cursor_visible(cursor_x)
        self._synchronize_preview_with_timeline(val)

    def _on_timeline_seek(self, ms):
        if self.video_preview.preview_tabs.currentIndex() != 0: return 
        if ms < 0: ms = 0 
        self.timeline_container.time_slider.setValue(ms)
        self.timeline_container.track_widget.set_playhead(ms)
        
        self.auto_scroll_active = True
        cursor_x = self.timeline_container.track_widget.ms_to_px(ms)
        self.timeline_container.ensure_cursor_visible(cursor_x)
        self._synchronize_preview_with_timeline(ms)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = VideoEditorUI()
    editor.show()
    sys.exit(app.exec())