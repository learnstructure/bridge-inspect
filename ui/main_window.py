from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QStackedWidget,
    QStatusBar,
)
from PySide6.QtGui import QAction

from ui.pages.home_page import HomePage
from ui.pages.pda_page import PDAPage
from ui.pages.dda_page import DDAPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Bridge Damage Detection")
        self.resize(1100, 650)

        # Menu
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        help_menu = menu.addMenu("Help")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Layout
        main_widget = QWidget()
        layout = QHBoxLayout()

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.addItems(["Home", "PDA", "DDA"])
        self.sidebar.setFixedWidth(180)

        # Pages
        self.stack = QStackedWidget()
        self.home = HomePage()
        self.pda = PDAPage()
        self.dda = DDAPage()

        self.stack.addWidget(self.home)
        self.stack.addWidget(self.pda)
        self.stack.addWidget(self.dda)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.sidebar.currentRowChanged.connect(self.switch_page)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        self.status.showMessage(f"Switched to {self.sidebar.item(index).text()}")
