from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QComboBox, QCheckBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

class TransposeWidget(QWidget):
    value_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Transpose")
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

        self.mode_combo = QComboBox()
        modes = ["clock", "cclock", "clock_flip", "cclock_flip", "hflip", "vflip"]
        self.mode_combo.addItems(modes)
        self.mode_combo.currentIndexChanged.connect(lambda i: self.value_changed.emit())
        
        form.addRow("Mode:", self.mode_combo)
        
        group = QGroupBox("Transpose Settings")
        group.setLayout(form)
        layout.addWidget(group)

    def get_data(self):
        return {
            'enabled': self.enable_cb.isChecked(),
            'Mode': self.mode_combo.currentText()
        }

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            self.mode_combo.setCurrentText("clock")
            return
        self.enable_cb.setChecked(data.get('enabled', False))
        self.mode_combo.setCurrentText(data.get('Mode', 'clock'))