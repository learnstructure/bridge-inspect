from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        label = QLabel("Bridge Damage Detection System")
        label.setStyleSheet("font-size: 20px; font-weight: bold;")

        layout.addWidget(label)
        self.setLayout(layout)
