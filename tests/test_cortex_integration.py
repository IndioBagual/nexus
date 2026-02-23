import unittest
from unittest.mock import MagicMock
from nexus.cortex.brain import CortexBrain

class TestCortexLogic(unittest.TestCase):
    def setUp(self):
        # Mock do Client para não precisar do Server rodando
        self.mock_client = MagicMock()
        self.mock_memory = MagicMock()
        self.mock_memory.retrieve.return_value = "No specific memory."
        
        # Instancia Brain com mocks
        self.brain = CortexBrain(self.mock_client, self.mock_memory)

    def test_rag_context_injection(self):
        """Testa se o contexto recuperado é injetado no prompt (Lógica interna)"""
        # Como o método process_message chama a API real do Google, 
        # aqui testamos apenas se o retrieve é chamado.
        # Para teste real E2E, precisaríamos de VCR.py ou API Key válida.
        try:
            self.brain.process_message("Teste")
        except:
            # Esperado falhar sem API Key no teste unitário puro
            pass
        self.mock_memory.retrieve.assert_called_with("Teste")

if __name__ == '__main__':
    unittest.main()