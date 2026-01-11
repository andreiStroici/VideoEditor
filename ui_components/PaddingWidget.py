from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QSpinBox, QCheckBox, QHBoxLayout, QComboBox
)
from PySide6.QtCore import Qt, Signal

class PaddingWidget(QWidget):
    value_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Padding")
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

        self.spin_top = self._create_spinbox()
        form.addRow("Top:", self.spin_top)
        self.spin_bottom = self._create_spinbox()
        form.addRow("Bottom:", self.spin_bottom)
        self.spin_left = self._create_spinbox()
        form.addRow("Left:", self.spin_left)
        self.spin_right = self._create_spinbox()
        form.addRow("Right:", self.spin_right)

        self.color_combo = QComboBox()
        self.color_combo.addItems(["black", "white", "red", "green", "blue", "transparent"])
        self.color_combo.currentIndexChanged.connect(lambda i: self.value_changed.emit())
        form.addRow("Color:", self.color_combo)

        group = QGroupBox("Padding Settings")
        group.setLayout(form)
        layout.addWidget(group)

    def _create_spinbox(self):
        sb = QSpinBox()
        sb.setRange(0, 5000)
        sb.setSuffix(" px")
        sb.valueChanged.connect(lambda v: self.value_changed.emit())
        return sb

    def get_data(self):
        return {
            'enabled': self.enable_cb.isChecked(),
            'Top': self.spin_top.value(),
            'Bottom': self.spin_bottom.value(),
            'Left': self.spin_left.value(),
            'Right': self.spin_right.value(),
            'Color': self.color_combo.currentText()
        }

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            self.spin_top.setValue(0)
            self.spin_bottom.setValue(0)
            self.spin_left.setValue(0)
            self.spin_right.setValue(0)
            self.color_combo.setCurrentText("black")
            return
        self.enable_cb.setChecked(data.get('enabled', False))
        self.spin_top.setValue(data.get('Top', 0))
        self.spin_bottom.setValue(data.get('Bottom', 0))
        self.spin_left.setValue(data.get('Left', 0))
        self.spin_right.setValue(data.get('Right', 0))
        self.color_combo.setCurrentText(data.get('Color', 'black'))