from pydantic import BaseModel
from typing import List, Optional, Dict

class HealthResponse(BaseModel):
    status: str
    version: str

class TaskRead(BaseModel):
    id: str
    title: str
    status: str
    priority: str
    due_date: Optional[str]

class TransactionRead(BaseModel):
    id: str
    amount: float
    type: str
    category: str
    date: str

class TreasurySummaryResponse(BaseModel):
    current_balance: float
    monthly_expense: float
    monthly_limit: float
    remaining_limit: float
    recent_transactions: List[TransactionRead]

class RPGStatusResponse(BaseModel):
    level: int
    total_xp: int
    xp_to_next: int
    progress_percentage: float
    attributes_max: int
    attributes: Dict[str, int]
    current_streak: int

class NoteRead(BaseModel):
    id: str
    title: str
    tags: List[str]
    last_modified: str
    content: Optional[str] = None

class NotesListResponse(BaseModel):
    notes: List[NoteRead]
    total_count: int