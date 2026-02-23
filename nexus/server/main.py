from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from nexus.server.commands import CommandHandler, TaskCreate, ExpenseCreate, NoteCreate, RPGAction
from typing import Optional
import os

from nexus.server.queries import ReadRepository

# Configuração de Caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "nexus.db")
NOTES_PATH = os.path.join(BASE_DIR, "data", "library", "inbox")
cmd_handler = CommandHandler(DB_PATH, NOTES_PATH)

app = FastAPI(title="NEXUS Data Access API")
repo = ReadRepository(DB_PATH, NOTES_PATH)

# CORS (Permitir desenvolvimento local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- ACTION API (WRITE) ---

@app.post("/api/chronos/tasks")
def create_task(task: TaskCreate):
    return cmd_handler.create_task(task)

@app.post("/api/treasury/expenses")
def create_expense(expense: ExpenseCreate):
    return cmd_handler.create_expense(expense)

@app.post("/api/library/notes")
def create_note(note: NoteCreate):
    return cmd_handler.create_note(note)

# --- Endpoints ---

@app.get("/api/health")
def health():
    return {"status": "ok", "db": os.path.exists(DB_PATH)}

@app.get("/api/chronos/today")
def get_chronos_today():
    return repo.get_todays_tasks()

@app.get("/api/treasury/summary")
def get_treasury_summary():
    return repo.get_monthly_summary()

@app.get("/api/rpg/status")
def get_rpg_status():
    return repo.get_rpg_status()

@app.get("/api/library/notes")
def get_library_notes(limit: int = 10):
    return repo.get_recent_notes(limit)

# Servir Frontend Estático (Deve ser o último para não conflitar com rotas API)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")