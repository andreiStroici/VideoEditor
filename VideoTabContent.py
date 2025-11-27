import sys
import os
import hashlib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, QSize, Signal, QTimer, QObject
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaMetaData
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QResizeEvent, QShowEvent

from ImagePlayer import ImagePlayer

class VideoTabContent(QWidget):
    player_state_changed = Signal(QMediaPlayer.PlaybackState)
    
    SUPPORTED_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
    SUPPORTED_VIDEO_EXT = {'.mp4', '.mov', '.avi', '.mkv'}
    SUPPORTED_AUDIO_EXT = {'.mp3', '.wav', '.flac'}


    def __init__(self, file_path, is_timeline=False):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: black;") 
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setAlignment(Qt.AlignCenter)

        self.file_path = os.path.abspath(file_path)
        self.ext = os.path.splitext(file_path)[1].lower()
        self.is_timeline = is_timeline  
        
        self.player = None 
        self.audio_output = None
        self.video_widget = None
        self.visual_label = None
        self.display_pixmap = None 

        self._logical_rate = 1.0
        self.reverse_timer = QTimer(self)
        self.reverse_timer.setInterval(33)
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
        if w <= 0 or h <= 0: return

        scaled_pix = self.display_pixmap.scaled(
            w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.visual_label.setPixmap(scaled_pix)

    def _create_optimized_cache(self, input_path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(base_dir, "filesFromTracks")
        os.makedirs(cache_dir, exist_ok=True)
        file_hash = hashlib.md5(input_path.encode('utf-8')).hexdigest()
        _, ext = os.path.splitext(input_path)
        cache_name = f"{file_hash}{ext}"
        cache_path = os.path.join(cache_dir, cache_name)
        if os.path.exists(cache_path): return cache_path
        if not os.path.exists(input_path): return None
        original = QPixmap(input_path)
        if original.isNull(): return None
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
            pix = QPixmap(100, 100)
            pix.fill(Qt.darkGray)
            return pix

    def _get_music_placeholder(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        music_path = os.path.join(base_dir, "icons", "music.jpg")
        

        if not os.path.exists(music_path):
            return self._get_black_placeholder()

        cached_path = self._create_optimized_cache(music_path)
        return QPixmap(cached_path)

    def _setup_image_view(self):
        self.visual_label = QLabel()
        self.visual_label.setAlignment(Qt.AlignCenter)
        self.visual_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.visual_label)
        cached_path = self._create_optimized_cache(self.file_path)
        if cached_path: self.display_pixmap = QPixmap(cached_path)
        else: self.display_pixmap = self._get_black_placeholder()
        if not self.display_pixmap.isNull(): self.visual_label.setPixmap(self.display_pixmap)
        self.player = ImagePlayer(duration_ms=5000, parent=self)
        self.player.playbackStateChanged.connect(self.player_state_changed)
        QTimer.singleShot(100, lambda: self.player.durationChanged.emit(5000))

    def _setup_video_player(self):
        self.video_widget = QVideoWidget()
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
        self.player.positionChanged.connect(self._check_position_for_end)

    def _setup_audio_player(self):
        self.visual_label = QLabel()
        self.visual_label.setAlignment(Qt.AlignCenter)
        self.visual_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.visual_label)
        
        if self.is_timeline:
            self.display_pixmap = self._get_black_placeholder()
        else:
            self.display_pixmap = self._get_music_placeholder()

        self.visual_label.setPixmap(self.display_pixmap)
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl.fromLocalFile(self.file_path))
        self.audio_output.setVolume(0.7)
        self.player.play()
        self.player.playbackStateChanged.connect(self.player_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.positionChanged.connect(self._check_position_for_end)

    def _setup_placeholder_view(self):
        self.visual_label = QLabel("Necunoscut")
        self.visual_label.setAlignment(Qt.AlignCenter)
        self.visual_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.visual_label)
        self.display_pixmap = self._get_black_placeholder()
        self.visual_label.setPixmap(self.display_pixmap)

    def cleanup(self):
        if self.player:
            self.player.stop()
            if isinstance(self.player, QMediaPlayer):
                self.player.setSource(QUrl())
        if self.reverse_timer.isActive():
            self.reverse_timer.stop()

    def step_frame(self, direction):
        if not self.player: return
        if self.reverse_timer.isActive():
            self.stop_reverse_logic()
            self.player_state_changed.emit(QMediaPlayer.PausedState)
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.player_state_changed.emit(QMediaPlayer.PausedState) 
        frame_duration = 33 
        if isinstance(self.player, QMediaPlayer):
            meta_data = self.player.metaData()
            if meta_data:
                fps = meta_data.value(QMediaMetaData.Key.VideoFrameRate)
                if fps and float(fps) > 0:
                    frame_duration = int(1000 / float(fps))
        current_pos = self.player.position()
        new_pos = current_pos + (direction * frame_duration)
        self.player.setPosition(new_pos)

    def go_to_start(self):
        if self.player:
            if self.reverse_timer.isActive(): self.reverse_timer.stop()
            self._logical_rate = 1.0
            if isinstance(self.player, QMediaPlayer):
                self.player.setPlaybackRate(1.0)
            elif isinstance(self.player, ImagePlayer):
                self.player.setPlaybackRate(1.0)

            self.player.pause()
            self.player.setPosition(0)
            if self.audio_output: self.audio_output.setMuted(False)
            self.player_state_changed.emit(QMediaPlayer.PausedState)

    def go_to_end(self):
        if self.player:
            if self.reverse_timer.isActive(): self.reverse_timer.stop()
            self.player.pause()
            self.player.setPosition(self.player.duration())
            if self.audio_output: self.audio_output.setMuted(False)
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
            if self.audio_output: self.audio_output.setMuted(False)
            self.player_state_changed.emit(QMediaPlayer.PausedState)
            return
        step_ms = 33 * abs(self._logical_rate)
        new_pos = int(max(0, self.player.position() - step_ms))
        self.player.setPosition(new_pos)

    def change_speed_mode(self, direction):
        if not self.player: return
        if direction == "backward":
            if self.player.position() <= 50: 
                self.reverse_timer.stop()
                self._logical_rate = 1.0
                self.player.pause()
                self.player_state_changed.emit(QMediaPlayer.PausedState)
                return

        current_pos = self.player.position()
        duration = self.player.duration()
        is_at_end = (abs(duration - current_pos) < 100)
        
        rate = self._logical_rate
        new_rate = 1.0
        rate = round(rate, 1)

        if direction == "forward":
            if rate < 0:
                new_rate = 1.0
            else:
                if rate == 1.0: new_rate = 1.5
                elif rate == 1.5: new_rate = 2.0
                elif rate == 2.0: new_rate = 0.5
                elif rate == 0.5: new_rate = 1.0
                else: new_rate = 1.0

        elif direction == "backward":
            if rate > 0:
                new_rate = -0.5
            else:
                if rate == -0.5: new_rate = -1.0
                elif rate == -1.0: new_rate = -1.5
                elif rate == -1.5: new_rate = -2.0
                elif rate == -2.0: new_rate = -0.5 
                else: new_rate = -0.5

        self._logical_rate = new_rate
        
        if new_rate > 0:
            self.reverse_timer.stop() 
            if self.audio_output: self.audio_output.setMuted(False)
            
            was_playing = (self.player.playbackState() == QMediaPlayer.PlayingState)
            
            self.player.pause()
            self.player.setPlaybackRate(new_rate)
            
            if not is_at_end:
                self.player.play()
            else:
                self.player_state_changed.emit(QMediaPlayer.PausedState)

        else:
            if self.audio_output: self.audio_output.setMuted(True)
            self.player.pause()
            self.player.setPlaybackRate(1.0) 
            if not self.reverse_timer.isActive():
                self.reverse_timer.start()

    def _check_position_for_end(self, pos):
        if not self.player: return
        if isinstance(self.player, ImagePlayer): return

        duration = self.player.duration()
        if duration <= 0: return

        remaining = duration - pos
        if 0 < remaining < 2000 and self._logical_rate > 1.0:
            self._logical_rate = 1.0
            self.player.setPlaybackRate(1.0)

        if pos >= duration and self.player.playbackState() == QMediaPlayer.PlayingState:
            self._on_media_status_changed(QMediaPlayer.EndOfMedia)

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.reverse_timer.stop()
            self._logical_rate = 1.0
            if isinstance(self.player, QMediaPlayer) or isinstance(self.player, ImagePlayer):
                self.player.setPlaybackRate(1.0)
            
            self.player.pause()
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
        if not self.player: return

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
        
        is_at_end = (abs(duration - current_pos) < 50) or \
                    (isinstance(self.player, QMediaPlayer) and self.player.mediaStatus() == QMediaPlayer.EndOfMedia)
        
        if is_at_end:
            self.player_state_changed.emit(QMediaPlayer.PausedState)
            return

        if self.audio_output:
            self.audio_output.setMuted(False)
        self._logical_rate = 1.0
        if isinstance(self.player, ImagePlayer):
            self.player.setPlaybackRate(1.0)

        self.player.play()
        self.player_state_changed.emit(QMediaPlayer.PlayingState)