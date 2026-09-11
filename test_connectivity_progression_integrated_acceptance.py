"""Regression coverage for the frozen Connectivity v2 / Progression boundary."""
import unittest

import connectivity_qualitative_evaluator
import progression_evaluator
from test_connectivity_engine_v2 import PRESETS, position_only


class ConnectivityProgressionIntegratedAcceptanceTests(unittest.TestCase):
    def test_all_presets_keep_frozen_topology_and_separate_regional_vocabularies(self):
        expected = {
            "4-2-3-1": (38, 16), "4-3-3": (40, 48), "4-4-2": (42, 32),
            "4-2-4": (38, 32), "3-4-2-1": (42, 25), "3-4-3": (38, 20),
            "3-5-2": (48, 40),
        }
        progression_statuses = {
            "advancement_to_forward", "advancement_to_intermediate",
            "support_or_lateral_only", "no_structural_advancement",
        }
        connectivity_statuses = {
            "multiple_structurally_distinct_route_families",
            "single_structural_route_family", "no_complete_regional_route_detected",
        }
        for formation, counts in expected.items():
            with self.subTest(formation=formation):
                v2 = position_only(PRESETS[formation])
                quality = connectivity_qualitative_evaluator.evaluate_connectivity_v2(v2)
                progression = progression_evaluator.evaluate_progression(v2, quality)
                self.assertEqual(counts, (len(v2["structural_links"]), len(v2["progression_routes"])))
                for region in ("left", "centre", "right"):
                    self.assertIn(quality["regional_connectivity"][region]["status"], connectivity_statuses)
                    self.assertIn(progression["regional_advancement"][region]["status"], progression_statuses)

    def test_line_skips_only_name_occupied_lines_and_stalls_keep_support_boundary(self):
        for formation, positions in PRESETS.items():
            with self.subTest(formation=formation):
                v2 = position_only(positions)
                progression = progression_evaluator.evaluate_progression(
                    v2, connectivity_qualitative_evaluator.evaluate_connectivity_v2(v2)
                )
                occupied = {node["vertical_index"] for node in v2["nodes"]}
                for item in progression["line_skips"]:
                    self.assertTrue(set(item["skipped_occupied_lines"]) <= occupied)
                    source_index = next(node["vertical_index"] for node in v2["nodes"] if node["node_id"] == item["source"])
                    target_index = next(node["vertical_index"] for node in v2["nodes"] if node["node_id"] == item["target"])
                    self.assertTrue(all(source_index < line < target_index
                                        for line in item["skipped_occupied_lines"]))
                for stall in progression["advance_then_stall"]:
                    self.assertIn("available_support_or_recycle", stall)


if __name__ == "__main__":
    unittest.main()
