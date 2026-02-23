from typing import Any

from nexus.adapters.base import NexusAdapter, NexusContext


class MockCalendarAdapter(NexusAdapter):
    @property
    def adapter_id(self) -> str:
        return "mock_google_calendar_v1"

    @property
    def required_permissions(self) -> list[str]:
        return ["PROPOSE_ACTION"]  # Pedindo permissão para gerar insights

    def connect(self) -> bool:
        # Aqui iria o fluxo de OAuth. Como é mock, sempre retorna True.
        return True

    def sync(self, last_cursor: str) -> dict[str, Any]:
        # Simula que a API do Google Calendar só retorna dados se o cursor estiver vazio
        if last_cursor == "":
            fake_google_data = [
                {
                    "id": "gcal_123",
                    "summary": "Reunião de Alinhamento",
                    "date": "2026-02-21T10:00:00Z",
                },
                {
                    "id": "gcal_124",
                    "summary": "Dentista",
                    "date": "2026-02-22T14:30:00Z",
                },
            ]
            return {"raw_data": fake_google_data, "new_cursor": "sync_token_8899"}

        # Se já tem cursor, simula que não há eventos novos
        return {"raw_data": [], "new_cursor": last_cursor}

    def map_to_internal_event(self, raw_data: list[Any], context: NexusContext):
        # Transforma o JSON do "Google" em um evento compreensível pelo NEXUS
        for item in raw_data:
            insight_text = f"Compromisso externo detectado: '{item['summary']}' em {item['date'][:10]}."

            # Usa o sandbox para injetar no sistema de forma segura
            context.emit_event(
                event_type="EXTERNAL_APPOINTMENT",
                domain="CALENDAR",
                insight=insight_text,
                payload=item,
                external_id=item["id"],
            )
