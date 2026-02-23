from nexus.adapters.manager import AdapterManager
from nexus.adapters.plugins.mock_calendar import MockCalendarAdapter

# 1. Instancia o Manager
manager = AdapterManager(db_path="nexus_simulado.db")

# 2. Registra o nosso plugin simulado
manager.register_adapter(MockCalendarAdapter())

# 3. Roda o ciclo (Vai puxar os 2 eventos do calendário)
manager.run_sync_cycle()

# Se você rodar de novo, ele dirá "Nenhum dado novo", 
# porque o AdapterManager salvou o cursor de sincronização!
manager.run_sync_cycle()