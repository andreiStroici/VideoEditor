from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QDoubleSpinBox, QCheckBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

class NoiseReductionWidget(QWidget):
    value_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Noise Reduction")
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

        self.strength_spin = QDoubleSpinBox()
        self.strength_spin.setRange(0.0, 30.0) 
        self.strength_spin.setSingleStep(0.5)
        self.strength_spin.setDecimals(2)
        self.strength_spin.setValue(4.0) 
        self.strength_spin.valueChanged.connect(lambda: self.value_changed.emit())
 
        method_info = QLabel("hqdn3d (Standard)")
        method_info.setStyleSheet("color: #555; font-style: italic;")

        form.addRow("Strength:", self.strength_spin)
        form.addRow("Method:", method_info)
        
        group = QGroupBox("Denoise Settings")
        group.setLayout(form)
        layout.addWidget(group)

    def get_data(self):
        return {
            'enabled': self.enable_cb.isChecked(),
            'Strength': self.strength_spin.value(),
            'Method': 'hqdn3d'
        }

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            self.strength_spin.setValue(4.0)
            return
        self.enable_cb.setChecked(data.get('enabled', False))
        self.strength_spin.setValue(float(data.get('Strength', 4.0)))