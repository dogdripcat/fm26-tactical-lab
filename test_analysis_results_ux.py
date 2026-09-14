import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parent
PRESENTER = ROOT / "web" / "static" / "js" / "analysis_results_presenter.js"


def present(payload):
    source = (
        f"import {{presentAnalysisResults}} from {json.dumps(PRESENTER.as_uri())};"
        f"console.log(JSON.stringify(presentAnalysisResults({json.dumps(payload, ensure_ascii=False)})));"
    )
    return json.loads(subprocess.check_output(["node", "--input-type=module", "-e", source], text=True, encoding="utf-8"))


class AnalysisResultsUxTests(unittest.TestCase):
    def test_three_cards_are_isolated_to_their_existing_presenter_outputs(self):
        result = present({
            "connectivity": {"continuity": "연결성 전용", "summary": "연결성 설명", "regions": []},
            "progression": {"continuity": "전진성 전용", "summary": "전진성 설명", "cards": []},
            "support": {"summary": "지원 구조 전용", "cards": []},
        })
        self.assertEqual(["연결성", "전진성", "지원 구조"], [card["title"] for card in result["cards"]])
        self.assertEqual("연결성 전용", result["cards"][0]["headline"])
        self.assertEqual("전진성 전용", result["cards"][1]["headline"])
        self.assertEqual("지원 구조 전용", result["cards"][2]["headline"])

    def test_issue_and_strength_limits_are_deterministic_and_score_free(self):
        result = present({
            "connectivity": {"continuity": "", "summary": "", "regions": [], "isolated": ["A", "B"], "deadEnds": ["C"], "dependency": []},
            "progression": {"continuity": "", "summary": "", "cards": [{"title": "왼쪽", "primary": "전방까지 전진", "detail": "경로", "representative_route_id": "a->b"}], "stalls": [], "dependencies": []},
            "support": {"summary": "", "cards": [{"title": "중앙", "primary": "전방 지원", "detail": "후속 연결", "node_ids": [], "link_ids": []}], "isolated": [], "single": [], "dependencies": []},
        })
        self.assertLessEqual(len(result["issues"]), 3)
        self.assertLessEqual(len(result["strengths"]), 2)
        self.assertNotIn("score", json.dumps(result, ensure_ascii=False).lower())
        self.assertNotIn("%", json.dumps(result, ensure_ascii=False))

    def test_static_ui_keeps_details_collapsed_and_exposes_pitch_focus_actions(self):
        index = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="primary-cards"', index)
        self.assertIn('id="primary-issues"', index)
        self.assertIn('id="primary-strengths"', index)
        self.assertIn('id="details-panel" class="details-panel" hidden', index)
        self.assertIn('id="show-details"', index)
        self.assertIn('id="incomplete-analysis-note"', index)
        self.assertIn("presentAnalysisResults({connectivity,progression,support})", app)
        self.assertIn("function activateResult(item)", app)
        self.assertIn("setRolePhase('IP')", app)
        self.assertIn("overviewPresentation(missing)", app)
        self.assertIn("$('#show-details').onclick", app)
        self.assertNotIn("win probability", app.lower())

    def test_product_flow_keeps_configuration_order_and_a_clear_analysis_action(self):
        index = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("전술을 구성하고 연결성 · 전진성 · 지원 구조를 분석해보세요.", index)
        self.assertIn("포메이션 → 공 소유·미소유 시 역할 → 팀 지침", index)
        self.assertIn('id="analyze" class="primary">분석하기', index)
        self.assertIn("다시 분석 필요", app)
        self.assertIn("scrollIntoView({behavior:'smooth',block:'start'})", app)
        self.assertIn("구조 분석은 선수 능력치와 실제 경기 상황을 포함하지 않습니다.", index)

    def test_stale_analysis_is_hidden_when_tactic_input_changes(self):
        app = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("$('#analysis-overview').hidden=true", app)
        self.assertIn("$('#details-panel').hidden=true", app)


if __name__ == "__main__":
    unittest.main()
