from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class Expense:
    amount: float
    category: str
    description: str
    currency: str = "BRL"
    id: int = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Task:
    title: str
    priority: str = "medium"
    status: str = "TODO"
    due_date: str = None
    id: int = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Note:
    content: str
    title: str
    tags: list[str]
    filepath: str = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
