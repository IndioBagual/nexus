import json
import sqlite3


class HubRepo:
    def __init__(self, db_path="hub.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._setup()

    def _setup(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS global_op_log (
                hub_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                op_id TEXT UNIQUE,
                actor_id TEXT,
                entity_type TEXT,
                entity_id TEXT,
                action TEXT,
                payload TEXT,
                timestamp TEXT
            )
        """)
        self.conn.commit()

    def push_ops(self, ops: list) -> int:
        cursor = self.conn.cursor()
        inserted = 0
        for op in ops:
            try:
                # INSERT OR IGNORE garante idempotência (ignora op_id duplicado)
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO global_op_log 
                    (op_id, actor_id, entity_type, entity_id, action, payload, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        op["op_id"],
                        op["actor_id"],
                        op["entity_type"],
                        op["entity_id"],
                        op["action"],
                        json.dumps(op["payload"]),
                        op["timestamp"],
                    ),
                )
                if cursor.rowcount > 0:
                    inserted += 1
            except sqlite3.Error as e:
                print(f"Hub Error on push: {e}")
        self.conn.commit()
        return inserted

    def pull_ops(self, cursor_seq: int) -> list:
        cursor = self.conn.execute(
            "SELECT * FROM global_op_log WHERE hub_seq > ? ORDER BY hub_seq ASC",
            (cursor_seq,),
        )
        rows = cursor.fetchall()

        result = []
        for r in rows:
            d = dict(r)
            d["payload"] = json.loads(
                d["payload"]
            )  # Converte string de volta para dict
            result.append(d)
        return result

    # NOVO MÉTODO (Adicione no final da classe HubRepo)
    def close(self):
        """Fecha a conexão com o banco para liberar o arquivo no Windows."""
        self.conn.close()
