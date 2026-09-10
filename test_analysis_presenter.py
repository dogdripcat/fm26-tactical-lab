import unittest

from web import api


class AnalysisPresenterTests(unittest.TestCase):
    def test_presentation_reads_existing_output_without_scores_or_new_states(self):
        report = api.analyze_payload(api.sample_tactic())
        presentation = report["presentation"]
        self.assertIn("connectivity", presentation)
        self.assertIn("progression", presentation)
        self.assertEqual("evidence_not_modelled", presentation["partnerships"]["status"])
        self.assertNotIn("score", presentation)
        states = {edge["status"] for group in presentation["connectivity"].values() for edge in group}
        self.assertTrue(states <= {"connected", "weakly_connected", "unknown", "structurally_unsupported"})

    def test_presentation_provenance_is_from_existing_edge(self):
        report = api.analyze_payload(api.sample_tactic())
        edges = [edge for group in report["presentation"]["connectivity"].values() for edge in group]
        self.assertTrue(all("evidence_ids" in edge for edge in edges))
