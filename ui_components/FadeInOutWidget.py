from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QSpinBox, QCheckBox, QHBoxLayout, QComboBox
)
from PySide6.QtCore import Qt, Signal

class FadeInOutWidget(QWidget):
    value_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Fade In/Out")
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

        self.spin_duration = QSpinBox()
        self.spin_duration.setRange(1, 10)
        self.spin_duration.setValue(1)
        self.spin_duration.setSuffix(" sec")
        self.spin_duration.valueChanged.connect(lambda v: self.value_changed.emit())
        form.addRow("Duration:", self.spin_duration)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["in", "out", "both"])
        self.type_combo.setCurrentText("both")
        self.type_combo.currentIndexChanged.connect(lambda i: self.value_changed.emit())
        form.addRow("Type:", self.type_combo)
        
        group = QGroupBox("Fade Settings")
        group.setLayout(form)
        layout.addWidget(group)

    def get_data(self):
        return {
            'enabled': self.enable_cb.isChecked(),
            'Duration': self.spin_duration.value(),
            'Type': self.type_combo.currentText()
        }

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            self.spin_duration.setValue(1)
            self.type_combo.setCurrentText("both")
            return
        self.enable_cb.setChecked(data.get('enabled', False))
        self.spin_duration.setValue(data.get('Duration', 1))
        self.type_combo.setCurrentText(data.get('Type', 'both'))