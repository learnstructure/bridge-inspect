from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QFileDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


class PDAPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Buttons
        btn_layout = QHBoxLayout()
        self.upload_btn = QPushButton("Upload Image")
        self.run_btn = QPushButton("Run PDA")
        btn_layout.addWidget(self.upload_btn)
        btn_layout.addWidget(self.run_btn)

        # Content layout
        content_layout = QHBoxLayout()

        # Image viewer
        self.image_label = QLabel("Image Viewer")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid gray;")

        # Results panel
        self.results = QTextEdit()
        self.results.setPlaceholderText("Results...")

        content_layout.addWidget(self.image_label, 2)
        content_layout.addWidget(self.results, 1)

        layout.addLayout(btn_layout)
        layout.addLayout(content_layout)

        self.setLayout(layout)

        self.upload_btn.clicked.connect(self.load_image)
        self.run_btn.clicked.connect(self.run_pda)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            pixmap = QPixmap(file_path)
            self.image_label.setPixmap(
                pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio)
            )
            self.results.append(f"Loaded: {file_path}")

    def run_pda(self):
        self.results.append("Running PDA...")
        self.results.append("Horizontal cracks: 3")
        self.results.append("Vertical cracks: 1")
        self.results.append("Damage State: Moderate")
