from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QDoubleSpinBox, QCheckBox, QHBoxLayout, QComboBox
)
from PySide6.QtCore import Qt, Signal

class EdgeDetectWidget(QWidget):
    value_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Edge Detect")
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

        self.method_combo = QComboBox()
 
        self.method_combo.addItems(["prewitt", "canny"])
        self.method_combo.setCurrentText("canny")

        self.method_combo.currentIndexChanged.connect(lambda i: self.value_changed.emit())
        form.addRow("Method:", self.method_combo)


        self.spin_threshold = QDoubleSpinBox()
        self.spin_threshold.setRange(0.0, 1.0)
        self.spin_threshold.setSingleStep(0.05)
        self.spin_threshold.setValue(0.1)
        self.spin_threshold.valueChanged.connect(lambda v: self.value_changed.emit())
        form.addRow("Threshold:", self.spin_threshold)

        group = QGroupBox("Edge Detection Settings")
        group.setLayout(form)
        layout.addWidget(group)

    def get_data(self):
        return {
            'enabled': self.enable_cb.isChecked(),
            'Method': self.method_combo.currentText(),
            'Threshold': self.spin_threshold.value()
        }

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            self.method_combo.setCurrentText("canny")
            self.spin_threshold.setValue(0.1)
            return

        self.enable_cb.setChecked(data.get('enabled', False))
        
        method = data.get('Method', 'canny')
        if self.method_combo.findText(method) == -1:
             method = "canny"
        self.method_combo.setCurrentText(method)
        
        self.spin_threshold.setValue(data.get('Threshold', 0.1))