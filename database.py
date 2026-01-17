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
        Возвращает список последних файлов (только существующих на диске).
        Удаляет из БД записи о несуществующих файлах.
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
