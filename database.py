import sqlite3
import os
from typing import List, Optional


class DatabaseManager:
    """
    Управляет подключением к SQLite и предоставляет методы
    для работы с таблицами приложения.
    """

    def __init__(self, db_path: str = "WTBase.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """Возвращает новое соединение с базой данных."""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Создаёт необходимые таблицы при первом запуске."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Таблица недавних файлов
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS recent_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filepath TEXT UNIQUE NOT NULL,
                    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.commit()

    def add_recent_file(self, filepath: str) -> bool:
        """Добавляет или обновляет запись о файле в recent_files."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Удаляем старую запись, чтобы обновить время
                cursor.execute(
                    "DELETE FROM recent_files WHERE filepath = ?", (filepath,)
                )
                cursor.execute(
                    "INSERT INTO recent_files (filepath) VALUES (?)", (filepath,)
                )
                return True
        except sqlite3.Error as e:
            print(f"Database error (add_recent_file): {e}")
            return False

    def get_recent_files(self, limit: int = 10) -> List[str]:
        """
        Returns a list of recent_files from the recent_files table.
        """
        valid_files = []
        to_remove = []

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT filepath FROM recent_files
                    ORDER BY opened_at DESC
                    LIMIT ?
                """,
                    (limit,),
                )

                for row in cursor.fetchall():
                    filepath = row[0]
                    if os.path.exists(filepath):
                        valid_files.append(filepath)
                    else:
                        to_remove.append(filepath)

                # Удаляем "битые" ссылки
                if to_remove:
                    placeholders = ",".join("?" * len(to_remove))
                    cursor.execute(
                        f"DELETE FROM recent_files WHERE filepath IN ({placeholders})",
                        to_remove,
                    )

        except sqlite3.Error as e:
            print(f"Database error (get_recent_files): {e}")

        return valid_files

    def get_projects(self) -> List[str]:
        """
        Returns a list of project names from the projects table.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT project_name FROM projects ORDER BY id")
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        except sqlite3.Error as e:
            print(f"Database error (get_projects): {e}")
            return []

    def get_billing(self) -> List[dict]:
        """
        Returns a list of billing records from the billing table.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                                SELECT id, tracker, started_at, hour_cost
                                FROM billing
                                ORDER BY tracker, started_at DESC
                            """
                )
                rows = cursor.fetchall()
                return [
                    {
                        "id": row[0],
                        "tracker": row[1],
                        "started_at": row[2],
                        "hour_cost": row[3],
                    }
                    for row in rows
                ]
        except sqlite3.Error as e:
            print(f"Database error (get_billing): {e}")
            return []

    def add_billing_record(self, tracker: str, started_at: int, hour_cost: int) -> bool:
        """
        Adds a new billing record to the billing table.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO billing (tracker, started_at, hour_cost)
                    VALUES (?, ?, ?)
                    """,
                    (tracker, started_at, hour_cost),
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error (add_billing_record): {e}")
            return False

    def get_time_worked_by_date(self, date_int: int) -> List[dict]:
        """
        Returns a list of time worked records for a specific date.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT tw.id, tw.hours, tw.minutes, tw.tracker, p.project_name
                    FROM time_worked tw
                    JOIN projects p ON tw.project = p.id
                    WHERE tw.date = ?
                """,
                    (date_int,),
                )
                rows = cursor.fetchall()
                return [
                    {
                        "id": row[0],
                        "hours": row[1],
                        "minutes": row[2],
                        "tracker": row[3],
                        "project_name": row[4],
                    }
                    for row in rows
                ]
        except sqlite3.Error as e:
            print(f"Database error (get_time_worked_by_date): {e}")
            return []

    def save_time_worked(
        self, project_id: int, hours: float, minutes: int, tracker: str, date_int: int
    ) -> bool:
        """
        Saves a new time worked entry.
        date_int — Unix timestamp.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO time_worked (project, hours, minutes, tracker, date)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (project_id, hours, minutes, tracker, date_int),
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error (save_time_worked): {e}")
            return False

    def update_time_worked(
        self, entry_id: int, project_id: int, hours: float, minutes: int, tracker: str
    ) -> bool:
        """
        Updates an existing time worked entry.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE time_worked
                    SET project = ?, hours = ?, minutes = ?, tracker = ?
                    WHERE id = ?
                """,
                    (project_id, hours, minutes, tracker, entry_id),
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error (update_time_worked): {e}")
            return False

    def delete_time_worked(self, entry_id: int) -> bool:
        """
        Deletes a time worked entry by its ID.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM time_worked WHERE id = ?", (entry_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error (delete_time_worked): {e}")
            return False

    def get_project_id_by_name(self, project_name: str) -> int:
        """
        Возвращает ID проекта по имени.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM projects WHERE project_name = ?", (project_name,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Database error (get_project_id_by_name): {e}")
            return None
