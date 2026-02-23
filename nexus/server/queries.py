import sqlite3
import os
import re
import math
from datetime import datetime
from typing import List, Dict, Any, Optional

class ReadRepository:
    def __init__(self, db_path: str, notes_path: str):
        self.db_path = db_path
        self.notes_path = notes_path

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    # --- CHRONOS ---
    def get_todays_tasks(self) -> List[Dict]:
        """Tarefas para hoje ou atrasadas, não concluídas."""
        today = datetime.now().strftime("%Y-%m-%d")
        query = """
            SELECT id, title, priority, due_date, status 
            FROM tasks 
            WHERE (due_date <= ? OR due_date IS NULL) 
            AND status != 'DONE'
            ORDER BY 
                CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END ASC,
                due_date ASC
        """
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, (today,)).fetchall()
            return [dict(row) for row in rows]

    def get_all_tasks(self, status: str = 'TODO', limit: int = 50) -> List[Dict]:
        query = "SELECT * FROM tasks WHERE status = ? ORDER BY id DESC LIMIT ?"
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, (status, limit)).fetchall()
            return [dict(row) for row in rows]

    # --- TREASURY ---
    def get_monthly_summary(self) -> Dict:
        start_of_month = datetime.now().strftime("%Y-%m-01")
        
        # 1. Total Gasto
        query_total = "SELECT SUM(amount) FROM expenses WHERE created_at >= ?"
        
        # 2. Top Categorias
        query_cats = """
            SELECT category, SUM(amount) as total 
            FROM expenses 
            WHERE created_at >= ? 
            GROUP BY category 
            ORDER BY total DESC LIMIT 3
        """
        
        with self._get_conn() as conn:
            total = conn.execute(query_total, (start_of_month,)).fetchone()[0] or 0.0
            
            conn.row_factory = sqlite3.Row
            cats = conn.execute(query_cats, (start_of_month,)).fetchall()
            
            top_cats = []
            for row in cats:
                percent = (row['total'] / total * 100) if total > 0 else 0
                top_cats.append({
                    "category": row['category'],
                    "total": row['total'],
                    "percent": round(percent, 1)
                })

            return {
                "range": "month",
                "total_spent": round(total, 2),
                "currency": "BRL",
                "top_categories": top_cats
            }

    # --- RPG ---
    def get_rpg_status(self) -> Dict:
        query = "SELECT name, total_xp, current_level FROM rpg_attributes"
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query).fetchall()
            
            attributes = {}
            levels = []
            
            for row in rows:
                lvl = row['current_level']
                xp = row['total_xp']
                
                # Cálculo Reverso do XP necessário para o PRÓXIMO nível
                # XP_Next = 100 * ((Current_Level + 1) - 1) ^ 1.5
                # Simplificando: 100 * (Level) ^ 1.5
                next_level_xp_threshold = int(100 * (lvl ** 1.5))
                
                # XP do nível atual (base) para calcular porcentagem relativa
                current_level_base_xp = int(100 * ((lvl - 1) ** 1.5)) if lvl > 1 else 0
                
                # Progresso dentro do nível
                range_xp = next_level_xp_threshold - current_level_base_xp
                gained_in_level = xp - current_level_base_xp
                progress = (gained_in_level / range_xp * 100) if range_xp > 0 else 0
                
                attributes[row['name']] = {
                    "level": lvl,
                    "current_xp": xp,
                    "next_level_xp": next_level_xp_threshold,
                    "progress_percent": min(100.0, round(progress, 1))
                }
                levels.append(lvl)

            # Histórico Recente
            hist_query = "SELECT description, xp_amount, attribute, created_at FROM rpg_history ORDER BY id DESC LIMIT 5"
            history_rows = conn.execute(hist_query).fetchall()
            history = [dict(r) for r in history_rows]

            return {
                "player_level": int(sum(levels) / len(levels)) if levels else 1,
                "attributes": attributes,
                "recent_history": history
            }

    # --- LIBRARY ---
    def _parse_frontmatter(self, content: str) -> Dict:
        """Parser simples de YAML Frontmatter sem dependências externas."""
        meta = {"tags": []}
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            yaml_block = match.group(1)
            # Extrair title
            t_match = re.search(r"^title:\s*(.+)$", yaml_block, re.MULTILINE)
            if t_match: meta["title"] = t_match.group(1).strip()
            # Extrair tags (formato simples [a, b])
            tags_match = re.search(r"^tags:\s*\[(.*?)\]", yaml_block, re.MULTILINE)
            if tags_match:
                meta["tags"] = [t.strip() for t in tags_match.group(1).split(',')]
        return meta

    def get_recent_notes(self, limit: int = 10) -> List[Dict]:
        if not os.path.exists(self.notes_path):
            return []
            
        files = [f for f in os.listdir(self.notes_path) if f.endswith('.md')]
        # Ordenar por data de modificação
        files.sort(key=lambda x: os.path.getmtime(os.path.join(self.notes_path, x)), reverse=True)
        
        notes = []
        for f in files[:limit]:
            path = os.path.join(self.notes_path, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read(500) # Ler apenas o começo
                    meta = self._parse_frontmatter(content)
                    
                    # Fallback Title
                    if "title" not in meta:
                        # Tenta pegar primeiro H1
                        h1 = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                        if h1:
                            meta["title"] = h1.group(1).strip()
                        else:
                            meta["title"] = f.replace(".md", "").replace("_", " ").title()
                    
                    notes.append({
                        "filename": f,
                        "title": meta.get("title"),
                        "tags": meta.get("tags", []),
                        "created_at": datetime.fromtimestamp(os.path.getctime(path)).isoformat()[:10]
                    })
            except Exception:
                continue # Pula arquivos corrompidos
                
        return notes