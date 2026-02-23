import os
import google.genai  # <--- Convenção padrão
from google.genai.types import content_types
from collections.abc import Iterable
from datetime import datetime
from typing import List
from nexus.domain.ports import CortexProvider

class GeminiCortexAdapter(CortexProvider):
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-flash"):
        # 1. Configuração da API Key
        api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY não encontrada. Defina no ambiente.")
        
        google.genai.configure(api_key=api_key)
        
        # 2. Definição das Ferramentas (Tools Schema)
        self.tools_schema = [
            {
                "name": "add_expense",
                "description": "Log a financial expense.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "amount": {"type": "NUMBER", "description": "Numeric value"},
                        "category": {"type": "STRING", "enum": ["Food", "Transport", "Health", "Education", "Leisure", "Bills", "Other"]},
                        "description": {"type": "STRING"},
                        "currency": {"type": "STRING"}
                    },
                    "required": ["amount", "category", "description"]
                }
            },
            {
                "name": "add_task",
                "description": "Create a task or reminder.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING"},
                        "priority": {"type": "STRING", "enum": ["low", "medium", "high"]},
                        "due_date": {"type": "STRING", "description": "ISO 8601 date (YYYY-MM-DD)"},
                        "status": {"type": "STRING", "enum": ["TODO", "DONE"]}
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "create_note",
                "description": "Save a thought, idea, or journal entry.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING"},
                        "content": {"type": "STRING"},
                        "tags": {"type": "ARRAY", "items": {"type": "STRING"}}
                    },
                    "required": ["content"]
                }
            },
            # Tool do RPG (Adicionada na etapa anterior)
            {
                "name": "log_rpg_action",
                "description": "Log a manual action for RPG XP gain.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action_type": {"type": "STRING", "enum": ["exercise", "meditation", "social", "reading", "study"]},
                        "quantity": {"type": "NUMBER", "description": "Duration in minutes or count"},
                        "description": {"type": "STRING"},
                        "attribute": {"type": "STRING", "enum": ["STR", "INT", "WIS", "CHA"]}
                    },
                    "required": ["action_type", "quantity", "description"]
                }
            }
        ]

        # 3. System Prompt
        self.current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.system_instruction = f"""
        Role: You are CORTEX, the routing kernel of a Life OS.
        Objective: Map user input to specific tool calls.
        Current Context: {self.current_time}
        Constraints:
        1. DO NOT chat. DO NOT explain.
        2. If the user input implies multiple actions, call multiple tools.
        3. If critical information is missing, respond with a text question.
        """

        # 4. Inicialização do Modelo usando 'genai'
        self.model = google.genai.GenerativeModel(
            model_name=model_name,
            tools=self.tools_schema,
            system_instruction=self.system_instruction
        )

    def parse_intent(self, text: str) -> List[dict]:
        """
        Envia texto para o Gemini e converte FunctionCalls em dicionários.
        """
        # Inicia chat (obrigatório para function calling automático no SDK novo)
        chat = self.model.start_chat(enable_automatic_function_calling=False)
        
        try:
            response = chat.send_message(text)
        except Exception as e:
            # Tratamento básico de erro de API
            return [{"action": "ask_user", "params": {"question": f"Erro na API do Gemini: {str(e)}"}}]

        intents = []

        # Itera sobre as partes da resposta (pode haver texto + função ou múltiplas funções)
        for part in response.parts:
            # Caso A: Chamada de Função Encontrada
            if fn := part.function_call:
                args = dict(fn.args)
                
                # Tratamento de defaults (Sanitização)
                if fn.name == "add_expense" and "currency" not in args:
                    args["currency"] = "BRL"
                if fn.name == "add_task":
                    if "priority" not in args: args["priority"] = "medium"
                    if "status" not in args: args["status"] = "TODO"

                intents.append({
                    "action": fn.name,
                    "params": args
                })
            
            # Caso B: Texto (Geralmente pergunta ou esclarecimento)
            elif text_content := part.text:
                if text_content.strip(): # Ignora espaços vazios
                    # Se tiver texto E function call, o texto costuma ser irrelevante ("Sure, I'll do that")
                    # Mas se NÃO tiver function call, é uma pergunta pro usuário.
                    if not any(p.function_call for p in response.parts):
                        intents.append({
                            "action": "ask_user",
                            "params": {"question": text_content.strip()}
                        })

        return intents