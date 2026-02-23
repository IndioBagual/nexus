import os
import shutil
import time
import unittest
import uuid

from client.local_repo import LocalRepo
from hub.repo import HubRepo


class TestNexusSync(unittest.TestCase):
    def setUp(self):
        # Limpa resíduos de testes
        for path in ["test_hub.db", "client_a.db", "client_b.db", "notes_a", "notes_b"]:
            if os.path.exists(path):
                if os.path.isdir(path):
                    # ignore_errors=True diz pro Python ignorar o bloqueio do OneDrive
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    try:
                        os.remove(path)
                    except PermissionError:
                        pass  # Ignora se o DB estiver preso

        # Inicia Hub Central
        self.hub = HubRepo("test_hub.db")

        # Inicia dois Clients Isolados
        self.client_a = LocalRepo("actor_A", "client_a.db", "notes_a")
        self.client_b = LocalRepo("actor_B", "client_b.db", "notes_b")

    def tearDown(self):
        """Garante que as conexões SQLite sejam fechadas após CADA teste."""
        self.hub.close()
        self.client_a.close()
        self.client_b.close()
        # Uma pequena pausa pro Windows respirar e liberar os handles
        time.sleep(0.1)

    def simulate_push(self, client: LocalRepo):
        cursor = client.conn.execute("SELECT * FROM sync_op_log WHERE synced = 0")
        ops = [dict(r) for r in cursor.fetchall()]
        for op in ops:
            op["payload"] = __import__("json").loads(op["payload"])

        if ops:
            self.hub.push_ops(ops)
            op_ids = [op["op_id"] for op in ops]
            placeholders = ",".join(["?"] * len(op_ids))
            client.conn.execute(
                f"UPDATE sync_op_log SET synced = 1 WHERE op_id IN ({placeholders})",
                op_ids,
            )
            client.conn.commit()

    def simulate_pull(self, client: LocalRepo):
        cursor = client.get_cursor()
        ops = self.hub.pull_ops(cursor)

        highest = cursor
        for op in ops:
            highest = max(highest, op["hub_seq"])
            if op["actor_id"] != client.actor_id:
                client.apply_to_db(
                    op["entity_type"], op["entity_id"], op["action"], op["payload"]
                )
        client.set_cursor(highest)

    def test_concurrent_inserts(self):
        """Cenário 1: Dispositivos inserem tarefas offline simultaneamente."""
        task_a_id = str(uuid.uuid4())
        task_b_id = str(uuid.uuid4())

        self.client_a.record_local_op("TASK", task_a_id, "CREATE", {"title": "Task A"})
        self.client_b.record_local_op("TASK", task_b_id, "CREATE", {"title": "Task B"})

        self.simulate_push(self.client_a)
        self.simulate_push(self.client_b)
        self.simulate_pull(self.client_a)
        self.simulate_pull(self.client_b)

        count_a = self.client_a.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        count_b = self.client_b.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        self.assertEqual(count_a, 2)
        self.assertEqual(count_b, 2)

    def test_field_level_merge(self):
        """Cenário 2: Atualização de campos diferentes na mesma tarefa offline."""
        task_id = str(uuid.uuid4())

        self.client_a.record_local_op("TASK", task_id, "CREATE", {"title": "Original"})
        self.simulate_push(self.client_a)
        self.simulate_pull(self.client_b)

        self.client_a.record_local_op("TASK", task_id, "UPDATE", {"status": "DONE"})
        self.client_b.record_local_op("TASK", task_id, "UPDATE", {"priority": "high"})

        self.simulate_push(self.client_a)
        self.simulate_push(self.client_b)
        self.simulate_pull(self.client_a)
        self.simulate_pull(self.client_b)

        task_a = self.client_a.conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        self.assertEqual(task_a["status"], "DONE")
        self.assertEqual(task_a["priority"], "high")

    def test_markdown_conflict_resolution(self):
        """Cenário 3: Resolução de conflitos em arquivos Markdown (Fork/Review)."""
        # Agora usamos UUID para não esbarrar em arquivos antigos presos no OneDrive
        note_id = str(uuid.uuid4())

        self.client_a.record_local_op("NOTE", note_id, "CREATE", {"content": "Base"})
        self.simulate_push(self.client_a)
        self.simulate_pull(self.client_b)

        self.client_a.record_local_op(
            "NOTE", note_id, "UPDATE", {"content": "Versão do A"}
        )
        self.client_b.record_local_op(
            "NOTE", note_id, "UPDATE", {"content": "Versão do B"}
        )

        self.simulate_push(self.client_b)
        self.simulate_pull(self.client_a)

        main_file = os.path.join("notes_a", f"{note_id}.md")
        conflict_file = os.path.join("notes_a", f"{note_id}_conflict.md")

        self.assertTrue(
            os.path.exists(conflict_file), "O arquivo de conflito não foi gerado."
        )

        with open(main_file, encoding="utf-8") as f:
            self.assertEqual(f.read(), "Versão do B")
        with open(conflict_file, encoding="utf-8") as f:
            self.assertEqual(f.read(), "Versão do A")


if __name__ == "__main__":
    unittest.main()
