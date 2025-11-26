import sys
import os
import hashlib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget, QTabBar, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, QSize , Signal , QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaMetaData
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QResizeEvent, QShowEvent


class VideoTabContent(QWidget):
    player_state_changed = Signal(QMediaPlayer.PlaybackState)
    SUPPORTED_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
    SUPPORTED_VIDEO_EXT = {'.mp4', '.mov', '.avi', '.mkv'}
    SUPPORTED_AUDIO_EXT = {'.mp3', '.wav', '.flac'}

    def __init__(self, file_path):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: blue;") 
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setAlignment(Qt.AlignCenter)

        self.file_path = os.path.abspath(file_path)
        self.ext = os.path.splitext(file_path)[1].lower()
        
        self.player = None 
        self.audio_output = None
        self.video_widget = None
        self.visual_label = None
        self.display_pixmap = None 

        self._logical_rate = 1.0
        self.reverse_timer = QTimer(self)
        self.reverse_timer.setInterval(33)  # 33ms = aprox 30 FPS
        self.reverse_timer.timeout.connect(self._on_reverse_timer_tick)

        if self.ext in self.SUPPORTED_IMAGE_EXT:
            self._setup_image_view()
        elif self.ext in self.SUPPORTED_VIDEO_EXT:
            self._setup_video_player()
        elif self.ext in self.SUPPORTED_AUDIO_EXT:
            self._setup_audio_player()
        else:
            self._setup_placeholder_view()

    def resizeEvent(self, event: QResizeEvent):
        if self.visual_label and self.display_pixmap:
            self._update_image_scaling()
        super().resizeEvent(event)

    def showEvent(self, event: QShowEvent):
        if self.visual_label and self.display_pixmap:
            self._update_image_scaling()
        super().showEvent(event)

    def _update_image_scaling(self):
        if not self.display_pixmap or self.display_pixmap.isNull(): 
            return
        
        w = self.width()
        h = self.height()

        if w <= 0 or h <= 0:
            return

        scaled_pix = self.display_pixmap.scaled(
            w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.visual_label.setPixmap(scaled_pix)

    def _create_optimized_cache(self, input_path):
        """Pune in cache imaginile in filesFromTracks (1920x1080)."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(base_dir, "filesFromTracks")
        os.makedirs(cache_dir, exist_ok=True)

        file_hash = hashlib.md5(input_path.encode('utf-8')).hexdigest()
        _, ext = os.path.splitext(input_path)
        cache_name = f"{file_hash}{ext}"
        cache_path = os.path.join(cache_dir, cache_name)

        if os.path.exists(cache_path):
            return cache_path

        if not os.path.exists(input_path):
            return None

        original = QPixmap(input_path)
        if original.isNull(): 
            print(f"DEBUG EROARE: Nu s-a putut incarca QPixmap pentru {input_path}")
            return None

        optimized = original.scaled(1920, 1080, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        optimized.save(cache_path)
        
        return cache_path

    def _get_black_placeholder(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        black_path = os.path.join(base_dir, "icons", "black.jpg")
        
        if os.path.exists(black_path):
            cached_path = self._create_optimized_cache(black_path)
            return QPixmap(cached_path)
        else:
            # Fallback
            pix = QPixmap(100, 100)
            pix.fill(Qt.darkGray)
            return pix

    def _setup_image_view(self):
        self.visual_label = QLabel("DEBUG: IMAGE VIEW")
        self.visual_label.setAlignment(Qt.AlignCenter)
        self.visual_label.setStyleSheet("background-color: yellow; color: black; font-weight: bold;") 
        
        self.visual_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.visual_label.setMinimumSize(QSize(100, 100)) 
        self.layout.addWidget(self.visual_label)
        
        cached_path = self._create_optimized_cache(self.file_path)
        
        if cached_path: 
            self.display_pixmap = QPixmap(cached_path)
            if self.display_pixmap.isNull():
                 self.visual_label.setStyleSheet("background-color: darkred; color: white;")
        else:
            self.display_pixmap = QPixmap(100, 100)
            self.display_pixmap.fill(Qt.darkRed)
            self.visual_label.setText("EROARE: Fisier original lipsa")
            self.visual_label.setStyleSheet("background-color: darkred; color: white;")
        
        if not self.display_pixmap.isNull():
             self.visual_label.setPixmap(self.display_pixmap)

    def _setup_video_player(self):
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: yellow;") 
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.video_widget)

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        
        self.player.setSource(QUrl.fromLocalFile(self.file_path))
        self.audio_output.setVolume(0.7)
        self.player.play()

        self.player.playbackStateChanged.connect(self.player_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

    def _setup_audio_player(self):
        self.visual_label = QLabel("Fisier audio incarcat")
        self.visual_label.setAlignment(Qt.AlignCenter)
        self.visual_label.setStyleSheet("background-color: yellow; color: black;")
        self.visual_label.setMinimumSize(QSize(100, 100)) 
        self.visual_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.visual_label)

        self.display_pixmap = self._get_black_placeholder()
        self.visual_label.setPixmap(self.display_pixmap)

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl.fromLocalFile(self.file_path))
        self.audio_output.setVolume(0.7)
        self.player.play()

        self.player.playbackStateChanged.connect(self.player_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)


    def _setup_placeholder_view(self):
        self.visual_label = QLabel("Necunoscut")
        self.visual_label.setAlignment(Qt.AlignCenter)
        self.visual_label.setStyleSheet("background-color: yellow; color: black;")
        self.visual_label.setMinimumSize(QSize(100, 100)) 
        self.visual_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.visual_label)
        
        self.display_pixmap = self._get_black_placeholder()
        self.visual_label.setPixmap(self.display_pixmap)


    def step_frame(self, direction):
        if not self.player:
            return

        if self.reverse_timer.isActive():
            self.stop_reverse_logic()
            self.player_state_changed.emit(QMediaPlayer.PausedState)

        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.player_state_changed.emit(QMediaPlayer.PausedState) 

        frame_duration = 33 
        
        meta_data = self.player.metaData()
        if meta_data:
            fps = meta_data.value(QMediaMetaData.Key.VideoFrameRate)
            if fps and float(fps) > 0:
                frame_duration = int(1000 / float(fps))
        
        current_pos = self.player.position()
        new_pos = current_pos + (direction * frame_duration)

        if new_pos < 0:
            new_pos = 0
        elif new_pos > self.player.duration():
            new_pos = self.player.duration()
            
        self.player.setPosition(new_pos)


    def go_to_start(self):
        if self.player:

            if self.reverse_timer.isActive():
                self.reverse_timer.stop()

            self._logical_rate = 1.0
            self.player.setPlaybackRate(1.0)

            self.player.pause()
            self.player.setPosition(0)
            if self.audio_output:
                self.audio_output.setMuted(False)
            self.player_state_changed.emit(QMediaPlayer.PausedState)

    def go_to_end(self):
        if self.player:
            if self.reverse_timer.isActive():
                self.reverse_timer.stop()
                self._logical_rate = 1.0

            self.player.pause()
            self.player.setPosition(self.player.duration())
            
            if self.audio_output:
                self.audio_output.setMuted(False)
            self.player_state_changed.emit(QMediaPlayer.PausedState)


    def _on_reverse_timer_tick(self):
        if not self.player:
            self.reverse_timer.stop()
            return

        if self.player.position() <= 0:
            self.reverse_timer.stop()
            self._logical_rate = 1.0
            self.player.pause()
            self.player.setPosition(0)
            if self.audio_output: 
                self.audio_output.setMuted(False)
            self.player_state_changed.emit(QMediaPlayer.PausedState)
            return
        step_ms = 33 * abs(self._logical_rate)
        new_pos = int(max(0, self.player.position() - step_ms))
        self.player.setPosition(new_pos)

    def change_speed_mode(self, direction):
        if not self.player:
            return
        if direction == "backward":
            if self.player.position() <= 0:
                self.player_state_changed.emit(QMediaPlayer.PausedState)
                return
        rate = self._logical_rate
        new_rate = 1.0
        rate = round(rate, 1)

        if direction == "forward":
            if rate == 1.0: new_rate = 1.5
            elif rate == 1.5: new_rate = 2.0
            elif rate == 2.0: new_rate = 0.5
            elif rate == 0.5: new_rate = 1.0
            else: new_rate = 1.0

        elif direction == "backward":
            if rate > 0: new_rate = -0.5
            elif rate == -0.5: new_rate = -1.0
            elif rate == -1.0: new_rate = -1.5
            elif rate == -1.5: new_rate = -2.0
            elif rate == -2.0: new_rate = -0.5 
            else: new_rate = -0.5

        self._logical_rate = new_rate
        print(f"Viteza setata la: {new_rate}x")
        if new_rate > 0:
            self.reverse_timer.stop() 
            if self.audio_output: self.audio_output.setMuted(False)
            self.player.setPlaybackRate(new_rate)
            duration = self.player.duration()
            position = self.player.position()
            
            if abs(duration - position) < 50:
                 self.player.pause()
                 self.player_state_changed.emit(QMediaPlayer.PausedState)
            else:
                if self.player.playbackState() != QMediaPlayer.PlayingState:
                    self.player.play()

        else:
            if self.audio_output: self.audio_output.setMuted(True)
            self.player.pause()
            self.player.setPlaybackRate(1.0) 
            
            if not self.reverse_timer.isActive():
                self.reverse_timer.start()

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.reverse_timer.stop()
            self._logical_rate = 1.0
            self.player.setPlaybackRate(1.0)
            self.player.pause()
            if self.player.duration() > 0:
                self.player.setPosition(self.player.duration())
            if self.audio_output: 
                self.audio_output.setMuted(False)
            self.player_state_changed.emit(QMediaPlayer.PausedState)


    def is_reversing(self):
        return self.reverse_timer.isActive()

    def stop_reverse_logic(self):
        if self.reverse_timer.isActive():
            self.reverse_timer.stop()  
        self._logical_rate = 1.0
        if self.audio_output:
            self.audio_output.setMuted(False)

    def toggle_play_safe(self):
        if not self.player:
            return

        if self.reverse_timer.isActive():
            self.stop_reverse_logic()
            self.player.pause()
            self.player_state_changed.emit(QMediaPlayer.PausedState)
            return

        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.player_state_changed.emit(QMediaPlayer.PausedState)
            return

        current_pos = self.player.position()
        duration = self.player.duration()

        is_at_end = (abs(duration - current_pos) < 50) or (self.player.mediaStatus() == QMediaPlayer.EndOfMedia)
        
        if is_at_end:
            self.player_state_changed.emit(QMediaPlayer.PausedState)
        else:
            if self.audio_output:
                self.audio_output.setMuted(False)
            self._logical_rate = 1.0
            self.player.play()
            self.player_state_changed.emit(QMediaPlayer.PlayingState)