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
from ui.widgets.log_panel import LogPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bridge Damage Detection")
        self.resize(1200, 700)

        # Menu
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        help_menu = menu.addMenu("Help")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Main layout
        main_widget = QWidget()
        layout = QHBoxLayout()

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.addItems(["Home", "PDA", "DDA"])
        self.sidebar.setFixedWidth(180)

        # Pages
        self.stack = QStackedWidget()
        self.home_page = HomePage()
        self.pda_page = PDAPage()
        self.dda_page = DDAPage()
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.pda_page)
        self.stack.addWidget(self.dda_page)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Status bar and log panel
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.log_panel = LogPanel()
        self.status.setMaximumHeight(120)
        self.status.addPermanentWidget(self.log_panel)
        self.log_panel.log("Application started")

        # Connect sidebar
        self.sidebar.currentRowChanged.connect(self.switch_page)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        page_name = self.sidebar.item(index).text()
        self.log_panel.log(f"Switched to {page_name}")
