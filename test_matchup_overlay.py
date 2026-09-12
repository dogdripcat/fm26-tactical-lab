"""Tests for the formation-only opponent-comparison overlay."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parent


def observations(formation: str) -> list[dict]:
    positions = ["GK", "LB", "LCB", "RCB", "RB", "DML", "DMR", "AML", "AMC", "AMR", "ST"]
    source = (
        "import {OPPONENT_SHAPES,buildMatchupObservations} from './web/static/js/matchup_overlay.js';"
        f"console.log(JSON.stringify(buildMatchupObservations({json.dumps(positions)},OPPONENT_SHAPES[{json.dumps(formation)}])));"
    )
    output = subprocess.check_output(["node", "--input-type=module", "--eval", source], cwd=ROOT, text=True, encoding="utf-8")
    return json.loads(output)


class MatchupOverlayTests(unittest.TestCase):
    def test_overlay_uses_only_qualitative_states_and_at_most_five_observations(self):
        rows = observations("4-3-3")
        self.assertLessEqual(len(rows), 5)
        self.assertTrue(rows)
        self.assertTrue(all(row["state"] in {"활용 가능", "주의", "충돌 집중"} for row in rows))
        self.assertTrue(all({"region", "band", "text", "detail"} <= set(row) for row in rows))

    def test_formation_change_recomputes_visual_observations(self):
        self.assertNotEqual(observations("4-3-3"), observations("4-4-2"))

    def test_static_ui_keeps_detail_collapsed_until_zone_selection(self):
        source = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        html = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("renderMatchupOverlay", source)
        self.assertIn("showMatchupZoneDetail", source)
        self.assertIn("details.id='matchup-zone-detail'", source)
        self.assertLess(html.index("</main>"), html.index('id="opponent-mode"'))
        self.assertIn("경기 데이터 기반 모델 준비 중", html)


if __name__ == "__main__":
    unittest.main()
