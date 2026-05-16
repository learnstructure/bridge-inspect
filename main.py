import sys
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Apply modern theme
    apply_stylesheet(app, theme="light_blue.xml")   # You can choose from various themes like "dark_blue.xml", "light_blue.xml", etc.

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
