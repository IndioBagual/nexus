import sqlite3
import json
import uuid
import os
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class SuggestionEngine:
    def __init__(self, db_path="nexus_simulado.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._setup()
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY não encontrada.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"

    def _setup(self):
        """Cria a tabela de propostas aguardando aprovação humana (HITL)."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS proposed_actions (
                id TEXT PRIMARY KEY,
                source_event_id TEXT,
                category TEXT,
                title TEXT,
                context_explanation TEXT,
                tool_name TEXT,
                payload TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at TEXT
            )
        """)
        self.conn.commit()

    def generate_proposals(self):
        """Lê eventos analíticos não processados e pede sugestões ao LLM."""
        cursor = self.conn.execute("SELECT * FROM analytical_events WHERE processed = 0")
        events = cursor.fetchall()

        if not events:
            print("📭 Nenhum novo padrão comportamental para analisar.")
            return

        print(f"💡 Analisando {len(events)} eventos comportamentais...")

        sys_prompt = """
        You are the NEXUS Suggestion Engine. Analyze the behavioral event and propose ONE concrete action to optimize the user's routine or finances.
        Available tools: `create_task`, `create_expense`.
        
        Respond STRICTLY in JSON format:
        {
            "category": "FINANCE" or "ORGANIZATION" or "HABIT",
            "title": "Short title of the suggestion",
            "context_explanation": "A friendly explanation of WHY you are suggesting this based on the data.",
            "tool_name": "the_tool_to_use",
            "payload": {"param1": "value1"} // The exact parameters for the tool
        }
        """

        for event in events:
            # Prepara o contexto do evento para o LLM
            user_prompt = f"""
            Event Type: {event['event_type']}
            Domain: {event['domain']}
            Insight: {event['insight']}
            Evidence: {event['data_evidence']}
            """

            try:
                # Chama o Gemini exigindo saída em JSON estruturado
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_prompt,
                        response_mime_type="application/json",
                        temperature=0.3 # Baixa temperatura para manter a lógica precisa
                    )
                )
                
                suggestion = json.loads(response.text)
                proposal_id = f"prop_{uuid.uuid4().hex[:12]}"
                now = datetime.utcnow().isoformat() + "Z"

                # Salva a proposta na fila de aprovação
                self.conn.execute("""
                    INSERT INTO proposed_actions 
                    (id, source_event_id, category, title, context_explanation, tool_name, payload, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    proposal_id, 
                    event['id'], 
                    suggestion['category'], 
                    suggestion['title'], 
                    suggestion['context_explanation'], 
                    suggestion['tool_name'], 
                    json.dumps(suggestion['payload']), 
                    now
                ))

                # Marca o evento original como processado
                self.conn.execute("UPDATE analytical_events SET processed = 1 WHERE id = ?", (event['id'],))
                self.conn.commit()

                print(f"✨ Proposta Gerada: {suggestion['title']} (Aguardando Aprovação)")

            except Exception as e:
                print(f"❌ Erro ao gerar proposta para o evento {event['id']}: {e}")

        self.conn.close()

if __name__ == "__main__":
    engine = SuggestionEngine(db_path="nexus_simulado.db")
    engine.generate_proposals()