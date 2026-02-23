import datetime
import json
import logging
import os
import sqlite3
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from nexus.adapters.manager import AdapterManager
from nexus.adapters.plugins.mock_calendar import MockCalendarAdapter
from nexus.config.settings import settings
from nexus.cortex.brain import CortexBrain
from nexus.cortex.client import APIClient
from nexus.cortex.memory import MemoryEngine

load_dotenv()

DB_PATH = settings.nexus_db_path


def cleanup_expired_proposals():
    """Remove propostas pendentes com mais de 48 horas."""
    try:
        conn = sqlite3.connect(DB_PATH)
        # Calcula a data limite (48 horas atrás)
        cutoff_date = (
            datetime.datetime.utcnow() - datetime.timedelta(hours=48)
        ).isoformat() + "Z"

        cursor = conn.execute(
            """
            UPDATE proposed_actions 
            SET status = 'EXPIRED' 
            WHERE status = 'PENDING' AND created_at < ?
        """,
            (cutoff_date,),
        )

        deleted_count = cursor.rowcount
        conn.commit()
        if deleted_count > 0:
            print(
                f"🧹 [TTL] Limpeza: {deleted_count} propostas expiradas foram removidas da fila."
            )
    except Exception as e:
        print(f"❌ Erro na limpeza de propostas: {e}")
    finally:
        conn.close()


# --- ROTINA DE BACKGROUND (CRON JOB) ---
def run_adapters_job():
    """Função que será executada automaticamente pelo agendador."""
    print("\n⏳ [CRON] A iniciar rotina de sincronização de adaptadores...")
    try:
        manager = AdapterManager(db_path=DB_PATH)
        manager.register_adapter(MockCalendarAdapter())
        manager.run_sync_cycle()
    except Exception as e:
        print(f"❌ Erro no Cron Job de adaptadores: {e}")


# --- GESTÃO DO CICLO DE VIDA DO FASTAPI ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_adapters_job, "interval", minutes=1)
    scheduler.add_job(cleanup_expired_proposals, "interval", hours=1)

    scheduler.start()
    print("🕒 Scheduler iniciado (Adaptadores e Limpeza TTL ativos).")
    yield
    scheduler.shutdown()


# Inicializamos a app com o ciclo de vida configurado
app = FastAPI(title="NEXUS Córtex API", lifespan=lifespan)

# --- CONFIGURAÇÃO DE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Permite o Vite (React)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialização do Córtex
api_client = APIClient(base_url="http://localhost:8000/api")
memory = MemoryEngine()
brain = CortexBrain(api_client, memory)


class ChatRequest(BaseModel):
    message: str


class IngestRequest(BaseModel):
    pass


@app.post("/cortex/chat")
def chat(req: ChatRequest):
    return brain.process_message(req.message)


@app.post("/cortex/ingest")
def ingest(req: IngestRequest):
    notes_path = settings.nexus_notes_dir
    count = 0
    if os.path.exists(notes_path):
        for f in os.listdir(notes_path):
            if f.endswith(".md"):
                with open(os.path.join(notes_path, f), encoding="utf-8") as file:
                    memory.ingest_note(f, file.read(), [])
                    count += 1
    return {"status": "success", "indexed_files": count}


@app.get("/cortex/proposals")
def list_pending_proposals():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM proposed_actions WHERE status = 'PENDING'")
        proposals = [dict(row) for row in cursor.fetchall()]

        for p in proposals:
            if p["payload"]:
                p["payload"] = json.loads(p["payload"])
        return {"proposals": proposals}
    finally:
        conn.close()


@app.post("/cortex/proposals/{proposal_id}/approve")
def approve_proposal(proposal_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM proposed_actions WHERE id = ? AND status = 'PENDING'",
            (proposal_id,),
        )
        proposal = cursor.fetchone()

        if not proposal:
            raise HTTPException(
                status_code=404, detail="Proposta não encontrada ou já processada."
            )

        tool_name = proposal["tool_name"]
        payload = json.loads(proposal["payload"])

        print(f"\n✅ EXECUTANDO AÇÃO APROVADA: {tool_name} com dados: {payload}")

        conn.execute(
            "UPDATE proposed_actions SET status = 'APPROVED' WHERE id = ?",
            (proposal_id,),
        )
        conn.commit()

        return {"status": "success", "message": "Proposta aprovada e executada."}
    finally:
        conn.close()


@app.post("/cortex/proposals/{proposal_id}/reject")
def reject_proposal(proposal_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE proposed_actions SET status = 'REJECTED' WHERE id = ?",
            (proposal_id,),
        )
        conn.commit()
        return {"status": "success", "message": "Proposta rejeitada."}
    finally:
        conn.close()


# =====================================================================
# --- ENDPOINTS DE LEITURA PARA A UI (DATA ACCESS API) ---
# =====================================================================


