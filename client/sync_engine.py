import json

import requests

from client.local_repo import LocalRepo


class SyncEngine:
    def __init__(self, repo: LocalRepo, hub_url="http://localhost:8000"):
        self.repo = repo
        self.hub_url = hub_url

    def push(self):
        """Envia operações locais não sincronizadas para o Hub."""
        cursor = self.repo.conn.execute("SELECT * FROM sync_op_log WHERE synced = 0")
        rows = cursor.fetchall()

        if not rows:
            return 0

        ops_to_push = []
        for r in rows:
            d = dict(r)
            d["payload"] = json.loads(d["payload"])
            ops_to_push.append(d)

        try:
            res = requests.post(
                f"{self.hub_url}/sync/push", json={"operations": ops_to_push}
            )
            if res.status_code == 200:
                # Marca como sincronizado localmente
                op_ids = [op["op_id"] for op in ops_to_push]
                placeholders = ",".join(["?"] * len(op_ids))
                self.repo.conn.execute(
                    f"UPDATE sync_op_log SET synced = 1 WHERE op_id IN ({placeholders})",
                    op_ids,
                )
                self.repo.conn.commit()
                return len(ops_to_push)
        except requests.exceptions.RequestException as e:
            print(f"Network error during push: {e}")
        return 0

    def pull(self):
        """Busca operações remotas e aplica."""
        last_cursor = self.repo.get_cursor()

        try:
            res = requests.get(f"{self.hub_url}/sync/pull?cursor={last_cursor}")
            if res.status_code == 200:
                data = res.json()
                ops = data.get("operations", [])

                highest_cursor = last_cursor
                applied = 0

                for op in ops:
                    highest_cursor = max(highest_cursor, op["hub_seq"])

                    # Ignora operações que nós mesmos geramos (loopback)
                    if op["actor_id"] == self.repo.actor_id:
                        continue

                    # Registra a operação remota no log local para histórico (opcional, mas bom pra auditoria)
                    # e Aplica a mutação no banco
                    self.repo.apply_to_db(
                        op["entity_type"], op["entity_id"], op["action"], op["payload"]
                    )
                    applied += 1

                # Atualiza cursor
                self.repo.set_cursor(highest_cursor)
                return applied

        except requests.exceptions.RequestException as e:
            print(f"Network error during pull: {e}")
        return 0
