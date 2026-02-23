import argparse
import os

from nexus.adapters.fs_repo import MarkdownFileAdapter

# --- MUDANÇA AQUI: Importar Gemini ---
from nexus.adapters.gemini_cortex import GeminiCortexAdapter
from nexus.adapters.sqlite_repo import SQLiteAdapter
from nexus.application.bus import EventBus
from nexus.application.services import NexusKernel

DB_PATH = "nexus.db"
NOTES_PATH = "data/library/inbox"


def main():
    parser = argparse.ArgumentParser(description="NEXUS LIFE OS - Gemini Core")
    parser.add_argument("input", type=str, help="Texto natural de entrada")
    args = parser.parse_args()

    # --- MUDANÇA AQUI: Verificar Chave do Google ---
    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌ Erro: Defina a variável de ambiente GOOGLE_API_KEY")
        print("   (No PowerShell: $env:GOOGLE_API_KEY='sua-chave')")
        return

    # 1. Infraestrutura
    sql_adapter = SQLiteAdapter(DB_PATH)
    fs_adapter = MarkdownFileAdapter(NOTES_PATH)

    # 2. Cérebro (Gemini 1.5 Flash)
    try:
        cortex_adapter = GeminiCortexAdapter(model_name="gemini-2.5-flash")
    except Exception as e:
        print(f"❌ Erro ao conectar no Gemini: {e}")
        return

    # 3. Aplicação
    bus = EventBus()
    kernel = NexusKernel(
        expense_repo=sql_adapter,
        task_repo=sql_adapter,
        note_repo=fs_adapter,
        rpg_repo=sql_adapter,
        cortex=cortex_adapter,
        bus=bus,
    )

    # 4. Execução
    print("🧠 Córtex (Gemini) analisando...")
    results = kernel.process_input(args.input)

    # 5. Output
    if not results:
        print("⚠️  Nenhuma ação identificada ou erro de conexão.")
    else:
        for res in results:
            print(res)


if __name__ == "__main__":
    main()
