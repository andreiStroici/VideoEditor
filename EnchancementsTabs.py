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
        RotateWidget,
        ScaleWidget,
        TransposeWidget,
        FadeInOutWidget,
        TextOperationWidget,
        TempoWidget,
        KernelFilteringWidget,
        EdgeDetectWidget,
        BlurWidget,
        VolumeWidget,
        NoiseReductionWidget,
        OverlayWidget,
        BlendWidget,
        EchoWidget,
        DelayWidget,
        ChorusWidget
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
        self.scale_ui = ScaleWidget()
        self.transpose_ui = TransposeWidget()
        
        trans_layout.addWidget(self.fps_ui)
        trans_layout.addWidget(self.speed_ui)
        trans_layout.addWidget(self.crop_ui)
        trans_layout.addWidget(self.padding_ui)
        trans_layout.addWidget(self.rotate_ui)
        trans_layout.addWidget(self.scale_ui)
        trans_layout.addWidget(self.transpose_ui)
        trans_layout.addStretch()

        scroll.setWidget(scroll_content)
        tab_layout = QVBoxLayout(self.transforms_tab)
        tab_layout.addWidget(scroll)
        
        self.tabs.addTab(self.transforms_tab, "Transforms")
        self.filters_tab = QWidget()
        filters_scroll = QScrollArea()
        filters_scroll.setWidgetResizable(True)
        filters_scroll_content = QWidget()
        self.filters_layout = QVBoxLayout(filters_scroll_content)
        self.tempo_ui = TempoWidget()
        self.kernel_ui = KernelFilteringWidget()
        self.edge_ui = EdgeDetectWidget()
        self.blur_ui = BlurWidget()
        self.volume_ui = VolumeWidget()
        self.noise_ui = NoiseReductionWidget()

        self.filters_layout.addWidget(self.tempo_ui)
        self.filters_layout.addWidget(self.kernel_ui)
        self.filters_layout.addWidget(self.edge_ui)
        self.filters_layout.addWidget(self.blur_ui)
        self.filters_layout.addWidget(self.volume_ui)
        self.filters_layout.addWidget(self.noise_ui)
        self.filters_layout.addStretch()
        filters_scroll.setWidget(filters_scroll_content)
        filters_tab_layout = QVBoxLayout(self.filters_tab)
        filters_tab_layout.setContentsMargins(0, 0, 0, 0)
        filters_tab_layout.addWidget(filters_scroll)
        
        self.tabs.addTab(self.filters_tab, "Filters")

        self.tabs.addTab(QWidget(), "Timing")
        self.tabs.addTab(QWidget(), "Text")
        
        self.composition_tab = QWidget()
        comp_scroll = QScrollArea()
        comp_scroll.setWidgetResizable(True)
        comp_scroll_content = QWidget()
        self.comp_layout = QVBoxLayout(comp_scroll_content)
        
        self.overlay_ui = OverlayWidget()
        self.blend_ui = BlendWidget()
        self.echo_ui = EchoWidget()
        self.delay_ui = DelayWidget()
        self.chorus_ui = ChorusWidget()
        
        self.comp_layout.addWidget(self.overlay_ui)
        self.comp_layout.addWidget(self.blend_ui)
        self.comp_layout.addWidget(self.echo_ui)
        self.comp_layout.addWidget(self.delay_ui)
        self.comp_layout.addWidget(self.chorus_ui)
        self.comp_layout.addStretch()
        
        comp_scroll.setWidget(comp_scroll_content)
        comp_tab_layout = QVBoxLayout(self.composition_tab)
        comp_tab_layout.setContentsMargins(0,0,0,0)
        comp_tab_layout.addWidget(comp_scroll)
        
        self.tabs.addTab(self.composition_tab, "Composition")

        self.timing_layout = QVBoxLayout(self.tabs.widget(2))
        self.fade_ui = FadeInOutWidget()
        self.timing_layout.addWidget(self.fade_ui)
        self.timing_layout.addStretch()

        self.text_layout = QVBoxLayout(self.tabs.widget(3))
        self.text_ui = TextOperationWidget()
        self.text_layout.addWidget(self.text_ui)
        self.text_layout.addStretch()

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

        self.scale_ui.setEnabled(is_visual)
        if not is_visual:
            self.scale_ui.enable_cb.setChecked(False)
            self.scale_ui.status_label.setText("(Not supported for Audio)")
        else:
            self.scale_ui.status_label.setText("")

        self.transpose_ui.setEnabled(is_visual)
        if not is_visual:
            self.transpose_ui.enable_cb.setChecked(False)
            self.transpose_ui.status_label.setText("(Not supported for Audio)")
        else:
            self.transpose_ui.status_label.setText("")

        self.fade_ui.setEnabled(is_video)
        if not is_video:
            self.fade_ui.enable_cb.setChecked(False)
            self.fade_ui.status_label.setText("(Video Only)")
        else:
            self.fade_ui.status_label.setText("")

        self.text_ui.setEnabled(is_video)
        if not is_video:
            self.text_ui.enable_cb.setChecked(False)
            self.text_ui.status_label.setText("(Video Only)")
        else:
            self.text_ui.status_label.setText("")

        self.tempo_ui.setEnabled(is_video)
        if not is_video:
            self.tempo_ui.enable_cb.setChecked(False)
            self.tempo_ui.status_label.setText("(Video Only)")
        else:
            self.tempo_ui.status_label.setText("")

        self.kernel_ui.setEnabled(is_visual)
        if not is_visual:
            self.kernel_ui.enable_cb.setChecked(False)
            self.kernel_ui.status_label.setText("(Visual Only)")
        else:
            self.kernel_ui.status_label.setText("")

        self.edge_ui.setEnabled(is_video)
        if not is_video:
            self.edge_ui.enable_cb.setChecked(False)
            self.edge_ui.status_label.setText("(Video Only)")
        else:
            self.edge_ui.status_label.setText("")

        self.blur_ui.setEnabled(is_video)
        if not is_video:
            self.blur_ui.enable_cb.setChecked(False)
            self.blur_ui.status_label.setText("(Video Only)")
        else:
            self.blur_ui.status_label.setText("")
        
        self.volume_ui.setEnabled(is_time_based)
        if not is_time_based:
            self.volume_ui.enable_cb.setChecked(False)
            self.volume_ui.status_label.setText("(Audio/Video Only)")
        else:
            self.volume_ui.status_label.setText("")

        self.noise_ui.setEnabled(is_video)
        if not is_video:
            self.noise_ui.enable_cb.setChecked(False)
            self.noise_ui.status_label.setText("(Video Only)")
        else:
             self.noise_ui.status_label.setText("")
        
        self.overlay_ui.setEnabled(is_visual)
        if not is_visual:
            self.overlay_ui.enable_cb.setChecked(False)
            self.overlay_ui.status_label.setText("(Visual Only)")
        else:
            self.overlay_ui.status_label.setText("")
            
        self.blend_ui.setEnabled(is_visual)
        if not is_visual:
            self.blend_ui.enable_cb.setChecked(False)
            self.blend_ui.status_label.setText("(Visual Only)")
        else:
            self.blend_ui.status_label.setText("")

        self.echo_ui.setEnabled(is_time_based)
        if not is_time_based:
            self.echo_ui.enable_cb.setChecked(False)
            self.echo_ui.status_label.setText("(Audio/Video Only)")
        else:
            self.echo_ui.status_label.setText("")

        self.delay_ui.setEnabled(is_time_based)
        self.chorus_ui.setEnabled(is_time_based)
        
        if not is_time_based:
            self.delay_ui.enable_cb.setChecked(False)
            self.delay_ui.status_label.setText("(Audio/Video Only)")
            self.chorus_ui.enable_cb.setChecked(False)
            self.chorus_ui.status_label.setText("(Audio/Video Only)")
        else:
            self.delay_ui.status_label.setText("")
            self.chorus_ui.status_label.setText("")

        overlays_list = clip_data.get('available_overlays', [])
        self.overlay_ui.update_overlay_list(overlays_list)
        self.blend_ui.update_blend_list(overlays_list)

        filters = clip_data.get('filters', {})
        transforms = filters.get('Transforms', {}).get('Video', {})
        timing_filters = filters.get('Timing', {}).get('Video', {})
        text_ops = filters.get('Text operation', {}).get('Video', {})
        filters_ops = filters.get('Filters', {}).get('Video', {})
        comp_ops = filters.get('Composition', {}).get('Video', {})
        comp_audio_ops = filters.get('Composition', {}).get('Audio', {})

        self.fps_ui.set_data(transforms.get('Change FPS', {}))
        self.speed_ui.set_data(transforms.get('Playback speed', {}))
        self.crop_ui.set_data(transforms.get('Crop', {}), clip_data.get('resolution', (0,0)))
        self.padding_ui.set_data(transforms.get('Padding', {}))
        self.rotate_ui.set_data(transforms.get('Rotate', {}))
        self.scale_ui.set_data(transforms.get('Scale', {}))
        self.transpose_ui.set_data(transforms.get('Transpose', {}))
        self.fade_ui.set_data(timing_filters.get('Fade in', {}))
        self.text_ui.set_data(text_ops.get('Text', {}))
        self.tempo_ui.set_data(filters_ops.get('Tempo', {}))
        self.kernel_ui.set_data(filters_ops.get('Kernel Filtering', {}))
        self.edge_ui.set_data(filters_ops.get('Edge Detect', {}))
        self.blur_ui.set_data(filters_ops.get('Blur', {}))
        self.volume_ui.set_data(filters_ops.get('Volume', {}))
        self.noise_ui.set_data(filters_ops.get('Noise Reduction', {}))
        self.overlay_ui.set_data(comp_ops.get('Overlay', {}))
        self.blend_ui.set_data(comp_ops.get('Blend videos', {}))
        self.echo_ui.set_data(comp_audio_ops.get('Echo', {}))
        self.delay_ui.set_data(comp_audio_ops.get('Delay', {}))
        self.chorus_ui.set_data(comp_audio_ops.get('Chorus', {}))

    def _on_apply(self):
        crop_values = self.crop_ui.get_data()
        fps_values = self.fps_ui.get_data()
        padding_values = self.padding_ui.get_data()
        speed_values = self.speed_ui.get_data()
        rotate_values = self.rotate_ui.get_data()
        scale_values = self.scale_ui.get_data()
        transpose_values = self.transpose_ui.get_data()
        fade_values = self.fade_ui.get_data()
        text_values = self.text_ui.get_data()
        tempo_values = self.tempo_ui.get_data()
        kernel_values = self.kernel_ui.get_data()
        edge_values = self.edge_ui.get_data()
        blur_values = self.blur_ui.get_data()
        volume_values = self.volume_ui.get_data()
        noise_values = self.noise_ui.get_data()
        overlay_values = self.overlay_ui.get_data()
        blend_values = self.blend_ui.get_data()
        echo_values = self.echo_ui.get_data()
        delay_values = self.delay_ui.get_data()
        chorus_values = self.chorus_ui.get_data()

        filter_stack = {
            'Transforms': {
                'Video': {
                    'Change FPS': fps_values,
                    'Playback speed': speed_values,
                    'Crop': crop_values,
                    'Padding': padding_values,
                    'Rotate': rotate_values,
                    'Scale': scale_values,
                    'Transpose': transpose_values
                }
            },
            'Timing': {
                'Video': {
                    'Fade in': fade_values
                }
            },
            'Text operation': {
                'Video': {
                    'Text': text_values
                }
            },
            'Filters': {
                'Video': {
                    'Tempo': tempo_values,
                    'Kernel Filtering': kernel_values,
                    'Edge Detect': edge_values,
                    'Blur': blur_values,
                    'Volume': volume_values,
                    'Noise Reduction': noise_values
                }
            },
            'Composition': {
                'Video': {
                    'Overlay': overlay_values,
                    'Blend videos': blend_values
                },
                'Audio': {
                    'Echo': echo_values,
                    'Delay': delay_values,
                    'Chorus': chorus_values
                }
            }
        }
        self.apply_filters_signal.emit(filter_stack)