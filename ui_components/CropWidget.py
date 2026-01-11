from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QSpinBox, QCheckBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

class CropWidget(QWidget):
    value_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Crop")
        self.enable_cb.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.enable_cb.setChecked(False)
        self.enable_cb.toggled.connect(lambda c: self.value_changed.emit())
        
        self.res_label = QLabel("Source: Unknown")
        self.res_label.setStyleSheet("color: gray; font-size: 11px;")
        self.status_label = self.res_label
        
        top_row.addWidget(self.enable_cb)
        top_row.addStretch()
        top_row.addWidget(self.res_label)
        layout.addLayout(top_row)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 9999)
        self.spin_x.setSuffix(" px")
        self.spin_x.valueChanged.connect(lambda: self.value_changed.emit())
        form.addRow("X:", self.spin_x)

        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 9999)
        self.spin_y.setSuffix(" px")
        self.spin_y.valueChanged.connect(lambda: self.value_changed.emit())
        form.addRow("Y:", self.spin_y)

        self.spin_w = QSpinBox()
        self.spin_w.setRange(1, 9999)
        self.spin_w.setSuffix(" px")
        self.spin_w.setValue(1920) 
        self.spin_w.valueChanged.connect(lambda: self.value_changed.emit())
        form.addRow("Width:", self.spin_w)

        self.spin_h = QSpinBox()
        self.spin_h.setRange(1, 9999)
        self.spin_h.setSuffix(" px")
        self.spin_h.setValue(1080) 
        self.spin_h.valueChanged.connect(lambda: self.value_changed.emit())
        form.addRow("Height:", self.spin_h)

        group = QGroupBox("Crop Settings")
        group.setLayout(form)
        layout.addWidget(group)

    def get_data(self):
        return {
            'enabled': self.enable_cb.isChecked(),
            'X': self.spin_x.value(),
            'Y': self.spin_y.value(),
            'Width': self.spin_w.value(),
            'Height': self.spin_h.value()
        }

    def set_data(self, data, original_res=(0,0)):
        w, h = original_res
        
        max_w = w if w > 0 else 10000
        max_h = h if h > 0 else 10000
        
        self.spin_x.setMaximum(max_w)
        self.spin_y.setMaximum(max_h)
        self.spin_w.setMaximum(max_w)
        self.spin_h.setMaximum(max_h)

        if w > 0 and h > 0:
            self.res_label.setText(f"Source: {w}x{h}")
        else:
            self.res_label.setText("Source: Unknown")

        if not data: 
            self.enable_cb.setChecked(False)
            self.spin_x.setValue(0)
            self.spin_y.setValue(0)
            self.spin_w.setValue(max_w if w > 0 else 1920)
            self.spin_h.setValue(max_h if h > 0 else 1080)
            return

        self.enable_cb.setChecked(data.get('enabled', False))
        self.spin_x.setValue(int(data.get('X', 0)))
        self.spin_y.setValue(int(data.get('Y', 0)))

        saved_w = int(data.get('Width', 0))
        saved_h = int(data.get('Height', 0))
        
        final_w = saved_w if 0 < saved_w <= max_w else max_w
        final_h = saved_h if 0 < saved_h <= max_h else max_h
        
        self.spin_w.setValue(final_w)
        self.spin_h.setValue(final_h)