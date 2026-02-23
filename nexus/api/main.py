import os
import glob
from datetime import datetime, timedelta
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nexus.config.settings import settings
from nexus.adapters.sqlite import SQLiteConnection
from nexus.api import schemas

app = FastAPI(title="NEXUS Data Access API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["GET"], # STRICTLY READ-ONLY
    allow_headers=["*"],
)

# Conexão reaproveitada (Somente leitura)
conn = SQLiteConnection(settings.nexus_db_path)

@app.get("/health", response_model=schemas.HealthResponse)
def health_check():
    return {"status": "online", "version": "1.0.0"}

# --- CHRONOS (Tarefas) ---

@app.get("/chronos/today", response_model=dict)
def get_chronos_today():
    today_str = datetime.now().strftime("%Y-%m-%d")
    with conn.get_cursor() as cursor:
        cursor.execute("SELECT * FROM tasks WHERE due_date <= ? AND status != 'DONE'", (today_str,))
        rows = cursor.fetchall()
        
    tasks = [{"id": str(r["id"]), "title": r["title"], "status": r["status"], "priority": r["priority"], "due_date": r["due_date"]} for r in rows]
    return {"today": tasks, "overdue_count": len([t for t in tasks if t["due_date"] and t["due_date"] < today_str])}

@app.get("/chronos/tasks", response_model=dict)
def get_chronos_tasks(status: str = Query("open", regex="^(open|done)$"), limit: int = 50, offset: int = 0):
    db_status = "TODO" if status == "open" else "DONE"
    with conn.get_cursor() as cursor:
        cursor.execute("SELECT * FROM tasks WHERE status = ? ORDER BY id DESC LIMIT ? OFFSET ?", (db_status, limit, offset))
        rows = cursor.fetchall()
        
    tasks = [{"id": str(r["id"]), "title": r["title"], "status": r["status"], "priority": r["priority"], "due_date": r["due_date"]} for r in rows]
    return {"tasks": tasks, "total_count": len(tasks)}

# --- TREASURY (Finanças) ---

@app.get("/treasury/summary", response_model=schemas.TreasurySummaryResponse)
def get_treasury_summary(range: str = "month"):
    # Mockando a lógica de balance e limites como regra de negócio pedida na Fase UI
    monthly_limit = 3000.00
    
    with conn.get_cursor() as cursor:
        cursor.execute("SELECT SUM(amount) as total FROM expenses")
        row = cursor.fetchone()
        monthly_expense = row["total"] if row and row["total"] else 0.0

        cursor.execute("SELECT * FROM expenses ORDER BY id DESC LIMIT 5")
        recent = cursor.fetchall()

    txs = [{
        "id": f"tx_{r['id']}", 
        "amount": r["amount"], 
        "type": "EXPENSE", 
        "category": r["category"], 
        "date": r["created_at"][:10]
    } for r in recent]

    return {
        "current_balance": 1500.00, # Fixo por enquanto até implementarmos incomes
        "monthly_expense": monthly_expense,
        "monthly_limit": monthly_limit,
        "remaining_limit": monthly_limit - monthly_expense,
        "recent_transactions": txs
    }

@app.get("/treasury/transactions", response_model=dict)
def get_treasury_transactions(range: str = "month", limit: int = 50, offset: int = 0):
    with conn.get_cursor() as cursor:
        cursor.execute("SELECT * FROM expenses ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
        rows = cursor.fetchall()
        
    txs = [{"id": f"tx_{r['id']}", "amount": r["amount"], "type": "EXPENSE", "category": r["category"], "date": r["created_at"][:10]} for r in rows]
    return {"transactions": txs, "total_count": len(txs)}

# --- RPG (Gamificação) ---

@app.get("/rpg/status", response_model=schemas.RPGStatusResponse)
def get_rpg_status():
    with conn.get_cursor() as cursor:
        cursor.execute("SELECT * FROM rpg_attributes")
        rows = cursor.fetchall()
        
    attributes = {r["name"]: r["current_level"] for r in rows} if rows else {"STR": 1, "INT": 1, "WIS": 1, "CHA": 1}
    
    return {
        "level": 1,
        "total_xp": sum(r["total_xp"] for r in rows) if rows else 0,
        "xp_to_next": 1000,
        "progress_percentage": 25.0, # Placeholder
        "attributes_max": 20,
        "attributes": attributes,
        "current_streak": 0
    }

# --- LIBRARY (Notas FS) ---

def _scan_notes():
    # Helper simples para ler arquivos MD da pasta de notas
    notes_dir = settings.nexus_notes_dir
    os.makedirs(notes_dir, exist_ok=True)
    files = glob.glob(os.path.join(notes_dir, "*.md"))
    
    results = []
    for f in files:
        filename = os.path.basename(f)
        mtime = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
        results.append({
            "id": filename,
            "title": filename.replace(".md", "").replace("_", " ").title(),
            "tags": ["note"],
            "last_modified": mtime
        })
    return sorted(results, key=lambda x: x["last_modified"], reverse=True)

@app.get("/library/notes", response_model=schemas.NotesListResponse)
def get_library_notes(limit: int = 50, offset: int = 0):
    all_notes = _scan_notes()
    return {"notes": all_notes[offset:offset+limit], "total_count": len(all_notes)}

@app.get("/library/search", response_model=schemas.NotesListResponse)
def search_library(q: str):
    all_notes = _scan_notes()
    q_lower = q.lower()
    filtered = [n for n in all_notes if q_lower in n["title"].lower()]
    return {"notes": filtered, "total_count": len(filtered)}

@app.get("/library/note/{id}", response_model=schemas.NoteRead)
def get_note_by_id(id: str):
    filepath = os.path.join(settings.nexus_notes_dir, id)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    mtime = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "id": id,
        "title": id.replace(".md", "").replace("_", " ").title(),
        "tags": ["note"],
        "last_modified": mtime,
        "content": content
    }