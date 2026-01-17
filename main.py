import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QStatusBar,
    QMessageBox,
    QFileDialog,
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QLabel,
    QDateEdit,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QComboBox,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QDate

from database import DatabaseManager


class WorkTimeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Work time tracker")
        self.resize(900, 600)

        self.db = DatabaseManager("WTBase.db")

        # === Центральная рабочая область с вкладками ===
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        # === Строка меню ===
        self.create_menu()

        # === Панель инструментов ===
        self.create_toolbar()

        # === Строка состояния ===
        self.setStatusBar(QStatusBar(self))

        self.load_recent_files()
        # Создаём первую вкладку по умолчанию
        self.new_file()

    def add_to_recent(self, filepath: str):
        self.db.add_recent_file(filepath)

    def get_recent_files(self, limit=10):
        return self.db.get_recent_files(limit)

    def load_recent_files(self):
        """Добавляет подменю 'Recent Files' в меню File."""
        recent_files = self.get_recent_files()
        if not hasattr(self, "_recent_menu"):
            file_menu = (
                self.menuBar().actions()[0].menu()
            )  # Получаем первое меню ("File")
            file_menu.addSeparator()
            self._recent_menu = file_menu.addMenu("Recent Files")
        else:
            self._recent_menu.clear()

        if recent_files:
            for filepath in recent_files:
                action = QAction(filepath, self)
                action.triggered.connect(
                    lambda checked, fp=filepath: self.open_file_by_path(fp)
                )
                self._recent_menu.addAction(action)
        else:
            empty_action = QAction("No recent files", self)
            empty_action.setEnabled(False)
            self._recent_menu.addAction(empty_action)

    def open_file_by_path(self, filepath: str):
        """Открывает файл по заданному пути."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            editor = QTextEdit()
            editor.setPlainText(content)
            filename = os.path.basename(filepath)
            self.tabs.addTab(editor, filename)
            self.tabs.setCurrentWidget(editor)
            self.add_to_recent(filepath)
            self.statusBar().showMessage(f"Opened: {filepath}", 2000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file:\n{e}")

    def create_menu(self):
        menubar = self.menuBar()

        # Меню "File"
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню "Help"
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # Кнопка "New"
        new_btn = QAction("New", self)
        new_btn.setStatusTip("Create a new file")
        new_btn.triggered.connect(self.new_file)
        toolbar.addAction(new_btn)

        # Кнопка "Open"
        open_btn = QAction("Open", self)
        open_btn.setStatusTip("Open an existing file")
        open_btn.triggered.connect(self.open_file)
        toolbar.addAction(open_btn)

        # Кнопка "Save"
        save_btn = QAction("Save", self)
        save_btn.setStatusTip("Save the current file")
        save_btn.triggered.connect(self.save_file)
        toolbar.addAction(save_btn)

        new_work_day_btn = QAction("New work day", self)
        new_work_day_btn.setStatusTip("Create a new work day")
        new_work_day_btn.triggered.connect(self.new_work_day)
        toolbar.addAction(new_work_day_btn)

    def new_file(self):
        editor = QTextEdit()
        index = self.tabs.addTab(editor, "Untitled")
        self.tabs.setCurrentIndex(index)
        editor.setFocus()

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if isinstance(widget, QTextEdit):
            # Здесь можно добавить проверку на сохранение изменений
            pass
        self.tabs.removeTab(index)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                editor = QTextEdit()
                editor.setPlainText(content)
                filename = file_path.split("/")[-1]
                self.tabs.addTab(editor, filename)
                self.tabs.setCurrentWidget(editor)
                self.add_to_recent(file_path)
                self.statusBar().showMessage(f"Opened: {file_path}", 2000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file:\n{e}")

    def save_file(self):
        current_widget = self.tabs.currentWidget()
        if not current_widget:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                content = current_widget.toPlainText()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                filename = file_path.split("/")[-1]
                self.tabs.setTabText(self.tabs.currentIndex(), filename)
                self.statusBar().showMessage(f"Saved: {file_path}", 2000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file:\n{e}")

    def show_about(self):
        QMessageBox.about(
            self,
            "About",
            "This is an attempt to create a comfortable program\n"
            "to take into account my working time in different programs\n"
            "and calculate the payment for the time worked.",
        )

    def remove_time_entry_row(self, row_widget):
        """Удаляет указанную строку из интерфейса."""
        if self.time_entries_layout.count() > 1:  # оставляем хотя бы одну
            self.time_entries_layout.removeWidget(row_widget)
            row_widget.deleteLater()
        else:
            QMessageBox.warning(self, "Внимание", "Нужна хотя бы одна запись.")

    def add_time_entry_row(self):
        """Добавляет новую строку для ввода часов, минут и трекера."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        project_combo = QComboBox()
        project_combo.addItems(["Roof app", "Geoproject", "SparkURL"])
        project_combo.setEditable(False)

        # Часы
        hours_spin = QSpinBox()
        hours_spin.setRange(0, 24)
        hours_spin.setSuffix(" ч")
        hours_spin.setFixedWidth(80)

        # Минуты
        minutes_spin = QSpinBox()
        minutes_spin.setRange(0, 59)
        minutes_spin.setSuffix(" мин")
        minutes_spin.setFixedWidth(80)

        # Трекер
        tracker_combo = QComboBox()
        tracker_combo.addItems(["LogWork", "UpWork"])
        tracker_combo.setEditable(False)

        # Кнопка удаления строки (опционально)
        remove_btn = QPushButton("🗑️")
        remove_btn.setFixedSize(30, 30)
        remove_btn.setToolTip("Удалить запись")
        remove_btn.clicked.connect(lambda: self.remove_time_entry_row(row_widget))

        # Собираем всё в строку
        row_layout.addWidget(project_combo)
        row_layout.addWidget(hours_spin)
        row_layout.addWidget(minutes_spin)
        row_layout.addWidget(tracker_combo)
        row_layout.addWidget(remove_btn)
        row_layout.addStretch()

        # Добавляем строку в общий контейнер
        self.time_entries_layout.addWidget(row_widget)

    def new_work_day(self):
        """Создаёт новую вкладку для учёта рабочего дня."""
        # Основной контейнер для прокрутки
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # === Поле выбора даты ===
        date_label = QLabel("Дата:")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")

        date_layout = QHBoxLayout()
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()

        layout.addLayout(date_layout)
        layout.addSpacing(15)

        # === Контейнер для строк времени ===
        self.time_entries_layout = QVBoxLayout()
        self.time_entries_layout.setSpacing(8)
        self.time_entries_widget = QWidget()
        self.time_entries_widget.setLayout(self.time_entries_layout)

        # Добавляем первую строку по умолчанию
        self.add_time_entry_row()

        layout.addWidget(self.time_entries_widget)

        # === Кнопка "Добавить запись" ===
        add_button = QPushButton("➕ Добавить запись")
        add_button.clicked.connect(self.add_time_entry_row)
        layout.addWidget(add_button)
        layout.addStretch()

        # Упаковываем в прокручиваемую область
        scroll.setWidget(content)

        # Добавляем вкладку
        index = self.tabs.addTab(scroll, "Рабочий день")
        self.tabs.setCurrentIndex(index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorkTimeApp()
    window.show()
    sys.exit(app.exec())
