import sqlite3
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
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QDate, QDateTime

from database import DatabaseManager


class WorkTimeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Work time tracker")
        self.setMinimumSize(550, 400)
        self.minimumSize()

        self.db = DatabaseManager("WTBase.db")

        # === Central widget with tabs ===
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self.create_menu()
        self.create_toolbar()
        self.setStatusBar(QStatusBar(self))

        self.load_recent_files()
        # Create the first tab by default
        self.new_work_day()

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
        file_menu = menubar.addMenu("&Main")

        billing_config = QAction("&Billing config", self)
        billing_config.setShortcut("Ctrl+B")
        billing_config.triggered.connect(self.billing_config)
        file_menu.addAction(billing_config)
        # new_action = QAction("&New", self)
        # new_action.setShortcut("Ctrl+N")
        # new_action.triggered.connect(self.new_file)
        # file_menu.addAction(new_action)
        #
        # open_action = QAction("&Open...", self)
        # open_action.setShortcut("Ctrl+O")
        # open_action.triggered.connect(self.open_file)
        # file_menu.addAction(open_action)
        #
        # save_action = QAction("&Save", self)
        # save_action.setShortcut("Ctrl+S")
        # save_action.triggered.connect(self.save_file)
        # file_menu.addAction(save_action)

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

    def refresh_billing_tab(self):
        """Refreshes the billing tab by recreating it."""
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Billing Config":
                self.tabs.removeTab(i)
                self.billing_config()
                break

    def save_billing_record(
        self, tracker: str, started_at: int, hour_cost: int, row_widget
    ):
        """Saves a new billing record and updates the UI."""
        success = self.db.add_billing_record(tracker, started_at, hour_cost)
        if success:
            QMessageBox.information(self, "Success", "Record saved successfully!")
            # Delete the row after saving
            self.billing_entries_layout.removeWidget(row_widget)
            row_widget.deleteLater()
            # Update the billing tab to reflect the new record
            self.refresh_billing_tab()
        else:
            QMessageBox.critical(self, "Error", "Failed to save record.")

    def remove_billing_entry_row(self, row_widget):
        """Delete a billing entry row from the UI."""
        if self.billing_entries_layout.count() > 1:
            self.billing_entries_layout.removeWidget(row_widget)
            row_widget.deleteLater()
        else:
            QMessageBox.warning(self, "Attention", "At least one record should remain.")

    def add_billing_entry_row(self, record: dict = None):
        """Add a new row to the billing entries."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        tracker_combo = QComboBox()
        tracker_combo.addItems(["LogWork", "UpWork"])
        if record:
            tracker_combo.setCurrentText(record["tracker"])

        started_at_date = QDateEdit()
        started_at_date.setCalendarPopup(True)
        started_at_date.setDisplayFormat("dd.MM.yyyy")

        if record:
            dt = QDateTime.fromSecsSinceEpoch(record["started_at"])
            started_at_date.setDate(dt.date())
        else:
            started_at_date.setDate(QDate.currentDate())

        hour_cost_spin = QSpinBox()
        hour_cost_spin.setRange(500, 2000)
        hour_cost_spin.setPrefix("₽ ")
        if record:
            hour_cost_spin.setValue(record["hour_cost"])

        if record is None:
            # Новая строка — кнопка "Сохранить"
            save_btn = QPushButton("💾 Save")
            save_btn.setFixedSize(70, 30)
            save_btn.setToolTip("Save this record")

            # Сохраняем ссылки на виджеты, чтобы получить значения при клике
            save_btn.clicked.connect(
                lambda: self.save_billing_record(
                    tracker_combo.currentText(),
                    started_at_date.date().startOfDay().toSecsSinceEpoch(),
                    hour_cost_spin.value(),
                    row_widget,
                )
            )
            btn_widget = save_btn
        else:
            # Существующая строка — кнопка "Удалить"
            remove_btn = QPushButton("🗑️")
            remove_btn.setFixedSize(30, 30)
            remove_btn.setToolTip("Delete record")
            remove_btn.clicked.connect(
                lambda: self.remove_billing_entry_row(row_widget)
            )
            btn_widget = remove_btn

        row_layout.addWidget(tracker_combo)
        row_layout.addWidget(started_at_date)
        row_layout.addWidget(hour_cost_spin)
        row_layout.addWidget(btn_widget)
        row_layout.addStretch()

        self.billing_entries_layout.addWidget(row_widget)

    def billing_config(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Заголовок
        title_label = QLabel("Billing Configuration")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        # === Контейнер для строк биллинга ===
        self.billing_entries_layout = QVBoxLayout()
        self.billing_entries_layout.setSpacing(8)
        self.billing_entries_widget = QWidget()
        self.billing_entries_widget.setLayout(self.billing_entries_layout)

        # Получаем записи из базы
        billing_records = self.db.get_billing()

        if billing_records:
            for record in billing_records:
                self.add_billing_entry_row(record)
        else:
            # If no records, add an empty row to start
            self.add_billing_entry_row(None)

        layout.addWidget(self.billing_entries_widget)

        # === Кнопка "Добавить запись" ===
        add_button = QPushButton("➕ Add Billing Record")
        add_button.clicked.connect(lambda: self.add_billing_entry_row(None))
        layout.addWidget(add_button)
        layout.addStretch()

        scroll.setWidget(content)

        # Добавляем вкладку
        index = self.tabs.addTab(scroll, "Billing Config")
        self.tabs.setCurrentIndex(index)

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
        if self.time_entries_layout.count() > 1:
            self.time_entries_layout.removeWidget(row_widget)
            row_widget.deleteLater()
        else:
            QMessageBox.warning(self, "Attention", "At least one record should be.")

    def add_time_entry_row(self):
        """Adding a new row to the time entries."""
        self.add_time_entry_row_with_data()

    def new_work_day(self):
        """Create a new work day tab."""
        # main container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        date_label = QLabel("Дата:")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")

        self.date_edit.dateChanged.connect(self.on_date_changed)

        date_layout = QHBoxLayout()
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()

        layout.addLayout(date_layout)
        layout.addSpacing(15)

        self.time_entries_layout = QVBoxLayout()
        self.time_entries_layout.setSpacing(8)
        self.time_entries_widget = QWidget()
        self.time_entries_widget.setLayout(self.time_entries_layout)

        date_int = self.date_edit.date().startOfDay().toSecsSinceEpoch()
        records = self.db.get_time_worked_by_date(date_int)

        if records:
            for rec in records:
                self.add_time_entry_row_with_data(rec)
        else:
            self.add_time_entry_row()

        layout.addWidget(self.time_entries_widget)

        # === Add record button ===
        add_button = QPushButton("➕ new tracker or project")
        add_button.clicked.connect(self.add_time_entry_row)
        layout.addWidget(add_button)
        layout.addStretch()

        # Packaging in a scrollable area
        scroll.setWidget(content)

        self.current_scroll_area = scroll

        # Adding a new tab and setting it as the current one
        index = self.tabs.addTab(
            scroll, "Working hours " + QDate.currentDate().toString("dd.MM.yyyy")
        )
        self.tabs.setCurrentIndex(index)

    def on_date_changed(self, date: QDate):
        """Updates the tab title and loads data for the selected date."""
        # Update the tab title with the new date
        tab_title = "Working hours " + date.toString("dd.MM.yyyy")
        index = self.tabs.indexOf(self.current_scroll_area)
        if index != -1:
            self.tabs.setTabText(index, tab_title)

        # Load and display data for the selected date
        date_int = self.date_edit.date().startOfDay().toSecsSinceEpoch()
        records = self.db.get_time_worked_by_date(date_int)

        # Clearing old rows before adding new ones
        while self.time_entries_layout.count():
            child = self.time_entries_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if records:
            for rec in records:
                self.add_time_entry_row_with_data(rec)
        else:
            self.add_time_entry_row()

    def add_time_entry_row_with_data(self, data: dict = None):
        """
        Adds a row with data from the database or an empty row.
        If data contains an 'id', then it is an existing record.
        """
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        project_combo = QComboBox()
        project_combo.addItems(self.db.get_projects())
        project_combo.setEditable(False)
        if data and data.get("project_name"):
            project_combo.setCurrentText(data["project_name"])

        hours_spin = QSpinBox()
        hours_spin.setRange(0, 24)
        hours_spin.setSuffix(" ч")
        hours_spin.setFixedWidth(80)
        if data and data.get("hours") is not None:
            hours_spin.setValue(int(data["hours"]))

        minutes_spin = QSpinBox()
        minutes_spin.setRange(0, 59)
        minutes_spin.setSuffix(" мин")
        minutes_spin.setFixedWidth(80)
        if data and data.get("minutes") is not None:
            minutes_spin.setValue(int(data["minutes"]))

        tracker_combo = QComboBox()
        tracker_combo.addItem(QIcon("images/logWork.png"), "LogWork")
        tracker_combo.addItem(QIcon("images/upWork.png"), "UpWork")
        tracker_combo.setEditable(False)
        if data and data.get("tracker"):
            tracker_combo.setCurrentText(data["tracker"])

        row_layout.addWidget(project_combo)
        row_layout.addWidget(hours_spin)
        row_layout.addWidget(minutes_spin)
        row_layout.addWidget(tracker_combo)

        # Determine the type of button based on the data
        if data and "id" in data:
            # Существующая запись — кнопки Update и Delete
            update_btn = QPushButton("🔄")
            update_btn.setFixedSize(30, 30)
            update_btn.setToolTip("Update this record")
            update_btn.clicked.connect(
                lambda: self.update_time_worked_entry(
                    data["id"],
                    project_combo.currentText(),
                    hours_spin.value(),
                    minutes_spin.value(),
                    tracker_combo.currentText(),
                    row_widget,
                )
            )

            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(30, 30)
            delete_btn.setToolTip("Delete record")
            delete_btn.clicked.connect(
                lambda: self.delete_time_worked_entry(data["id"], row_widget)
            )

            row_layout.addWidget(update_btn)
            row_layout.addWidget(delete_btn)
        else:
            # Новая запись — кнопка Save
            save_btn = QPushButton("💾")
            save_btn.setFixedSize(30, 30)
            save_btn.setToolTip("Save this record")
            save_btn.clicked.connect(
                lambda: self.save_new_time_worked_entry(
                    project_combo.currentText(),
                    hours_spin.value(),
                    minutes_spin.value(),
                    tracker_combo.currentText(),
                    row_widget,
                )
            )
            row_layout.addWidget(save_btn)

        row_layout.addStretch()

        self.time_entries_layout.addWidget(row_widget)

    def save_new_time_worked_entry(
        self, project_name: str, hours: int, minutes: int, tracker: str, row_widget
    ):
        """Сохраняет новую запись в БД."""
        # Получаем project_id по имени
        project_id = self.db.get_project_id_by_name(project_name)
        if project_id is None:
            QMessageBox.critical(self, "Error", f"Project '{project_name}' not found.")
            return

        # Конвертируем дату в Unix timestamp
        date_int = self.date_edit.date().startOfDay().toSecsSinceEpoch()

        success = self.db.save_time_worked(
            project_id, hours, minutes, tracker, date_int
        )
        if success:
            QMessageBox.information(self, "Success", "Record saved successfully!")
            self.time_entries_layout.removeWidget(row_widget)
            row_widget.deleteLater()
            self.refresh_current_tab()
        else:
            QMessageBox.critical(self, "Error", "Failed to save record.")

    def update_time_worked_entry(
        self,
        entry_id: int,
        project_name: str,
        hours: int,
        minutes: int,
        tracker: str,
        row_widget,
    ):
        """Обновляет существующую запись в БД."""
        project_id = self.db.get_project_id_by_name(project_name)
        if project_id is None:
            QMessageBox.critical(self, "Error", f"Project '{project_name}' not found.")
            return

        success = self.db.update_time_worked(
            entry_id, project_id, hours, minutes, tracker
        )
        if success:
            QMessageBox.information(self, "Success", "Record updated successfully!")
            self.refresh_current_tab()
        else:
            QMessageBox.critical(self, "Error", "Failed to update record.")

    def delete_time_worked_entry(self, entry_id: int, row_widget):
        """Удаляет запись из БД."""
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Are you sure you want to delete this record?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = self.db.delete_time_worked(entry_id)
            if success:
                QMessageBox.information(self, "Success", "Record deleted successfully!")
                self.time_entries_layout.removeWidget(row_widget)
                row_widget.deleteLater()
                self.refresh_current_tab()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete record.")

    def refresh_current_tab(self):
        """Обновляет текущую вкладку 'Working hours'."""
        for i in range(self.tabs.count()):
            if "Working hours" in self.tabs.tabText(i):
                self.tabs.removeTab(i)
                self.new_work_day()
                break


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorkTimeApp()
    window.show()
    sys.exit(app.exec())
