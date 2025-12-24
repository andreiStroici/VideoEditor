from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont
import os 
import copy

class TimelineTrackWidget(QWidget):
    seek_request = Signal(int)
    mouse_pressed_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #f0f0f0;") 
        
        self.duration_ms = 60000 
        self.playhead_pos_ms = 0
        self.pixels_per_second = 50 
        self.clips = []
        
        self.selected_index = -1
        self._dragging_playhead = False
        self.is_active_track = False
        
        # Culori standard
        self.COLOR_VIDEO = "#800080"
        self.COLOR_AUDIO = "#FFA500"
        self.COLOR_IMAGE = "#3a6ea5"
        self.COLOR_GAP   = "#000000"

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.black_path = os.path.join(base_dir, "icons", "blackCat.jpg")

        self._update_dimensions()

    def resizeEvent(self, event):
        self._update_dimensions()
        super().resizeEvent(event)

    def set_duration(self, ms):
        self.duration_ms = max(ms, 60000)
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

        if force_duration_to is not None:
            if current_time < force_duration_to:
                gap_duration = force_duration_to - current_time
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

    def set_duration_and_fill_gaps(self, max_ms):
        """
        Seteaza durata si umple cu gap-uri pana la acea durata.
        """
        self.duration_ms = max(max_ms, 60000)
        self._rebuild_track_with_gaps(force_duration_to=max_ms)
        self._update_dimensions()
        self.update()

    def insert_clip_physically(self, clip_dict):
        self.clips.append(clip_dict)

        self._rebuild_track_with_gaps() 
        self.update()
    
    def remove_clip_by_path_and_start(self, path, start_ms):
        for i, clip in enumerate(self.clips):
            if not clip.get('is_auto_gap', False):
                if clip['path'] == path and abs(clip['start'] - start_ms) < 50:
                    del self.clips[i]
                    return True
        return False

    def shift_clips_after(self, threshold_ms, shift_amount_ms):
        if shift_amount_ms <= 0: return

        for clip in self.clips:
            if not clip.get('is_auto_gap', False):
                if clip['start'] >= threshold_ms:
                    clip['start'] += shift_amount_ms
        
        self._rebuild_track_with_gaps()
        self.update()


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

    def delete_selected_clip(self):
        if self.selected_index != -1 and 0 <= self.selected_index < len(self.clips):
            if self.clips[self.selected_index].get('is_auto_gap', False):
                return False
            del self.clips[self.selected_index]
            self.selected_index = -1 
            self._rebuild_track_with_gaps()
            self.update()
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
        if not self.clips: return 0
        max_end = 0
        for clip in self.clips:
            end = clip['start'] + clip['duration']
            if end > max_end: max_end = end
        return max_end

    def ms_to_px(self, ms):
        return int((ms / 1000) * self.pixels_per_second)

    def px_to_ms(self, px):
        return int((px / self.pixels_per_second) * 1000)

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

        ph_x = self.ms_to_px(self.playhead_pos_ms)
        if visible_rect.left() - 10 <= ph_x <= visible_rect.right() + 10:
            painter.setPen(QPen(QColor("#ff0000"), 2))
            painter.drawLine(ph_x, 0, ph_x, self.height())
            painter.setBrush(QColor("#ff0000"))
            painter.drawPolygon([QPoint(ph_x - 6, 0), QPoint(ph_x + 6, 0), QPoint(ph_x, 15)])


    def mousePressEvent(self, event):
        self.mouse_pressed_signal.emit() 
        if event.button() == Qt.LeftButton:
            x = event.x()
            y = event.y()
            ms = self.px_to_ms(x)

            if abs(x - self.ms_to_px(self.playhead_pos_ms)) <= 10:
                self._dragging_playhead = True
                return 

            self._dragging_playhead = False
            
            track_y_start = 40
            track_y_end = 100
            clicked_clip = False
            if track_y_start <= y <= track_y_end:
                for i in range(len(self.clips)-1, -1, -1):
                    c = self.clips[i]
                    if not c.get('is_auto_gap', False):
                        c_start = self.ms_to_px(c['start'])
                        c_w = self.ms_to_px(c['duration'])
                        if c_start <= x <= c_start + c_w:
                            self.selected_index = i
                            clicked_clip = True
                            break
            
            if not clicked_clip:
                self.selected_index = -1
                self.set_playhead(ms)
                self.seek_request.emit(ms)
            
            self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._dragging_playhead:
            ms = max(0, self.px_to_ms(event.x()))
            self.playhead_pos_ms = ms
            self.seek_request.emit(ms)
            self.update()

    def mouseReleaseEvent(self, event):
        self._dragging_playhead = False