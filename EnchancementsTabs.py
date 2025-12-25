import sys
from PySide6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QScrollArea, QLabel, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

try:
    from ui_components import (
        CropWidget, 
        ChangeFPSWidget, 
        PaddingWidget, 
        PlaybackSpeedWidget,
        RotateWidget
    )
except ImportError as e:
    print(f"Error importing UI components: {e}")


class EnchancementsTabs(QWidget):
    apply_filters_signal = Signal(dict)

    def __init__(self, SPACING, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(5, 5, 5, 5)
        self.info_lbl = QLabel("No clip selected")
        self.info_lbl.setStyleSheet("font-style: italic; color: #666;")
        
        self.apply_btn = QPushButton("Apply Effects")
        self.apply_btn.setStyleSheet("background-color: #3a6ea5; color: white; padding: 6px; font-weight: bold;")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._on_apply)
        
        top_bar.addWidget(self.info_lbl)
        top_bar.addStretch()
        top_bar.addWidget(self.apply_btn)
        layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        

        self.transforms_tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        trans_layout = QVBoxLayout(scroll_content)
        
        self.fps_ui = ChangeFPSWidget()
        self.speed_ui = PlaybackSpeedWidget()
        self.crop_ui = CropWidget()
        self.padding_ui = PaddingWidget()
        self.rotate_ui = RotateWidget()
        
        trans_layout.addWidget(self.fps_ui)
        trans_layout.addWidget(self.speed_ui)
        trans_layout.addWidget(self.crop_ui)
        trans_layout.addWidget(self.padding_ui)
        trans_layout.addWidget(self.rotate_ui)
        trans_layout.addStretch()

        scroll.setWidget(scroll_content)
        tab_layout = QVBoxLayout(self.transforms_tab)
        tab_layout.addWidget(scroll)
        
        self.tabs.addTab(self.transforms_tab, "Transforms")
        self.tabs.addTab(QWidget(), "Filters")
        self.tabs.addTab(QWidget(), "Timing")
        self.tabs.addTab(QWidget(), "Text")
        self.tabs.addTab(QWidget(), "Composition")

        layout.addWidget(self.tabs)
        self.tabs.setEnabled(False)
        self.current_clip_data = None

    def load_clip_data(self, clip_data):
        self.current_clip_data = clip_data
        
        if not clip_data:
            self.tabs.setEnabled(False)
            self.apply_btn.setEnabled(False)
            self.info_lbl.setText("No clip selected")
            return

        self.tabs.setEnabled(True)
        self.apply_btn.setEnabled(True)
        
        full_name = clip_data.get('name', 'Unknown')
        display_name = full_name[:25] + "..." if len(full_name) > 25 else full_name
        self.info_lbl.setText(f"Editing: {display_name}")
        self.info_lbl.setToolTip(full_name)

        media_type = clip_data.get('media_type', 'video')
        
        is_audio = (media_type == 'audio')
        is_video = (media_type == 'video')
        is_visual = (media_type == 'video' or media_type == 'image')
        is_time_based = (media_type == 'video' or media_type == 'audio')
        

        self.fps_ui.setEnabled(is_video)
        if not is_video:
            self.fps_ui.enable_cb.setChecked(False)
            reason = "(Not supported for Audio)" if is_audio else "(Not supported for Images)"
            self.fps_ui.status_label.setText(reason)
        else:
            self.fps_ui.status_label.setText("")

        self.speed_ui.setEnabled(is_time_based)
        if not is_time_based:
            self.speed_ui.enable_cb.setChecked(False)
            self.speed_ui.status_label.setText("(Not supported for Images)")
        else:
            self.speed_ui.status_label.setText("")

        self.crop_ui.setEnabled(is_visual)
        if not is_visual:
             self.crop_ui.enable_cb.setChecked(False)

        self.padding_ui.setEnabled(is_visual)
        if not is_visual:
            self.padding_ui.enable_cb.setChecked(False)
            self.padding_ui.status_label.setText("(Not supported for Audio)")
        else:
            self.padding_ui.status_label.setText("")

        self.rotate_ui.setEnabled(is_visual)
        if not is_visual:
            self.rotate_ui.enable_cb.setChecked(False)
            self.rotate_ui.status_label.setText("(Not supported for Audio)")
        else:
            self.rotate_ui.status_label.setText("")

        filters = clip_data.get('filters', {})
        transforms = filters.get('Transforms', {}).get('Video', {})
        
        self.fps_ui.set_data(transforms.get('Change FPS', {}))
        self.speed_ui.set_data(transforms.get('Playback speed', {}))
        self.crop_ui.set_data(transforms.get('Crop', {}), clip_data.get('resolution', (0,0)))
        self.padding_ui.set_data(transforms.get('Padding', {}))
        self.rotate_ui.set_data(transforms.get('Rotate', {}))

    def _on_apply(self):
        crop_values = self.crop_ui.get_data()
        fps_values = self.fps_ui.get_data()
        padding_values = self.padding_ui.get_data()
        speed_values = self.speed_ui.get_data()
        rotate_values = self.rotate_ui.get_data()
        
        filter_stack = {
            'Transforms': {
                'Video': {
                    'Change FPS': fps_values,
                    'Playback speed': speed_values,
                    'Crop': crop_values,
                    'Padding': padding_values,
                    'Rotate': rotate_values
                }
            }
        }
        self.apply_filters_signal.emit(filter_stack)