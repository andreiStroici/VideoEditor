from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QDoubleSpinBox, QComboBox, QCheckBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

class BlendWidget(QWidget):
    value_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Blend")
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
        self.blend_combo = QComboBox()
        self.blend_combo.setPlaceholderText("Select a clip...")
        self.blend_combo.currentIndexChanged.connect(lambda: self.value_changed.emit())

        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.0, 1.0)
        self.alpha_spin.setSingleStep(0.1)
        self.alpha_spin.setValue(0.5) 
        self.alpha_spin.valueChanged.connect(lambda: self.value_changed.emit())

        self.mode_combo = QComboBox()
        modes = ["overlay", "multiply", "screen", "addition", "subtract", "difference"]
        self.mode_combo.addItems(modes)
        self.mode_combo.setCurrentText("overlay")
        self.mode_combo.currentIndexChanged.connect(lambda: self.value_changed.emit())
        
        form.addRow("Blend With:", self.blend_combo)
        form.addRow("Alpha:", self.alpha_spin)
        form.addRow("Mode:", self.mode_combo)
        
        group = QGroupBox("Blend Composition")
        group.setLayout(form)
        layout.addWidget(group)

    def update_blend_list(self, clips_list):
        current_path = self.blend_combo.currentData(Qt.UserRole)
        self.blend_combo.blockSignals(True)
        self.blend_combo.clear()

        self.blend_combo.addItem("None (Disabled)", None)
        
        for item in clips_list:
            name = item.get('name', 'Unknown')
            path = item.get('path', '')
            self.blend_combo.addItem(name, path)
            
        if current_path:
            idx = self.blend_combo.findData(current_path, Qt.UserRole)
            if idx != -1:
                self.blend_combo.setCurrentIndex(idx)
        self.blend_combo.blockSignals(False)

    def get_data(self):
        selected_path = self.blend_combo.currentData(Qt.UserRole)
        is_checked = self.enable_cb.isChecked()
        final_enabled = is_checked and (selected_path is not None)

        return {
            'enabled': final_enabled,
            'blend_path': selected_path,
            'Alpha': self.alpha_spin.value(),  
            'Mode': self.mode_combo.currentText()
        }

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            self.blend_combo.setCurrentIndex(0)
            self.alpha_spin.setValue(0.5)
            self.mode_combo.setCurrentText("overlay")
            return
            
        self.enable_cb.setChecked(data.get('enabled', False))
        self.alpha_spin.setValue(float(data.get('Alpha', 0.5)))
        
        mode_str = data.get('Mode', 'overlay')
        idx = self.mode_combo.findText(mode_str)
        if idx != -1:
            self.mode_combo.setCurrentIndex(idx)
        else:
            self.mode_combo.setCurrentText("overlay")
            
        saved_path = data.get('blend_path')
        if saved_path:
            idx = self.blend_combo.findData(saved_path, Qt.UserRole)
            if idx != -1:
                self.blend_combo.setCurrentIndex(idx)