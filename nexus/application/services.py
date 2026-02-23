import logging
from pydantic import BaseModel, ValidationError
from typing import List, Optional
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

# ============================================================================
# --- SAFETY SCHEMAS (Allowlist & Validation) ---
# ============================================================================

class AddExpenseArgs(BaseModel):
    amount: float
    category: str
    description: str
    currency: str = "BRL"

class AddTaskArgs(BaseModel):
    title: str
    priority: str = "medium"
    status: str = "TODO"
    due_date: Optional[str] = None

class CreateNoteArgs(BaseModel):
    content: str
    title: str = "Untitled Note"
    tags: List[str] = []

class LogRpgActionArgs(BaseModel):
    action_type: str
    quantity: float = 1.0
    description: str
    attribute: Optional[str] = None

ALLOWED_ACTIONS = {
    'add_expense': AddExpenseArgs,
    'add_task': AddTaskArgs,
    'create_note': CreateNoteArgs,
    'log_rpg_action': LogRpgActionArgs
}

# ============================================================================

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
        self.rpg_engine = RPGEngine() 
        
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
            
            # 1. Tratamento Direto de Pergunta da IA
            if action == 'ask_user':
                msg = f"❓ CÓRTEX: {params.get('question')}"
                logger.info(msg)
                report.messages.append(msg)
                continue

            # 2. Segurança: Blocklist / Allowlist
            if action not in ALLOWED_ACTIONS:
                msg = f"⚠️ Ação de segurança ativada: A ferramenta '{action}' não existe ou foi bloqueada."
                logger.warning(msg)
                report.errors.append(msg)
                continue

            # 3. Segurança: Validação Estrita via Pydantic
            try:
                SchemaClass = ALLOWED_ACTIONS[action]
                validated_params = SchemaClass(**params)
            except ValidationError as e:
                # Extrai os erros para formar uma mensagem limpa ao invés de estourar a API
                missing = [err['loc'][0] for err in e.errors() if err['type'] == 'missing']
                invalid = [err['loc'][0] for err in e.errors() if err['type'] != 'missing']
                
                clarification = f"❓ CÓRTEX: Faltam detalhes para processar '{action}'."
                if missing: clarification += f" Preciso saber: {', '.join(map(str, missing))}."
                if invalid: clarification += f" Os dados parecem incorretos: {', '.join(map(str, invalid))}."
                
                logger.info(clarification)
                report.messages.append(clarification)
                continue # Pula a execução desta ferramenta e pede ajuda ao usuário

            # 4. Execução Segura (HitL bypassado apenas se os dados forem perfeitos)
            try:
                safe_data = validated_params.model_dump()

                if action == 'add_expense':
                    expense = Expense(**safe_data)
                    eid = self.expense_repo.add(expense)
                    self.bus.publish(Event(EVENT_EXPENSE_ADDED, {"id": eid, "amount": expense.amount}))
                    report.actions_executed.append(action)
                    report.events_emitted.append(EVENT_EXPENSE_ADDED)
                    msg = f"💸 [TREASURY] R${expense.amount} em '{expense.category}': {expense.description}"
                    logger.info(msg)
                    report.messages.append(msg)
                
                elif action == 'add_task':
                    task = Task(**safe_data)
                    tid = self.task_repo.add(task)
                    self.bus.publish(Event(EVENT_TASK_CREATED, {"id": tid, "priority": task.priority}))
                    report.actions_executed.append(action)
                    report.events_emitted.append(EVENT_TASK_CREATED)
                    msg = f"✅ [CHRONOS] Task '{task.title}' para {task.due_date or 'Hoje'}"
                    logger.info(msg)
                    report.messages.append(msg)
                    
                elif action == 'create_note':
                    note = Note(**safe_data)
                    path = self.note_repo.save(note)
                    self.bus.publish(Event(EVENT_NOTE_CREATED, {"filepath": path, "tags": note.tags}))
                    report.actions_executed.append(action)
                    report.events_emitted.append(EVENT_NOTE_CREATED)
                    msg = f"📝 [LIBRARY] Nota salva: {note.title}"
                    logger.info(msg)
                    report.messages.append(msg)

                elif action == 'log_rpg_action':
                    attr_map = {
                        "exercise": "STR", "meditation": "WIS", 
                        "social": "CHA", "reading": "INT", "study": "INT"
                    }
                    action_type = safe_data.get('action_type')
                    attr_name = safe_data.get('attribute') or attr_map.get(action_type, "WIS")
                    
                    qty = safe_data.get('quantity', 1)
                    xp_amount = max(int(qty) * 1, 5) # Mínimo de 5 XP

                    self._apply_xp(attr_name, xp_amount, "MANUAL", "user_input", safe_data.get('description'))
                    report.actions_executed.append(action)
                    msg = f"⚔️ [RPG] Ação manual registrada: {safe_data.get('description')}"
                    logger.info(msg)
                    report.messages.append(msg)

            except Exception as e:
                err_msg = f"❌ Erro interno ao executar {action}: {str(e)}"
                logger.error(err_msg)
                report.errors.append(err_msg)

        return report

    # --- RPG Helpers ---
    def _apply_xp(self, attr_name: str, amount: int, source_type: str, source_id: str, desc: str):
        attr = self.rpg_repo.get_attribute(attr_name)
        events = self.rpg_engine.process_xp_gain(attr, amount)
        self.rpg_repo.update_attribute(attr)
        self.rpg_repo.log_xp_history(attr_name, amount, source_type, source_id, desc)
        
        for evt in events:
            if evt.name == EVENT_RPG_XP_GAINED:
                logger.info(f"✨ [RPG] +{evt.payload['amount']} {evt.payload['attribute']} (Total: {evt.payload['total_xp']})")
            elif evt.name == EVENT_RPG_LEVEL_UP:
                logger.info(f"🎉 [RPG] LEVEL UP! {evt.payload['attribute']} alcançou Nível {evt.payload['new_level']}!")

    # --- Event Handlers ---
    def _on_expense_added(self, event: Event):
        self._apply_xp("WIS", 5, "TREASURY", str(event.payload['id']), "Despesa registrada")

    def _on_task_created(self, event: Event):
        xp = 10 if event.payload.get('priority') == 'high' else 5
        self._apply_xp("WIS", xp, "CHRONOS", str(event.payload['id']), "Tarefa planejada")

    def _on_note_created(self, event: Event):
        self._apply_xp("INT", 10, "LIBRARY", event.payload['filepath'], "Conhecimento capturado")