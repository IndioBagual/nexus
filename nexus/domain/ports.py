from abc import ABC, abstractmethod
from typing import List
from .entities import Expense, Task, Note

class ExpenseRepository(ABC):
    @abstractmethod
    def add(self, expense: Expense) -> int: pass

class TaskRepository(ABC):
    @abstractmethod
    def add(self, task: Task) -> int: pass

class NoteRepository(ABC):
    @abstractmethod
    def save(self, note: Note) -> str: pass # Retorna filepath

class RPGRepository(ABC):
    @abstractmethod
    def get_attribute(self, name: str): pass # Retorna RPGAttribute
    @abstractmethod
    def update_attribute(self, attr): pass
    @abstractmethod
    def log_xp_history(self, attribute: str, amount: int, source: str, event_id: str, desc: str): pass

class CortexProvider(ABC):
    @abstractmethod
    def parse_intent(self, text: str) -> List[dict]: pass
