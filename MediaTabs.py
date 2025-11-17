import os
from PySide6.QtWidgets import QWidget, QTabWidget, QListWidget, QVBoxLayout, QListWidgetItem, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap


class MediaTabs(QWidget):
    SUPPORTED_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
    SUPPORTED_VIDEO_EXT = {'.mp4', '.mov', '.avi', '.mkv'}
    SUPPORTED_AUDIO_EXT = {'.mp3', '.wav', '.flac'}

    def __init__(self, SPACING, parent=None):
        super().__init__(parent)

        # initial setup
        base_dir = os.path.dirname(__file__)
        self.thumb_dir = os.path.join(base_dir, "video_thumbnails_cache")
        os.makedirs(self.thumb_dir, exist_ok=True)

        self._existing = set()  # evitarea duplicatelor
        self._all_files = []    # pentru ordonare si sortare

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.media_tabs = QTabWidget()
        self.media_tabs.setContentsMargins(0, 0, 0, 0)

        self.show_all_tab_list = QListWidget()
        self._setup_media_grid(self.show_all_tab_list, SPACING)

        self.video_list = QListWidget()
        self._setup_media_grid(self.video_list, SPACING)

        self.audio_list = QListWidget()
        self._setup_media_grid(self.audio_list, SPACING)

        # self.picture_list = QListWidget() # good for functionality but bad for symmetry?

        self.media_tabs.addTab(self.show_all_tab_list, "Show All")
        self.media_tabs.addTab(self.video_list, "Video")
        self.media_tabs.addTab(self.audio_list, "Audio")

        layout.addWidget(self.media_tabs)

    def _setup_media_grid(self, file_list, SPACING):
        file_list.setViewMode(QListWidget.IconMode)  # grid mode
        file_list.setResizeMode(QListWidget.Adjust)
        file_list.setIconSize(QSize(160, 90))  # aspect ratio 16:9
        file_list.setGridSize(QSize(180, 130))
        file_list.setMovement(QListWidget.Static)
        file_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        file_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        file_list.setSpacing(SPACING)
        file_list.setWordWrap(False)
        file_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        file_list.resizeEvent = self._on_resize

    def _on_resize(self, event):
        self._update_grid_size()
        QListWidget.resizeEvent(self.show_all_tab_list, event)

    def _update_grid_size(self):
        """Adjust grid width so items are centered horizontally."""
        count = self.show_all_tab_list.count()
        if count == 0:
            return
        list_width = self.show_all_tab_list.viewport().width()
        icon_width = self.show_all_tab_list.iconSize().width()
        spacing = self.show_all_tab_list.spacing()

        items_per_row = max(1, list_width // (icon_width + spacing))
        extra_space = list_width - (items_per_row * icon_width)
        if items_per_row > 1:
            dynamic_spacing = extra_space // (items_per_row + 1)
        else:
            dynamic_spacing = extra_space // 2

        self.show_all_tab_list.setGridSize(
            QSize(icon_width + dynamic_spacing, self.show_all_tab_list.gridSize().height())
        )

    def _generate_video_thumbnail(self, path):
        base = os.path.basename(path)
        name, _ = os.path.splitext(base)
        out_thumb = os.path.join(self.thumb_dir, f"{name}_thumb.jpg")

        # Use cached file if already generated
        if os.path.exists(out_thumb):
            return out_thumb

        # FFmpeg command: extract first good frame and scale to 160x90
        cmd = (
        f'ffmpeg -y -i "{path}" '
        f'-vf "thumbnail,scale=160:90:force_original_aspect_ratio=decrease" '
        f'-frames:v 1 -update 1 "{out_thumb}"'
        )

        os.system(cmd)

        if os.path.exists(out_thumb):
            return out_thumb
        return None

    def _make_icon_for_file(self, path, ext):
        try:
            if ext in self.SUPPORTED_IMAGE_EXT:
                pix = QPixmap(path)
                if not pix.isNull():
                    thumb = pix.scaled(
                        160, 90, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                    )
                    return QIcon(thumb)

            if ext in self.SUPPORTED_AUDIO_EXT:
                return QIcon("icons/audio_file.png") if os.path.exists("icons/audio_file.png") else QIcon()

            if ext in self.SUPPORTED_VIDEO_EXT:
                thumb = self._generate_video_thumbnail(path)
                if thumb and os.path.exists(thumb):
                    pix = QPixmap(thumb)
                    if not pix.isNull():
                        return QIcon(pix)
                # fallback icon
                return QIcon("icons/video_file.png") if os.path.exists("icons/video_file.png") else QIcon()
        except Exception:
            pass

        return QIcon("icons/generic_file.png") if os.path.exists("icons/generic_file.png") else QIcon()

    def _refresh_list(self):
        self.show_all_tab_list.clear()
        self.video_list.clear()
        self.audio_list.clear()

        for filePath in self._all_files:
            ext = os.path.splitext(filePath)[1].lower()
            icon = self._make_icon_for_file(filePath, ext)
            base_name = os.path.basename(filePath)
            display_name = base_name if len(base_name) <= 20 else (base_name[:15] + "...")

            item = QListWidgetItem(icon, display_name)
            item.setToolTip(filePath)
            item.setData(Qt.UserRole, filePath)
            item.setTextAlignment(Qt.AlignCenter)

            self.show_all_tab_list.addItem(item)

            if ext in self.SUPPORTED_AUDIO_EXT:
                self.audio_list.addItem(QListWidgetItem(icon, display_name))
            elif ext in self.SUPPORTED_VIDEO_EXT:
                self.video_list.addItem(QListWidgetItem(icon, display_name))

        self._update_grid_size()

    def add_files(self, paths: list):
        added = 0
        for p in paths:
            p = os.path.abspath(p)
            if p in self._existing or not os.path.isfile(p):
                continue
            self._existing.add(p)
            self._all_files.insert(0, p)
            added += 1
        self._refresh_list()
        return added

    def add_folder(self, folder_path: str):
        if not os.path.isdir(folder_path):
            return 0

        exts = self.SUPPORTED_AUDIO_EXT | self.SUPPORTED_IMAGE_EXT | self.SUPPORTED_VIDEO_EXT
        found = []

        for entry in os.listdir(folder_path):
            fullPath = os.path.join(folder_path, entry)
            if os.path.isfile(fullPath) and os.path.splitext(fullPath)[1].lower() in exts:
                found.append(fullPath)

        return self.add_files(found)
