import math
from dataclasses import dataclass
from typing import Optional, List
from nexus.domain.events import Event

# Constantes de Eventos de Saída
EVENT_RPG_XP_GAINED = "RPG_XP_GAINED"
EVENT_RPG_LEVEL_UP = "RPG_LEVEL_UP"

@dataclass
class RPGAttribute:
    name: str  # STR, INT, WIS, CHA
    total_xp: int
    current_level: int

class RPGEngine:
    """
    Domínio puro: Calcula progresso e decide se houve Level Up.
    Não salva no banco, apenas processa lógica.
    """
    
    @staticmethod
    def calculate_level(total_xp: int) -> int:
        """
        Calcula o nível baseado no XP total.
        XP_Necessario = 100 * (Level - 1) ^ 1.5
        Inverso: Level = (XP / 100) ^ (1 / 1.5) + 1
        """
        if total_xp < 100: 
            return 1
        
        # Usamos 2/3 que é o mesmo que 1/1.5
        # Somamos +1 pois o Nível 1 é o estado inicial (0 XP)
        raw_level = (total_xp / 100) ** (2/3)
        
        # O int() trunca para baixo, então adicionamos um epsilon de segurança
        return int(raw_level + 1e-9) + 1

    def process_xp_gain(self, attribute: RPGAttribute, xp_amount: int) -> List[Event]:
        """
        Aplica XP e retorna eventos resultantes (Ganho + Possível Level Up).
        """
        events = []
        
        # 1. Aplica XP
        old_level = attribute.current_level
        attribute.total_xp += xp_amount
        new_level = self.calculate_level(attribute.total_xp)
        attribute.current_level = new_level

        # 2. Evento de Ganho
        events.append(Event(EVENT_RPG_XP_GAINED, {
            "attribute": attribute.name,
            "amount": xp_amount,
            "total_xp": attribute.total_xp,
            "level": new_level
        }))

        # 3. Verifica Level Up
        if new_level > old_level:
            events.append(Event(EVENT_RPG_LEVEL_UP, {
                "attribute": attribute.name,
                "old_level": old_level,
                "new_level": new_level,
                "total_xp": attribute.total_xp
            }))

        return events