from dataclasses import dataclass
from typing import Any

@dataclass
class Event:
    name: str
    payload: dict[str, Any]

# Constantes de Eventos
EVENT_EXPENSE_ADDED = "TREASURY_EXPENSE_ADDED"
EVENT_TASK_CREATED = "CHRONOS_TASK_CREATED"
EVENT_NOTE_CREATED = "LIBRARY_NOTE_CREATED"