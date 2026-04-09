from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QComboBox,
)


class DDAPage(QWidget):
    def __init__(self, bridge_list=None):
        super().__init__()
        layout = QVBoxLayout()

        self.label = QLabel("Detailed Damage Assessment")
        self.bridge_selector = QComboBox()
        self.bridge_selector.addItems(bridge_list or ["Bridge_001", "Bridge_002"])
        self.load_btn = QPushButton("Load Properties")
        self.run_btn = QPushButton("Run Analysis")
        self.output = QTextEdit()

        layout.addWidget(self.label)
        layout.addWidget(self.bridge_selector)
        layout.addWidget(self.load_btn)
        layout.addWidget(self.run_btn)
        layout.addWidget(self.output)

        self.setLayout(layout)

        # Connect buttons
        self.load_btn.clicked.connect(self.load_properties)
        self.run_btn.clicked.connect(self.run_analysis)

    def load_properties(self):
        bridge_id = self.bridge_selector.currentText()
        self.output.append(f"Loaded properties for {bridge_id}")

    def run_analysis(self):
        self.output.append("Running nonlinear analysis...")
        self.output.append("Drift: 3.2%")
        self.output.append("Damage State: Severe")
