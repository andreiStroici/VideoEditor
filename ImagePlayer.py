from PySide6.QtCore import Signal, QTimer, QObject
from PySide6.QtMultimedia import QMediaPlayer

class ImagePlayer(QObject):
    positionChanged = Signal(int)
    durationChanged = Signal(int)
    playbackStateChanged = Signal(QMediaPlayer.PlaybackState)
    mediaStatusChanged = Signal(QMediaPlayer.MediaStatus)

    def __init__(self, duration_ms=5000, parent=None):
        super().__init__(parent)
        self._duration = duration_ms
        self._position = 0
        self._state = QMediaPlayer.StoppedState
        self._playback_rate = 1.0  # Viteză implicită
        
        self.timer = QTimer(self)
        self.timer.setInterval(33) # ~30 FPS
        self.timer.timeout.connect(self._on_tick)

    def play(self):
        self._state = QMediaPlayer.PlayingState
        self.timer.start()
        self.playbackStateChanged.emit(self._state)

    def pause(self):
        self._state = QMediaPlayer.PausedState
        self.timer.stop()
        self.playbackStateChanged.emit(self._state)

    def stop(self):
        self._state = QMediaPlayer.StoppedState
        self.timer.stop()
        self._position = 0
        self.positionChanged.emit(0)
        self.playbackStateChanged.emit(self._state)

    def setPosition(self, position):
        self._position = max(0, min(position, self._duration))
        self.positionChanged.emit(self._position)
        
        if self._position >= self._duration:
            if self._state == QMediaPlayer.PlayingState:
                self.pause()
            self.mediaStatusChanged.emit(QMediaPlayer.EndOfMedia)

    def position(self):
        return self._position

    def duration(self):
        return self._duration

    def playbackState(self):
        return self._state
    
    def mediaStatus(self):
        if self._position >= self._duration:
            return QMediaPlayer.EndOfMedia
        return QMediaPlayer.LoadedMedia

    def setPlaybackRate(self, rate):
        self._playback_rate = rate

    def playbackRate(self):
        return self._playback_rate

    def _on_tick(self):
        step = int(33 * self._playback_rate)
        
        self._position += step
        
        if self._position >= self._duration:
            self._position = self._duration
            self.pause() # Stop la final
            self.positionChanged.emit(self._position)
            self.mediaStatusChanged.emit(QMediaPlayer.EndOfMedia)
        else:
            self.positionChanged.emit(self._position)
            
    def setSource(self, source):
        pass