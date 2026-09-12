import copy
import json
import unittest

from core.team_instructions import normalize_team_instructions, validate_catalog
from web import api


class TeamInstructionCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = validate_catalog(json.loads(api.TEAM_INSTRUCTION_CATALOG_PATH.read_text(encoding="utf-8-sig")))

    def test_verified_category_counts_and_exact_korean_labels(self):
        grouped = api.team_instructions_payload()
        self.assertEqual(18, len(grouped["IP"]))
        self.assertEqual(9, len(grouped["OOP"]))
        self.assertEqual(["패스 방식", "템포", "시간 보내기", "공격 전환", "공격 폭", "세트피스 유도", "창조성", "빌드업 전술", "골킥", "골키퍼 배급", "공격 가담", "드리블", "전진", "패스 스타일", "참을성", "중거리 슛", "크로스 스타일", "골키퍼 배급(속도)"], [x["display_name_ko"] for x in grouped["IP"]])
        self.assertEqual(["압박 기준선", "수비 라인", "압박 실행", "수비 전환", "태클", "크로스 플레이", "압박 트랩", "골키퍼 짧은 볼 배급", "수비 라인 행동"], [x["display_name_ko"] for x in grouped["OOP"]])

    def test_only_observed_values_and_truncated_set_piece_remains_unresolved(self):
        set_piece = next(x for x in self.catalog["instructions"] if x["internal_id"] == "set_piece_inducement")
        self.assertEqual([], set_piece["selectable_values"])
        self.assertTrue(set_piece["limitations"])
        self.assertTrue(all(len(x["selectable_values"]) <= 1 for x in self.catalog["instructions"]))

    def test_validator_rejects_unknown_value_and_phase_mismatch(self):
        with self.assertRaises(ValueError):
            normalize_team_instructions({"not_real": "x"}, "IP", self.catalog)
        with self.assertRaises(ValueError):
            normalize_team_instructions({"tempo": "not_real"}, "IP", self.catalog)
        with self.assertRaises(ValueError):
            normalize_team_instructions({"tempo": "tempo_high"}, "OOP", self.catalog)

    def test_analyze_accepts_verified_input_without_effect_inference(self):
        tactic = api.sample_tactic()
        original = copy.deepcopy(tactic)
        tactic.update(api.sample_team_instructions_payload())
        result = api.analyze_payload(tactic)
        self.assertEqual(original, api.sample_tactic())
        self.assertEqual("effect_not_modelled", result["team_instruction_input_status"]["status"])
        self.assertIn("not yet modelled", result["team_instruction_input_status"]["limitation"])
        self.assertNotIn("team_instruction_effects", result)

    def test_legacy_tactic_without_phased_instructions_still_works(self):
        result = api.analyze_payload(api.sample_tactic())
        self.assertEqual({}, result["team_instruction_input_status"]["ip"])
        self.assertEqual({}, result["team_instruction_input_status"]["oop"])

    def test_web_assets_render_instruction_sections_and_statuses(self):
        html = (api.ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        script = (api.ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="ip-team-instructions"', html)
        self.assertIn('id="oop-team-instructions"', html)
        self.assertIn("전술 효과는 아직 분석하지 않습니다", html)
        self.assertIn("선택값 검증 필요", script)

    def test_web_state_preserves_instructions_across_ip_formation_change(self):
        script = (api.ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("tactic.ip_team_instructions=old.ip_team_instructions||{}", script)
        self.assertIn("tactic.oop_team_instructions=old.oop_team_instructions||{}", script)
        self.assertIn("function inputValidation", script)

    def test_desktop_input_workspace_keeps_phase_catalogues_compact_and_separate(self):
        script = (api.ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        stylesheet = (api.ROOT / "web" / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn("groups[phase].forEach(category", script)
        self.assertIn(".app-layout>.instructions{grid-column:2;grid-row:1", stylesheet)
        self.assertIn("#ip-team-instructions,#oop-team-instructions{display:grid;grid-template-columns:repeat(2", stylesheet)
        self.assertIn("#instruction-panel-${value}`).hidden=value!==phase", script)

    def test_role_phase_control_is_separate_from_team_instruction_phase_control(self):
        html = (api.ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        script = (api.ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="role-phase-tab-IP"', html)
        self.assertIn('id="role-phase-tab-OOP"', html)
        self.assertIn("function setRolePhase(phase)", script)
        self.assertIn("activeRolePhase='IP'", script)
        self.assertIn("roles(p,phase)", script)


if __name__ == "__main__":
    unittest.main()
