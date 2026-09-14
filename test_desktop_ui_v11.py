import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class DesktopUiV11Tests(unittest.TestCase):
    def test_single_phase_control_drives_pitch_and_instruction_panels(self):
        html = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertEqual(1, html.count('class="role-phase-control"'))
        self.assertIn('class="instruction-tabs" role="tablist" aria-label="팀 지침 국면" hidden', html)
        self.assertIn("$('#instruction-phase-label').textContent=phase==='IP'?'공 소유 · 18개':'공 미소유 · 9개'", script)

    def test_desktop_pitch_and_instruction_editor_are_prominent_but_compact(self):
        stylesheet = (ROOT / "web" / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".workspace .pitch{width:min(100%,500px)}", stylesheet)
        self.assertIn(".instruction-row{grid-template-columns:minmax(105px,1fr) minmax(120px,1fr)", stylesheet)
        self.assertIn(".instruction-tabs{display:none!important}", stylesheet)

    def test_compact_rebuild_uses_recognition_and_dual_role_cells(self):
        html = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertNotIn('id="formation"', html)
        self.assertIn('id="playing-approach" disabled', html)
        self.assertLess(html.index('style-control'), html.index('approach-control'))
        self.assertNotIn('id="pitch-legend"', html)
        self.assertIn("const knownFormation=phase=>", script)
        self.assertIn("shirt-icon", script)
        self.assertIn("dual-role-cells", script)
        self.assertIn("['IP','OOP'].forEach", script)


if __name__ == "__main__":
    unittest.main()
