from client.local_repo import LocalRepo
from client.sync_engine import SyncEngine
import uuid
import time

def rodar_simulacao():
    print("🚀 Iniciando Simulação do Cliente NEXUS...")
    
    # 1. Inicializa o banco local do dispositivo (Offline)
    # Cada device tem seu actor_id único.
    meu_actor_id = "usr_bagual:laptop"
    repo = LocalRepo(actor_id=meu_actor_id, db_path="nexus_simulado.db", notes_path="notas_simuladas")
    engine = SyncEngine(repo, hub_url="http://localhost:8000")
    
    print(f"✅ Banco local criado/carregado para o ator: {meu_actor_id}")

    # 2. Ação Offline (Criando uma tarefa)
    task_id = str(uuid.uuid4())
    print(f"📝 Criando tarefa localmente (Offline)... ID: {task_id[:8]}...")
    
    repo.record_local_op(
        entity_type="TASK", 
        entity_id=task_id, 
        action="CREATE", 
        payload={"title": "Comprar erva-mate", "priority": "high"}
    )
    print("✅ Tarefa salva no SQLite local (mas ainda não enviada para a nuvem).")
    
    # 3. Fazendo o PUSH (Enviando para o Hub)
    print("\n🔄 Iniciando PUSH para o servidor...")
    ops_enviadas = engine.push()
    print(f"✅ PUSH concluído: {ops_enviadas} operação(ões) enviada(s).")
    
    # 4. Fazendo o PULL (Buscando novidades do Hub)
    print("\n🔄 Iniciando PULL do servidor...")
    ops_recebidas = engine.pull()
    print(f"✅ PULL concluído: {ops_recebidas} nova(s) operação(ões) aplicada(s) localmente.")

    # Fechando a conexão (importante no Windows)
    repo.close()
    print("\n🏁 Simulação finalizada com sucesso!")

if __name__ == "__main__":
    rodar_simulacao()