@app.get("/api/chronos/today")
def get_chronos_today():
    return {
        "today": [
            {
                "id": "t1",
                "title": "Revisar arquitetura do NEXUS",
                "status": "TODO",
                "priority": "high",
                "due_date": None,
            },
            {
                "id": "t2",
                "title": "Treino físico (30 min)",
                "status": "TODO",
                "priority": "medium",
                "due_date": None,
            },
            {
                "id": "t3",
                "title": "Ler 10 páginas",
                "status": "DONE",
                "priority": "low",
                "due_date": None,
            },
        ],
        "overdue_count": 1,
    }


@app.get("/api/chronos/tasks")
def get_chronos_tasks(status: str = "open"):
    if status == "open":
        tasks = [
            {
                "id": "t1",
                "title": "Revisar arquitetura do NEXUS",
                "status": "TODO",
                "priority": "high",
                "due_date": "Hoje",
            },
            {
                "id": "t2",
                "title": "Treino físico (30 min)",
                "status": "TODO",
                "priority": "medium",
                "due_date": "Hoje",
            },
        ]
    else:
        tasks = [
            {
                "id": "t3",
                "title": "Ler 10 páginas",
                "status": "DONE",
                "priority": "low",
                "due_date": "Ontem",
            }
        ]
    return {"tasks": tasks, "total_count": len(tasks)}


@app.get("/api/treasury/summary")
def get_treasury_summary(range: str = "week"):
    # REGRA DE NEGÓCIO MANTIDA NO BACKEND:
    monthly_limit = 3000.00
    monthly_expense = 850.00
    remaining_limit = monthly_limit - monthly_expense

    return {
        "current_balance": 1450.00,
        "monthly_expense": monthly_expense,
        "monthly_limit": monthly_limit,
        "remaining_limit": remaining_limit,  # Enviado calculado para a UI
        "recent_transactions": [
            {
                "id": "tx1",
                "amount": 45.90,
                "type": "EXPENSE",
                "category": "Ifood",
                "date": "2026-02-20",
            },
            {
                "id": "tx4",
                "amount": 120.00,
                "type": "EXPENSE",
                "category": "Mercado",
                "date": "2026-02-18",
            },
            {
                "id": "tx2",
                "amount": 2500.00,
                "type": "INCOME",
                "category": "Pagamento",
                "date": "2026-02-15",
            },
        ],
    }


@app.get("/api/treasury/transactions")
def get_treasury_transactions(range: str = "month"):
    txs = [
        {
            "id": "tx1",
            "amount": 45.90,
            "type": "EXPENSE",
            "category": "Ifood",
            "date": "2026-02-20",
        },
        {
            "id": "tx4",
            "amount": 120.00,
            "type": "EXPENSE",
            "category": "Mercado",
            "date": "2026-02-18",
        },
        {
            "id": "tx2",
            "amount": 2500.00,
            "type": "INCOME",
            "category": "Pagamento",
            "date": "2026-02-15",
        },
    ]
    return {"transactions": txs, "total_count": len(txs)}


@app.get("/api/rpg/status")
def get_rpg_status():
    # REGRA DE NEGÓCIO MANTIDA NO BACKEND:
    xp_to_next = 550
    total_xp_for_level = 1000
    current_level_xp = total_xp_for_level - xp_to_next
    progress_percentage = (current_level_xp / total_xp_for_level) * 100

    return {
        "level": 14,
        "total_xp": 8450,
        "xp_to_next": xp_to_next,
        "progress_percentage": progress_percentage,  # Enviado calculado para a UI
        "attributes_max": 20,  # Limite do atributo enviado para a UI
        "attributes": {"INT": 18, "FOR": 12, "CAR": 10},
        "current_streak": 7,
    }


@app.get("/api/library/notes")
def get_library_notes(limit: int = 5, offset: int = 0):
    return {
        "notes": [
            {
                "id": "n1",
                "title": "Cibersegurança: Descoberta de IPs",
                "tags": ["tech", "aula"],
                "last_modified": "2026-02-19",
            },
            {
                "id": "n2",
                "title": "Ideias para o App de Flert",
                "tags": ["projetos", "web"],
                "last_modified": "2026-02-15",
            },
            {
                "id": "n3",
                "title": "Saúde Mental: Estrutura da Apresentação",
                "tags": ["psicologia", "palestra"],
                "last_modified": "2026-02-10",
            },
        ],
        "total_count": 3,
    }


@app.get("/api/library/search")
def search_library(q: str):
    mock_notes = [
        {
            "id": "n1",
            "title": "Cibersegurança: Descoberta de IPs",
            "tags": ["tech", "aula"],
            "last_modified": "2026-02-19",
        },
        {
            "id": "n2",
            "title": "Ideias para o App de Flert",
            "tags": ["projetos", "web"],
            "last_modified": "2026-02-15",
        },
        {
            "id": "n3",
            "title": "Saúde Mental: Estrutura da Apresentação",
            "tags": ["psicologia", "palestra"],
            "last_modified": "2026-02-10",
        },
    ]

    q_lower = q.lower()
    filtered = [
        n
        for n in mock_notes
        if q_lower in n["title"].lower()
        or any(q_lower in tag.lower() for tag in n["tags"])
    ]

    return {"notes": filtered, "total_count": len(filtered)}


@app.get("/cortex/health")
def health():
    return {"status": "active", "memory": "chromadb_connected"}
