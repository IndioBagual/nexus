
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client()

print("🔍 Vasculhando a API do Google em busca dos modelos de Embedding...\n")

try:
    for model in client.models.list():
        # Procuramos qualquer modelo que tenha a palavra 'embed' no nome ou nos métodos suportados
        if "embed" in str(model).lower() or "embed" in model.name.lower():
            print(f"✅ NOME EXATO PARA USAR: {model.name}")
except Exception as e:
    print(f"Erro ao consultar API: {e}")
