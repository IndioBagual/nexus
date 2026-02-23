from abc import ABC, abstractmethod
from typing import List, Dict, Any
import sqlite3
import json
import uuid
import re
from datetime import datetime

class NexusContext:
    def __init__(self, db_path: str, adapter_id: str, permissions: List[str]):
        self.db_path = db_path
        self.adapter_id = adapter_id
        self.permissions = permissions

    def _sanitize_text(self, text: str) -> str:
        """Filtra palavras perigosas e limita o tamanho do input externo."""
        if not text: return ""
        text = str(text)[:500] # Limite de 500 caracteres (evita estouro de token)
        
        # Remove caracteres muito estranhos, mantendo pontuação básica
        clean = re.sub(r'[^\w\s.,;:!?@/-]', '', text)
        
        # Bloqueia comandos clássicos de prompt injection
        palavras_proibidas = ["ignore", "esqueça", "apague", "instruções anteriores", "bypass"]
        for palavra in palavras_proibidas:
            clean = re.compile(re.escape(palavra), re.IGNORECASE).sub('[BLOQUEADO]', clean)
            
        return clean

    def emit_event(self, event_type: str, domain: str, insight: str, payload: dict, external_id: str):
        if "PROPOSE_ACTION" not in self.permissions:
            raise PermissionError(f"[{self.adapter_id}] Sem permissão para emitir eventos.")

        # APLICA A SANITIZAÇÃO ANTES DE GUARDAR
        insight_seguro = self._sanitize_text(insight)
        
        audit_trail = {
            "source_adapter": self.adapter_id,
            "external_entity_id": external_id,
            "sync_timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # O payload também é convertido para string segura (evita injeção via JSON profundo)
        safe_payload = {k: self._sanitize_text(str(v)) for k, v in payload.items()}
        full_evidence = {"raw_payload": safe_payload, "audit_trail": audit_trail}
        
        conn = sqlite3.connect(self.db_path)
        event_id = f"evt_ext_{uuid.uuid4().hex[:10]}"
        now = datetime.utcnow().isoformat() + "Z"
        
        conn.execute("""
            INSERT INTO analytical_events 
            (id, event_type, domain, confidence, insight, data_evidence, created_at, processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (event_id, event_type, domain, 1.0, insight_seguro, json.dumps(full_evidence), now))
        
        conn.commit()
        conn.close()

class NexusAdapter(ABC):
    """Interface padrão que todo plugin/integração deve respeitar."""
    
    @property
    @abstractmethod
    def adapter_id(self) -> str: pass

    @property
    @abstractmethod
    def required_permissions(self) -> List[str]: pass

    @abstractmethod
    def connect(self) -> bool: pass

    @abstractmethod
    def sync(self, last_cursor: str) -> Dict[str, Any]: pass

    @abstractmethod
    def map_to_internal_event(self, raw_data: List[Any], context: NexusContext): pass