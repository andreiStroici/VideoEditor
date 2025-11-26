import sys
import os
import hashlib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget, QTabBar, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, QSize , Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
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
        

    def _setup_placeholder_view(self):
        self.visual_label = QLabel("Necunoscut")
        self.visual_label.setAlignment(Qt.AlignCenter)
        self.visual_label.setStyleSheet("background-color: yellow; color: black;")
        self.visual_label.setMinimumSize(QSize(100, 100)) 
        self.visual_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.visual_label)
        
        self.display_pixmap = self._get_black_placeholder()
        self.visual_label.setPixmap(self.display_pixmap)
