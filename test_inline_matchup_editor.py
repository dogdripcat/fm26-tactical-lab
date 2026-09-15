from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent


class ReferenceLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        cls.app = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "web" / "static" / "style.css").read_text(encoding="utf-8")

    def test_global_control_bar_is_above_the_two_editor_cards(self):
        control = self.index.index('class="control-bar"')
        workspace = self.index.index('class="workspace"')
        self.assertLess(control, workspace)
        self.assertLess(self.index.index('id="tactical-style"'), workspace)
        self.assertLess(self.index.index('id="playing-approach"'), workspace)
        self.assertIn('.control-bar{grid-column:1/-1', self.css)
        self.assertIn('.control-bar .toolbar{display:flex', self.css)

    def test_editor_cards_share_equal_desktop_grid_and_pitch_variables(self):
        self.assertIn(':root{--tactic-pitch-width:320px;--tactic-pitch-height:480px;--editor-max-width:1280px}', self.css)
        self.assertIn('grid-template-columns:minmax(0,1fr) minmax(0,1fr)', self.css)
        self.assertIn('.workspace .pitch,.opponent-pitch{width:var(--tactic-pitch-width);height:var(--tactic-pitch-height)', self.css)
        self.assertNotIn('--tactic-pitch-width:400px', self.css)
        self.assertNotIn('width:min(100%,560px)', self.css.split('/* v1.2 reference-layout rebuild')[1])

    def test_right_card_switches_between_instruction_and_opponent_editor_only(self):
        self.assertIn('id="right-panel" class="right-panel"', self.index)
        self.assertIn('id="team-instructions" class="instructions"', self.index)
        self.assertIn('id="opponent-editor" class="opponent-editor" hidden', self.index)
        self.assertNotIn('id="opponent-mode"', self.index)
        self.assertNotIn('id="compare"', self.index)
        self.assertIn("$('#team-instructions').hidden=opponent", self.app)
        self.assertIn("$('#opponent-editor').hidden=!opponent", self.app)

    def test_compact_nodes_show_only_position_and_role_abbreviations(self):
        self.assertIn("cell.textContent=role?.display_abbr||'—'", self.app)
        self.assertIn("cell.textContent=role?.display_abbr||'—'", self.app)
        self.assertIn('.role-cell::before{display:none!important}', self.css)
        self.assertIn('.node,.opponent-pitch .node{min-width:0;width:max-content;padding:0;border:0', self.css)
        self.assertIn('id="own-tactic-heading">내 전술 (공 소유 시)', self.index)
        self.assertIn('상대 전술 (공 소유 시)', self.index)

    def test_matchup_results_are_below_editor_and_default_pitch_has_no_overlay(self):
        self.assertIn('id="matchup-result" class="matchup-result" hidden', self.index)
        self.assertIn("matchup-state-cards", self.app)
        self.assertIn("['활용 가능','주의','충돌 집중']", self.app)
        self.assertNotIn('renderMatchupOverlay(pitch,matchupObservations)', self.app)
        self.assertIn('.matchup-state-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))', self.css)

    def test_phase_heading_and_engine_boundary_remain_explicit(self):
        self.assertIn("$('#own-tactic-heading').textContent", self.app)
        self.assertIn("analysis=analyzeTactic(tactic,data)", self.app)
        self.assertIn("buildMatchupObservations(active('IP'),opponentActive())", self.app)

    def test_desktop_instruction_card_uses_equal_height_and_compact_two_column_grid(self):
        self.assertIn('.workspace,.right-panel,.right-panel>.instructions{height:566px;min-height:566px}', self.css)
        self.assertIn('#ip-team-instructions,#oop-team-instructions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))', self.css)
        self.assertIn('#ip-team-instructions{grid-template-rows:repeat(9,minmax(0,1fr));grid-auto-flow:column}', self.css)
        self.assertIn('#oop-team-instructions{grid-template-rows:repeat(5,minmax(0,1fr));grid-auto-flow:column}', self.css)
        self.assertIn('select.instruction-options{min-height:26px;height:26px', self.css)

    def test_tablet_editor_stacks_before_cards_become_unusable(self):
        self.assertIn('@media (min-width:761px) and (max-width:1000px)', self.css)
        self.assertIn('.app-layout>.workspace,.app-layout>.right-panel{grid-column:1;grid-row:auto}', self.css)


if __name__ == "__main__":
    unittest.main()
