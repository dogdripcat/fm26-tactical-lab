import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class TacticBuilderOverhaulTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "role_catalog.json").read_text(encoding="utf-8"))
        cls.registry = json.loads((ROOT / "configured_position_registry.json").read_text(encoding="utf-8"))
        cls.app = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        cls.html = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")

    def test_forward_catalogue_has_exact_confirmed_phase_identities(self):
        rows = [row for row in self.catalog if "FW" in row["role_families"]]
        self.assertEqual({row["display_abbr"] for row in rows if row["phase"] == "IP"}, {"CFD", "CHF", "DLF", "F9", "P", "TF"})
        self.assertEqual({row["display_abbr"] for row in rows if row["phase"] == "OOP"}, {"CFD", "OCF", "TCF"})
        confirmed_labels = {
            "DLF": "딥라잉 포워드",
            "F9": "폴스 나인",
            "P": "포처",
            "TF": "타깃형 포워드",
        }
        for row in rows:
            if row["phase"] == "IP" and row["display_abbr"] in confirmed_labels:
                self.assertEqual(row["role_name_ko"], confirmed_labels[row["display_abbr"]])
                self.assertEqual(row["display_label_provenance"], "user_confirmed")
                self.assertIsNone(row["role_behaviour_ref"])
            elif row["phase"] == "OOP" and row["display_abbr"] in {"OCF", "TCF"}:
                self.assertIsNone(row["role_name_ko"])
                self.assertIsNone(row["role_behaviour_ref"])

    def test_builder_keeps_independent_ip_and_oop_position_state(self):
        self.assertIn("ip_positions:playerSlots", self.app)
        self.assertIn("oop_positions:playerSlots", self.app)
        self.assertIn("const positionKey=phase", self.app)
        self.assertIn("function setRolePhase(phase)", self.app)
        self.assertIn("activeInstructionPhase=phase", self.app)

    def test_moving_a_player_swaps_occupied_slot_and_clears_only_invalid_roles(self):
        self.assertIn("const otherRole=tactic[key][destination]", self.app)
        self.assertIn("positions[otherId]=source", self.app)
        self.assertIn("roles(destination,phase).some", self.app)
        self.assertIn("roles(source,phase).some", self.app)

    def test_analysis_and_matchup_keep_ip_as_evaluator_input(self):
        self.assertIn("active('IP').filter", self.app)
        self.assertIn("buildMatchupObservations(active('IP'),shape)", self.app)

    def test_buttons_and_style_catalogue_do_not_imply_instruction_effects(self):
        self.assertIn("instruction-options", self.app)
        styles = json.loads((ROOT / "data" / "tactical_style_catalog.json").read_text(encoding="utf-8"))["styles"]
        self.assertEqual(len(styles), 10)
        self.assertTrue(all(row["team_instruction_preset"] is None for row in styles))
        self.assertIn("function applyTacticalStyle(style)", self.app)
        self.assertIn("tactic.tactical_style_modified=true", self.app)
        self.assertIn("team_instruction_preset?.[phase]", self.app)

    def test_removed_primary_all_controls_are_not_user_facing(self):
        self.assertNotIn("show-primary", self.html)
        self.assertNotIn("show-all", self.html)
        self.assertNotIn("주요 연결", self.html)
        self.assertNotIn("전체 연결", self.html)

    def test_connectivity_overlay_uses_explicit_four_state_classifier(self):
        self.assertIn("classifyConnectivityLinks", self.app)
        stylesheet = (ROOT / "web" / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn("connectivity-very-strong", stylesheet)
        self.assertIn("파랑 연결 매우 강력", self.html)
        self.assertIn("초록 연결 원활", self.html)
        self.assertIn("핑크 연결 약함", self.html)
        self.assertIn("회색 연결 안됨", self.html)

    def test_desktop_polish_keeps_validation_compact_and_legend_analysis_only(self):
        self.assertIn('id="analyze" class="primary">전술 분석', self.html)
        self.assertIn('id="pitch-legend"', self.html)
        self.assertIn("$('#pitch-legend').hidden=!analysis||activeRolePhase!=='IP'", self.app)
        self.assertIn('overviewPresentation(missing)', self.app)
        self.assertIn("incomplete.hidden=!missing.length", self.app)

    def test_interaction_layers_are_explicitly_click_through(self):
        stylesheet = (ROOT / "web" / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".pitch-markings{position:absolute;inset:0;width:100%;height:100%;z-index:0;pointer-events:none}", stylesheet)
        self.assertIn(".edge-overlay{position:absolute;inset:0;width:100%;height:100%;z-index:1;pointer-events:none}", stylesheet)
        self.assertIn(".svg-edge{pointer-events:none}", stylesheet)

    def test_initial_pitch_render_wires_all_player_nodes_and_controls(self):
        self.assertIn("Object.entries(players).forEach", self.app)
        self.assertIn("node.onpointerdown=event=>beginPointerDrag(event,playerId,position,node)", self.app)
        self.assertIn("$('#role-phase-tab-IP').onclick=()=>setRolePhase('IP')", self.app)
        self.assertIn("$('#role-phase-tab-OOP').onclick=()=>setRolePhase('OOP')", self.app)
        self.assertIn("$('#analyze').onclick=analyze", self.app)
        self.assertIn("select.onchange=()=>{tactic=blank(select.value)", self.app)

    def test_role_popover_has_explicit_toggle_switch_and_outside_close_state(self):
        self.assertIn("activeRolePlayerId=null", self.app)
        self.assertIn("if(activeRolePlayerId===popupId){closeRolePopover();return;}", self.app)
        self.assertIn("function closeRolePopover()", self.app)
        self.assertIn("event.target.closest('.role-popover')||event.target.closest('.node')", self.app)
        self.assertIn("dragClickPlayerId", self.app)

    def test_project_defaults_are_explicit_non_official_and_validate_role_availability(self):
        defaults = json.loads((ROOT / "data" / "tactic_default_profiles.json").read_text(encoding="utf-8"))
        static_defaults = json.loads((ROOT / "web" / "static" / "data" / "tactic_default_profiles.json").read_text(encoding="utf-8"))
        by_id = {row["internal_id"]: row for row in self.catalog}
        self.assertEqual("tactical_lab_project_default_v1", defaults["profile_id"])
        self.assertEqual("project_default", defaults["provenance"])
        self.assertEqual("not_official", defaults["official_status"])
        self.assertEqual(defaults, static_defaults)
        self.assertEqual("passing_directness_standard", defaults["team_instruction_defaults"]["IP"]["passing_directness"])
        self.assertEqual("tempo_standard", defaults["team_instruction_defaults"]["IP"]["tempo"])
        self.assertEqual("attacking_width_standard", defaults["team_instruction_defaults"]["IP"]["attacking_width"])
        self.assertEqual({}, defaults["team_instruction_defaults"]["OOP"])
        self.assertNotIn("forward", defaults["role_defaults_by_family"]["OOP"])
        for phase, families in defaults["role_defaults_by_family"].items():
            for role_id in families.values():
                self.assertEqual(phase, by_id[role_id]["phase"])
        self.assertIn("function defaultRoles(formation,phase)", self.app)
        self.assertIn("available.find(item=>item.role_internal_id===requested)", self.app)
        self.assertIn("ip_roles:defaultRoles(formation,'IP')", self.app)
        self.assertIn("oop_roles:defaultRoles(formation,'OOP')", self.app)
        self.assertIn("const formation=tactic.ip_formation;tactic=blank(formation)", self.app)

    def test_direct_drag_snaps_to_canonical_slots_and_keeps_role_editor_click_focused(self):
        self.assertIn("function nearestDragSlot(clientX,clientY,origin=null)", self.app)
        self.assertIn("node.setPointerCapture?.(event.pointerId)", self.app)
        self.assertIn("node.onpointermove=movePointerDrag", self.app)
        self.assertIn("node.onpointerup=event=>finishPointerDrag(event)", self.app)
        self.assertIn("if(destination&&destination!==state.origin){movePlayer(state.playerId,destination);}", self.app)
        self.assertNotIn("destinationInitial.textContent='위치 이동'", self.app)

    def test_lateral_forward_slots_keep_st_as_the_only_display_label(self):
        resolver = (ROOT / "web" / "static" / "js" / "configured_position_display.js").read_text(encoding="utf-8")
        positions = {row["position_id"]: row for row in self.registry["positions"]}
        for position_id, lane in (("forward_left", "left"), ("forward_centre", "centre"), ("forward_right", "right")):
            self.assertEqual(positions[position_id]["position_family"], "forward")
            self.assertEqual(positions[position_id]["lateral_slot"], lane)
            self.assertIn(f"{position_id}: 'ST'", resolver)
        self.assertIn("getConfiguredPositionDisplayLabel(position)", self.app)
        self.assertIn("strong.textContent=displayPosition", self.app)

    def test_lateral_am_slots_are_not_aml_amc_or_amr(self):
        positions = {row["position_id"]: row for row in self.registry["positions"]}
        resolver = (ROOT / "web" / "static" / "js" / "configured_position_display.js").read_text(encoding="utf-8")
        role_resolution = (ROOT / "web" / "static" / "js" / "role_resolution.js").read_text(encoding="utf-8")
        for position_id, lane in (("attacking_midfield_left", "left"), ("attacking_midfield_centre", "centre"), ("attacking_midfield_right", "right")):
            self.assertEqual(positions[position_id]["position_family"], "attacking_midfield")
            self.assertEqual(positions[position_id]["vertical_band"], "attacking_midfield")
            self.assertEqual(positions[position_id]["vertical_index"], 5)
            self.assertEqual(positions[position_id]["lateral_slot"], lane)
            self.assertIn(f"{position_id}: 'AM'", resolver)
            self.assertIn(f"{position_id}:[['AM'],[]]", role_resolution)
        self.assertEqual(positions["AML"]["position_id"], "AML")
        self.assertEqual(positions["AMC"]["position_id"], "AMC")
        self.assertEqual(positions["AMR"]["position_id"], "AMR")

    def test_lateral_slots_preserve_configured_lane_for_analysis_and_phase_state(self):
        self.assertIn("attacking_midfield_left:[39,30]", self.app)
        self.assertIn("attacking_midfield_centre:[50,30]", self.app)
        self.assertIn("attacking_midfield_right:[61,30]", self.app)
        self.assertIn("preferredCentre=origin?.startsWith('attacking_midfield_')?'attacking_midfield_centre'", self.app)
        self.assertIn("nearestDragSlot(event.clientX,event.clientY,state.origin)", self.app)
        self.assertIn("ip_positions:playerSlots", self.app)
        self.assertIn("oop_positions:playerSlots", self.app)
        self.assertIn("positions=tactic[positionKey(phase)]", self.app)
        self.assertIn("forward_centre: 'ST'", (ROOT / "web" / "static" / "js" / "configured_position_display.js").read_text(encoding="utf-8"))
        self.assertIn("attacking_midfield_centre: 'AMC'", (ROOT / "web" / "static" / "js" / "configured_position_display.js").read_text(encoding="utf-8"))
        self.assertIn("normalizeConfiguredPositionForPreset", self.app)

    def test_role_popover_uses_rendered_geometry_and_container_clamping(self):
        stylesheet = (ROOT / "web" / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn("function placeRolePopover(box,node)", self.app)
        self.assertIn("pitch.getBoundingClientRect()", self.app)
        self.assertIn("node.getBoundingClientRect()", self.app)
        self.assertIn("box.getBoundingClientRect()", self.app)
        self.assertIn("belowFits", self.app)
        self.assertIn("aboveFits", self.app)
        self.assertIn("pitch.clientWidth-boxRect.width", self.app)
        self.assertIn("pitch.clientHeight-boxRect.height", self.app)
        self.assertIn("clamp(left,0,maxLeft)", self.app)
        self.assertIn("clamp(preferredTop,0,maxTop)", self.app)
        self.assertNotIn("transform:translate(-50%,12px)", stylesheet)

    def test_team_instruction_click_rerenders_selected_phase_state(self):
        self.assertIn("const key=phase==='IP'?'ip_team_instructions':'oop_team_instructions'", self.app)
        self.assertIn("button.classList.toggle('active',(tactic[key]?.[category.internal_id]||'')===value.internal_id)", self.app)
        self.assertIn("updateTacticalStyleStatus();clear();renderInstructions();", self.app)

    def test_current_browser_ui_contract_keeps_instruction_events_and_visible_overlay_separate(self):
        self.assertIn("button.onclick=()=>{if(value.internal_id)tactic[key][category.internal_id]=value.internal_id;else delete tactic[key][category.internal_id];", self.app)
        self.assertIn("updateTacticalStyleStatus();clear();renderInstructions();", self.app)
        self.assertIn("if(analysis&&activeRolePhase==='IP')overlay();", self.app)
        self.assertIn("$('#pitch-legend').hidden=!analysis||activeRolePhase!=='IP';", self.app)
        self.assertIn("$('#pitch').append(svg);", self.app)

    def test_classifier_state_is_normalized_to_the_visible_css_class(self):
        self.assertIn("const visualState=(states.get(edge.link_id)?.state||'smooth').replaceAll('_','-');", self.app)
        self.assertIn("`connectivity-${visualState}`", self.app)

if __name__ == "__main__":
    unittest.main()
