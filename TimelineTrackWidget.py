from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont
import os 

class TimelineTrackWidget(QWidget):
    seek_request = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #f0f0f0;") 
        
        self.duration_ms = 60000 
        self.playhead_pos_ms = 0
        self.pixels_per_second = 50 
        self.clips = []
        
        self.selected_index = -1
        self._dragging_playhead = False

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
        # Auto-expand
        if self.playhead_pos_ms > self.duration_ms:
             self.set_duration(self.playhead_pos_ms + 5000)
        self.update()

    def clear_tracks(self):
        self.clips = []
        self.selected_index = -1
        self.playhead_pos_ms = 0
        self.update()

    def _rebuild_track_with_gaps(self):
        """
        Reconstructs self.clips. If there is space between clips, 
        insert a blackCat.jpg clip of EXACT required duration.
        """
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
                        'color': "#000000", 
                        'is_auto_gap': True 
                    }
                    new_clip_list.append(black_clip)
            
            new_clip_list.append(clip)
            current_time = clip['start'] + clip['duration']
            
        self.clips = new_clip_list

    def add_clip(self, file_path, duration_ms, color):
        self.add_clip_at_pos(file_path, self.playhead_pos_ms, duration_ms, color)

    def shift_clips_after(self, threshold_ms, shift_amount_ms):
        for clip in self.clips:
            if not clip.get('is_auto_gap', False) and clip['start'] >= threshold_ms:
                clip['start'] += shift_amount_ms
        self.update()

    def add_clip_at_pos(self, file_path, start_pos, duration_ms, color):
        import os
        
        self.shift_clips_after(start_pos, duration_ms)

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
        
        # Restore selection
        for i, c in enumerate(self.clips):
            if c.get('start') == start_pos and c.get('path') == file_path:
                self.selected_index = i
                break

        max_end = 0
        for c in self.clips:
            end = c['start'] + c['duration']
            if end > max_end: max_end = end
            
        if max_end > self.duration_ms:
            self.set_duration(max_end + 5000) 
        else:
            self.update()

    def trim_clip_at(self, ms):
        did_trim = False
        for clip in self.clips:
            if clip.get('is_auto_gap', False): continue
            
            start = clip['start']
            end = start + clip['duration']
            if start < ms < end:
                new_duration = ms - start
                clip['duration'] = new_duration
                did_trim = True
        
        if did_trim:
            self._rebuild_track_with_gaps()
            
        return did_trim

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
    
    def get_next_clip_start_after(self, ms):
        next_start = None
        for clip in self.clips:
            if clip['start'] > ms:
                if next_start is None or clip['start'] < next_start:
                    next_start = clip['start']
        return next_start

    def get_end_of_clip_before(self, current_pos):
        best_end = 0
        for clip in self.clips:
            end = clip['start'] + clip['duration']
            if end <= current_pos:
                if end > best_end:
                    best_end = end
        return best_end

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
        painter.fillRect(visible_rect, QColor("#f0f0f0"))
        ruler_height = 30
        ruler_rect = QRect(visible_rect.left(), 0, visible_rect.width(), ruler_height)
        painter.fillRect(ruler_rect, QColor("#e0e0e0"))
        
        pen_tick = QPen(QColor("#888888"))
        pen_text = QPen(QColor("#333333"))
        
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)

        start_sec = int(self.px_to_ms(visible_rect.left()) / 1000)
        max_visible_ms = self.px_to_ms(visible_rect.right())
        end_sec = int(max_visible_ms / 1000) + 1
        current_width_sec = int(self.width() / self.pixels_per_second) + 2
        end_sec = min(end_sec, current_width_sec)

        for sec in range(start_sec, end_sec):
            x = self.ms_to_px(sec * 1000)
            
            painter.setPen(pen_tick)
            painter.drawLine(x, 15, x, 30)
            
            if sec % 5 == 0:
                painter.setPen(pen_text)
                time_str = f"{sec // 60}:{sec % 60:02d}"
                painter.drawText(x + 2, 12, time_str)
            
            x_half = self.ms_to_px(sec * 1000 + 500)
            painter.drawLine(x_half, 22, x_half, 30)

        track_y = 40
        track_height = 60
        track_rect = QRect(visible_rect.left(), track_y, visible_rect.width(), track_height)
        painter.fillRect(track_rect, QColor("#ffffff")) 
        painter.setPen(QColor("#d0d0d0"))
        painter.drawLine(visible_rect.left(), track_y, visible_rect.right(), track_y)
        painter.drawLine(visible_rect.left(), track_y + track_height, visible_rect.right(), track_y + track_height)

        for i, clip in enumerate(self.clips):
            x_start = self.ms_to_px(clip['start'])
            w_clip = self.ms_to_px(clip['duration'])
            x_end = x_start + w_clip

            if x_end < visible_rect.left() or x_start > visible_rect.right():
                continue

            clip_rect = QRect(x_start, track_y + 2, w_clip, track_height - 4)
            
            color_code = clip.get('color', '#3a6ea5')
            painter.fillRect(clip_rect, QColor(color_code))
            
            is_gap = clip.get('is_auto_gap', False)
            
            if i == self.selected_index and not is_gap:
                high_pen = QPen(QColor("yellow"), 3)
                painter.setPen(high_pen)
                painter.drawRect(clip_rect)
            elif is_gap:
                painter.setPen(QColor("black")) # Visual debug for gap
            else:
                painter.setPen(QColor("white"))
                painter.drawRect(clip_rect)
            
            painter.setPen(QColor("white"))
            painter.drawText(clip_rect, Qt.AlignCenter, clip['name'])

        ph_x = self.ms_to_px(self.playhead_pos_ms)
        if visible_rect.left() - 10 <= ph_x <= visible_rect.right() + 10:
            painter.setPen(QPen(QColor("#ff0000"), 2))
            painter.drawLine(ph_x, 0, ph_x, self.height())
            painter.setBrush(QColor("#ff0000"))
            painter.drawPolygon([
                QPoint(ph_x - 6, 0),
                QPoint(ph_x + 6, 0),
                QPoint(ph_x, 15)
            ])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.x()
            y = event.y()

            current_ph_x = self.ms_to_px(self.playhead_pos_ms)
            if abs(x - current_ph_x) <= 10:
                self._dragging_playhead = True
                return 

            self._dragging_playhead = False
            
            if not self.clips:
                 ms = self.px_to_ms(x)
                 self.set_playhead(ms)
                 self.seek_request.emit(ms)
                 return

            track_y_start = 40
            track_y_end = 100
            
            clicked_on_clip = False
            if track_y_start <= y <= track_y_end:
                for i in range(len(self.clips) - 1, -1, -1):
                    clip = self.clips[i]
                    x_start = self.ms_to_px(clip['start'])
                    w_clip = self.ms_to_px(clip['duration'])
                    
                    if x_start <= x <= x_start + w_clip:
                        # Prevent selecting gaps
                        if not clip.get('is_auto_gap', False):
                            self.selected_index = i
                            clicked_on_clip = True
                        break
            if not clicked_on_clip:
                self.selected_index = -1
                ms = self.px_to_ms(x)
                self.set_playhead(ms)
                self.seek_request.emit(ms)
            
            self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            if self._dragging_playhead:
                x = event.x()
                ms = self.px_to_ms(x)
                ms = max(0, ms)
                self.playhead_pos_ms = ms
                self.seek_request.emit(ms)
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging_playhead = False