import unittest
# Deve apontar para o pacote nexus
from nexus.domain.rpg_engine import RPGEngine, RPGAttribute, EVENT_RPG_LEVEL_UP, EVENT_RPG_XP_GAINED

class TestRPGEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RPGEngine()

    def test_level_calculation(self):
        # < 100 XP = Nível 1
        self.assertEqual(self.engine.calculate_level(0), 1)
        self.assertEqual(self.engine.calculate_level(99), 1)
        # 100 XP = Nível 2
        self.assertEqual(self.engine.calculate_level(100), 2)
        # 283 XP = Nível 3 (Threshold exato é ~282.84)
        self.assertEqual(self.engine.calculate_level(283), 3)

    def test_xp_gain_no_level_up(self):
        attr = RPGAttribute(name="STR", total_xp=0, current_level=1)
        events = self.engine.process_xp_gain(attr, 50)
        
        self.assertEqual(attr.total_xp, 50)
        self.assertEqual(attr.current_level, 1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].name, EVENT_RPG_XP_GAINED)

    def test_xp_gain_with_level_up(self):
        attr = RPGAttribute(name="INT", total_xp=90, current_level=1)
        # Ganha 20 XP (Total 110) -> Deve ir para Nível 2
        events = self.engine.process_xp_gain(attr, 20)
        
        self.assertEqual(attr.total_xp, 110)
        self.assertEqual(attr.current_level, 2)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[1].name, EVENT_RPG_LEVEL_UP)
        self.assertEqual(events[1].payload['new_level'], 2)

if __name__ == '__main__':
    unittest.main()