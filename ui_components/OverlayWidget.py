from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QDoubleSpinBox, QSpinBox, QCheckBox, QHBoxLayout, QComboBox
)
from PySide6.QtCore import Qt, Signal

class OverlayWidget(QWidget):
    value_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Overlay")
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

        self.overlay_combo = QComboBox()
        self.overlay_combo.setPlaceholderText("Select a clip...")
        self.overlay_combo.currentIndexChanged.connect(lambda: self.value_changed.emit())

        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.0, 1.0)
        self.alpha_spin.setSingleStep(0.1)
        self.alpha_spin.setValue(1.0)
        self.alpha_spin.valueChanged.connect(lambda: self.value_changed.emit())

        self.pos_x_spin = QSpinBox()
        self.pos_x_spin.setRange(0, 10000)
        self.pos_x_spin.setValue(0)
        self.pos_x_spin.setSuffix(" px")
        self.pos_x_spin.valueChanged.connect(lambda: self.value_changed.emit())


        self.pos_y_spin = QSpinBox()
        self.pos_y_spin.setRange(0, 10000)
        self.pos_y_spin.setValue(0)
        self.pos_y_spin.setSuffix(" px")
        self.pos_y_spin.valueChanged.connect(lambda: self.value_changed.emit())
        
        form.addRow("Overlay Clip:", self.overlay_combo)
        form.addRow("Alpha:", self.alpha_spin)
        form.addRow("Pos X:", self.pos_x_spin)
        form.addRow("Pos Y:", self.pos_y_spin)
        
        group = QGroupBox("Overlay Composition")
        group.setLayout(form)
        layout.addWidget(group)

    def update_overlay_list(self, overlays):
        current_path = self.overlay_combo.currentData(Qt.UserRole)
        self.overlay_combo.blockSignals(True)
        self.overlay_combo.clear()
        
        self.overlay_combo.addItem("None", None)
        
        for item in overlays:
            name = item.get('name', 'Unknown')
            path = item.get('path', '')
            self.overlay_combo.addItem(name, path)
            
        if current_path:
            idx = self.overlay_combo.findData(current_path, Qt.UserRole)
            if idx != -1:
                self.overlay_combo.setCurrentIndex(idx)
        self.overlay_combo.blockSignals(False)

    def get_data(self):
        return {
            'enabled': self.enable_cb.isChecked(),
            'overlay_path': self.overlay_combo.currentData(Qt.UserRole),
            'Alpha': self.alpha_spin.value(),
            'Position': (self.pos_x_spin.value(), self.pos_y_spin.value())
        }

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            self.overlay_combo.setCurrentIndex(0)
            self.alpha_spin.setValue(1.0)
            self.pos_x_spin.setValue(0)
            self.pos_y_spin.setValue(0)
            return
        self.enable_cb.setChecked(data.get('enabled', False))
        self.alpha_spin.setValue(float(data.get('Alpha', 1.0)))
        pos = data.get('Position', (0,0))
        if isinstance(pos, (list, tuple)) and len(pos) >= 2:
            self.pos_x_spin.setValue(int(pos[0]))
            self.pos_y_spin.setValue(int(pos[1]))
            
        saved_path = data.get('overlay_path')
        if saved_path:
            idx = self.overlay_combo.findData(saved_path, Qt.UserRole)
            if idx != -1:
                self.overlay_combo.setCurrentIndex(idx)