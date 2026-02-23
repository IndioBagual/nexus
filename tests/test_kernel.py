import unittest

from nexus.application.bus import EventBus
from nexus.domain.events import Event


# Mocks simples para teste unitário
class MockRepo:
    def add(self, item):
        return 1

    def save(self, item):
        return "path/file.md"

    def log_xp(self, a, b, c, d):
        pass


class MockCortex:
    def parse_intent(self, text):
        return [
            {
                "action": "add_expense",
                "params": {"amount": 10, "category": "Food", "description": "Test"},
            }
        ]


class TestNexusKernel(unittest.TestCase):
    def test_bus_publish(self):
        bus = EventBus()
        result = []
        bus.subscribe("TEST_EVENT", lambda e: result.append(e.payload))
        bus.publish(Event("TEST_EVENT", {"data": 123}))
        self.assertEqual(result[0]["data"], 123)


if __name__ == "__main__":
    unittest.main()
