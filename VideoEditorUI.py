import sys
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

       
        toolbar=Toolbar(SPACING)
        media_tabs=MediaTabs(SPACING)
        video_preview=VideoPreview(SPACING)
        enchancements_tabs=EnchancementsTabs(SPACING)
        timeline_container=TimelineAndTracks(SPACING)

        main.addWidget(toolbar, 0, 0, 1, 2)     
        main.addWidget(media_tabs, 1, 0)
        main.addWidget(video_preview,1,1)
        main.addWidget(enchancements_tabs, 2, 0)
        main.addWidget(timeline_container, 2, 1)
        
        # Stretching / proportions
        main.setRowStretch(1, 3)
        main.setRowStretch(2, 2)

        main.setColumnStretch(0, 1)
        main.setColumnStretch(1, 2)

        #conections
        #toolbar to media tab for open files/folder
        toolbar.files_selected.connect(media_tabs.add_files)
        toolbar.folder_selected.connect(media_tabs.add_folder)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = VideoEditorUI()
    editor.show()
    sys.exit(app.exec())


#source envPIU/bin/activate
#python VideoEditorUI.py
#ps aux | grep python.
#kill -9 24847 