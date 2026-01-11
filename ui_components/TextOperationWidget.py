from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QSpinBox, QCheckBox, QHBoxLayout, QComboBox, QLineEdit, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal

class TextOperationWidget(QWidget):
    value_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        top_row = QHBoxLayout()
        self.enable_cb = QCheckBox("Enable Text Overlay")
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

        self.edit_text = QLineEdit()
        self.edit_text.setPlaceholderText("Enter text here...")
        self.edit_text.textChanged.connect(lambda t: self.value_changed.emit())
        form.addRow("Text:", self.edit_text)

        pos_layout = QHBoxLayout()
        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 9999)
        self.spin_x.setValue(10)
        self.spin_x.setPrefix("X: ")
        
        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 9999)
        self.spin_y.setValue(10)
        self.spin_y.setPrefix("Y: ")
        
        pos_layout.addWidget(self.spin_x)
        pos_layout.addWidget(self.spin_y)
        form.addRow("Position:", pos_layout)

        self.combo_font = QComboBox()
        self.combo_font.addItems(["Arial", "Verdana", "Times New Roman", "Courier New", "Georgia", "Impact"])
        form.addRow("Font:", self.combo_font)


        self.spin_size = QSpinBox()
        self.spin_size.setRange(8, 200)
        self.spin_size.setValue(24)
        form.addRow("Size:", self.spin_size)


        self.combo_color = QComboBox()
        self.combo_color.addItems(["white", "black", "red", "yellow", "green", "blue"])
        form.addRow("Color:", self.combo_color)


        self.spin_opacity = QDoubleSpinBox()
        self.spin_opacity.setRange(0.0, 1.0)
        self.spin_opacity.setSingleStep(0.1)
        self.spin_opacity.setValue(1.0)
        form.addRow("Opacity:", self.spin_opacity)
        
        group = QGroupBox("Text Settings")
        group.setLayout(form)
        layout.addWidget(group)

    def get_data(self):
        return {
            'enabled': self.enable_cb.isChecked(),
            'Text': self.edit_text.text(),
            'Position': (self.spin_x.value(), self.spin_y.value()),
            'Font': self.combo_font.currentText(),
            'Size': self.spin_size.value(),
            'Color': self.combo_color.currentText(),
            'Opacity': self.spin_opacity.value()
        }

    def set_data(self, data):
        if not data:
            self.enable_cb.setChecked(False)
            return
        self.enable_cb.setChecked(data.get('enabled', False))
        self.edit_text.setText(data.get('Text', ""))
        pos = data.get('Position', (10, 10))
        self.spin_x.setValue(pos[0])
        self.spin_y.setValue(pos[1])
        self.combo_font.setCurrentText(data.get('Font', "Arial"))
        self.spin_size.setValue(data.get('Size', 24))
        self.combo_color.setCurrentText(data.get('Color', "white"))
        self.spin_opacity.setValue(data.get('Opacity', 1.0))