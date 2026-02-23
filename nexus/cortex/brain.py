import os
from datetime import datetime

from google import genai
from google.genai import types


class CortexBrain:
    def __init__(self, api_client, memory_engine):
        self.client_api = api_client
        self.memory = memory_engine

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY não encontrada.")

        # NOVA SDK: Inicializa o cliente
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"

        # Definição de Ferramentas (Usando dicionários compatíveis com a nova SDK)
        self.tools = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="read_agenda",
                        description="Check today's tasks and schedule.",
                    ),
                    types.FunctionDeclaration(
                        name="read_finances",
                        description="Check current month's financial summary.",
                    ),
                    types.FunctionDeclaration(
                        name="create_task",
                        description="Create a new task.",
                        parameters=types.Schema(
                            type="OBJECT",
                            properties={
                                "title": types.Schema(type="STRING"),
                                "priority": types.Schema(
                                    type="STRING", enum=["low", "medium", "high"]
                                ),
                                "due_date": types.Schema(type="STRING"),
                            },
                            required=["title"],
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="create_expense",
                        description="Log a financial expense.",
                        parameters=types.Schema(
                            type="OBJECT",
                            properties={
                                "amount": types.Schema(type="NUMBER"),
                                "category": types.Schema(type="STRING"),
                                "description": types.Schema(type="STRING"),
                            },
                            required=["amount", "category", "description"],
                        ),
                    ),
                ]
            )
        ]

    def process_message(self, user_message):
        # 1. RAG Retrieval
        context = self.memory.retrieve(user_message)

        # 2. System Prompt
        sys_instructions = f"""
        You are CORTEX, the active intelligence of NEXUS Life OS.
        Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}

        CORE DIRECTIVES:
        1. **TOOL-FIRST:** Before answering ANY factual question (schedule, finance, status), you MUST call the appropriate Read-Tool. Do not guess.
        2. **ACT TO WRITE:** If the user implies an action (e.g., "remind me", "spent", "log"), use the Write-Tools immediately.
        3. **GROUNDING:** When using information from the "CONTEXT FROM MEMORY" block, you MUST append `[Source: filename]` to the sentence. If the info is not there, say "I don't have this record."
        4. **NO AMBIGUITY:** If a write-command is missing critical parameters (e.g., Expense without Amount, Task without Title), ask ONE clarification question and stop.
        5. **CONCISE:** Output natural, brief responses. No pleasantries ("Hello", "Sure"). Just the execution report or answer.
        
        CONTEXT FROM MEMORY:
        {context}
        """

        # 3. Inicializa Chat (Nova Sintaxe)
        chat = self.client.chats.create(
            model=self.model_id,
            config=types.GenerateContentConfig(
                tools=self.tools, system_instruction=sys_instructions, temperature=0.7
            ),
        )

        # 4. Envia mensagem e processa Tools Automaticamente (ou manual se preferir)
        # Na nova SDK, podemos fazer loop manual para ter controle total do report
        response = chat.send_message(user_message)

        execution_report = []
        final_reply = ""

        try:
            # Loop de execução de ferramentas
            # O modelo pode retornar várias partes, algumas sendo function_calls
            while response.function_calls:
                for call in response.function_calls:
                    tool_name = call.name
                    args = call.args

                    execution_report.append(f"Tool Call: {tool_name} {args}")

                    # Executa a ferramenta
                    result = {"status": "error", "msg": "Tool not found"}
                    if tool_name == "read_agenda":
                        result = self.client_api.get_agenda()
                    elif tool_name == "read_finances":
                        result = self.client_api.get_finances()
                    elif tool_name == "create_task":
                        result = self.client_api.post_task(
                            title=args.get("title"),
                            priority=args.get("priority", "medium"),
                            due_date=args.get("due_date"),
                        )
                    elif tool_name == "create_expense":
                        result = self.client_api.post_expense(
                            amount=args.get("amount"),
                            category=args.get("category"),
                            description=args.get("description"),
                        )

                    # Envia o resultado de volta para o modelo
                    response = chat.send_message(
                        types.Part.from_function_response(
                            name=tool_name, response={"result": result}
                        )
                    )

            # Se não há mais function calls, o texto restante é a resposta final
            if response.text:
                final_reply = response.text
            else:
                final_reply = "Ação executada."

        except Exception as e:
            final_reply = f"Erro no processamento: {str(e)}"

        return {"reply": final_reply, "citations": context, "report": execution_report}
