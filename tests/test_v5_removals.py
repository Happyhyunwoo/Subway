"""Regression checks for v5 event-log and inventory removal."""
import ast
from pathlib import Path
import unittest

APP = Path(__file__).resolve().parents[1] / 'PDF_merge.py'


class RemovedFeaturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP.read_text(encoding='utf-8')
        cls.tree = ast.parse(cls.source)

    def test_no_logging_ui_or_recording(self):
        for token in ('add_event_log(', 'id="event-log"', 'd.eventLog',
                      '"eventLog":', '📋 이벤트 로그', '.log-item{{'):
            self.assertNotIn(token, self.source)

    def test_no_item_catalog_or_user_controls(self):
        for token in ('ITEMS =', 'def add_item(', '보유 아이템',
                      '2배 이동 활성화', '면제 카드 보유', '아이템 카드 획득'):
            self.assertNotIn(token, self.source)
        # The retired keys are only allowed in the session-state cleanup tuple.
        for key in ('hand_items', 'active_item', 'score_x2'):
            self.assertEqual(self.source.count(f'"{key}"'), 1)

    def test_blue_events_have_no_inventory_reward(self):
        assignment = next(node for node in self.tree.body
                          if isinstance(node, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'BLUE_EVENTS'
                                  for t in node.targets))
        blue = ast.literal_eval(assignment.value)
        self.assertEqual(len(blue), 6)
        self.assertTrue(all('item' not in event for event in blue))
        self.assertTrue(any(event.get('score') == 10 for event in blue))
        self.assertTrue(any(event.get('extra_roll') for event in blue))

    def test_correct_answer_has_fixed_base_points(self):
        self.assertIn('gained = 10', self.source)
        self.assertIn('dice = roll_dice_value()', self.source)
        self.assertIn('st.error("오답! 뒤로 가기 주사위 (최대 4칸 후퇴)")', self.source)


if __name__ == '__main__':
    unittest.main()
