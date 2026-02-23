import os
import tempfile
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from nexus.adapters.sqlite import SQLiteConnection, ExpenseSQLiteRepo, TaskSQLiteRepo
from nexus.adapters.fs_repo import MarkdownFileAdapter
from nexus.domain.entities import Expense, Task, Note
from nexus.application.services import NexusKernel
from nexus.application.bus import EventBus
from nexus.api.main import app

# --- 1. Teste da API Read-Only (/health) ---
def test_api_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "online", "version": "1.0.0"}

# --- 2. Testes de Repositórios SQLite ---
def test_expense_sqlite_repo():
    # Usa banco em memória para ser instantâneo e não sujar o disco
    conn = SQLiteConnection(":memory:")
    repo = ExpenseSQLiteRepo(conn)
    expense = Expense(amount=25.50, category="Food", description="Almoço", currency="BRL")
    
    eid = repo.add(expense)
    assert eid == 1 # O ID gerado deve ser 1 no banco vazio

def test_task_sqlite_repo():
    conn = SQLiteConnection(":memory:")
    repo = TaskSQLiteRepo(conn)
    task = Task(title="Comprar café", priority="high", status="TODO")
    
    tid = repo.add(task)
    assert tid == 1

# --- 3. Testes do Markdown Indexer (FS Repo) ---
def test_markdown_indexer_save():
    # Usa pasta temporária que se auto-destrói
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = MarkdownFileAdapter(tmpdir)
        note = Note(title="Ideias", content="# Projeto X", tags=["work"])
        
        filepath = repo.save(note)
        assert os.path.exists(filepath)
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            assert "title: Ideias" in content
            assert "# Projeto X" in content

def test_markdown_indexer_fallback_title():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = MarkdownFileAdapter(tmpdir)
        note = Note(title="", content="Sem titulo explicito", tags=[])
        
        filepath = repo.save(note)
        assert os.path.exists(filepath)

# --- 4. Teste do Fluxo de Ação (Kernel -> Execution Report) ---
def test_kernel_action_flow():
    # Mockando a infraestrutura para focar na regra de negócio
    mock_expense_repo = MagicMock()
    mock_task_repo = MagicMock()
    mock_note_repo = MagicMock()
    mock_rpg_repo = MagicMock()
    mock_cortex = MagicMock()
    
    # Simulando o Córtex retornando uma intenção perfeita
    mock_cortex.parse_intent.return_value = [{
        "action": "add_task",
        "params": {"title": "Revisar testes", "priority": "high", "status": "TODO"}
    }]
    
    kernel = NexusKernel(
        mock_expense_repo, mock_task_repo, mock_note_repo, 
        mock_rpg_repo, mock_cortex, EventBus()
    )
    
    # Executa a string de input falso
    report = kernel.process_input("Me lembre de revisar os testes urgente")
    
    # Verifica o ExecutionReport
    assert "add_task" in report.actions_executed
    assert "TaskCreated" in report.events_emitted
    assert len(report.errors) == 0
    assert "Revisar testes" in report.messages[0]
    
    # Verifica se o repositório foi efetivamente chamado
    mock_task_repo.add.assert_called_once()