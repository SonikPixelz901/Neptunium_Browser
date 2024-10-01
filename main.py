import sys
import os
import json
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *


class BookmarkManager(QDockWidget):
    def __init__(self, parent=None):
        super(BookmarkManager, self).__init__(parent)
        self.setWindowTitle("Bookmarks")
        self.layout = QVBoxLayout()
        self.bookmark_list = QListWidget()
        self.add_button = QPushButton("Add Bookmark")
        self.remove_button = QPushButton("Remove Bookmark")

        self.add_button.clicked.connect(self.add_bookmark)
        self.remove_button.clicked.connect(self.remove_bookmark)

        self.layout.addWidget(self.bookmark_list)
        self.layout.addWidget(self.add_button)
        self.layout.addWidget(self.remove_button)

        container = QWidget()
        container.setLayout(self.layout)
        self.setWidget(container)

    def add_bookmark(self):
        current_url = self.parent().current_tab().url().toString()
        if current_url:
            self.bookmark_list.addItem(current_url)

    def remove_bookmark(self):
        selected_item = self.bookmark_list.currentItem()
        if selected_item:
            row = self.bookmark_list.row(selected_item)
            self.bookmark_list.takeItem(row)


class HistoryViewer(QDockWidget):
    def __init__(self, parent=None):
        super(HistoryViewer, self).__init__(parent)
        self.setWindowTitle("History")
        self.history_list = QListWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.history_list)

        container = QWidget()
        container.setLayout(layout)
        self.setWidget(container)

    def add_to_history(self, url):
        self.history_list.addItem(url)


