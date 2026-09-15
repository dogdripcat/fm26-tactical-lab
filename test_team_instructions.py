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

    def test_only_observed_values_include_verified_set_piece_states(self):
        set_piece = next(x for x in self.catalog["instructions"] if x["internal_id"] == "set_piece_inducement")
        self.assertEqual(["세트피스를 노려라", "인플레이 상황을 유지하라"], [x["display_name_ko"] for x in set_piece["selectable_values"]])
        self.assertEqual([], set_piece["limitations"])
        self.assertTrue(all(x["verification"] == "user_ingame_verified" for x in set_piece["selectable_values"]))

    def test_complete_option_sets_are_exact_and_partial_categories_stay_explicit(self):
        by_id = {row["internal_id"]: row for row in self.catalog["instructions"]}
        labels = lambda category_id: [x["display_label_ko"] for x in by_id[category_id]["selectable_values"]]
        self.assertEqual(["아주 짧게", "짧게", "보통", "더 다이렉트", "훨씬 더 다이렉트"], labels("passing_directness"))
        self.assertEqual(["더욱 낮게", "낮게", "보통", "높게", "더욱 높게"], labels("tempo"))
        self.assertEqual(["매우 좁게", "좁게", "보통", "넓게", "매우 넓게"], labels("attacking_width"))
        self.assertEqual(["낮은 블록", "중간 블록", "강한 압박"], labels("pressing_line"))
        self.assertEqual(["세트피스를 노려라", "인플레이 상황을 유지하라"], labels("set_piece_inducement"))
        self.assertEqual({"passing_directness", "tempo", "attacking_width", "pressing_line", "set_piece_inducement"}, {key for key, value in by_id.items() if value["completion_status"] == "complete"})
        self.assertTrue(all(value["completion_status"] == "partial" for key, value in by_id.items() if key not in {"passing_directness", "tempo", "attacking_width", "pressing_line", "set_piece_inducement"}))

    def test_unconfigured_state_is_ui_only_and_never_a_verified_game_option(self):
        for category in self.catalog["instructions"]:
            self.assertIsNone(category["default_option"])
            self.assertEqual("미설정", category["unconfigured_option"]["display_label_ko"])
            self.assertIsNone(category["unconfigured_option"]["id"])
            self.assertEqual("input_unconfigured", category["unconfigured_option"]["provenance"])
            self.assertNotIn("미설정", [option["display_label_ko"] for option in category["selectable_values"]])
            self.assertTrue(all(option["internal_id"] for option in category["selectable_values"]))

    def test_validator_rejects_ui_unset_when_it_is_misrepresented_as_a_game_option(self):
        invalid = copy.deepcopy(self.catalog)
        invalid["instructions"][0]["selectable_values"].append({
            "id": "unset_is_not_an_option", "internal_id": "unset_is_not_an_option",
            "display_label_ko": "미설정", "display_name_ko": "미설정",
            "verification": "user_ingame_verified", "provenance": "user_ingame_verified",
            "source_reference": [], "evidence_ids": [], "analysis_status": "effect_not_modelled",
        })
        with self.assertRaises(ValueError):
            validate_catalog(invalid)

    def test_catalogue_provenance_and_ids_prevent_guessed_or_duplicate_options(self):
        evidence_ids = {row["evidence_id"] for row in json.loads((api.ROOT / "data" / "team_instruction_evidence.json").read_text(encoding="utf-8"))["evidence"]}
        for category in self.catalog["instructions"]:
            self.assertEqual(category["internal_id"], category["id"])
            self.assertEqual("user_ingame_verified", category["provenance"])
            self.assertEqual("effect_not_modelled", category["effect_model_status"])
            self.assertIsNone(category["default_option"])
            self.assertEqual("미설정", category["unconfigured_option"]["display_label_ko"])
            option_ids = [option["id"] for option in category["selectable_values"]]
            option_labels = [option["display_label_ko"] for option in category["selectable_values"]]
            self.assertEqual(len(option_ids), len(set(option_ids)))
            self.assertEqual(len(option_labels), len(set(option_labels)))
            for option in category["selectable_values"]:
                self.assertEqual(option["internal_id"], option["id"])
                self.assertEqual(option["display_name_ko"], option["display_label_ko"])
                self.assertIn(option["provenance"], {"user_ingame_verified", "terminology_supported"})
                self.assertEqual(option["evidence_ids"], option["source_reference"])
                self.assertTrue(set(option["source_reference"]).issubset(evidence_ids))

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
        self.assertIn("현재 선택된 국면의 팀 지침입니다", html)
        self.assertIn("instruction-options", script)

    def test_web_state_reinitializes_only_verified_instruction_defaults_on_formation_change(self):
        script = (api.ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("const defaultInstructions=phase=>structuredClone(data.tacticDefaults?.team_instruction_defaults?.[phase]||{})", script)
        self.assertIn("const recognized=knownFormation('IP')", script)
        self.assertIn("ip_team_instructions:defaultInstructions('IP')", script)
        self.assertIn("oop_team_instructions:defaultInstructions('OOP')", script)
        self.assertIn("function inputValidation", script)

    def test_web_renders_unset_state_for_every_category_and_keeps_phases_independent(self):
        script = (api.ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("unset.textContent='미설정'", script)
        self.assertIn("else delete tactic[key][category.internal_id]", script)
        self.assertIn("const key=phase==='IP'?'ip_team_instructions':'oop_team_instructions'", script)
        self.assertIn("tactic=blank(formation)", script)

    def test_desktop_input_workspace_keeps_phase_catalogues_compact_and_separate(self):
        script = (api.ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        stylesheet = (api.ROOT / "web" / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn("groups[phase].forEach(category", script)
        self.assertIn(".app-layout>.instructions{grid-column:2;grid-row:1", stylesheet)
        self.assertIn("#ip-team-instructions,#oop-team-instructions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))", stylesheet)
        self.assertIn("#instruction-panel-${value}`).hidden=value!==phase", script)

    def test_role_phase_control_synchronises_team_instruction_phase(self):
        html = (api.ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        script = (api.ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="role-phase-tab-IP"', html)
        self.assertIn('id="role-phase-tab-OOP"', html)
        self.assertIn("function setRolePhase(phase)", script)
        self.assertIn("activeRolePhase='IP'", script)
        self.assertIn("activeInstructionPhase=phase", script)


if __name__ == "__main__":
    unittest.main()
