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
    QLineEdit,
    QPlainTextEdit,
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QDate, QDateTime

from database import DatabaseManager, backup_database_to_zip


class WorkTimeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.period_report_label = None
        self.total_cost_label = None
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

        # Create the first tab by default
        self.new_work_day()

    def create_menu(self):
        menubar = self.menuBar()

        # Меню "File"
        file_menu = menubar.addMenu("&Main")

        projects_config_menu = QAction("&Projects", self)
        projects_config_menu.triggered.connect(self.projects_config)
        file_menu.addAction(projects_config_menu)

        billing_config_menu = QAction("&Billing config", self)
        billing_config_menu.setShortcut("Ctrl+B")
        billing_config_menu.triggered.connect(self.billing_config)
        file_menu.addAction(billing_config_menu)

        new_work_day_menu = QAction("&New work day", self)
        new_work_day_menu.setShortcut("Ctrl+N")
        new_work_day_menu.triggered.connect(self.new_work_day)
        file_menu.addAction(new_work_day_menu)

        period_cost_menu = QAction("&Period cost", self)
        period_cost_menu.setShortcut("Ctrl+P")
        period_cost_menu.triggered.connect(self.period_cost)
        file_menu.addAction(period_cost_menu)

        backup_menu = QAction("&Backup", self)
        backup_menu.setShortcut("Ctrl+Shift+B")
        backup_menu.triggered.connect(self.on_backup_action)
        file_menu.addAction(backup_menu)

        file_menu.addSeparator()

        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # "Help" menu
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        new_work_day_btn = QAction("New work day", self)
        new_work_day_btn.setStatusTip("Create a new work day")
        new_work_day_btn.triggered.connect(self.new_work_day)
        toolbar.addAction(new_work_day_btn)

        period_cost_btn = QAction("Period cost", self)
        period_cost_btn.setStatusTip("Calculate the cost for a period")
        period_cost_btn.triggered.connect(self.period_cost)
        toolbar.addAction(period_cost_btn)

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
            # self.refresh_billing_tab()
            self.on_date_changed(self.date_edit.date())
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

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if isinstance(widget, QTextEdit):
            # Здесь можно добавить проверку на сохранение изменений
            pass
        self.tabs.removeTab(index)

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

        # === Total cost label ===
        self.total_cost_label = QLabel("Total cost: ₽0.00")
        self.total_cost_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: gray;"
        )
        layout.addWidget(self.total_cost_label)

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

        cost = self.calculate_daily_cost()
        if cost == 0:
            self.total_cost_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: gray;"
            )
        else:
            self.total_cost_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: #2c6f2e;"
            )
        self.total_cost_label.setText(f"Total cost: ₽{cost:.2f}")

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

        day_note_edit = QPlainTextEdit()
        day_note_edit.setPlaceholderText("Note (optional)")
        day_note_edit.setMaximumHeight(80)
        if data and data.get("day_note"):
            day_note_edit.setPlainText(data["day_note"])

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
                    day_note_edit.toPlainText().strip(),
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
                    day_note_edit.toPlainText().strip(),
                    row_widget,
                )
            )
            row_layout.addWidget(save_btn)

        row_layout.addStretch()

        self.time_entries_layout.addWidget(row_widget)
        note_layout = QHBoxLayout()
        note_label = QLabel("Note:")
        note_label.setFixedWidth(40)
        note_layout.addWidget(note_label)
        note_layout.addWidget(day_note_edit)
        self.time_entries_layout.addLayout(note_layout)

    def save_new_time_worked_entry(
        self,
        project_name: str,
        hours: int,
        minutes: int,
        tracker: str,
        day_note: str,
        row_widget,
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
            project_id, hours, minutes, tracker, date_int, day_note
        )
        if success:
            QMessageBox.information(self, "Success", "Record saved successfully!")
            self.time_entries_layout.removeWidget(row_widget)
            row_widget.deleteLater()
            self.on_date_changed(self.date_edit.date())
        else:
            QMessageBox.critical(self, "Error", "Failed to save record.")

    def update_time_worked_entry(
        self,
        entry_id: int,
        project_name: str,
        hours: int,
        minutes: int,
        tracker: str,
        day_note: str,
        row_widget,
    ):
        """Обновляет существующую запись в БД."""
        project_id = self.db.get_project_id_by_name(project_name)
        if project_id is None:
            QMessageBox.critical(self, "Error", f"Project '{project_name}' not found.")
            return

        success = self.db.update_time_worked(
            entry_id, project_id, hours, minutes, tracker, day_note
        )
        if success:
            QMessageBox.information(self, "Success", "Record updated successfully!")
            self.on_date_changed(self.date_edit.date())
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
                self.on_date_changed(self.date_edit.date())
            else:
                QMessageBox.critical(self, "Error", "Failed to delete record.")

    def calculate_daily_cost(self):
        """Calculates total cost for the current date based on time entries and billing rates."""
        date_int = self.date_edit.date().startOfDay().toSecsSinceEpoch()
        time_records = self.db.get_time_worked_by_date(date_int)

        # Получаем актуальные ставки: {tracker: hour_cost}
        billing_rates = {}
        for rec in self.db.get_billing():
            # Берём самую свежую ставку для каждого трекера (по started_at DESC)
            tracker = rec["tracker"]
            if (
                tracker not in billing_rates
                or rec["started_at"] > billing_rates[tracker]["started_at"]
            ):
                billing_rates[tracker] = rec

        total_cost = 0.0
        for rec in time_records:
            tracker = rec["tracker"]
            hours = rec["hours"] + rec["minutes"] / 60.0
            rate_record = billing_rates.get(tracker)
            if rate_record:
                total_cost += hours * rate_record["hour_cost"]

        return round(total_cost, 2)

    def period_cost(self):
        """Open a new tab to calculate cost over a selected date range."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # === Date range selection ===
        date_range_layout = QHBoxLayout()

        start_label = QLabel("Start:")
        self.period_start_edit = QDateEdit()
        self.period_start_edit.setCalendarPopup(True)
        self.period_start_edit.setDisplayFormat("dd.MM.yyyy")

        end_label = QLabel("End:")
        self.period_end_edit = QDateEdit()
        self.period_end_edit.setCalendarPopup(True)
        self.period_end_edit.setDisplayFormat("dd.MM.yyyy")

        # Set defaults: end = today, start = Monday of previous week
        today = QDate.currentDate()
        self.period_end_edit.setDate(today)

        # Find Monday of the previous week:
        # Go back 7 days to last week, then to its Monday
        days_since_monday = today.dayOfWeek() - 1  # Monday = 1 → offset = 0
        last_monday = today.addDays(-days_since_monday)
        prev_week_monday = last_monday.addDays(-7)
        self.period_start_edit.setDate(prev_week_monday)

        # Connect to recalculate on change
        self.period_start_edit.dateChanged.connect(self.update_period_report)
        self.period_end_edit.dateChanged.connect(self.update_period_report)

        date_range_layout.addWidget(start_label)
        date_range_layout.addWidget(self.period_start_edit)
        date_range_layout.addWidget(end_label)
        date_range_layout.addWidget(self.period_end_edit)
        date_range_layout.addStretch()

        layout.addLayout(date_range_layout)
        layout.addSpacing(15)

        # === Report area ===
        self.period_report_label = QLabel("Select a period to calculate.")
        self.period_report_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.period_report_label)

        layout.addStretch()

        scroll.setWidget(content)
        index = self.tabs.addTab(scroll, "Period Cost")
        self.tabs.setCurrentIndex(index)

        # Trigger initial calculation
        self.update_period_report()

    def update_period_report(self):
        """Recalculates and displays the cost report for the selected period."""
        start_date = self.period_start_edit.date()
        end_date = self.period_end_edit.date()

        if start_date > end_date:
            self.period_report_label.setText(
                "<b>Error:</b> Start date must be ≤ End date."
            )
            return

        # Get all dates in range
        current = QDate(start_date)
        total_cost = 0.0
        daily_lines = []

        # Preload billing rates (most recent per tracker)
        billing_rates = {}
        for rec in self.db.get_billing():
            tracker = rec["tracker"]
            if (
                tracker not in billing_rates
                or rec["started_at"] > billing_rates[tracker]["started_at"]
            ):
                billing_rates[tracker] = rec

        while current <= end_date:
            date_int = current.startOfDay().toSecsSinceEpoch()
            records = self.db.get_time_worked_by_date(date_int)

            if records:
                day_total = 0.0
                day_details = []
                for rec in records:
                    hours = rec["hours"] + rec["minutes"] / 60.0
                    rate_rec = billing_rates.get(rec["tracker"])
                    cost = hours * rate_rec["hour_cost"] if rate_rec else 0
                    day_total += cost
                    proj = rec.get("project_name", "—")
                    day_details.append(
                        f"  • {proj} | {rec['tracker']} | {rec['hours']}ч {rec['minutes']}мин → ₽{cost:.2f}"
                    )

                total_cost += day_total
                date_str = current.toString("dd.MM.yyyy (ddd)")
                daily_lines.append(f"<b>{date_str}</b>: ₽{day_total:.2f}")
                daily_lines.extend(day_details)
            else:
                pass
                # Optional: show empty days
                # date_str = current.toString("dd.MM.yyyy (ddd)")
                # daily_lines.append(f"<b>{date_str}</b>: no entries")

            current = current.addDays(1)

        if daily_lines:
            report = f"<h3>Total cost: ₽{total_cost:.2f}</h3>\n" + "<br>".join(
                daily_lines
            )
        else:
            report = "<i>No work records found in the selected period.</i>"

        self.period_report_label.setText(report)

    def projects_config(self):
        """Open a tab to manage projects."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        title_label = QLabel("Projects Management")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        # Container for project rows
        self.projects_entries_layout = QVBoxLayout()
        self.projects_entries_widget = QWidget()
        self.projects_entries_widget.setLayout(self.projects_entries_layout)

        # Load existing projects
        projects = self.db.get_all_projects_with_ids()
        if projects:
            for proj in projects:
                self.add_project_entry_row(proj)
        else:
            self.add_project_entry_row(None)  # empty row for new project

        layout.addWidget(self.projects_entries_widget)

        # Add button
        add_button = QPushButton("➕ Add Project")
        add_button.clicked.connect(lambda: self.add_project_entry_row(None))
        layout.addWidget(add_button)
        layout.addStretch()

        scroll.setWidget(content)
        index = self.tabs.addTab(scroll, "Projects")
        self.tabs.setCurrentIndex(index)

    def add_project_entry_row(self, project: dict = None):
        """Add a row for a new or existing project."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        name_edit = QLineEdit()
        if project:
            name_edit.setText(project["name"])
        else:
            name_edit.setPlaceholderText("Enter project name")

        if project is None:
            # New project → Save button
            save_btn = QPushButton("💾 Save")
            save_btn.setFixedSize(70, 30)
            save_btn.clicked.connect(
                lambda: self.save_new_project(name_edit.text(), row_widget)
            )
            btn_widget = save_btn
        else:
            # Existing project → Update & Delete
            update_btn = QPushButton("🔄")
            update_btn.setFixedSize(30, 30)
            update_btn.clicked.connect(
                lambda: self.update_existing_project(
                    project["id"], name_edit.text(), row_widget
                )
            )

            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(30, 30)
            delete_btn.clicked.connect(
                lambda: self.delete_existing_project(project["id"], row_widget)
            )

            btn_layout = QHBoxLayout()
            btn_layout.addWidget(update_btn)
            btn_layout.addWidget(delete_btn)
            btn_widget = QWidget()
            btn_widget.setLayout(btn_layout)

        row_layout.addWidget(name_edit)
        row_layout.addWidget(btn_widget)
        row_layout.addStretch()

        self.projects_entries_layout.addWidget(row_widget)

    def save_new_project(self, name: str, row_widget):
        if not name.strip():
            QMessageBox.warning(self, "Warning", "Project name cannot be empty.")
            return
        success = self.db.add_project(name)
        if success:
            QMessageBox.information(self, "Success", "Project added successfully!")
            self.projects_entries_layout.removeWidget(row_widget)
            row_widget.deleteLater()
            # Refresh the entire tab
            self.refresh_projects_tab()
        else:
            QMessageBox.critical(
                self, "Error", "Failed to add project.\nIt may already exist."
            )

    def update_existing_project(self, proj_id: int, new_name: str, row_widget):
        if not new_name.strip():
            QMessageBox.warning(self, "Warning", "Project name cannot be empty.")
            return
        success = self.db.update_project(proj_id, new_name)
        if success:
            QMessageBox.information(self, "Success", "Project updated successfully!")
            self.refresh_projects_tab()
        else:
            QMessageBox.critical(
                self, "Error", "Failed to update project.\nName may already be in use."
            )

    def delete_existing_project(self, proj_id: int, row_widget):
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this project?\nAll related time records will also be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = self.db.delete_project(proj_id)
            if success:
                QMessageBox.information(
                    self, "Success", "Project deleted successfully!"
                )
                self.projects_entries_layout.removeWidget(row_widget)
                row_widget.deleteLater()
                # Also refresh combo boxes in other tabs
                self.refresh_projects_in_combos()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete project.")

    def refresh_projects_tab(self):
        """Recreates the Projects tab to reflect changes."""
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Projects":
                self.tabs.removeTab(i)
                self.projects_config()
                break

    def refresh_projects_in_combos(self):
        """Optionally reload project lists in open work-day tabs (advanced)."""
        # For simplicity, we skip dynamic update of other tabs.
        # In real app, you might emit a signal or store references to combos.
        pass

    def on_backup_action(self):
        db_path = self.db.db_path
        archive_path = backup_database_to_zip(db_path)
        if archive_path:
            QMessageBox.information(self, "Success", f"Backup saved:\n{archive_path}")
        else:
            QMessageBox.critical(self, "Error", "Failed to create backup!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorkTimeApp()
    window.show()
    sys.exit(app.exec())
