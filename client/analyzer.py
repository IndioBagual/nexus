import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from statistics import mode, StatisticsError

class BehavioralAnalyzer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._setup()

    def _setup(self):
        """Cria a tabela para armazenar os eventos detectados."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS analytical_events (
                id TEXT PRIMARY KEY,
                event_type TEXT,
                domain TEXT,
                confidence REAL,
                insight TEXT,
                data_evidence TEXT,
                created_at TEXT,
                processed INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def _save_event(self, event_type: str, domain: str, confidence: float, insight: str, data_evidence: dict):
        """Grava o evento no banco se ele for inédito (evita spam diário do mesmo insight)."""
        # Checa se já geramos um insight parecido nos últimos 3 dias
        cursor = self.conn.execute("""
            SELECT count(*) FROM analytical_events 
            WHERE event_type = ? AND insight = ? AND processed = 0
        """, (event_type, insight))
        
        if cursor.fetchone()[0] == 0:
            event_id = f"evt_{uuid.uuid4().hex[:12]}"
            now = datetime.utcnow().isoformat() + "Z"
            
            self.conn.execute("""
                INSERT INTO analytical_events (id, event_type, domain, confidence, insight, data_evidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (event_id, event_type, domain, confidence, insight, json.dumps(data_evidence), now))
            self.conn.commit()
            print(f"💡 Novo Evento [{event_type}]: {insight}")

    def analyze_chronos_density(self, days=30):
        """Regra 1: Detecta pico de energia (horário em que mais conclui tarefas)."""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Busca todas as vezes que o Córtex ou o App marcou uma tarefa como DONE
        cursor = self.conn.execute("""
            SELECT timestamp FROM sync_op_log 
            WHERE entity_type = 'TASK' 
              AND action = 'UPDATE' 
              AND payload LIKE '%"status": "DONE"%'
              AND timestamp > ?
        """, (cutoff_date,))
        
        rows = cursor.fetchall()
        if len(rows) < 5: 
            return # Poucos dados para inferir padrão

        # Extrai a hora de cada timestamp
        hours = []
        for r in rows:
            try:
                # O formato do banco é ISO 8601
                dt = datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00'))
                hours.append(dt.hour)
            except ValueError:
                continue

        try:
            # Encontra a hora mais comum (Moda)
            peak_hour = mode(hours)
            # Calcula a densidade (quantas % das tarefas foram feitas nessa hora ou arredores)
            peak_count = sum(1 for h in hours if peak_hour - 1 <= h <= peak_hour + 1)
            density = peak_count / len(hours)

            if density >= 0.40: # Se 40%+ do trabalho é feito numa janela de 3h
                self._save_event(
                    event_type="PATTERN_DETECTED",
                    domain="CHRONOS",
                    confidence=round(density, 2),
                    insight=f"Pico de produtividade detectado por volta das {peak_hour}h.",
                    data_evidence={
                        "metric": "task_completion_density",
                        "window": f"{days}d",
                        "value": f"{int(density*100)}% das tarefas concluídas na janela de {peak_hour-1}h às {peak_hour+1}h."
                    }
                )
        except StatisticsError:
            pass # Sem moda clara (comportamento errático)

    def analyze_treasury_optimization(self, days=14):
        """Regra 2: Detecta oportunidades financeiras (Frequência excessiva em uma categoria)."""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Como as finanças não têm timestamp explícito no MVP da Fase 3, usamos o log de operações
        cursor = self.conn.execute("""
            SELECT payload FROM sync_op_log 
            WHERE entity_type = 'EXPENSE' AND action = 'CREATE' AND timestamp > ?
        """, (cutoff_date,))
        
        expenses = [json.loads(r['payload']) for r in cursor.fetchall()]
        if not expenses: return

        # Agrupa por categoria
        category_counts = {}
        category_sums = {}
        for exp in expenses:
            cat = exp.get('category', 'Outros')
            amt = float(exp.get('amount', 0))
            category_counts[cat] = category_counts.get(cat, 0) + 1
            category_sums[cat] = category_sums.get(cat, 0) + amt

        for cat, count in category_counts.items():
            if count >= 4: # Fricção alta: 4 ou mais gastos na mesma categoria em 14 dias
                self._save_event(
                    event_type="OPTIMIZATION_OPPORTUNITY",
                    domain="TREASURY",
                    confidence=0.85,
                    insight=f"Múltiplos gastos registrados na categoria '{cat}'.",
                    data_evidence={
                        "metric": "transaction_frequency",
                        "window": f"{days}d",
                        "value": f"{count} transações totalizando R$ {category_sums[cat]:.2f}. Pode gerar fadiga de registro."
                    }
                )

    def analyze_habit_risk(self, days=7):
        """Regra 3: Tarefas antigas mofando na caixa de entrada (Risco de procrastinação)."""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Tarefas que não estão prontas e foram criadas via log há mais de X dias
        cursor = self.conn.execute("""
            SELECT id, title FROM tasks WHERE status != 'DONE'
        """)
        tasks = cursor.fetchall()
        
        stale_tasks = []
        for t in tasks:
            # Verifica quando foi a última movimentação dessa tarefa
            cur = self.conn.execute("""
                SELECT timestamp FROM sync_op_log 
                WHERE entity_id = ? ORDER BY timestamp DESC LIMIT 1
            """, (t['id'],))
            last_op = cur.fetchone()
            if last_op and last_op['timestamp'] < cutoff_date:
                stale_tasks.append(t['title'])

        if len(stale_tasks) >= 3:
            self._save_event(
                event_type="HABIT_RISK",
                domain="CHRONOS",
                confidence=0.90,
                insight="Acúmulo de tarefas antigas intocadas.",
                data_evidence={
                    "metric": "stale_tasks_count",
                    "window": f">{days}d",
                    "value": f"{len(stale_tasks)} tarefas sem movimentação recente. Ex: {stale_tasks[0]}"
                }
            )

    def run_all(self):
        print("🔍 Iniciando varredura comportamental...")
        self.analyze_chronos_density(days=30)
        self.analyze_treasury_optimization(days=14)
        self.analyze_habit_risk(days=7)
        print("✅ Varredura concluída.\n")
        self.conn.close()

if __name__ == "__main__":
    # Testando diretamente no banco local do device simulado
    analyzer = BehavioralAnalyzer(db_path="nexus_simulado.db")
    analyzer.run_all()