import json
import os
import sqlite3
import uuid

# NOVA IMPORTAÇÃO
from datetime import datetime, timezone


class LocalRepo:
    def __init__(self, actor_id: str, db_path: str, notes_path: str):
        self.actor_id = actor_id
        self.notes_path = notes_path
        os.makedirs(self.notes_path, exist_ok=True)

        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._setup()

    def _setup(self):
        # Migração: Usamos TEXT para IDs (UUIDs)
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, title TEXT, priority TEXT, status TEXT, due_date TEXT
            );
            CREATE TABLE IF NOT EXISTS expenses (
                id TEXT PRIMARY KEY, amount REAL, category TEXT, description TEXT
            );
            CREATE TABLE IF NOT EXISTS sync_op_log (
                op_id TEXT PRIMARY KEY, actor_id TEXT, entity_type TEXT, 
                entity_id TEXT, action TEXT, payload TEXT, timestamp TEXT,
                synced INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS sync_state (
                id INTEGER PRIMARY KEY, last_cursor INTEGER DEFAULT 0
            );
            INSERT OR IGNORE INTO sync_state (id, last_cursor) VALUES (1, 0);
        """)
        self.conn.commit()

    def get_cursor(self):
        return self.conn.execute(
            "SELECT last_cursor FROM sync_state WHERE id = 1"
        ).fetchone()[0]

    def set_cursor(self, cursor: int):
        self.conn.execute(
            "UPDATE sync_state SET last_cursor = ? WHERE id = 1", (cursor,)
        )
        self.conn.commit()

    def record_local_op(
        self, entity_type: str, entity_id: str, action: str, payload: dict
    ):
        """Grava a intenção no log e aplica localmente imediatamente (Offline First)."""
        op_id = str(uuid.uuid4())

        # CORREÇÃO DO WARNING AQUI
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # 1. Grava no log local de operações pendentes
        self.conn.execute(
            """
            INSERT INTO sync_op_log (op_id, actor_id, entity_type, entity_id, action, payload, timestamp, synced)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """,
            (
                op_id,
                self.actor_id,
                entity_type,
                entity_id,
                action,
                json.dumps(payload),
                timestamp,
            ),
        )
        self.conn.commit()

        # 2. Aplica na tabela real
        self.apply_to_db(entity_type, entity_id, action, payload)

    def apply_to_db(self, entity_type: str, entity_id: str, action: str, payload: dict):
        """Merge determinístico no SQLite baseado na operação."""
        cursor = self.conn.cursor()
        if entity_type == "TASK":
            if action == "CREATE":
                cursor.execute(
                    "INSERT OR IGNORE INTO tasks (id, title, priority, status) VALUES (?, ?, ?, ?)",
                    (
                        entity_id,
                        payload.get("title"),
                        payload.get("priority", "medium"),
                        "TODO",
                    ),
                )
            elif action == "UPDATE":
                # Merge em nível de campo: só atualiza os campos presentes no payload
                for key, value in payload.items():
                    if key in ["title", "priority", "status", "due_date"]:
                        cursor.execute(
                            f"UPDATE tasks SET {key} = ? WHERE id = ?",
                            (value, entity_id),
                        )

        elif entity_type == "EXPENSE":
            if action == "CREATE":
                cursor.execute(
                    "INSERT OR IGNORE INTO expenses (id, amount, category, description) VALUES (?, ?, ?, ?)",
                    (
                        entity_id,
                        payload.get("amount"),
                        payload.get("category"),
                        payload.get("description"),
                    ),
                )

        elif entity_type == "NOTE":
            file_path = os.path.join(self.notes_path, f"{entity_id}.md")
            new_content = payload.get("content", "")

            if action in ["CREATE", "UPDATE"]:
                if os.path.exists(file_path):
                    with open(file_path, encoding="utf-8") as f:
                        local_content = f.read()
                    # Resolução de Conflito Markdown: Se o texto local difere do remoto recebido, fazemos o fork
                    if local_content != new_content:
                        conflict_path = os.path.join(
                            self.notes_path, f"{entity_id}_conflict.md"
                        )
                        with open(conflict_path, "w", encoding="utf-8") as f:
                            f.write(local_content)  # Salva o local como conflito
                        print(
                            f"⚠️ CONFLITO DETECTADO na nota {entity_id}. Merge manual necessário."
                        )

                # Sobrescreve com a versão mais recente
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

    def close(self):
        """Fecha a conexão com o banco para liberar o arquivo no Windows."""
        self.conn.close()
