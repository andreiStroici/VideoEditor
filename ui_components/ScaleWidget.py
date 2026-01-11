from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QDoubleSpinBox, QCheckBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

class ScaleWidget(QWidget):
    value_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Scale")
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

        self.spin_scale_x = QDoubleSpinBox()
        self.spin_scale_x.setRange(0.1, 10.0)
        self.spin_scale_x.setSingleStep(0.1)
        self.spin_scale_x.setValue(1.0)
        self.spin_scale_x.valueChanged.connect(lambda v: self.value_changed.emit())
        form.addRow("Scale X:", self.spin_scale_x)

        self.spin_scale_y = QDoubleSpinBox()
        self.spin_scale_y.setRange(0.1, 10.0)
        self.spin_scale_y.setSingleStep(0.1)
        self.spin_scale_y.setValue(1.0)
        self.spin_scale_y.valueChanged.connect(lambda v: self.value_changed.emit())
        form.addRow("Scale Y:", self.spin_scale_y)
        
        group = QGroupBox("Scale Settings")
        group.setLayout(form)
        layout.addWidget(group)

    def get_data(self):
        return {
            'enabled': self.enable_cb.isChecked(),
            'Scale x': self.spin_scale_x.value(),
            'Scale y': self.spin_scale_y.value()
        }

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            self.spin_scale_x.setValue(1.0)
            self.spin_scale_y.setValue(1.0)
            return
        self.enable_cb.setChecked(data.get('enabled', False))
        self.spin_scale_x.setValue(data.get('Scale x', 1.0))
        self.spin_scale_y.setValue(data.get('Scale y', 1.0))