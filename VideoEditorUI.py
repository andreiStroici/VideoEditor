import sys
import os



from PySide6.QtWidgets import QGridLayout,QWidget,QApplication
from PySide6.QtCore import Qt,QSize
from Toolbar import Toolbar
from MediaTabs import MediaTabs
from VideoPreview import VideoPreview
from EnchancementsTabs import EnchancementsTabs
from TimelineAndTracks  import TimelineAndTracks


class VideoEditorUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Editor")
        self.showMaximized()

        SPACING = 8   # regula: multiplu de 8px peste tot

        main = QGridLayout(self)
        main.setSpacing(SPACING*2)
        main.setContentsMargins(SPACING, SPACING, SPACING, SPACING)

       
        self.toolbar = Toolbar(SPACING)
        self.media_tabs = MediaTabs(SPACING)
        self.video_preview = VideoPreview(SPACING) 
        self.enchancements_tabs = EnchancementsTabs(SPACING)
        self.timeline_container = TimelineAndTracks(SPACING)

        main.addWidget(self.toolbar, 0, 0, 1, 2)
        main.addWidget(self.media_tabs, 1, 0)
        main.addWidget(self.video_preview, 1, 1)
        main.addWidget(self.enchancements_tabs, 2, 0)
        main.addWidget(self.timeline_container, 2, 1)
        
        # Stretching / proportions
        main.setRowStretch(1, 2)
        main.setRowStretch(2, 1)

        main.setColumnStretch(0, 2)
        main.setColumnStretch(1, 5)

        self.toolbar.files_selected.connect(self.media_tabs.add_files)
        self.toolbar.folder_selected.connect(self.media_tabs.add_folder)

        self.media_tabs.file_double_clicked.connect(self.video_preview.add_media_tab)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = VideoEditorUI()
    editor.show()
    sys.exit(app.exec())


#source envPIU/bin/activate
#python VideoEditorUI.py
#ps aux | grep python.
#kill -9 24847 