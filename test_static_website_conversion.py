"""Parity tests for the static browser runtime; Python remains the reference oracle."""
import json
from pathlib import Path
import subprocess
import unittest
import connectivity_engine
from fm26lab import ROLE_ALIASES
import role_behaviours
import role_constraints
from web.analysis_presenter import present

ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "web" / "static" / "js" / "parity_runner.mjs"


def compact_python(tactic):
    graph = connectivity_engine.build_connectivity(
        tactic, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), ROLE_ALIASES,
    )
    def edge(item):
        provenance = item["provenance"]
        return {key: item[key] for key in ("from_node", "to_node", "path_type", "status")} | {
            key: provenance[key] for key in ("source_method", "target_method", "semantic_ids", "behaviour_ids", "evidence_ids", "evidence_completeness")
        }
    return {
        "nodes": [{"node_id": item["node_id"], "role_internal_id": item["role_internal_id"]} for item in graph["nodes"]],
        "edges": [edge(item) for item in graph["edges"]],
        "progression_chains": [{"node_ids": item["node_ids"], "status": item["status"]} for item in graph["progression_chains"]],
        "isolated_nodes": [item["node_id"] for item in graph["isolated_nodes"]],
        "evidence_completeness": graph["evidence_completeness"],
        "presentation": present({"connectivity": graph}),
    }


class StaticWebsiteConversionTests(unittest.TestCase):
    def browser_result(self, fixture):
        output = subprocess.check_output(["node", str(RUNNER), str(fixture)], cwd=ROOT, text=True, encoding="utf-8")
        return json.loads(output)

    def test_static_assets_have_no_api_or_localhost_runtime_dependency(self):
        source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "web" / "static").rglob("*.js"))
        index = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("/api/", source)
        self.assertNotIn("localhost", source.lower())
        self.assertNotIn("localhost", index.lower())
        self.assertIn('type="module"', index)
        self.assertIn("./style.css", index)

    def test_required_static_catalogues_and_seven_presets_exist(self):
        static_data = ROOT / "web" / "static" / "data"
        for filename in ("role_catalog.json", "role_behaviours.json", "configured_position_registry.json", "team_instruction_catalog.json", "team_instruction_evidence.json", "connectivity_semantic_vocabulary.json", "expected_role_space_ontology.json"):
            self.assertTrue((static_data / filename).is_file(), filename)
        self.assertEqual(len(json.loads((static_data / "presets.json").read_text(encoding="utf-8"))["presets"]), 7)

    def test_python_and_browser_match_all_golden_fixtures(self):
        fixtures = [ROOT / "sample_leicester_4231.json", ROOT / "static_parity_fixture_433.json", ROOT / "static_parity_fixture_442.json", ROOT / "static_parity_fixture_3421.json"]
        for fixture in fixtures:
            with self.subTest(fixture=fixture.name):
                tactic = json.loads(fixture.read_text(encoding="utf-8-sig"))
                self.assertEqual(self.browser_result(fixture), compact_python(tactic))

    def test_three_back_fixture_keeps_dedicated_wing_back_nodes(self):
        result = self.browser_result(ROOT / "static_parity_fixture_3421.json")
        self.assertEqual({item["node_id"] for item in result["nodes"]} & {"IP:wing_back_left", "IP:wing_back_right"}, {"IP:wing_back_left", "IP:wing_back_right"})
