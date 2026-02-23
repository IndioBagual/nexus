import sqlite3

from nexus.adapters.base import NexusAdapter, NexusContext


class AdapterManager:
    def __init__(self, db_path: str = "nexus_simulado.db"):
        self.db_path = db_path
        self.adapters: list[NexusAdapter] = []
        self._setup_db()

    def _setup_db(self):
        """Tabela para o NEXUS lembrar até onde sincronizou cada adaptador."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS adapter_cursors (
                adapter_id TEXT PRIMARY KEY,
                last_cursor TEXT,
                last_sync_time TEXT
            )
        """)
        conn.commit()
        conn.close()

    def register_adapter(self, adapter: NexusAdapter):
        """Registra um novo plugin no motor."""
        self.adapters.append(adapter)
        print(f"🔌 Adaptador registrado: {adapter.adapter_id}")

    def get_cursor(self, adapter_id: str) -> str:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT last_cursor FROM adapter_cursors WHERE adapter_id = ?",
            (adapter_id,),
        ).fetchone()
        conn.close()
        return row[0] if row else ""

    def save_cursor(self, adapter_id: str, new_cursor: str):
        import datetime

        now = datetime.datetime.utcnow().isoformat() + "Z"
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO adapter_cursors (adapter_id, last_cursor, last_sync_time)
            VALUES (?, ?, ?)
            ON CONFLICT(adapter_id) DO UPDATE SET last_cursor=excluded.last_cursor, last_sync_time=excluded.last_sync_time
        """,
            (adapter_id, new_cursor, now),
        )
        conn.commit()
        conn.close()

    def run_sync_cycle(self):
        """O coração do Manager. Roda todos os adaptadores de forma isolada."""
        print("\n🔄 Iniciando ciclo de sincronização externa...")

        for adapter in self.adapters:
            print(f"\n[{adapter.adapter_id}] Verificando conexão...")
            if not adapter.connect():
                print(f"⚠️ Falha na conexão com {adapter.adapter_id}. Pulando.")
                continue

            # Cria o sandbox para este adaptador
            context = NexusContext(
                self.db_path, adapter.adapter_id, adapter.required_permissions
            )

            # Puxa o cursor local (onde paramos da última vez)
            last_cursor = self.get_cursor(adapter.adapter_id)
            print(f"[{adapter.adapter_id}] Cursor atual: '{last_cursor}'")

            try:
                # O Adaptador busca os dados brutos na API externa
                sync_result = adapter.sync(last_cursor)
                raw_data = sync_result.get("raw_data", [])
                new_cursor = sync_result.get("new_cursor", last_cursor)

                if raw_data:
                    print(
                        f"[{adapter.adapter_id}] {len(raw_data)} novos itens encontrados. Mapeando..."
                    )
                    # O Adaptador mapeia e usa o context para injetar no NEXUS
                    adapter.map_to_internal_event(raw_data, context)
                else:
                    print(f"[{adapter.adapter_id}] Nenhum dado novo.")

                # Salva o novo cursor apenas se tudo deu certo
                self.save_cursor(adapter.adapter_id, new_cursor)

            except Exception as e:
                print(f"❌ Erro crítico no adaptador {adapter.adapter_id}: {e}")

        print("\n✅ Ciclo de sincronização finalizado.")
