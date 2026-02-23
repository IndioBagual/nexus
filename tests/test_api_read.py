import unittest
import os
import sqlite3
import shutil
from nexus.server.queries import ReadRepository

class TestReadRepository(unittest.TestCase):
    def setUp(self):
        # 1. Definição dos caminhos
        self.test_db = "test_read.db"
        self.test_notes = "test_notes_dir"

        # 2. LIMPEZA PRÉVIA (A Correção)
        # Garante que não existe lixo de testes anteriores
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except PermissionError:
                pass # Tenta seguir mesmo se falhar (raro)

        if os.path.exists(self.test_notes):
            shutil.rmtree(self.test_notes, ignore_errors=True)
        
        # 3. Setup do Ambiente Limpo
        os.makedirs(self.test_notes, exist_ok=True)
        
        # 4. Popular DB
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        
        # Usamos IF NOT EXISTS por segurança extra, mas o os.remove acima já deve resolver
        cursor.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT, priority TEXT, status TEXT, due_date TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, amount REAL, category TEXT, created_at TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS rpg_attributes (name TEXT, total_xp INTEGER, current_level INTEGER)")
        cursor.execute("CREATE TABLE IF NOT EXISTS rpg_history (id INTEGER, description TEXT, xp_amount INTEGER, attribute TEXT, created_at TEXT)")
        
        # Dados Mockados
        cursor.execute("INSERT INTO tasks (title, priority, status, due_date) VALUES ('Task 1', 'high', 'TODO', '2026-01-01')")
        cursor.execute("INSERT INTO expenses (amount, category, created_at) VALUES (100, 'Food', '2030-01-01')")
        cursor.execute("INSERT INTO rpg_attributes (name, total_xp, current_level) VALUES ('STR', 100, 2)")
        
        conn.commit()
        conn.close()

        self.repo = ReadRepository(self.test_db, self.test_notes)

    def tearDown(self):
        # Limpeza pós-teste
        if os.path.exists(self.test_db): 
            try:
                os.remove(self.test_db)
            except: pass
            
        if os.path.exists(self.test_notes): 
            try:
                shutil.rmtree(self.test_notes)
            except: pass

    def test_chronos_today(self):
        tasks = self.repo.get_todays_tasks()
        # Task 1 está atrasada (2026-01-01), então deve aparecer hoje
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], 'Task 1')

    def test_markdown_parsing(self):
        # Criar nota fake
        note_path = os.path.join(self.test_notes, "note1.md")
        with open(note_path, "w", encoding="utf-8") as f:
            f.write("---\ntitle: Test Note\ntags: [a, b]\n---\n# Content")
        
        notes = self.repo.get_recent_notes(limit=1)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]['title'], 'Test Note')
        self.assertEqual(notes[0]['tags'], ['a', 'b'])

    def test_markdown_fallback_title(self):
        # Nota sem frontmatter
        note_path = os.path.join(self.test_notes, "raw_note.md")
        with open(note_path, "w", encoding="utf-8") as f:
            f.write("# My Header\nContent")
            
        notes = self.repo.get_recent_notes(limit=1)
        # O sistema deve pegar o H1 como título
        if notes:
            self.assertEqual(notes[0]['title'], 'My Header')

if __name__ == '__main__':
    unittest.main()