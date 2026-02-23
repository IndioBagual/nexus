import logging
from pydantic import BaseModel
from typing import List
from nexus.domain.entities import Expense, Task, Note
from nexus.domain.ports import ExpenseRepository, TaskRepository, NoteRepository, RPGRepository, CortexProvider
from nexus.domain.events import *
from nexus.domain.rpg_engine import RPGEngine, RPGAttribute, EVENT_RPG_LEVEL_UP, EVENT_RPG_XP_GAINED
from nexus.application.bus import EventBus

logger = logging.getLogger(__name__)

class ExecutionReport(BaseModel):
    actions_executed: List[str] = []
    events_emitted: List[str] = []
    messages: List[str] = []
    errors: List[str] = []

class NexusKernel:
    def __init__(self, 
                 expense_repo: ExpenseRepository,
                 task_repo: TaskRepository,
                 note_repo: NoteRepository,
                 rpg_repo: RPGRepository,
                 cortex: CortexProvider,
                 bus: EventBus):
        self.expense_repo = expense_repo
        self.task_repo = task_repo
        self.note_repo = note_repo
        self.rpg_repo = rpg_repo
        self.cortex = cortex
        self.bus = bus
        self.rpg_engine = RPGEngine() # Instancia o motor lógico
        
        # Registrar listeners
        self.bus.subscribe(EVENT_EXPENSE_ADDED, self._on_expense_added)
        self.bus.subscribe(EVENT_TASK_CREATED, self._on_task_created)
        self.bus.subscribe(EVENT_NOTE_CREATED, self._on_note_created)

    def process_input(self, text: str) -> ExecutionReport:
        report = ExecutionReport()
        try:
            intents = self.cortex.parse_intent(text)
        except Exception as e:
            err_msg = f"❌ Erro de conexão com Córtex: {str(e)}"
            logger.error(err_msg)
            report.errors.append(err_msg)
            return report

        for intent in intents:
            action = intent.get('action')
            params = intent.get('params') or {}
            
            if action == 'ask_user':
                msg = f"❓ CÓRTEX: {params.get('question')}"
                logger.info(msg)
                report.messages.append(msg)
                continue

            try:
                if action == 'add_expense':
                    expense = Expense(**params)
                    eid = self.expense_repo.add(expense)
                    self.bus.publish(Event(EVENT_EXPENSE_ADDED, {"id": eid, "amount": expense.amount}))
                    report.actions_executed.append(action)
                    report.events_emitted.append(EVENT_EXPENSE_ADDED)
                    msg = f"💸 [TREASURY] R${expense.amount} em '{expense.category}': {expense.description}"
                    logger.info(msg)
                    report.messages.append(msg)
                
                elif action == 'add_task':
                    task = Task(**params)
                    tid = self.task_repo.add(task)
                    self.bus.publish(Event(EVENT_TASK_CREATED, {"id": tid, "priority": task.priority}))
                    report.actions_executed.append(action)
                    report.events_emitted.append(EVENT_TASK_CREATED)
                    msg = f"✅ [CHRONOS] Task '{task.title}' para {task.due_date or 'Hoje'}"
                    logger.info(msg)
                    report.messages.append(msg)
                    
                elif action == 'create_note':
                    note = Note(**params)
                    if not note.title: note.title = "Untitled Note" 
                    path = self.note_repo.save(note)
                    self.bus.publish(Event(EVENT_NOTE_CREATED, {"filepath": path, "tags": note.tags}))
                    report.actions_executed.append(action)
                    report.events_emitted.append(EVENT_NOTE_CREATED)
                    msg = f"📝 [LIBRARY] Nota salva: {note.title}"
                    logger.info(msg)
                    report.messages.append(msg)

                elif action == 'log_rpg_action':
                    # Ação manual: Exercício, Meditação, etc.
                    attr_map = {
                        "exercise": "STR",
                        "meditation": "WIS",
                        "social": "CHA",
                        "reading": "INT",
                        "study": "INT"
                    }
                    action_type = params.get('action_type')
                    # Usa atributo explícito ou infere
                    attr_name = params.get('attribute') or attr_map.get(action_type, "WIS")
                    
                    # Cálculo arbitrário para manual action (Ex: 1 xp por minuto/unidade)
                    qty = params.get('quantity', 1)
                    xp_amount = int(qty) * 1 # 1 XP por unidade como base
                    if xp_amount < 5: xp_amount = 5 # Mínimo 5 XP

                    # Aplica XP direto
                    self._apply_xp(attr_name, xp_amount, "MANUAL", "user_input", params.get('description'))
                    report.actions_executed.append(action)
                    msg = f"⚔️ [RPG] Ação manual registrada: {params.get('description')}"
                    logger.info(msg)
                    report.messages.append(msg)

            except Exception as e:
                err_msg = f"❌ Erro ao executar {action}: {str(e)}"
                logger.error(err_msg)
                report.errors.append(err_msg)

        return report

    # --- RPG Helpers ---
    
    def _apply_xp(self, attr_name: str, amount: int, source_type: str, source_id: str, desc: str):
        # 1. Carrega Estado
        attr = self.rpg_repo.get_attribute(attr_name)
        
        # 2. Processa Lógica (Domain)
        events = self.rpg_engine.process_xp_gain(attr, amount)
        
        # 3. Salva Estado (Adapter)
        self.rpg_repo.update_attribute(attr)
        self.rpg_repo.log_xp_history(attr_name, amount, source_type, source_id, desc)
        
        # 4. Feedback
        for evt in events:
            if evt.name == EVENT_RPG_XP_GAINED:
                logger.info(f"✨ [RPG] +{evt.payload['amount']} {evt.payload['attribute']} (Total: {evt.payload['total_xp']})")
            elif evt.name == EVENT_RPG_LEVEL_UP:
                logger.info(f"🎉 [RPG] LEVEL UP! {evt.payload['attribute']} alcançou Nível {evt.payload['new_level']}!")

    # --- Event Handlers ---

    def _on_expense_added(self, event: Event):
        # Regra: Registrar gastos aumenta Sabedoria (WIS)
        self._apply_xp("WIS", 5, "TREASURY", str(event.payload['id']), "Despesa registrada")

    def _on_task_created(self, event: Event):
        # Regra: Planejar tarefas aumenta Sabedoria (WIS) ou Intelecto se for estudo?
        # Por enquanto, simplificado: Planejamento = WIS
        xp = 10 if event.payload.get('priority') == 'high' else 5
        self._apply_xp("WIS", xp, "CHRONOS", str(event.payload['id']), "Tarefa planejada")

    def _on_note_created(self, event: Event):
        # Regra: Notas aumentam Intelecto (INT)
        self._apply_xp("INT", 10, "LIBRARY", event.payload['filepath'], "Conhecimento capturado")