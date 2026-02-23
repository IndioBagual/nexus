from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# --- CORTEX SCHEMAS ---
class CortexRequest(BaseModel):
    text: str

class CortexResponse(BaseModel):
    assistant_message: str
    execution_report: Dict[str, Any]
    citations: List[Dict[str, str]] = []
    needs_clarification: bool = False
    question: Optional[str] = None

# --- DIRECT ACTION SCHEMAS ---
class ExpenseCreate(BaseModel):
    amount: float
    category: str
    description: str
    currency: str = "BRL"

class TaskCreate(BaseModel):
    title: str
    priority: str = "medium"
    status: str = "TODO"
    due_date: Optional[str] = None

class NoteCreate(BaseModel):
    title: str
    content: str
    tags: List[str] = []