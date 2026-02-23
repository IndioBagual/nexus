import sqlite3
from contextlib import contextmanager
from typing import Generator


class SQLiteConnection:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with self.get_cursor() as cursor:
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, amount REAL, category TEXT, description TEXT, currency TEXT, created_at TEXT)"""
            )
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT, priority TEXT, status TEXT, due_date TEXT, created_at TEXT)"""
            )
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS rpg_attributes (name TEXT PRIMARY KEY, total_xp INTEGER, current_level INTEGER)"""
            )
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS rpg_history (id INTEGER PRIMARY KEY, attribute TEXT, xp_amount INTEGER, source_type TEXT, source_id TEXT, description TEXT, created_at TEXT)"""
            )

    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn.cursor()
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
