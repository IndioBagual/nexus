import re

from nexus.domain.ports import CortexProvider


class RegexCortexStub(CortexProvider):
    """
    Um roteador 'burro' baseada em regras para teste local sem custo de LLM.
    Simula o que o GPT faria com Function Calling.
    """

    def parse_intent(self, text: str) -> list[dict]:
        intents = []
        text_lower = text.lower()

        # Regra 1: Gastos (ex: "gastei 50 no almoço")
        expense_match = re.search(
            r"gastei (\d+)(?: reais)? (?:no|na|em) (.+)", text_lower
        )
        if expense_match:
            intents.append(
                {
                    "action": "add_expense",
                    "params": {
                        "amount": float(expense_match.group(1)),
                        "category": "Geral",  # Stub não infere categoria bem
                        "description": expense_match.group(2).strip(),
                        "currency": "BRL",
                    },
                }
            )

        # Regra 2: Tarefas (ex: "lembrar de pagar conta")
        if "lembrar de" in text_lower or "fazer" in text_lower:
            clean_text = (
                text_lower.replace("lembrar de", "").replace("fazer", "").strip()
            )
            intents.append(
                {
                    "action": "add_task",
                    "params": {
                        "title": clean_text.capitalize(),
                        "priority": "medium",
                        "status": "TODO",
                    },
                }
            )

        # Regra 3: Notas (ex: "ideia sobre projeto x")
        if "ideia" in text_lower or "nota" in text_lower:
            intents.append(
                {
                    "action": "create_note",
                    "params": {
                        "title": "Nota Rápida",
                        "content": text,
                        "tags": ["inbox", "quick-capture"],
                    },
                }
            )

        return intents
