import json
import os
from google import genai # Nova importação
import math
from datetime import datetime
from typing import List

MEMORY_FILE = "nexus_memory_lite.json"

class MemoryEngine:
    def __init__(self, persist_path=MEMORY_FILE):
        self.persist_path = persist_path
        self.documents = []
        self._load()
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            # Inicializa Cliente Nova SDK
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    def _load(self):
        if os.path.exists(self.persist_path):
            with open(self.persist_path, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)

    def _save(self):
        with open(self.persist_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f)

    def _get_embedding(self, text: str) -> List[float]:
        """Gera embedding usando a nova SDK (google.genai)"""
        if not self.client: return []
        try:
            # Mudança aqui: usando o modelo de embedding universal
            result = self.client.models.embed_content(
                model="models/gemini-embedding-001",
                contents=text
            )
            return result.embeddings[0].values
        except Exception as e:
            print(f"⚠️ Erro ao gerar embedding: {e}")
            return []

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2: return 0.0
        dot_product = sum(a*b for a, b in zip(v1, v2))
        magnitude1 = math.sqrt(sum(a*a for a in v1))
        magnitude2 = math.sqrt(sum(b*b for b in v2))
        if magnitude1 == 0 or magnitude2 == 0: return 0.0
        return dot_product / (magnitude1 * magnitude2)

    def ingest_note(self, filename, content, tags):
        embedding = self._get_embedding(content)
        doc = {
            "id": filename,
            "text": content,
            "metadata": {"source": filename, "type": "note", "tags": tags, "date": datetime.now().isoformat()},
            "embedding": embedding
        }
        self.documents = [d for d in self.documents if d['id'] != filename]
        self.documents.append(doc)
        self._save()

    def retrieve(self, query, n_results=3):
        if not self.client: return "Memory disabled (No API Key)"
        try:
            query_embedding = self._get_embedding(query)
            
            scored_docs = []
            for doc in self.documents:
                if 'embedding' in doc and doc['embedding']:
                    score = self._cosine_similarity(query_embedding, doc['embedding'])
                    scored_docs.append((score, doc))
            
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            top_k = scored_docs[:n_results]
            
            context = []
            for score, doc in top_k:
                if score > 0.4:
                    meta = doc['metadata']
                    context.append(f"[Source: {meta.get('source')} | Score: {score:.2f}]\n{doc['text'][:500]}...")
            
            return "\n\n".join(context) if context else "No relevant memory found."

        except Exception as e:
            return f"Error retrieving memory: {str(e)}"