class DownloadManager(QDockWidget):
    def __init__(self, parent=None):
        super(DownloadManager, self).__init__(parent)
        self.setWindowTitle("Downloads")
        self.download_list = QListWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.download_list)

        container = QWidget()
        container.setLayout(layout)
        self.setWidget(container)

    def add_download(self, file_name):
        self.download_list.addItem(file_name)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.browser = QTabWidget()
        self.setCentralWidget(self.browser)
        self.showMaximized()

        self.initUI()
        self.history_viewer = HistoryViewer(self)
        self.download_manager = DownloadManager(self)
        self.bookmark_manager = BookmarkManager(self)

        self.addDockWidget(Qt.RightDockWidgetArea, self.history_viewer)
        self.addDockWidget(Qt.RightDockWidgetArea, self.download_manager)

        self.user_profiles = {}
        self.current_profile = None
        self.load_settings()
        self.create_context_menu()
        self.create_sidebar()

    def initUI(self):
        navbar = QToolBar()
        self.addToolBar(navbar)

        back_btn = QAction('Back', self)
        back_btn.triggered.connect(lambda: self.current_tab().back())
        navbar.addAction(back_btn)

        forward_btn = QAction('Forward', self)
        forward_btn.triggered.connect(lambda: self.current_tab().forward())
        navbar.addAction(forward_btn)

        reload_btn = QAction('Reload', self)
        reload_btn.triggered.connect(lambda: self.current_tab().reload())
        navbar.addAction(reload_btn)

        home_btn = QAction('Home', self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)

        new_tab_btn = QAction('New Tab', self)
        new_tab_btn.triggered.connect(self.add_new_tab)
        navbar.addAction(new_tab_btn)

        more_btn = QAction('More', self)
        more_btn.triggered.connect(self.show_more_options)
        navbar.addAction(more_btn)

        settings_btn = QAction('Settings', self)
        settings_btn.triggered.connect(self.open_settings)
        navbar.addAction(settings_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        self.browser.currentChanged.connect(self.current_tab_changed)

        self.add_new_tab()  # Open a new tab with a default URL

    def show_more_options(self):
        more_dialog = QDialog(self)
        more_dialog.setWindowTitle("More Options")
        layout = QVBoxLayout(more_dialog)

        bookmarks_btn = QPushButton("Manage Bookmarks", self)
        bookmarks_btn.clicked.connect(self.bookmark_manager.show)
        layout.addWidget(bookmarks_btn)

        history_btn = QPushButton("View History", self)
        history_btn.clicked.connect(self.history_viewer.show)
        layout.addWidget(history_btn)

        downloads_btn = QPushButton("View Downloads", self)
        downloads_btn.clicked.connect(self.download_manager.show)
        layout.addWidget(downloads_btn)

        more_dialog.exec_()

    def create_context_menu(self):
        # Create the context menu
        self.tab_context_menu = QMenu(self)

        # Add action for deleting the current tab
        delete_action = QAction("Delete Tab", self)
        delete_action.triggered.connect(self.delete_current_tab)
        self.tab_context_menu.addAction(delete_action)

        # Add action for duplicating the current tab
        duplicate_action = QAction("Duplicate Tab", self)
        duplicate_action.triggered.connect(self.duplicate_current_tab)
        self.tab_context_menu.addAction(duplicate_action)

        # Connect the context menu to the tab bar
        self.browser.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.browser.tabBar().customContextMenuRequested.connect(self.show_tab_context_menu)

    def show_tab_context_menu(self, position):
        # Show the context menu at the position where the user right-clicked
        self.tab_context_menu.exec_(self.browser.tabBar().mapToGlobal(position))

    def delete_current_tab(self):
        # Get the current index and delete the tab if there's more than one
        current_index = self.browser.currentIndex()
        if self.browser.count() > 1:
            self.browser.removeTab(current_index)

    def duplicate_current_tab(self):
        # Duplicate the current tab by getting the URL and adding a new tab with the same URL
        current_tab = self.current_tab()
        current_url = current_tab.url().toString()
        self.add_new_tab(current_url)

    def create_sidebar(self):
        self.bookmark_manager.setVisible(True)
        self.bookmark_manager.setFixedWidth(200)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.bookmark_manager)

    def add_new_tab(self, url='https://www.google.com/'):
        if not isinstance(url, str):  # Ensure the URL is a string
            url = 'https://www.google.com/'

        new_tab = QWebEngineView()
        new_tab.setUrl(QUrl.fromUserInput(url))  # Ensure valid URL input
        new_tab.urlChanged.connect(self.update_url)
        new_tab.titleChanged.connect(lambda title: self.set_tab_title(new_tab, title))

        self.browser.addTab(new_tab, url)
        self.browser.setCurrentWidget(new_tab)

        new_tab.loadFinished.connect(lambda _: self.history_viewer.add_to_history(url))

    def current_tab(self):
        return self.browser.currentWidget()

    def current_tab_changed(self):
        if self.current_tab():
            self.url_bar.setText(self.current_tab().url().toString())

    def update_url(self, q):
        self.url_bar.setText(q.toString())

    def navigate_home(self):
        self.current_tab().setUrl(QUrl('https://www.google.com/'))

    def navigate_to_url(self):
        url = self.url_bar.text()
        if "." not in url:  # If it doesn't contain a dot, assume it's a search query
            search_query = url.replace(" ", "+")
            url = f"https://www.google.com/search?q={search_query}"
        elif not url.startswith('http'):
            url = 'https://' + url
        self.current_tab().setUrl(QUrl(url))

    def set_tab_title(self, tab, title):
        index = self.browser.indexOf(tab)
        self.browser.setTabText(index, title)

    def delete_current_tab(self):
        current_index = self.browser.currentIndex()
        if self.browser.count() > 1:  # Ensure at least one tab remains
            self.browser.removeTab(current_index)

    def duplicate_current_tab(self):
        current_tab = self.current_tab()
        current_url = current_tab.url().toString()
        self.add_new_tab(current_url)

    def open_settings(self):
        settings_window = SettingsWindow(self)
        settings_window.exec_()

    def load_settings(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as file:
                settings = json.load(file)
                self.apply_settings(settings)

        if os.path.exists("profiles.json"):
            with open("profiles.json", "r") as file:
                self.user_profiles = json.load(file)

    def apply_settings(self, settings):
        theme = settings.get("theme", "Light")
        font_size = settings.get("font_size", "12")
        self.set_style(theme, font_size)

    def set_style(self, theme, font_size):
        if theme == "Dark":
            qApp.setStyleSheet(f"QWidget {{ background-color: #2E2E2E; color: white; font-size: {font_size}px; }}")
        elif theme == "Blue":
            qApp.setStyleSheet(f"QWidget {{ background-color: #007BFF; color: white; font-size: {font_size}px; }}")
        elif theme == "Green":
            qApp.setStyleSheet(f"QWidget {{ background-color: #28A745; color: white; font-size: {font_size}px; }}")
        else:  # Default Light theme
            qApp.setStyleSheet(f"QWidget {{ background-color: white; color: black; font-size: {font_size}px; }}")


class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super(SettingsWindow, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.layout = QVBoxLayout()

        self.current_settings = {
            "theme": "Light",  # Default value
            "font_size": "12"  # Default value
        }
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as file:
                self.current_settings = json.load(file)

        self.theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Blue", "Green"])
        self.theme_combo.setCurrentText(self.current_settings.get("theme", "Light"))

        self.font_size_label = QLabel("Font Size:")
        self.font_size_input = QLineEdit()
        self.font_size_input.setText(str(self.current_settings.get("font_size", "12")))

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)

        self.layout.addWidget(self.theme_label)
        self.layout.addWidget(self.theme_combo)
        self.layout.addWidget(self.font_size_label)
        self.layout.addWidget(self.font_size_input)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

    def save_settings(self):
        theme = self.theme_combo.currentText()
        font_size = self.font_size_input.text()

        settings = {
            "theme": theme,
            "font_size": font_size
        }

        with open("settings.json", "w") as file:
            json.dump(settings, file)

        self.parent().apply_settings(settings)
        self.close()


app = QApplication(sys.argv)
QApplication.setApplicationName('Neptunium Browser')
window = MainWindow()
window.show()
sys.exit(app.exec_())
