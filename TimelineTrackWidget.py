import copy
import json
import time
import os
import subprocess
import uuid
from PySide6.QtWidgets import QWidget, QApplication, QScrollArea
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize, QMimeData, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont, QDrag, QPixmap, QCursor

class TimelineTrackWidget(QWidget):
    seek_request = Signal(int)
    mouse_pressed_signal = Signal()
    scroll_request = Signal(int, int)
    track_changed = Signal() 
    request_overlap_insertion = Signal(dict, int) 
    zoom_request_signal = Signal(int, int) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #f0f0f0;") 
        self.setAcceptDrops(True)
        self.duration_ms = 0
        
        self.playhead_pos_ms = 0
        self.pixels_per_second = 50 
        self.clips = []
        
        self.selected_index = -1
        self._dragging_playhead = False
        self.is_active_track = False
        
        self.COLOR_VIDEO = "#800080"
        self.COLOR_AUDIO = "#FFA500"
        self.COLOR_IMAGE = "#3a6ea5"
        self.COLOR_GAP   = "#000000"

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.black_path = os.path.join(base_dir, "icons", "blackCat.jpg")
        self.files_cache_dir = os.path.join(base_dir, "filesFromTracks")
        os.makedirs(self.files_cache_dir, exist_ok=True)

        self._drag_start_pos = QPoint()
        self.ghost_clip = None 
        self.current_drag_clip_info = None 
        self.last_drag_global_pos = None 
        self.current_snap_x = None 

        self._auto_scroll_timer = QTimer(self)
        self._auto_scroll_timer.setInterval(50) 
        self._auto_scroll_timer.timeout.connect(self._on_auto_scroll_tick)
        self._scroll_direction_x = 0
        self._scroll_direction_y = 0 
        self.last_expand_time = 0.0

        self._update_dimensions()

    def update_clip_path_and_filters(self, idx, new_path, new_duration, filter_data):
        if 0 <= idx < len(self.clips):
            clip = self.clips[idx]
            if 'original_path' not in clip:
                clip['original_path'] = clip['path']
            
            clip['path'] = new_path
            clip['filters'] = filter_data
            if new_duration > 0:
                clip['duration'] = new_duration
            
            clip['name'] = "[FX] " + os.path.basename(clip['original_path'])
            
            self._rebuild_track_with_gaps()
            self.track_changed.emit()
            self.update()

    def showEvent(self, event):
        super().showEvent(event)
        self._rebuild_track_with_gaps(force_duration_to=self.duration_ms)
        self.update()

    def resizeEvent(self, event):
        self._update_dimensions()
        super().resizeEvent(event)

    def set_scale(self, new_pixels_per_second):
        self.pixels_per_second = new_pixels_per_second
        self._update_dimensions()
        self.update()

    def set_duration(self, ms):
        self.duration_ms = max(0, ms)
        self._update_dimensions() 
        self.update()

    def _update_dimensions(self):
        duration_width = self.ms_to_px(self.duration_ms) + 100
        viewport_width = 0
        if self.parent():
            viewport_width = self.parent().width()
        final_width = max(duration_width, viewport_width)
        self.setMinimumWidth(final_width)
        self.setMinimumHeight(300)

    def set_playhead(self, ms):
        self.playhead_pos_ms = max(0, ms)
        if self.playhead_pos_ms > self.duration_ms:
             self.set_duration(self.playhead_pos_ms + 5000)
        self.update()

    def clear_tracks(self):
        self.clips = []
        self.selected_index = -1
        self.playhead_pos_ms = 0
        self.update()
        self.track_changed.emit()

    def _rebuild_track_with_gaps(self, force_duration_to=None):
        user_clips = [c for c in self.clips if not c.get('is_auto_gap', False)]
        user_clips.sort(key=lambda x: x['start'])
        
        new_clip_list = []
        current_time = 0
    
        for clip in user_clips:
            if clip['start'] > current_time:
                gap_duration = clip['start'] - current_time
                if gap_duration > 0:
                    black_clip = {
                        'path': self.black_path,
                        'start': current_time,
                        'duration': gap_duration, 
                        'name': "Gap",
                        'color': self.COLOR_GAP, 
                        'is_auto_gap': True
                    }
                    new_clip_list.append(black_clip)
            
            new_clip_list.append(clip)
            current_time = clip['start'] + clip['duration']

        content_end = current_time
        final_duration = content_end
        
        if force_duration_to is not None:
            final_duration = max(content_end, force_duration_to)

        if final_duration > 0 and current_time < final_duration:
            gap_duration = final_duration - current_time
            if gap_duration > 0:
                final_gap = {
                    'path': self.black_path,
                    'start': current_time,
                    'duration': gap_duration,
                    'name': "Gap",
                    'color': self.COLOR_GAP,
                    'is_auto_gap': True
                }
                new_clip_list.append(final_gap)
        
        self.clips = new_clip_list
        self.duration_ms = final_duration
        self._update_dimensions()

    def set_duration_and_fill_gaps(self, max_ms):
        self._rebuild_track_with_gaps(force_duration_to=max_ms)
        self.update()

    def insert_clip_physically(self, clip_dict):
        self.clips.append(clip_dict)
        self._rebuild_track_with_gaps() 
        self.update()
        self.track_changed.emit()
    
    def remove_clip_by_path_and_start(self, path, start_ms):
        for i, clip in enumerate(self.clips):
            if not clip.get('is_auto_gap', False):
                if clip['path'] == path and abs(clip['start'] - start_ms) < 50:
                    del self.clips[i]
                    self.track_changed.emit()
                    return True
        return False

    def shift_clips_after(self, threshold_ms, shift_amount_ms):
        if shift_amount_ms == 0: return

        for clip in self.clips:
            if not clip.get('is_auto_gap', False):
                if clip['start'] >= threshold_ms:
                    clip['start'] += shift_amount_ms
                    if clip['start'] < 0:
                        clip['start'] = 0

        self._rebuild_track_with_gaps()
        self.update()
        self.track_changed.emit()

    def add_clip_at_pos(self, file_path, start_pos, duration_ms, color):
        name = os.path.basename(file_path)
        new_clip = {
            'path': file_path,
            'start': start_pos,
            'duration': duration_ms,
            'name': name,
            'color': color,
            'is_auto_gap': False
        }
        self.clips.append(new_clip)
        self._rebuild_track_with_gaps()
        self.update()
        self.track_changed.emit()

    def delete_selected_clip(self):
        if self.selected_index != -1 and 0 <= self.selected_index < len(self.clips):
            if self.clips[self.selected_index].get('is_auto_gap', False):
                return False
            del self.clips[self.selected_index]
            self.selected_index = -1 
            self._rebuild_track_with_gaps()
            self.update()
            self.track_changed.emit()
            return True
        return False

    def get_clip_at_ms(self, ms):
        for clip in self.clips:
            start = clip['start']
            end = start + clip['duration']
            if start <= ms < end:
                return clip
        return None

    def get_content_end_ms(self):
        max_end = 0
        for clip in self.clips:
            if not clip.get('is_auto_gap', False):
                end = clip['start'] + clip['duration']
                if end > max_end: max_end = end
        return max_end

    def ms_to_px(self, ms):
        return int((ms / 1000) * self.pixels_per_second)

    def px_to_ms(self, px):
        return int((px / self.pixels_per_second) * 1000)

    def delete_clip_by_index(self, idx):
        if 0 <= idx < len(self.clips):
            del self.clips[idx]
            self._rebuild_track_with_gaps()
            self.update()
            self.track_changed.emit()

    def _find_scroll_area(self):
        p = self.parentWidget()
        while p:
            if isinstance(p, QScrollArea):
                return p
            p = p.parentWidget()
        return None

    def is_overlapping(self, start_ms, duration_ms, excluded_index=-1):
        end_ms = start_ms + duration_ms
        
        for i, clip in enumerate(self.clips):
            if i == excluded_index:
                continue
                
            if clip.get('is_auto_gap', False):
                continue
            
            c_start = clip['start']
            c_end = c_start + clip['duration']
            
            if start_ms < c_end and end_ms > c_start:
                return True
        return False
    
    def _calculate_snap_position(self, proposed_start_ms, clip_duration_ms, exclude_index=-1):
        SNAP_THRESHOLD_PX = 15
        snap_threshold_ms = self.px_to_ms(SNAP_THRESHOLD_PX)
        candidates = [0]
        for i, clip in enumerate(self.clips):
            if i == exclude_index: continue
            if clip.get('is_auto_gap', False): continue
            candidates.append(clip['start'])
            candidates.append(clip['start'] + clip['duration'])
        best_start = proposed_start_ms
        min_diff = float('inf')
        snap_indicator_x = None
        for cand in candidates:
            diff = abs(proposed_start_ms - cand)
            if diff < snap_threshold_ms and diff < min_diff:
                min_diff = diff
                best_start = cand
                snap_indicator_x = self.ms_to_px(cand)
        proposed_end_ms = proposed_start_ms + clip_duration_ms
        for cand in candidates:
            diff = abs(proposed_end_ms - cand)
            if diff < snap_threshold_ms and diff < min_diff:
                min_diff = diff
                best_start = cand - clip_duration_ms
                snap_indicator_x = self.ms_to_px(cand)

        return best_start, snap_indicator_x

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos() 
            x = event.x()
            y = event.y()
            ms = self.px_to_ms(x)

            if abs(x - self.ms_to_px(self.playhead_pos_ms)) <= 10:
                self._dragging_playhead = True
                self.mouse_pressed_signal.emit()
                return 

            self._dragging_playhead = False
            
            track_y_start = 40
            track_y_end = 100
            clicked_clip_idx = -1
            if track_y_start <= y <= track_y_end:
                for i in range(len(self.clips)-1, -1, -1):
                    c = self.clips[i]
                    if not c.get('is_auto_gap', False):
                        c_start = self.ms_to_px(c['start'])
                        c_w = self.ms_to_px(c['duration'])
                        if c_start <= x <= c_start + c_w:
                            clicked_clip_idx = i
                            break

            if clicked_clip_idx != -1:
                self.selected_index = clicked_clip_idx
            else:
                self.selected_index = -1
                self.set_playhead(ms)
                self.seek_request.emit(ms)
            
            self.update()
            self.mouse_pressed_signal.emit()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._dragging_playhead:
            ms = max(0, self.px_to_ms(event.x()))
            self.playhead_pos_ms = ms
            self.seek_request.emit(ms)
            self.update()
            return

        if event.buttons() & Qt.LeftButton and self.selected_index != -1:
            dist = (event.pos() - self._drag_start_pos).manhattanLength()
            if dist > QApplication.startDragDistance():
                self._start_clip_drag(self.selected_index)

    def mouseReleaseEvent(self, event):
        self._dragging_playhead = False
        super().mouseReleaseEvent(event)

    def _start_clip_drag(self, clip_idx):
        clip = self.clips[clip_idx]
        if clip.get('is_auto_gap', False): return

        click_x_px = self._drag_start_pos.x()
        click_time_ms = self.px_to_ms(click_x_px)
        offset_ms = click_time_ms - clip['start']

        mime_data = QMimeData()
        clip_data_full = {
            'clip': clip,
            'origin_index': clip_idx,
            'offset_ms': offset_ms 
        }
        mime_data.setData("application/x-vem-clip", json.dumps(clip_data_full).encode())

        clip_w = self.ms_to_px(clip['duration'])
        clip_h = 60
        pixmap = QPixmap(clip_w, clip_h)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setOpacity(0.5) 
        painter.fillRect(pixmap.rect(), QColor(clip['color']))
        painter.setPen(Qt.white)
        painter.drawRect(0, 0, clip_w-1, clip_h-1)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, clip['name'])
        painter.end()

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(pixmap)
        offset_px = self.ms_to_px(offset_ms)
        drag.setHotSpot(QPoint(offset_px, clip_h // 2))

        action = drag.exec_(Qt.MoveAction)

        self.ghost_clip = None
        self.current_drag_clip_info = None
        self.last_drag_global_pos = None
        self.current_snap_x = None 
        self._scroll_direction_x = 0
        self._scroll_direction_y = 0
        self._auto_scroll_timer.stop()
        self.update()
        self._rebuild_track_with_gaps()
        self.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-vem-clip"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def _on_auto_scroll_tick(self):
        if self._scroll_direction_x != 0 or self._scroll_direction_y != 0:
            self.scroll_request.emit(self._scroll_direction_x, self._scroll_direction_y)
            
            if self._scroll_direction_x == 1:
                current_time = time.time()
                if current_time - self.last_expand_time > 0.5:
                    visible_rect = self.visibleRegion().boundingRect()
                    if visible_rect.right() > self.width() - 100:
                        new_dur = self.duration_ms + 5000
                        self.set_duration(new_dur)
                        self.last_expand_time = current_time 
            
            if self.current_drag_clip_info and self.last_drag_global_pos:
                local_pos = self.mapFromGlobal(self.last_drag_global_pos)
                x = local_pos.x()
                drop_ms = self.px_to_ms(x)
                
                offset = self.current_drag_clip_info.get('offset_ms', self.current_drag_clip_info['duration'] / 2)
                raw_start = max(0, int(drop_ms - offset))
                exclude_idx = -1
                if 'origin_index' in self.current_drag_clip_info:
                    pass 
                final_start, snap_x = self._calculate_snap_position(raw_start, self.current_drag_clip_info['duration'])
                self.current_snap_x = snap_x

                self.ghost_clip = {
                    'start': final_start,
                    'duration': self.current_drag_clip_info['duration'],
                    'color': self.current_drag_clip_info['color'],
                    'name': self.current_drag_clip_info['name']
                }
                self.update()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-vem-clip"):
            event.acceptProposedAction()
            
            local_pos_f = event.position()
            local_pos = local_pos_f.toPoint()
            x = local_pos.x()
            
            self.last_drag_global_pos = self.mapToGlobal(local_pos)
            
            try:
                data = event.mimeData().data("application/x-vem-clip")
                data_dict = json.loads(data.data().decode())
                clip_dict = data_dict['clip']
                self.current_drag_clip_info = clip_dict
                
                drop_ms = self.px_to_ms(x)
                
                if 'offset_ms' in data_dict:
                    offset = data_dict['offset_ms']
                else:
                    offset = clip_dict['duration'] / 2

                raw_start = max(0, int(drop_ms - offset))
                exclude_index = -1
                if event.source() == self:
                    exclude_index = data_dict['origin_index']
                
                final_start, snap_x = self._calculate_snap_position(raw_start, clip_dict['duration'], exclude_index)
                self.current_snap_x = snap_x
                
                self.ghost_clip = {
                    'start': final_start,
                    'duration': clip_dict['duration'],
                    'color': clip_dict['color'],
                    'name': clip_dict['name']
                }
                self.update() 
            except Exception as e:
                pass

            scroll_area = self._find_scroll_area()
            visible_rect = self.visibleRegion().boundingRect()
            vis_left = visible_rect.left()
            vis_right = visible_rect.right()
            scroll_margin = 60 
            
            if x < vis_left + scroll_margin:
                self._scroll_direction_x = -1
            elif x > vis_right - scroll_margin:
                self._scroll_direction_x = 1
            else:
                self._scroll_direction_x = 0

            self._scroll_direction_y = 0
            if scroll_area:
                pos_in_sa = scroll_area.viewport().mapFromGlobal(self.last_drag_global_pos)
                sa_height = scroll_area.viewport().height()
                vertical_margin = 40 
                if pos_in_sa.y() < vertical_margin:
                     self._scroll_direction_y = -1 
                elif pos_in_sa.y() > sa_height - vertical_margin:
                     self._scroll_direction_y = 1  

            if self._scroll_direction_x != 0 or self._scroll_direction_y != 0:
                if not self._auto_scroll_timer.isActive():
                    self._auto_scroll_timer.start()
            else:
                if self._auto_scroll_timer.isActive():
                    self._auto_scroll_timer.stop()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.ghost_clip = None
        self.current_drag_clip_info = None
        self.last_drag_global_pos = None
        self.current_snap_x = None
        self._scroll_direction_x = 0
        self._scroll_direction_y = 0 
        self._auto_scroll_timer.stop()
        self.update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self.ghost_clip = None
        self.current_drag_clip_info = None
        self.last_drag_global_pos = None
        self.current_snap_x = None
        self._scroll_direction_x = 0
        self._scroll_direction_y = 0 
        self._auto_scroll_timer.stop()
        
        if event.mimeData().hasFormat("application/x-vem-clip"):
            data = event.mimeData().data("application/x-vem-clip")
            data_dict = json.loads(data.data().decode())
            clip_dict = data_dict['clip']
            
            drop_x = event.pos().x()
            drop_ms = self.px_to_ms(drop_x)

            if 'offset_ms' in data_dict:
                offset = data_dict['offset_ms']
            else:
                offset = clip_dict['duration'] / 2

            raw_start = max(0, int(drop_ms - offset))
            
            source = event.source()
            exclude_index = -1
            if source == self:
                exclude_index = data_dict['origin_index']
            final_start, _ = self._calculate_snap_position(raw_start, clip_dict['duration'], exclude_index)

            if self.is_overlapping(final_start, clip_dict['duration'], excluded_index=exclude_index):
                clip_dict['start'] = final_start
                if source == self:
                    self.delete_clip_by_index(data_dict['origin_index'])
                elif isinstance(source, TimelineTrackWidget):
                    source.delete_clip_by_index(data_dict['origin_index'])
                
                self.request_overlap_insertion.emit(clip_dict, final_start)
                event.accept()
                return

            clip_dict['start'] = final_start
            
            if source != self and isinstance(source, TimelineTrackWidget):
                source.delete_clip_by_index(data_dict['origin_index'])
            elif source == self:
                orig_idx = data_dict['origin_index']
                if 0 <= orig_idx < len(self.clips):
                     del self.clips[orig_idx]
            
            self.clips.append(clip_dict)
            
            event.setDropAction(Qt.MoveAction)
            event.accept()
            
            self._rebuild_track_with_gaps()
            self.track_changed.emit()
            self.update()
        else:
            event.ignore()

    def split_clip_at_playhead(self):
        target_clip_index = -1
        target_clip = None
        if self.selected_index != -1 and self.selected_index < len(self.clips):
            candidate = self.clips[self.selected_index]
            if not candidate.get('is_auto_gap', False):
                start = candidate['start']
                end = start + candidate['duration']
                if start < self.playhead_pos_ms < end:
                    target_clip_index = self.selected_index
                    target_clip = candidate
        if target_clip is None:
            return False
        split_point_global = self.playhead_pos_ms
        split_point_local_ms = split_point_global - target_clip['start']
        split_point_sec = split_point_local_ms / 1000.0
        
        original_path = target_clip['path']
        original_duration = target_clip['duration']
        is_image = original_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))
        if is_image:

            part1 = target_clip.copy()
            part1['duration'] = split_point_local_ms

            part2 = target_clip.copy()
            part2['start'] = split_point_global
            part2['duration'] = original_duration - split_point_local_ms
            part2['name'] = part2['name'] + "_p2"

            del self.clips[target_clip_index]
            self.clips.insert(target_clip_index, part1)
            self.clips.insert(target_clip_index + 1, part2)
            
        else:
            unique_id = str(uuid.uuid4())[:8]
            base_name = os.path.splitext(os.path.basename(original_path))[0]
            ext = os.path.splitext(original_path)[1]
            
            part1_filename = f"{base_name}_part1_{unique_id}{ext}"
            part2_filename = f"{base_name}_part2_{unique_id}{ext}"
            
            part1_path = os.path.join(self.files_cache_dir, part1_filename)
            part2_path = os.path.join(self.files_cache_dir, part2_filename)
            cmd1 = [
                'ffmpeg', '-y', 
                '-ss', '0', 
                '-i', original_path, 
                '-t', str(split_point_sec), 
                '-c', 'copy', 
                '-avoid_negative_ts', 'make_zero',
                part1_path
            ]

            cmd2 = [
                'ffmpeg', '-y', 
                '-ss', str(split_point_sec), 
                '-i', original_path, 
                '-c', 'copy', 
                '-avoid_negative_ts', 'make_zero',
                part2_path
            ]
            try:
                subprocess.run(cmd1, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(cmd2, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                part1 = target_clip.copy()
                part1['path'] = part1_path
                part1['original_path'] = part1_path

                part1['duration'] = split_point_local_ms 
                
                part2 = target_clip.copy()
                part2['path'] = part2_path
                part2['original_path'] = part2_path
                part2['start'] = split_point_global
                part2['duration'] = original_duration - split_point_local_ms
                part2['name'] = base_name + "_p2"
                
                del self.clips[target_clip_index]
                self.clips.insert(target_clip_index, part1)
                self.clips.insert(target_clip_index + 1, part2)
                
            except Exception as e:
                print(f"Error splitting file: {e}")
                return False

        self.selected_index = -1 
        self._rebuild_track_with_gaps()
        self.track_changed.emit()
        self.update()
        return True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        visible_rect = event.rect()
        
        bg_color = QColor("#f0f0f0")
        if self.is_active_track:
            bg_color = QColor("#e6f3ff") 
            
        painter.fillRect(visible_rect, bg_color)
        if self.is_active_track:
            pen = QPen(QColor("#3a6ea5"), 2)
            painter.setPen(pen)
            painter.drawRect(visible_rect.adjusted(1,1,-1,-1))
        ruler_height = 30
        painter.fillRect(QRect(visible_rect.left(), 0, visible_rect.width(), ruler_height), QColor("#e0e0e0"))
        
        pen_tick = QPen(QColor("#888888"))
        pen_text = QPen(QColor("#333333"))
        painter.setFont(QFont("Arial", 8))

        start_sec = int(self.px_to_ms(visible_rect.left()) / 1000)
        end_sec = int(self.px_to_ms(visible_rect.right()) / 1000) + 2

        for sec in range(start_sec, end_sec):
            x = self.ms_to_px(sec * 1000)
            painter.setPen(pen_tick)
            painter.drawLine(x, 15, x, 30)
            if sec % 5 == 0:
                painter.setPen(pen_text)
                painter.drawText(x + 2, 12, f"{sec // 60}:{sec % 60:02d}")
            x_half = self.ms_to_px(sec * 1000 + 500)
            painter.drawLine(x_half, 22, x_half, 30)

        track_y = 40
        track_height = 60
        painter.fillRect(QRect(visible_rect.left(), track_y, visible_rect.width(), track_height), QColor("#ffffff"))

        for i, clip in enumerate(self.clips):
            x_start = self.ms_to_px(clip['start'])
            w_clip = self.ms_to_px(clip['duration'])
            if x_start + w_clip < visible_rect.left() or x_start > visible_rect.right():
                continue
            clip_rect = QRect(x_start, track_y + 2, w_clip, track_height - 4)
            painter.fillRect(clip_rect, QColor(clip.get('color', '#3a6ea5')))
            is_gap = clip.get('is_auto_gap', False)
            if i == self.selected_index and not is_gap:
                painter.setPen(QPen(QColor("yellow"), 3))
                painter.drawRect(clip_rect)
            elif not is_gap:
                painter.setPen(QColor("white"))
                painter.drawRect(clip_rect)
                painter.drawText(clip_rect, Qt.AlignCenter, clip['name'])

        if self.ghost_clip:
            g_start = self.ms_to_px(self.ghost_clip['start'])
            g_width = self.ms_to_px(self.ghost_clip['duration'])
            g_rect = QRect(g_start, track_y + 2, g_width, track_height - 4)
            
            c = QColor(self.ghost_clip.get('color', '#3a6ea5'))
            c.setAlpha(128) 
            painter.fillRect(g_rect, c)
            
            pen_ghost = QPen(Qt.white, 2, Qt.DashLine)
            painter.setPen(pen_ghost)
            painter.drawRect(g_rect)
            
            painter.setPen(Qt.white)
            painter.drawText(g_rect, Qt.AlignCenter, self.ghost_clip.get('name', ''))

        if self.current_snap_x is not None:
             painter.setPen(QPen(QColor("#00FF00"), 2))
             painter.drawLine(self.current_snap_x, 0, self.current_snap_x, self.height())

        ph_x = self.ms_to_px(self.playhead_pos_ms)
        if visible_rect.left() - 10 <= ph_x <= visible_rect.right() + 10:
            painter.setPen(QPen(QColor("#ff0000"), 2))
            painter.drawLine(ph_x, 0, ph_x, self.height())
            painter.setBrush(QColor("#ff0000"))
            painter.drawPolygon([QPoint(ph_x - 6, 0), QPoint(ph_x + 6, 0), QPoint(ph_x, 15)])
        
    def clear_selection(self):
        if self.selected_index != -1:
            self.selected_index = -1
            self.update()