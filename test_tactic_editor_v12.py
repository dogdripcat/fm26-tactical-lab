import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent


class TacticEditorV12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        cls.index = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        cls.approaches = json.loads((ROOT / "data" / "playing_approach_catalog.json").read_text(encoding="utf-8"))
        cls.static_approaches = json.loads((ROOT / "web" / "static" / "data" / "playing_approach_catalog.json").read_text(encoding="utf-8"))
        cls.catalog = json.loads((ROOT / "data" / "team_instruction_catalog.json").read_text(encoding="utf-8"))

    def test_playing_approach_catalogue_keeps_unset_as_ui_sentinel_and_normal_as_design_reference(self):
        self.assertIn('id="playing-approach"', self.index)
        self.assertIn('<option value="">미설정</option>', self.index)
        self.assertNotIn('id="playing-approach" disabled', self.index)
        self.assertEqual(self.approaches, self.static_approaches)
        self.assertEqual("design_reference_only", self.approaches["status"])
        self.assertNotIn("미설정", [value.get("label") for value in self.approaches["values"]])
        self.assertEqual(1, len(self.approaches["values"]))
        normal = self.approaches["values"][0]
        self.assertEqual("normal", normal["id"])
        self.assertEqual("일반형", normal["label"])
        self.assertTrue(normal["selectable"])
        self.assertEqual("design_reference", normal["evidence_level"])
        self.assertEqual("needs_ingame_confirmation", normal["label_verification"])
        self.assertEqual(["CHATGPT_LIBRARY_FM26_PLAYING_APPROACH_DESIGN_001"], normal["evidence_ids"])

    def test_playing_approach_ui_preserves_evidence_level_without_main_ui_warning(self):
        self.assertIn("initPlayingApproaches()", self.app)
        self.assertIn("option.dataset.evidenceLevel=value.evidence_level||'unknown'", self.app)
        self.assertIn("프로젝트 자료 기반 명칭 · 인게임 표기 확인 필요", self.app)
        self.assertIn("select.value=tactic.playing_approach||''", self.app)

    def test_dual_cells_use_catalogue_abbreviations_and_direct_phase_editing(self):
        self.assertIn("cell.textContent=role?.display_abbr||'—'", self.app)
        self.assertIn("role?.display_abbr||'—'} — ${role?.role_name_ko", self.app)
        self.assertIn("popover(playerId,phasePosition,node,phase)", self.app)
        self.assertIn("function popover(playerId,position,node,requestedPhase=activeRolePhase)", self.app)
        self.assertIn("const popupId=`${requestedPhase}:${playerId}`", self.app)
        self.assertIn("if(dragState)return", self.app)
        self.assertIn("event.target.closest('.role-cell')", self.app)

    def test_terminology_values_are_selectable_but_keep_evidence_status(self):
        values = [value for category in self.catalog["instructions"] for value in category["selectable_values"]]
        terminology = [value for value in values if value.get("evidence_level") == "terminology_supported"]
        self.assertEqual(73, len(values))
        self.assertTrue(terminology)
        self.assertTrue(all(value["selectable"] is True for value in terminology))
        self.assertTrue(all(value["verification"] == "terminology_supported" for value in terminology))
        self.assertTrue(all(value.get("label_verification") == "needs_ingame_confirmation" for value in terminology))
        labels = {value["display_label_ko"] for value in terminology}
        self.assertTrue({"형태 유지", "역습", "수비 진영에서 빌드업"}.issubset(labels))

    def test_opponent_editor_uses_independent_player_state_and_structural_matchup_only(self):
        self.assertIn("const blankOpponent=(formation='4-3-3')", self.app)
        self.assertIn("ip:{position,role:", self.app)
        self.assertIn("function moveOpponentPlayer", self.app)
        self.assertIn("function opponentDragSlot", self.app)
        self.assertIn("opponentDragClickPlayerId", self.app)
        self.assertIn("opponentRoleOptions", self.app)
        self.assertIn("buildMatchupObservations(active('IP'),opponentActive())", self.app)
        self.assertNotIn('id="opponent-formation"', self.index)


if __name__ == "__main__":
    unittest.main()
