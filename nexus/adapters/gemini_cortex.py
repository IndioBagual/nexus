from datetime import datetime
from typing import List
from google import genai
from google.genai import types
from nexus.domain.ports import CortexProvider
from nexus.config.settings import settings

class GeminiCortexAdapter(CortexProvider):
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-flash"):
        # 1. Configuração da API Key via Pydantic Settings
        api_key = api_key or settings.google_api_key
        if not api_key:
            raise ValueError("GOOGLE_API_KEY não encontrada. Defina no ambiente.")
        
        # O novo SDK inicializa um Client invés de usar métodos globais
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        
        # 2. Definição das Ferramentas usando a estrutura correta do google-genai (types.Schema)
        self.tools = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="add_expense",
                        description="Log a financial expense.",
                        parameters=types.Schema(
                            type="OBJECT",
                            properties={
                                "amount": types.Schema(type="NUMBER", description="Numeric value"),
                                "category": types.Schema(type="STRING", enum=["Food", "Transport", "Health", "Education", "Leisure", "Bills", "Other"]),
                                "description": types.Schema(type="STRING"),
                                "currency": types.Schema(type="STRING")
                            },
                            required=["amount", "category", "description"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="add_task",
                        description="Create a task or reminder.",
                        parameters=types.Schema(
                            type="OBJECT",
                            properties={
                                "title": types.Schema(type="STRING"),
                                "priority": types.Schema(type="STRING", enum=["low", "medium", "high"]),
                                "due_date": types.Schema(type="STRING", description="ISO 8601 date (YYYY-MM-DD)"),
                                "status": types.Schema(type="STRING", enum=["TODO", "DONE"])
                            },
                            required=["title"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="create_note",
                        description="Save a thought, idea, or journal entry.",
                        parameters=types.Schema(
                            type="OBJECT",
                            properties={
                                "title": types.Schema(type="STRING"),
                                "content": types.Schema(type="STRING"),
                                "tags": types.Schema(type="ARRAY", items=types.Schema(type="STRING"))
                            },
                            required=["content"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="log_rpg_action",
                        description="Log a manual action for RPG XP gain.",
                        parameters=types.Schema(
                            type="OBJECT",
                            properties={
                                "action_type": types.Schema(type="STRING", enum=["exercise", "meditation", "social", "reading", "study"]),
                                "quantity": types.Schema(type="NUMBER", description="Duration in minutes or count"),
                                "description": types.Schema(type="STRING"),
                                "attribute": types.Schema(type="STRING", enum=["STR", "INT", "WIS", "CHA"])
                            },
                            required=["action_type", "quantity", "description"]
                        )
                    )
                ]
            )
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

    def parse_intent(self, text: str) -> List[dict]:
        """
        Envia texto para o Gemini e extrai chamadas de função usando o SDK v1+.
        """
        # A configuração de ferramentas e instruções agora é passada na sessão
        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            tools=self.tools,
            temperature=0.0,
        )
        
        chat = self.client.chats.create(model=self.model_name, config=config)
        
        try:
            response = chat.send_message(text)
        except Exception as e:
            return [{"action": "ask_user", "params": {"question": f"Erro na API do Gemini: {str(e)}"}}]

        intents = []

        # O novo SDK centraliza as chamadas de função no array function_calls
        if response.function_calls:
            for fc in response.function_calls:
                args = dict(fc.args) if fc.args else {}
                
                # Tratamento de defaults (Sanitização)
                if fc.name == "add_expense" and "currency" not in args:
                    args["currency"] = "BRL"
                if fc.name == "add_task":
                    if "priority" not in args: args["priority"] = "medium"
                    if "status" not in args: args["status"] = "TODO"

                intents.append({
                    "action": fc.name,
                    "params": args
                })
        # Se não houver chamadas de função, verifica se o modelo respondeu com texto
        elif response.text and response.text.strip():
            intents.append({
                "action": "ask_user",
                "params": {"question": response.text.strip()}
            })

        return intents