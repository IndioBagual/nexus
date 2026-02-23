
from pydantic import BaseModel

from nexus.adapters.fs_repo import MarkdownFileAdapter
from nexus.adapters.sqlite_repo import SQLiteAdapter
from nexus.application.bus import EventBus
from nexus.application.services import NexusKernel
from nexus.domain.entities import Expense, Note, Task
from nexus.domain.ports import CortexProvider


# Modelos Pydantic para validação de entrada da API
class TaskCreate(BaseModel):
    title: str
    priority: str = "medium"
    due_date: str | None = None


class ExpenseCreate(BaseModel):
    amount: float
    category: str
    description: str


class NoteCreate(BaseModel):
    title: str
    content: str
    tags: list[str] = []


class RPGAction(BaseModel):
    action_type: str
    quantity: float
    description: str


# Stub para satisfazer a injeção de dependência do Kernel (já que a API recebe o comando pronto)
class NoOpCortex(CortexProvider):
    def parse_intent(self, text):
        return []


class CommandHandler:
    def __init__(self, db_path: str, notes_path: str):
        self.sql_repo = SQLiteAdapter(db_path)
        self.fs_repo = MarkdownFileAdapter(notes_path)
        self.bus = EventBus()
        # Instancia o Kernel para garantir que eventos (XP) sejam disparados
        self.kernel = NexusKernel(
            self.sql_repo,
            self.sql_repo,
            self.fs_repo,
            self.sql_repo,
            NoOpCortex(),
            self.bus,
        )

    def create_task(self, data: TaskCreate):
        task = Task(title=data.title, priority=data.priority, due_date=data.due_date)
        tid = self.sql_repo.add(task)
        # Dispara evento manualmente ou via kernel se refatorado.
        # Aqui chamamos o listener direto para simplificar o MVP
        self.kernel._on_task_created(
            type(
                "Event", (object,), {"payload": {"id": tid, "priority": task.priority}}
            )()
        )
        return {"id": tid, "status": "created"}

    def create_expense(self, data: ExpenseCreate):
        expense = Expense(
            amount=data.amount, category=data.category, description=data.description
        )
        eid = self.sql_repo.add(expense)
        self.kernel._on_expense_added(
            type(
                "Event", (object,), {"payload": {"id": eid, "amount": expense.amount}}
            )()
        )
        return {"id": eid, "status": "created"}

    def create_note(self, data: NoteCreate):
        note = Note(title=data.title, content=data.content, tags=data.tags)
        path = self.fs_repo.save(note)
        self.kernel._on_note_created(
            type("Event", (object,), {"payload": {"filepath": path}})()
        )
        return {"path": path, "status": "created"}
