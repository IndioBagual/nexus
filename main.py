import argparse
import logging

from nexus.adapters.fs_repo import MarkdownFileAdapter
from nexus.adapters.gemini_cortex import GeminiCortexAdapter
from nexus.adapters.sqlite import (
    ExpenseSQLiteRepo,
    RpgSQLiteRepo,
    SQLiteConnection,
    TaskSQLiteRepo,
)
from nexus.application.bus import EventBus
from nexus.application.services import NexusKernel
from nexus.config.settings import settings

# Configuração global de logs para o terminal
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="NEXUS LIFE OS - Gemini Core")
    parser.add_argument("input", type=str, help="Texto natural de entrada")
    args = parser.parse_args()

    # 1. Infraestrutura (Usando as configurações centralizadas)
    conn = SQLiteConnection(settings.nexus_db_path)
    expense_repo = ExpenseSQLiteRepo(conn)
    task_repo = TaskSQLiteRepo(conn)
    rpg_repo = RpgSQLiteRepo(conn)

    fs_adapter = MarkdownFileAdapter(settings.nexus_notes_dir)

    # 2. Cérebro (Gemini)
    try:
        # A API Key e os caminhos agora são puxados automaticamente pelo settings
        cortex_adapter = GeminiCortexAdapter(model_name="gemini-2.5-flash")
    except Exception as e:
        logger.error(f"Erro ao conectar no Gemini: {e}")
        return

    # 3. Aplicação (Injeção das novas dependências segregadas)
    bus = EventBus()
    kernel = NexusKernel(
        expense_repo=expense_repo,
        task_repo=task_repo,
        note_repo=fs_adapter,
        rpg_repo=rpg_repo,
        cortex=cortex_adapter,
        bus=bus,
    )

    # 4. Execução
    logger.info("Córtex (Gemini) a analisar a intenção...")
    report = kernel.process_input(args.input)

    # 5. Output (Formatando o novo ExecutionReport do Commit 5)
    print("\n" + "=" * 40)
    print("🧠 RELATÓRIO DE EXECUÇÃO DO CÓRTEX")
    print("=" * 40)

    if not report.actions_executed and not report.messages and not report.errors:
        print("⚠️ Nenhuma ação identificada ou o Córtex não retornou dados.")
    else:
        if report.actions_executed:
            print(f"🛠️  Ferramentas ativadas: {', '.join(report.actions_executed)}")

        if report.events_emitted:
            print(f"📡 Eventos de Domínio: {', '.join(report.events_emitted)}")

        if report.messages:
            print("\n💬 Respostas:")
            for msg in report.messages:
                print(f"  - {msg}")

        if report.errors:
            print("\n❌ Erros Críticos:")
            for err in report.errors:
                print(f"  - {err}")

    print("=" * 40 + "\n")


if __name__ == "__main__":
    main()
