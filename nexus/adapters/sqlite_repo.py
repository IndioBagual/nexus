import sqlite3

from nexus.domain.entities import Expense, Note, Task
from nexus.domain.ports import (
    ExpenseRepository,
    NoteRepository,
    RPGRepository,
    TaskRepository,
)
from nexus.domain.rpg_engine import RPGAttribute


class SQLiteAdapter(ExpenseRepository, TaskRepository, NoteRepository, RPGRepository):
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._setup_tables()
        self._init_rpg_state()  # Inicializa atributos se vazio

    def _setup_tables(self):
        cursor = self.conn.cursor()
        # ... (Tabelas expenses e tasks já existentes - manter igual) ...
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL, category TEXT, description TEXT, 
                currency TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, priority TEXT, status TEXT, 
                due_date TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- TABELAS RPG ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rpg_attributes (
                name TEXT PRIMARY KEY,
                total_xp INTEGER DEFAULT 0,
                current_level INTEGER DEFAULT 1,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rpg_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attribute TEXT,
                xp_amount INTEGER,
                source_type TEXT, 
                source_id TEXT, 
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def _init_rpg_state(self):
        """Garante que STR, INT, WIS, CHA existam."""
        cursor = self.conn.cursor()
        attributes = ["STR", "INT", "WIS", "CHA"]
        for attr in attributes:
            cursor.execute(
                "INSERT OR IGNORE INTO rpg_attributes (name, total_xp, current_level) VALUES (?, 0, 1)",
                (attr,),
            )
        self.conn.commit()

    # ... (Métodos add expense/task mantidos) ...
    def add(self, item) -> int:
        cursor = self.conn.cursor()
        if isinstance(item, Expense):
            cursor.execute(
                "INSERT INTO expenses (amount, category, description, currency) VALUES (?, ?, ?, ?)",
                (item.amount, item.category, item.description, item.currency),
            )
        elif isinstance(item, Task):
            cursor.execute(
                "INSERT INTO tasks (title, priority, status, due_date) VALUES (?, ?, ?, ?)",
                (item.title, item.priority, item.status, item.due_date),
            )
        self.conn.commit()
        return cursor.lastrowid

    def save(self, note: Note) -> str:
        # Stub para manter compatibilidade com interface NoteRepository se estiver usando este adapter
        # No código anterior usamos fs_adapter, mas se precisar:
        return "saved_in_fs"

    # --- IMPLEMENTAÇÃO RPG ---

    def get_attribute(self, name: str) -> RPGAttribute:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name, total_xp, current_level FROM rpg_attributes WHERE name = ?",
            (name,),
        )
        row = cursor.fetchone()
        if row:
            return RPGAttribute(name=row[0], total_xp=row[1], current_level=row[2])
        return RPGAttribute(name=name, total_xp=0, current_level=1)

    def update_attribute(self, attr: RPGAttribute):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE rpg_attributes SET total_xp = ?, current_level = ?, last_updated = CURRENT_TIMESTAMP WHERE name = ?",
            (attr.total_xp, attr.current_level, attr.name),
        )
        self.conn.commit()

    def log_xp_history(
        self, attribute: str, amount: int, source: str, event_id: str, desc: str
    ):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO rpg_history (attribute, xp_amount, source_type, source_id, description) VALUES (?, ?, ?, ?, ?)",
            (attribute, amount, source, str(event_id), desc),
        )
        self.conn.commit()

    # O método antigo log_xp era genérico, agora removemos ou adaptamos se necessário.
    # Vamos usar os métodos específicos acima.
