from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox, QHBoxLayout
from PySide6.QtCore import Qt, Signal

class DelayWidget(QWidget):
    value_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Delay")
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

        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 5000)
        self.delay_spin.setSingleStep(50)
        self.delay_spin.setValue(500)
        self.delay_spin.setSuffix(" ms")
        self.delay_spin.valueChanged.connect(lambda: self.value_changed.emit())

        self.mix_spin = QDoubleSpinBox()
        self.mix_spin.setRange(0.0, 1.0)
        self.mix_spin.setSingleStep(0.1)
        self.mix_spin.setValue(0.5)
        self.mix_spin.valueChanged.connect(lambda: self.value_changed.emit())
        
        form.addRow("Delay Time:", self.delay_spin)
        form.addRow("Mix:", self.mix_spin)
        
        group = QGroupBox("Delay (Audio)")
        group.setLayout(form)
        layout.addWidget(group)

    def get_data(self):
        return {'enabled': self.enable_cb.isChecked(), 'Delay': self.delay_spin.value(), 'Mix': self.mix_spin.value()}

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            self.delay_spin.setValue(500)
            self.mix_spin.setValue(0.5)
            return
        self.enable_cb.setChecked(data.get('enabled', False))
        self.delay_spin.setValue(int(data.get('Delay', 500)))
        self.mix_spin.setValue(float(data.get('Mix', 0.5)))