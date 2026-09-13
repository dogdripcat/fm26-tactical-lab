"""Presentation-only contracts for the visual density pass."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent


class VisualDensityTests(unittest.TestCase):
    def test_analysis_cards_keep_the_compact_three_card_contract(self):
        index = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        stylesheet = (ROOT / "web" / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn('id="primary-cards" class="dimension-cards"', index)
        self.assertIn(".dimension-cards{gap:var(--space-2);grid-auto-rows:1fr}", stylesheet)
        self.assertIn(".dimension-card{min-height:0", stylesheet)
        self.assertIn("@media(max-width:700px){.workspace", stylesheet)

    def test_nodes_keep_human_position_and_role_labels_without_internal_ids(self):
        app = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        stylesheet = (ROOT / "web" / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn("getConfiguredPositionDisplayLabel(position)", app)
        self.assertIn("role?.role_name_ko", app)
        self.assertIn(".node b{font-size:.86rem", stylesheet)
        self.assertIn(".node small{max-width:102px;max-height:2.3em", stylesheet)

    def test_matchup_and_detail_views_remain_compact_and_mobile_safe(self):
        stylesheet = (ROOT / "web" / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".opponent-pitch{min-height:370px", stylesheet)
        self.assertIn(".matchup-observations{gap:var(--space-1)", stylesheet)
        self.assertIn(".details-panel{max-width:1040px}", stylesheet)
        self.assertIn(".opponent-pitch{min-height:330px}", stylesheet)


if __name__ == "__main__":
    unittest.main()
