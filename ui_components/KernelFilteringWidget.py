from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QDoubleSpinBox, QCheckBox, QHBoxLayout, QGridLayout
)
from PySide6.QtCore import Qt, Signal

class KernelFilteringWidget(QWidget):
    value_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header Row
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Kernel Filtering")
        self.enable_cb.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.enable_cb.setChecked(False)
        self.enable_cb.toggled.connect(lambda c: self.value_changed.emit())
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red; font-size: 10px; font-weight: bold;")
        
        top_row.addWidget(self.enable_cb)
        top_row.addStretch()
        top_row.addWidget(self.status_label)
        layout.addLayout(top_row)

        group = QGroupBox("Kernel Matrix (3x3)")
        group_layout = QVBoxLayout()

        self.grid_layout = QGridLayout()
        self.matrix_inputs = []

        for row in range(3):
            row_inputs = []
            for col in range(3):
                spin = QDoubleSpinBox()
                spin.setRange(-50.0, 50.0)
                spin.setSingleStep(0.1)
                spin.setDecimals(2)
                spin.setAlignment(Qt.AlignCenter)

                if row == 1 and col == 1:
                    spin.setValue(1.0)
                else:
                    spin.setValue(0.0)
                
                spin.valueChanged.connect(lambda v: self.value_changed.emit())
                self.grid_layout.addWidget(spin, row, col)
                row_inputs.append(spin)
            self.matrix_inputs.append(row_inputs)

        group_layout.addLayout(self.grid_layout)

        self.normalize_cb = QCheckBox("Normalize Kernel")
        self.normalize_cb.setChecked(True)
        self.normalize_cb.setToolTip("Divide result by sum of kernel elements")
        self.normalize_cb.toggled.connect(lambda c: self.value_changed.emit())
        group_layout.addWidget(self.normalize_cb)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def get_data(self):
        kernel_matrix = []
        for row_inputs in self.matrix_inputs:
            row_values = [spin.value() for spin in row_inputs]
            kernel_matrix.append(row_values)

        return {
            'enabled': self.enable_cb.isChecked(),
            'Kernel': kernel_matrix,
            'Normalize': self.normalize_cb.isChecked()
        }

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            self.normalize_cb.setChecked(True)
            for r in range(3):
                for c in range(3):
                    self.matrix_inputs[r][c].setValue(1.0 if r==1 and c==1 else 0.0)
            return

        self.enable_cb.setChecked(data.get('enabled', False))
        self.normalize_cb.setChecked(data.get('Normalize', True))
        
        kernel = data.get('Kernel', [])
        if kernel and len(kernel) == 3 and all(len(row) == 3 for row in kernel):
            for r in range(3):
                for c in range(3):
                    self.matrix_inputs[r][c].setValue(kernel[r][c])