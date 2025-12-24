import sys
import os
import hashlib
import subprocess
import time
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QSlider, QScrollArea
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon

from TimelineTrackWidget import TimelineTrackWidget

class TimelineAndTracks(QWidget):
    seek_request = Signal(int)
    timeline_changed = Signal()
    IMG_EXT = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
    VID_EXT = {'.mp4', '.mov', '.avi', '.mkv'}
    AUD_EXT = {'.mp3', '.wav', '.flac'}

    def __init__(self, SPACING, parent=None):
        super().__init__(parent)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.tracks_cache_dir = os.path.join(base_dir, "filesFromTracks")
        os.makedirs(self.tracks_cache_dir, exist_ok=True)
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING)
        layout.setContentsMargins(SPACING, SPACING, SPACING, SPACING)

        self.timeline_container = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_container)
        self.timeline_layout.setSpacing(SPACING)
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)

        # --- TOOLBAR ---
        self.timeline_topbar = QHBoxLayout()
        self.timeline_topbar.setSpacing(SPACING)

        self.add_tracks_button = self._create_icon_btn("icons/plus.png")
        self.align_tracks_button = self._create_icon_btn("icons/magnet.png")
        self.cut_button = self._create_icon_btn("icons/cut.png")
        self.place_button = self._create_icon_btn("icons/place.png") 
        self.delete_button = self._create_icon_btn("icons/trash.png") 

        self.timeline_topbar.addWidget(self.add_tracks_button)
        self.timeline_topbar.addWidget(self.align_tracks_button)
        self.timeline_topbar.addWidget(self.cut_button)
        self.timeline_topbar.addWidget(self.place_button)
        self.timeline_topbar.addWidget(self.delete_button)

        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(10000) 
        self.time_slider.setFocusPolicy(Qt.NoFocus)
        self.time_slider.setValue(0)
        
        self.timeline_topbar.addWidget(self.time_slider)
        self.timeline_layout.addLayout(self.timeline_topbar)

        # --- SCROLL AREA ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFocusPolicy(Qt.NoFocus) 
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.tracks_container_widget = QWidget()
        self.tracks_layout_vertical = QVBoxLayout(self.tracks_container_widget)
        self.tracks_layout_vertical.setContentsMargins(0, 0, 0, 0)
        self.tracks_layout_vertical.setSpacing(2)
        self.tracks_layout_vertical.addStretch() 

        self.scroll_area.setWidget(self.tracks_container_widget)
        self.timeline_layout.addWidget(self.scroll_area)

        layout.addWidget(self.timeline_container)

        self.track_widgets = []
        self.active_track = None

        self.add_new_track()

        self.add_tracks_button.clicked.connect(self.add_new_track)

    def _create_icon_btn(self, icon_path):
        btn = QPushButton()
        btn.setIcon(QIcon(icon_path))
        btn.setIconSize(QSize(32,32))
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setStyleSheet("""
            QPushButton { border: none; background: transparent; padding: 0; }
            QPushButton:hover { background: rgba(255,255,255,0.1); }
        """)
        return btn

    def add_new_track(self):
        new_track = TimelineTrackWidget()
        
        current_max_dur = self.get_content_end_all_tracks()
        if current_max_dur == 0:
            current_max_dur = 0

        
        current_pos = self.time_slider.value()
        new_track.playhead_pos_ms = current_pos
        
        new_track.set_duration_and_fill_gaps(current_max_dur)
        
        new_track.mouse_pressed_signal.connect(lambda: self.set_active_track(new_track))
        new_track.seek_request.connect(self.seek_request.emit)
        
        self.tracks_layout_vertical.insertWidget(self.tracks_layout_vertical.count() - 1, new_track)
        self.track_widgets.append(new_track)
        
        self.set_active_track(new_track)

    def set_active_track(self, track_widget):
        for t in self.track_widgets:
            t.is_active_track = False
            t.update()
        
        track_widget.is_active_track = True
        track_widget.update()
        self.active_track = track_widget

    def get_active_track(self):
        return self.active_track
    
    def get_content_end_all_tracks(self):
        max_end = 0
        for t in self.track_widgets:
            e = t.get_content_end_ms()
            if e > max_end: max_end = e
        return max_end

    def set_global_playhead(self, ms):
        for t in self.track_widgets:
            t.playhead_pos_ms = ms
            t.update()

    def set_global_duration(self, ms):
        for t in self.track_widgets:
            t.set_duration_and_fill_gaps(ms)
            
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


    def insert_media_at_playhead(self, file_path):
        if not os.path.exists(file_path): return -1
        
        active_track = self.get_active_track()
        if not active_track: return -1

        insert_duration_ms = self._get_file_duration(file_path)
        playhead_pos = active_track.playhead_pos_ms
        clip_under_cursor = active_track.get_clip_at_ms(playhead_pos)

        if not clip_under_cursor or clip_under_cursor.get('is_auto_gap', False):
            insert_end = playhead_pos + insert_duration_ms
            should_shift = False
            for c in active_track.clips:
                if not c.get('is_auto_gap', False):
                    if c['start'] >= playhead_pos and c['start'] < insert_end:
                        should_shift = True
                        break
            
            if should_shift:
                active_track.shift_clips_after(playhead_pos, insert_duration_ms)
            
            self._add_single_clip_to_track(active_track, file_path, playhead_pos, insert_duration_ms)
        else:
            original_path = clip_under_cursor['path']
            original_start = clip_under_cursor['start']
            original_dur = clip_under_cursor['duration']
            split_point_local_ms = playhead_pos - original_start
            if split_point_local_ms < 100: 
                 active_track.shift_clips_after(original_start, insert_duration_ms)
                 self._add_single_clip_to_track(active_track, file_path, original_start, insert_duration_ms)
                 return original_start
            
            if abs(original_dur - split_point_local_ms) < 100:
                 end_pos = original_start + original_dur
                 active_track.shift_clips_after(end_pos, insert_duration_ms)
                 self._add_single_clip_to_track(active_track, file_path, end_pos, insert_duration_ms)
                 return end_pos
            
            _, ext = os.path.splitext(original_path)
            is_image = ext.lower() in self.IMG_EXT
            part1_path = None
            part2_path = None
            
            if is_image:
                part1_path = original_path
                part2_path = original_path
            else:
                split_sec = split_point_local_ms / 1000.0
                total_sec = original_dur / 1000.0
                part1_path = self._split_video_file(original_path, 0, split_sec, "part1")
                part2_path = self._split_video_file(original_path, split_sec, total_sec, "part2")
                
                if not part1_path or not part2_path: return -1

            active_track.remove_clip_by_path_and_start(original_path, original_start)
            old_clip_end = original_start + original_dur
            active_track.shift_clips_after(old_clip_end, insert_duration_ms)
            
            self._add_single_clip_to_track(active_track, part1_path, original_start, split_point_local_ms)
            insert_pos = original_start + split_point_local_ms
            self._add_single_clip_to_track(active_track, file_path, insert_pos, insert_duration_ms)
            
            part2_pos = insert_pos + insert_duration_ms
            part2_dur = original_dur - split_point_local_ms
            self._add_single_clip_to_track(active_track, part2_path, part2_pos, part2_dur)

        return playhead_pos

    def _get_file_duration(self, path):
        if path.endswith(tuple(self.IMG_EXT)):
            return 5000
        try:
            cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path}"'
            res = subprocess.check_output(cmd, shell=True)
            return float(res) * 1000
        except: 
            return 5000

    def _split_video_file(self, source_path, start_sec, end_sec, part_suffix):
        base_name = os.path.basename(source_path)
        name, ext = os.path.splitext(base_name)
        unique = hashlib.md5(f"{source_path}_{start_sec}_{end_sec}_{time.time()}".encode()).hexdigest()[:6]
        
        out_name = f"{name}_{part_suffix}_{unique}{ext}"
        out_path = os.path.join(self.tracks_cache_dir, out_name)
        
        duration = end_sec - start_sec
        cmd = f'ffmpeg -y -ss {start_sec} -i "{source_path}" -t {duration} -c:v libx264 -preset ultrafast -c:a aac "{out_path}"'
        try:
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(out_path): return out_path
        except Exception as e:
            print(f"[Timeline] FFMPEG Error: {e}")
        return None

    def _add_single_clip_to_track(self, track_widget, path, start_ms, duration_ms):
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
        track_widget.insert_clip_physically(clip_data)