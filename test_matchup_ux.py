import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parent
MODULE = ROOT / "web" / "static" / "js" / "matchup_overlay.js"


def observations(formation):
    source = (
        f"import {{OPPONENT_SHAPES,buildMatchupObservations}} from {json.dumps(MODULE.as_uri())};"
        "const own=['GK','LB','LCB','RCB','RB','DML','DMR','AML','AMC','AMR','ST'];"
        f"console.log(JSON.stringify(buildMatchupObservations(own,OPPONENT_SHAPES[{json.dumps(formation)}])));"
    )
    return json.loads(subprocess.check_output(["node", "--input-type=module", "-e", source], text=True, encoding="utf-8"))


class MatchupUxTests(unittest.TestCase):
    def test_all_supported_formations_keep_existing_structural_states_and_limit(self):
        for formation in ("4-3-3", "4-2-3-1", "4-4-2", "4-1-4-1", "3-4-2-1", "3-5-2", "3-4-3"):
            with self.subTest(formation=formation):
                result = observations(formation)
                self.assertLessEqual(len(result), 5)
                self.assertTrue(all(item["state"] in {"활용 가능", "주의", "충돌 집중"} for item in result))

    def test_matchup_ui_has_summary_limitations_collapsed_details_and_existing_overlay_focus(self):
        app = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        index = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("matchup-state-cards", app)
        self.assertIn("function focusMatchup(item)", app)
        self.assertIn("matchupSelected=item", app)
        self.assertIn("details.id='matchup-details'", app)
        self.assertIn("matchup-limitation", app)
        self.assertNotIn("예상 승률", index)
        self.assertNotIn("xG", app)
        self.assertNotIn("win probability", app.lower())

    def test_own_tactic_analysis_remains_separate_from_matchup_presentation(self):
        app = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("analysis=analyzeTactic(tactic,data)", app)
        self.assertIn("buildMatchupObservations(active('IP'),opponentActive())", app)
        self.assertNotIn("analyzeTactic(tactic,data,shape)", app)


if __name__ == "__main__":
    unittest.main()
