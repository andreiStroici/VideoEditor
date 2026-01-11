from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QSpinBox, QCheckBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

class ChangeFPSWidget(QWidget):
    value_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Change FPS")
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

        self.spin_fps = QSpinBox()
        self.spin_fps.setRange(1, 120)
        self.spin_fps.setValue(30)
        self.spin_fps.setSuffix(" fps")
        self.spin_fps.valueChanged.connect(lambda v: self.value_changed.emit())
        
        form.addRow("Target FPS:", self.spin_fps)
        
        group = QGroupBox("Frame Rate Settings")
        group.setLayout(form)
        layout.addWidget(group)

    def get_data(self):
        return {
            'enabled': self.enable_cb.isChecked(),
            'fps': self.spin_fps.value()
        }

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            self.spin_fps.setValue(30)
            return
        self.enable_cb.setChecked(data.get('enabled', False))
        self.spin_fps.setValue(data.get('fps', 30))