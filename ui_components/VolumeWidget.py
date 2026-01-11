from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QDoubleSpinBox, QCheckBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

class VolumeWidget(QWidget):
    value_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Volume")
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

        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(-60.0, 30.0)
        self.gain_spin.setSingleStep(0.5)
        self.gain_spin.setValue(0.0)
        self.gain_spin.setSuffix(" dB")
        self.gain_spin.valueChanged.connect(lambda: self.value_changed.emit())
        
        form.addRow("Gain:", self.gain_spin)
        
        group = QGroupBox("Audio Volume")
        group.setLayout(form)
        layout.addWidget(group)

    def get_data(self):
        return {
            'enabled': self.enable_cb.isChecked(),
            'Gain': self.gain_spin.value()
        }

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            self.gain_spin.setValue(0.0)
            return
        self.enable_cb.setChecked(data.get('enabled', False))
        self.gain_spin.setValue(float(data.get('Gain', 0.0)))