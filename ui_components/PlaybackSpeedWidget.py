from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QDoubleSpinBox, QCheckBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

class PlaybackSpeedWidget(QWidget):
    value_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Playback Speed")
        self.enable_cb.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.enable_cb.setChecked(False)
        self.enable_cb.toggled.connect(lambda c: self.value_changed.emit())
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red; font-size: 10px; font-weight: bold;")
        
        top_row.addWidget(self.enable_cb)
        top_row.addStretch()
        top_row.addWidget(self.status_label)
        layout.addLayout(top_row)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.spin_factor = QDoubleSpinBox()
        self.spin_factor.setRange(0.1, 5.0)
        self.spin_factor.setSingleStep(0.1)
        self.spin_factor.setValue(1.0)
        self.spin_factor.setSuffix("x")
        self.spin_factor.valueChanged.connect(lambda v: self.value_changed.emit())
        
        form.addRow("Factor:", self.spin_factor)
        
        group = QGroupBox("Speed Settings")
        group.setLayout(form)
        layout.addWidget(group)

    def get_data(self):
        return {
            'enabled': self.enable_cb.isChecked(),
            'Factor': self.spin_factor.value()
        }

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            self.spin_factor.setValue(1.0)
            return
        self.enable_cb.setChecked(data.get('enabled', False))
        self.spin_factor.setValue(data.get('Factor', 1.0))