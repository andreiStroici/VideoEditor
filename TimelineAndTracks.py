import sys
import os
import hashlib
import subprocess
import time
import shutil
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QSlider, QScrollArea
)
from PySide6.QtCore import Qt, QSize, Signal, QEvent, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QCursor, QShortcut

from TimelineTrackWidget import TimelineTrackWidget

class TimelineAndTracks(QWidget):
    seek_request = Signal(int)
    timeline_structure_changed = Signal() 
    track_clicked_signal = Signal()
    
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
        self.scroll_area.setAcceptDrops(True)
        self.scroll_area.viewport().installEventFilter(self)
        
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
        self.zoom_in_shortcut = QShortcut(QKeySequence("Ctrl+="), self)
        self.zoom_in_shortcut.activated.connect(lambda: self._perform_zoom(1))
        self.zoom_in_kp_shortcut = QShortcut(QKeySequence("Ctrl++"), self)
        self.zoom_in_kp_shortcut.activated.connect(lambda: self._perform_zoom(1))
        self.zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        self.zoom_out_shortcut.activated.connect(lambda: self._perform_zoom(-1))
        self.add_new_track()
        self.add_tracks_button.clicked.connect(lambda: self.add_new_track(insert_index=-1))
        self.cut_button.clicked.connect(self._on_cut_clicked)

    def eventFilter(self, source, event):
        if source == self.scroll_area.viewport() and event.type() == QEvent.Wheel:
            if event.modifiers() & Qt.ControlModifier:
                delta = event.angleDelta().y()
                viewport_x = event.position().x()
                scroll_x = self.scroll_area.horizontalScrollBar().value()
                absolute_mouse_x = viewport_x + scroll_x
                self._on_track_zoom_request(delta, absolute_mouse_x)
                return True 
        return super().eventFilter(source, event)

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

    def add_new_track(self, insert_index=-1):
        new_track = TimelineTrackWidget()
        if self.track_widgets:
            current_zoom_pps = self.track_widgets[0].pixels_per_second
            new_track.set_scale(current_zoom_pps)
        current_max_dur = self.get_content_end_all_tracks()
        current_pos = self.time_slider.value()
        new_track.playhead_pos_ms = current_pos
        new_track.set_duration_and_fill_gaps(current_max_dur)
        
        new_track.mouse_pressed_signal.connect(lambda: self.set_active_track(new_track))
        new_track.mouse_pressed_signal.connect(self.track_clicked_signal.emit)
        new_track.seek_request.connect(self.seek_request.emit)
        new_track.scroll_request.connect(self._handle_auto_scroll)
        
        new_track.track_changed.connect(self.timeline_structure_changed.emit)
        new_track.track_changed.connect(self._sync_all_tracks_duration)

        new_track.request_overlap_insertion.connect(lambda clip, start: self._handle_overlap_insertion(new_track, clip, start))

        if insert_index == -1:
            idx = self.tracks_layout_vertical.count() - 1
            self.tracks_layout_vertical.insertWidget(idx, new_track)
            self.track_widgets.append(new_track)
        else:
            self.tracks_layout_vertical.insertWidget(insert_index, new_track)
            self.track_widgets.insert(insert_index, new_track)

        self.set_active_track(new_track)
        self._sync_all_tracks_duration()
        self.set_global_playhead(current_pos)
        return new_track

    def _perform_zoom(self, direction):
        if not self.track_widgets: return
        global_mouse_pos = QCursor.pos()
        local_mouse_pos = self.scroll_area.mapFromGlobal(global_mouse_pos)
        if not self.scroll_area.rect().contains(local_mouse_pos):
            return
        current_pps = self.track_widgets[0].pixels_per_second
        zoom_factor = 1.25 if direction > 0 else 0.8
        new_pps = max(10, min(600, int(current_pps * zoom_factor)))
        if new_pps == current_pps: return
        viewport_x = local_mouse_pos.x()
        h_bar = self.scroll_area.horizontalScrollBar()
        current_scroll = h_bar.value()
        absolute_mouse_x = viewport_x + current_scroll
        time_at_mouse = absolute_mouse_x / current_pps
        for t in self.track_widgets:
            t.set_scale(new_pps)  
        new_absolute_mouse_x = time_at_mouse * new_pps
        new_scroll_pos = int(new_absolute_mouse_x - viewport_x)
        h_bar.setValue(new_scroll_pos)

    def _on_track_zoom_request(self, delta, absolute_mouse_x):
        if not self.track_widgets: return
        current_pps = self.track_widgets[0].pixels_per_second
        zoom_factor = 1.1 if delta > 0 else 0.9
        new_pps = max(10, min(500, int(current_pps * zoom_factor)))
        if new_pps == current_pps: return
        time_at_mouse = absolute_mouse_x / current_pps
        h_bar = self.scroll_area.horizontalScrollBar()
        current_scroll = h_bar.value()
        screen_offset = absolute_mouse_x - current_scroll
        for t in self.track_widgets:
            t.set_scale(new_pps) 
        new_abs_mouse_x = time_at_mouse * new_pps
        new_scroll_pos = int(new_abs_mouse_x - screen_offset)
        h_bar.setValue(new_scroll_pos)

    def _on_cut_clicked(self):
        active_track = self.get_active_track()
        if active_track:
            active_track.playhead_pos_ms = self.time_slider.value()
            success = active_track.split_clip_at_playhead()
            if success:
                self.timeline_structure_changed.emit()

    def _handle_overlap_insertion(self, source_track, clip_data, start_ms):
        try:
            idx = self.track_widgets.index(source_track)
        except ValueError:
            idx = -1
        
        if idx != -1:
            new_track = self.add_new_track(insert_index=idx)
            new_track.add_clip_at_pos(clip_data['path'], start_ms, clip_data['duration'], clip_data['color'])
            self.timeline_structure_changed.emit()

    def _sync_all_tracks_duration(self):
        global_max = 0
        for t in self.track_widgets:
            end = t.get_content_end_ms()
            if end > global_max:
                global_max = end
        self.time_slider.setMaximum(global_max)
        
        if global_max == 0:
            self.time_slider.setValue(0)
        for t in self.track_widgets:
            t.set_duration_and_fill_gaps(global_max)

    def _handle_auto_scroll(self, dx, dy):
        if dx != 0:
            h_bar = self.scroll_area.horizontalScrollBar()
            h_step = 20 * dx
            h_bar.setValue(h_bar.value() + h_step)
        if dy != 0:
            v_bar = self.scroll_area.verticalScrollBar()
            v_step = 10 * dy
            v_bar.setValue(v_bar.value() + v_step)

    def set_active_track(self, track_widget):
        for t in self.track_widgets:
            if t != track_widget:
                t.is_active_track = False
                t.clear_selection()
                t.update()
            else:
                t.is_active_track = True
                t.update()
        
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

    def _cache_file(self, file_path):
        if not os.path.exists(file_path): return file_path
        base_name = os.path.basename(file_path)
        name, ext = os.path.splitext(base_name)
        file_hash = hashlib.md5(f"{file_path}_{time.time()}".encode()).hexdigest()[:8]
        new_name = f"{name}_{file_hash}{ext}"
        new_path = os.path.join(self.tracks_cache_dir, new_name)
        try:
            shutil.copy2(file_path, new_path)
            return new_path
        except Exception as e:
            print(f"Cache Error: {e}")
            return file_path

    def insert_media_at_playhead(self, file_path):
        if not os.path.exists(file_path): return -1
        
        active_track = self.get_active_track()
        if not active_track: return -1

        cached_path = self._cache_file(file_path)
        insert_duration_ms = self._get_file_duration(cached_path)
        playhead_pos = active_track.playhead_pos_ms
        if active_track.is_overlapping(playhead_pos, insert_duration_ms):
            idx = self.track_widgets.index(active_track)
            new_track = self.add_new_track(insert_index=idx)
            self._add_single_clip_to_track(new_track, cached_path, playhead_pos, insert_duration_ms)
            
        else:
            self._add_single_clip_to_track(active_track, cached_path, playhead_pos, insert_duration_ms)

        self.timeline_structure_changed.emit()
        self._sync_all_tracks_duration()
        
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
        return source_path 

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