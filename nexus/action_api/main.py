from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nexus.config.settings import settings
from nexus.adapters.sqlite import SQLiteConnection, ExpenseSQLiteRepo, TaskSQLiteRepo, RpgSQLiteRepo
from nexus.adapters.fs_repo import MarkdownFileAdapter
from nexus.adapters.gemini_cortex import GeminiCortexAdapter
from nexus.application.bus import EventBus
from nexus.application.services import NexusKernel
from nexus.domain.entities import Expense, Task, Note
from nexus.action_api import schemas

app = FastAPI(title="NEXUS Action & Cortex API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["POST", "PUT", "DELETE"], # STRICTLY WRITES
    allow_headers=["*"],
)

# 1. Injeção de Dependências
conn = SQLiteConnection(settings.nexus_db_path)
expense_repo = ExpenseSQLiteRepo(conn)
task_repo = TaskSQLiteRepo(conn)
rpg_repo = RpgSQLiteRepo(conn)
note_repo = MarkdownFileAdapter(settings.nexus_notes_dir)
bus = EventBus()

try:
    cortex_adapter = GeminiCortexAdapter()
except Exception as e:
    cortex_adapter = None # Permite iniciar a API mesmo sem chave, mas bloqueia o /cortex

kernel = NexusKernel(
    expense_repo=expense_repo,
    task_repo=task_repo,
    note_repo=note_repo,
    rpg_repo=rpg_repo,
    cortex=cortex_adapter,
    bus=bus
)

# --- CORTEX ENDPOINTS ---

@app.post("/cortex/chat", response_model=schemas.CortexResponse)
@app.post("/cortex/command", response_model=schemas.CortexResponse)
def process_cortex_command(req: schemas.CortexRequest):
    if not cortex_adapter:
        raise HTTPException(status_code=500, detail="Córtex offline. Verifique sua GOOGLE_API_KEY.")
    
    # Processa via Kernel (Domain)
    report = kernel.process_input(req.text)
    
    needs_clarification = False
    question = None
    assistant_message = ""
    
    # Human-in-the-loop: Avalia as mensagens retornadas pelo Kernel
    for msg in report.messages:
        if msg.startswith("❓ CÓRTEX:"):
            needs_clarification = True
            question = msg.replace("❓ CÓRTEX:", "").strip()
            assistant_message += f"**Clarificação necessária:** {question}\n\n"
        else:
            assistant_message += f"- {msg}\n"
            
    if not assistant_message:
        if report.errors:
            assistant_message = "**Erros encontrados:**\n" + "\n".join([f"- {e}" for e in report.errors])
        else:
            assistant_message = "Comando processado, mas nenhuma ação gerou feedback."

    return schemas.CortexResponse(
        assistant_message=assistant_message,
        execution_report=report.model_dump(),
        citations=[], # Placeholder para RAG futuro
        needs_clarification=needs_clarification,
        question=question
    )

# --- DIRECT ACTION ENDPOINTS (Bypass Cortex) ---

@app.post("/chronos/task")
def create_task(req: schemas.TaskCreate):
    task = Task(title=req.title, priority=req.priority, status=req.status, due_date=req.due_date)
    tid = task_repo.add(task)
    return {"status": "success", "task_id": tid}

@app.post("/treasury/expense")
def create_expense(req: schemas.ExpenseCreate):
    expense = Expense(amount=req.amount, category=req.category, description=req.description, currency=req.currency)
    eid = expense_repo.add(expense)
    return {"status": "success", "expense_id": eid}

@app.post("/library/note")
def create_note(req: schemas.NoteCreate):
    note = Note(title=req.title, content=req.content, tags=req.tags)
    path = note_repo.save(note)
    return {"status": "success", "filepath": path}