import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parent


class FormationRecognitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("node"):
            raise unittest.SkipTest("Node.js is required for browser-module verification")
        registry = json.loads((ROOT / "web/static/data/configured_position_registry.json").read_text(encoding="utf-8"))
        families = json.loads((ROOT / "web/static/data/formation_families.json").read_text(encoding="utf-8"))
        cls.registry = registry
        cls.families = families

    def recognize(self, positions):
        program = """
import {recognizeFormation} from './web/static/js/formation_recognition.js';
const [positions,registry,families]=JSON.parse(process.argv[1]);
process.stdout.write(JSON.stringify(recognizeFormation(positions,registry,families)));
"""
        result = subprocess.run(
            ["node", "--input-type=module", "-e", program, json.dumps([positions, self.registry, self.families])],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True,
        )
        return json.loads(result.stdout)

    def test_supported_formation_family_matrix(self):
        fixtures = {
            "4-4-2": ["GK","LB","LCB","RCB","RB","ML","MCL","MCR","MR","ST","CF"],
            "4-4-1-1": ["GK","LB","LCB","RCB","RB","ML","MCL","MCR","MR","AMC","ST"],
            "4-2-3-1": ["GK","LB","LCB","RCB","RB","DML","DMR","AML","AMC","AMR","ST"],
            "4-3-3": ["GK","LB","LCB","RCB","RB","DM","MCL","MCR","AML","AMR","ST"],
            "4-1-4-1": ["GK","LB","LCB","RCB","RB","DM","ML","MCL","MCR","MR","ST"],
            "4-3-2-1": ["GK","LB","LCB","RCB","RB","MCL","MC","MCR","AML","AMC","ST"],
            "4-1-2-1-2": ["GK","LB","LCB","RCB","RB","DM","MCL","MCR","AMC","ST","CF"],
            "4-3-1-2": ["GK","LB","LCB","RCB","RB","MCL","MC","MCR","AMC","ST","CF"],
            "4-2-2-2": ["GK","LB","LCB","RCB","RB","DML","DMR","AML","AMR","ST","CF"],
            "4-2-4": ["GK","LB","LCB","RCB","RB","MCL","MCR","AML","AMR","ST","CF"],
            "4-5-1": ["GK","LB","LCB","RCB","RB","ML","MCL","MC","MCR","MR","ST"],
            "3-4-3": ["GK","LCB","DC","RCB","wing_back_left","wing_back_right","MCL","MCR","AML","AMR","ST"],
            "3-4-2-1": ["GK","LCB","DC","RCB","wing_back_left","wing_back_right","MCL","MCR","AML","AMC","ST"],
            "3-4-1-2": ["GK","LCB","DC","RCB","wing_back_left","wing_back_right","MCL","MCR","AMC","ST","CF"],
            "3-5-2": ["GK","LCB","DC","RCB","wing_back_left","wing_back_right","MCL","MC","MCR","ST","CF"],
            "3-1-4-2": ["GK","LCB","DC","RCB","DM","ML","MCL","MCR","MR","ST","CF"],
            "3-2-4-1": ["GK","LCB","DC","RCB","DML","DMR","ML","MCL","MCR","MR","ST"],
            "5-4-1": ["GK","LB","LCB","DC","RCB","RB","ML","MCL","MCR","MR","ST"],
            "5-3-2": ["GK","LB","LCB","DC","RCB","RB","MCL","MC","MCR","ST","CF"],
            "5-2-2-1": ["GK","LB","LCB","DC","RCB","RB","MCL","MCR","AML","AMR","ST"],
        }
        for expected, positions in fixtures.items():
            with self.subTest(expected=expected):
                self.assertEqual(expected, self.recognize(positions)["formation"])

    def test_invalid_lane_distribution_and_impossible_count_are_custom(self):
        invalid_lanes=["GK","LB","LCB","CB","DC","ML","MCL","MCR","MR","ST","CF"]
        self.assertEqual("사용자 구성", self.recognize(invalid_lanes)["formation"])
        self.assertEqual("사용자 구성", self.recognize(["GK","LB","LCB","RCB","RB","MCL","MCR","ST"])["formation"])

    def test_442_regression_and_role_independence(self):
        shape=["GK","LB","LCB","RCB","RB","ML","MCL","MCR","MR","ST","CF"]
        result=self.recognize(shape)
        self.assertEqual("4-4-2", result["formation"])
        self.assertEqual("recognized", result["status"])

    def test_static_data_and_app_use_the_general_engine(self):
        app=(ROOT/"web/static/app.js").read_text(encoding="utf-8")
        loader=(ROOT/"web/static/js/data_loader.js").read_text(encoding="utf-8")
        self.assertIn("recognizeFormation(active(phase),data.registry,data.formationFamilies)", app)
        self.assertIn("recognizeFormation(opponentActive(),data.registry,data.formationFamilies)", app)
        self.assertIn("loadJson('formation_families.json')", loader)
        self.assertEqual(self.families, json.loads((ROOT/"data/formation_families.json").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
