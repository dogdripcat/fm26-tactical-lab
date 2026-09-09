import copy
import json
from pathlib import Path
import unittest

import connectivity_engine
import role_behaviours
import role_constraints
import role_evidence_registry
import role_connectivity_readiness
import role_knowledge_coverage


class RoleKnowledgeCoverageTests(unittest.TestCase):
    def setUp(self):
        self.catalog = role_constraints.load_role_catalog()
        self.knowledge = role_behaviours.load_knowledge_base()
        self.report = role_knowledge_coverage.build_coverage_report(self.catalog, self.knowledge)

    def status_for(self, internal_id):
        return next(row['status'] for row in self.report['roles'] if row['internal_id'] == internal_id)

    def test_current_coverage_distinguishes_partial_identity_and_ambiguity(self):
        self.assertEqual((self.report['verified'], self.report['partial'], self.report['identity_only'], self.report['unresolved']), (0, 10, 57, 2))
        self.assertEqual(self.status_for('catalog:ip:winger:if'), 'partial')
        self.assertEqual(self.status_for('catalog:ip:winger:inside-winger'), 'identity_only')
        self.assertEqual(self.status_for('catalog:ip:winger:playmaking-winger'), 'unresolved')

    def test_explicitly_complete_evidence_coverage_can_be_verified(self):
        knowledge = copy.deepcopy(self.knowledge)
        next(row for row in knowledge if row['role'] == 'IF')['coverage_status'] = 'verified'
        report = role_knowledge_coverage.build_coverage_report(self.catalog, knowledge)
        self.assertEqual(next(row['status'] for row in report['roles'] if row['internal_id'] == 'catalog:ip:winger:if'), 'verified')

    def test_evidence_less_behaviour_cannot_validate_or_create_coverage(self):
        knowledge = copy.deepcopy(self.knowledge)
        entry = next(row for row in knowledge if row['role'] == 'IF')
        entry['behaviours'][0]['evidence_ids'] = []
        with self.assertRaises(ValueError):
            role_behaviours.validate_knowledge_base(knowledge)

    def test_extended_json_ready_records_do_not_invent_connectivity_semantics(self):
        records = role_behaviours.behaviour_records(self.knowledge, self.catalog)
        target = next(row for row in records if row['behaviour_id'] == 'IF_IP_TAG_MOVE_INSIDE')
        self.assertEqual(target['role_internal_id'], 'catalog:ip:winger:if')
        self.assertEqual(target['source_kind'], 'user_ingame')
        self.assertEqual(target['connectivity_semantics'], {'send': [], 'receive': [], 'space': [], 'movement': []})
        self.assertEqual(target['limitations'], [])

    def test_existing_semantics_are_mapped_only_from_their_own_behaviour(self):
        records = role_behaviours.behaviour_records(self.knowledge, self.catalog)
        semantics = {
            row['behaviour_id']: row['connectivity_semantics']
            for row in records
        }
        self.assertEqual(semantics['DLP_IP_FORWARD_PASSES']['send'][0]['semantic_id'], 'send_forward')
        self.assertEqual(semantics['AM_IP_RECEIVE_BETWEEN_LINES']['receive'][0]['semantic_id'], 'receive_between_lines')
        self.assertEqual(semantics['IF_IP_CENTRAL_RECEIVING']['receive'][0]['semantic_id'], 'receive_centrally')
        self.assertEqual(semantics['CFD_IP_PRIMARY_SCORER'], {'send': [], 'receive': [], 'space': [], 'movement': []})

    def test_readiness_is_per_semantic_group_not_overall_role_coverage(self):
        readiness = {
            row['role_internal_id']: row['analysis_readiness']['connectivity']
            for row in role_connectivity_readiness.build_analysis_readiness(self.catalog, self.knowledge)
        }
        self.assertEqual(readiness['catalog:ip:dm:dlp'], {'send': 'verified', 'receive': 'unknown', 'space': 'verified', 'movement': 'unknown'})
        self.assertEqual(readiness['catalog:ip:fw:cfd'], {'send': 'unknown', 'receive': 'unknown', 'space': 'unknown', 'movement': 'unknown'})
        knowledge = copy.deepcopy(self.knowledge)
        item = next(row for row in knowledge if row['role'] == 'DLP')['behaviours']
        next(row for row in item if row['behaviour_id'] == 'DLP_IP_FORWARD_PASSES')['connectivity_semantics']['send'][0]['coverage'] = 'partial'
        readiness = {
            row['role_internal_id']: row['analysis_readiness']['connectivity']
            for row in role_connectivity_readiness.build_analysis_readiness(self.catalog, knowledge)
        }
        self.assertEqual(readiness['catalog:ip:dm:dlp']['send'], 'partial')

    def test_evidence_registry_uses_supported_levels(self):
        registry = role_evidence_registry.build_evidence_registry(self.knowledge)
        levels = {item['verification_level'] for item in registry}
        self.assertIn('user_ingame_verified', levels)
        self.assertIn('official_verified', levels)

    def test_identity_only_role_remains_unknown_to_connectivity(self):
        result = connectivity_engine.build_connectivity(
            {'ip_roles': {'DML': 'CHF', 'AMC': 'AM'}},
            self.catalog, self.knowledge, {},
        )
        self.assertEqual(result['edges'][0]['status'], 'unknown')

    def test_semantic_edge_uses_source_and_target_evidence(self):
        result = connectivity_engine.build_connectivity(
            {'ip_roles': {'DML': 'DLP', 'AMC': 'AM'}}, self.catalog, self.knowledge, {},
        )
        edge = result['edges'][0]
        self.assertEqual(edge['status'], 'connected')
        self.assertEqual(edge['source_basis'][0]['semantic_id'], 'send_forward')
        self.assertEqual(edge['target_basis'][0]['semantic_id'], 'receive_between_lines')

    def test_approved_non_edge_semantics_keep_provenance_without_edge_inference(self):
        vocabulary = json.loads((Path(__file__).with_name('connectivity_semantic_vocabulary.json')).read_text(encoding='utf-8'))
        groups = {row['semantic_id']: row['group'] for row in vocabulary}
        self.assertEqual(groups['send_simple_pass'], 'send')
        self.assertEqual(groups['move_to_receive'], 'movement')
        records = {row['behaviour_id']: row for row in role_behaviours.behaviour_records(self.knowledge, self.catalog)}
        cb = records['CB_IP_SIMPLE_PASS_TO_CREATIVE_PLAYERS']['connectivity_semantics']['send'][0]
        bgk = records['BGK_IP_MOVE_TO_RECEIVE']['connectivity_semantics']['movement'][0]
        self.assertEqual(cb['semantic_id'], 'send_simple_pass')
        self.assertEqual(bgk['semantic_id'], 'move_to_receive')
        self.assertFalse(cb['edge_eligible']); self.assertFalse(bgk['edge_eligible'])
        self.assertEqual(cb['evidence_ids'], ['USER_FM26_IP_CB_DESCRIPTION_001'])
        self.assertEqual(bgk['evidence_ids'], ['USER_FM26_IP_BGK_DESCRIPTION_001'])
        self.assertNotEqual(cb['semantic_id'], 'send_forward')
        self.assertNotIn(cb['semantic_id'], ('receive_centrally', 'receive_between_lines'))


if __name__ == '__main__':
    unittest.main()
