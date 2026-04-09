from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit


class DDAPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.label = QLabel("Detailed Damage Assessment")
        self.run_btn = QPushButton("Run Analysis")
        self.output = QTextEdit()

        layout.addWidget(self.label)
        layout.addWidget(self.run_btn)
        layout.addWidget(self.output)

        self.setLayout(layout)

        self.run_btn.clicked.connect(self.run_analysis)

    def run_analysis(self):
        self.output.append("Running nonlinear analysis...")
        self.output.append("Drift: 3.2%")
        self.output.append("Damage State: Severe")
