# ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QStatusBar,
    QTreeWidget, QTreeWidgetItem
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from ui.pages.home_page import HomePage
from ui.pages.pda_page import PDAPage
from ui.pages.dda_page import DDAPage
from ui.widgets.log_panel import LogPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bridge Damage Detection")
        self.resize(1200, 700)
        self._setup_ui()

    def _setup_ui(self):
        # --- Menu Bar ---
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # --- Main Layout ---
        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)

        # --- Sidebar Navigation ---
        self.sidebar = QTreeWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setHeaderHidden(True)
        layout.addWidget(self.sidebar)

        # --- Page Container ---
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # --- Instantiate Pages ---
        self.home_page = HomePage()
        self.pda_page = PDAPage()
        self.dda_page = DDAPage()

        # --- Add Pages to Stack ---
        self.page_indices = {
            "home": self.stack.addWidget(self.home_page),
            "pda": self.stack.addWidget(self.pda_page),
            "dda": self.stack.addWidget(self.dda_page),
        }

        # --- Populate Sidebar ---
        self._populate_sidebar()

        self.setCentralWidget(main_widget)

        # --- Status Bar and Log Panel ---
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.log_panel = LogPanel()
        self.status.setMaximumHeight(120)
        self.status.addPermanentWidget(self.log_panel)
        self.log_panel.log("Application started")

        # --- Connect Signals ---
        self.sidebar.itemClicked.connect(self.on_item_clicked)
        self.sidebar.currentItemChanged.connect(self.on_nav_item_changed)

        # --- Set Initial State ---
        self.sidebar.blockSignals(True)
        home_item = self.sidebar.topLevelItem(0)
        self.sidebar.setCurrentItem(home_item)
        self.stack.setCurrentIndex(self.page_indices["home"])
        self.sidebar.blockSignals(False)

    def _populate_sidebar(self):
        """Creates the navigation items in the QTreeWidget."""
        self._add_nav_item("Home", "home")

        pda_item = self._add_nav_item("PDA", "pda")
        self._add_nav_item("Damage State Rules", "pda", "pda_rules", parent=pda_item)
        self._add_nav_item("PDA Analysis", "pda", "pda_analysis", parent=pda_item)
        self._add_nav_item("Correction", "pda", "pda_correction", parent=pda_item)
        self._add_nav_item("Summary Report", "pda", "pda_report", parent=pda_item)

        self._add_nav_item("DDA", "dda")
        
        pda_item.setExpanded(True)

    def _add_nav_item(self, text, main_page_key, sub_page_key=None, parent=None):
        """Helper to create and add a navigation item."""
        item = QTreeWidgetItem(parent or self.sidebar)
        item.setText(0, text)
        item.setData(0, Qt.UserRole, main_page_key)
        item.setData(0, Qt.UserRole + 1, sub_page_key)
        return item

    def on_item_clicked(self, item, column):
        """Handles expanding/collapsing parent items when they are clicked."""
        if item.childCount() > 0:
            item.setExpanded(not item.isExpanded())

    def on_nav_item_changed(self, current, previous):
        """Switches the main page and, if applicable, the sub-page."""
        if current is None: return

        main_page_key = current.data(0, Qt.UserRole)
        sub_page_key = current.data(0, Qt.UserRole + 1)

        # If a parent item like 'PDA' is selected, default to its first child
        if main_page_key == "pda" and sub_page_key is None:
            first_child = current.child(0)
            if first_child and self.sidebar.currentItem() != first_child:
                self.sidebar.setCurrentItem(first_child)
            return

        if main_page_key in self.page_indices:
            main_index = self.page_indices[main_page_key]
            if self.stack.currentIndex() != main_index:
                self.stack.setCurrentIndex(main_index)
            
            self.log_panel.log(f"Switched to {current.text(0)}")

            if main_page_key == "pda" and sub_page_key:
                self.pda_page.set_current_page_by_key(sub_page_key)
