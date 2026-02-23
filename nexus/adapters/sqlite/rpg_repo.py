from datetime import datetime

from nexus.adapters.sqlite.connection import SQLiteConnection
from nexus.domain.ports import RPGRepository
from nexus.domain.rpg_engine import RPGAttribute


class RpgSQLiteRepo(RPGRepository):
    def __init__(self, conn: SQLiteConnection):
        self.conn = conn

    def get_attribute(self, name: str) -> RPGAttribute:
        with self.conn.get_cursor() as cursor:
            cursor.execute(
                "SELECT name, total_xp, current_level FROM rpg_attributes WHERE name = ?",
                (name,),
            )
            row = cursor.fetchone()
            if row:
                return RPGAttribute(
                    name=row["name"],
                    total_xp=row["total_xp"],
                    current_level=row["current_level"],
                )
            return RPGAttribute(name=name, total_xp=0, current_level=1)

    def update_attribute(self, attr: RPGAttribute):
        with self.conn.get_cursor() as cursor:
            cursor.execute(
                "SELECT name FROM rpg_attributes WHERE name = ?", (attr.name,)
            )
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE rpg_attributes SET total_xp = ?, current_level = ? WHERE name = ?",
                    (attr.total_xp, attr.current_level, attr.name),
                )
            else:
                cursor.execute(
                    "INSERT INTO rpg_attributes (name, total_xp, current_level) VALUES (?, ?, ?)",
                    (attr.name, attr.total_xp, attr.current_level),
                )

    def log_xp_history(
        self, attr_name: str, amount: int, source_type: str, source_id: str, desc: str
    ):
        with self.conn.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO rpg_history (attribute, xp_amount, source_type, source_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (attr_name, amount, source_type, source_id, desc, datetime.now()),
            )
