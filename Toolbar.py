import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFileDialog
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon

class Toolbar(QWidget):
    files_selected = Signal(list);
    folder_selected = Signal(str);
    def __init__(self,SPACING,parent=None):
        super().__init__()
        self.toolbar = QHBoxLayout(self)
        self.toolbar.setSpacing(SPACING*5)
        self.toolbar.setContentsMargins(0, 0, 0, 0)

        #add file button
        self.add_files_button=QPushButton()
        add_file_icon=QIcon("icons/add_file.png")
        self.add_files_button.setIcon(add_file_icon)
        self.add_files_button.setIconSize(QSize(32,32))
        self.add_files_button.setStyleSheet(self._btn_style())

        #Open Folder Button
        self.open_folder_button=QPushButton()
        open_folder_icon=QIcon("icons/open_folder.png")
        self.open_folder_button.setIcon(open_folder_icon)
        self.open_folder_button.setIconSize(QSize(32,32))
        self.open_folder_button.setStyleSheet(self._btn_style())
        #Save Project Button
        self.save_project_button=QPushButton()
        save_project_icon=QIcon("icons/save_project.png")
        self.save_project_button.setIcon(save_project_icon)
        self.save_project_button.setIconSize(QSize(32,32))
        self.save_project_button.setStyleSheet(self._btn_style())
        #Undo Button
        self.undo_button=QPushButton()
        undo_icon=QIcon("icons/undo.png")
        self.undo_button.setIcon(undo_icon)
        self.undo_button.setIconSize(QSize(32,32))
        self.undo_button.setStyleSheet(self._btn_style())
        #Redo Button
        self.redo_button=QPushButton()
        redo_icon=QIcon("icons/redo.png")
        self.redo_button.setIcon(redo_icon)
        self.redo_button.setIconSize(QSize(32,32))
        self.redo_button.setStyleSheet(self._btn_style())
        #Export Project Button
        self.export_project_button=QPushButton()
        export_project_icon=QIcon("icons/export_project.png")
        self.export_project_button.setIcon(export_project_icon)
        self.export_project_button.setIconSize(QSize(32,32))
        self.export_project_button.setStyleSheet(self._btn_style())

        #add all buttons to toolbar
        self.toolbar.addSpacing(SPACING*3)
        self.toolbar.addWidget(self.add_files_button)
        self.toolbar.addWidget(self.open_folder_button)
        self.toolbar.addWidget(self.save_project_button)
        self.toolbar.addWidget(self.undo_button)
        self.toolbar.addWidget(self.redo_button)
        self.toolbar.addWidget(self.export_project_button)
        self.toolbar.addStretch()

        #defined signals conections
        self.add_files_button.clicked.connect(self._on_add_files)
        self.open_folder_button.clicked.connect(self._on_open_folder)


    def _btn_style(self):
            return """
            QPushButton {
                border: none;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
            """
        
    def _on_add_files(self):
            filters = "Media files (*.png *.jpg *.bmp *.gif *.mp4 *.mov *.avi *.mkv *.mp3 *.wav);;All files (*)"
            paths, _ = QFileDialog.getOpenFileNames(self, "Select files", os.path.expanduser("~"), filters)
            if paths:
                self.files_selected.emit(paths)   

    def _on_open_folder(self):
            folder = QFileDialog.getExistingDirectory(self,"Select folder",os.path.expanduser("~"))
            if folder:
                self.folder_selected.emit(folder)    
