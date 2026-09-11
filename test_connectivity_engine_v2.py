"""Structural-first v2 stays separate from the legacy evidence graph."""
import copy
import json
from pathlib import Path
import subprocess
import unittest

import connectivity_engine
import connectivity_engine_v2
from fm26lab import ROLE_ALIASES
import role_behaviours
import role_constraints

ROOT=Path(__file__).resolve().parent
RUNNER=ROOT / 'web' / 'static' / 'js' / 'parity_runner_v2.mjs'
PRESETS=json.loads((ROOT/'web'/'static'/'data'/'presets.json').read_text(encoding='utf-8'))['presets']

def tactic(path='sample_leicester_4231.json'):
    return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))

def v2(data=None, kb=None):
    return connectivity_engine_v2.build_connectivity_v2(tactic(), data or role_constraints.load_role_catalog(), kb or role_behaviours.load_knowledge_base(), ROLE_ALIASES)

def position_only(positions):
    return connectivity_engine_v2.build_connectivity_v2(
        {'ip_roles': {position: None for position in positions}},
        role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), ROLE_ALIASES,
    )

class ConnectivityV2Tests(unittest.TestCase):
    def test_structural_baseline_survives_missing_behaviour_evidence(self):
        baseline=v2()
        no_behaviour=copy.deepcopy(role_behaviours.load_knowledge_base())
        for entry in no_behaviour:
            entry['behaviour_verified']=False
        without=v2(kb=no_behaviour)
        self.assertTrue(baseline['structural_links'])
        self.assertEqual([(x['source'],x['target'],x['relation_type']) for x in baseline['structural_links']],[(x['source'],x['target'],x['relation_type']) for x in without['structural_links']])
        self.assertEqual(without['role_modifiers'],[])

    def test_role_semantics_modify_but_do_not_create_links(self):
        result=v2()
        semantic_links=[link for link in result['structural_links'] if link['role_modifiers']]
        self.assertTrue(semantic_links)
        self.assertTrue(any(item['semantic_id']=='send_forward' for link in semantic_links for item in link['role_modifiers']))
        self.assertTrue(all('structural_basis' in link for link in result['structural_links']))

    def test_regions_routes_and_bottlenecks_are_structural_and_scoreless(self):
        result=v2()
        self.assertEqual(set(result['network_regions']),{'left','centre','right'})
        self.assertTrue(result['progression_routes'])
        self.assertTrue(result['bottlenecks'])
        def keys(value):
            if isinstance(value,dict):
                return set(value) | set().union(*(keys(item) for item in value.values()))
            if isinstance(value,list):
                return set().union(*(keys(item) for item in value)) if value else set()
            return set()
        self.assertFalse({'score','probability','pass_success_estimate'} & keys(result))

    def test_three_back_wing_backs_and_team_instructions_do_not_change_v2(self):
        raw=tactic('static_parity_fixture_3421.json')
        first=connectivity_engine_v2.build_connectivity_v2(raw,role_constraints.load_role_catalog(),role_behaviours.load_knowledge_base(),ROLE_ALIASES)
        second_raw=copy.deepcopy(raw);second_raw['ip_team_instructions']={'tempo':'anything'}
        second=connectivity_engine_v2.build_connectivity_v2(second_raw,role_constraints.load_role_catalog(),role_behaviours.load_knowledge_base(),ROLE_ALIASES)
        self.assertTrue({'IP:wing_back_left','IP:wing_back_right'} <= {node['node_id'] for node in first['nodes']})
        self.assertEqual(first['structural_links'],second['structural_links'])

    def test_occupied_line_adjacency_matches_all_seven_presets(self):
        expected={
            '4-2-3-1':(38,16), '4-3-3':(40,48), '4-4-2':(42,32),
            '4-2-4':(38,32), '3-4-2-1':(42,25), '3-4-3':(38,20), '3-5-2':(48,40),
        }
        for formation, counts in expected.items():
            with self.subTest(formation=formation):
                result=position_only(PRESETS[formation])
                self.assertEqual((len(result['structural_links']),len(result['progression_routes'])),counts)
        repaired=position_only(PRESETS['4-4-2'])
        admitted=[link for link in repaired['structural_links'] if link['structural_basis']['adjacency_basis']=='occupied_line_adjacency']
        self.assertEqual(len(admitted),8)
        self.assertTrue(all(link['direction']=='forward' for link in admitted))
        self.assertTrue(all(link['lateral_relation'] in {'same_lane','adjacent_lane'} for link in admitted))

    def test_display_priority_preserves_topology_and_reveals_less_by_default(self):
        expected_links={'4-2-3-1':38,'4-3-3':40,'4-4-2':42,'4-2-4':38,'3-4-2-1':42,'3-4-3':38,'3-5-2':48}
        for formation, total in expected_links.items():
            with self.subTest(formation=formation):
                result=position_only(PRESETS[formation]); plan=result['display_plan']
                self.assertEqual(len(result['structural_links']),total)
                self.assertEqual(plan['full_link_count'],total)
                self.assertEqual(sum(plan['counts'].values()),total)
                self.assertLess(plan['default_visible_count'],total)
                self.assertTrue(all(link['presentation_class'] in {'PRIMARY','SECONDARY','HIDDEN_DEFAULT'} for link in result['structural_links']))
                self.assertTrue(all('default_visible' in link for link in result['structural_links']))

    def test_display_route_families_are_deterministic_and_evidence_independent(self):
        first=v2(); second=v2()
        self.assertEqual(first['display_plan']['route_families'],second['display_plan']['route_families'])
        no_behaviour=copy.deepcopy(role_behaviours.load_knowledge_base())
        for entry in no_behaviour: entry['behaviour_verified']=False
        without=v2(kb=no_behaviour)
        self.assertEqual(
            [(link['link_id'],link['presentation_class'],link['default_visible']) for link in first['structural_links'] if link['presentation_class']=='PRIMARY'],
            [(link['link_id'],link['presentation_class'],link['default_visible']) for link in without['structural_links'] if link['presentation_class']=='PRIMARY'],
        )
        self.assertTrue(any(link['direction']=='backward' and link['presentation_class']=='HIDDEN_DEFAULT' for link in first['structural_links']))

    def test_position_only_progression_topologies_and_evidence_independence(self):
        cb_cm_st=position_only(['DC','MC','ST'])
        self.assertIn(['IP:DC','IP:MC','IP:ST'],[route['node_ids'] for route in cb_cm_st['progression_routes']])
        cb_dm_am_st=position_only(['DC','DM','AMC','ST'])
        self.assertIn(['IP:DC','IP:DM','IP:AMC','IP:ST'],[route['node_ids'] for route in cb_dm_am_st['progression_routes']])
        self.assertTrue(any(link['source']=='IP:DC' and link['target']=='IP:wing_back_left' for link in position_only(['DC','wing_back_left','AML'])['structural_links']))
        self.assertTrue(any(link['source']=='IP:DC' and link['target']=='IP:MCL' for link in position_only(['DC','MCL','AML'])['structural_links']))
        three=position_only(['LCB','DC','RCB','MCL','MCR','ST','CF'])
        self.assertTrue(three['progression_routes'])
        kb=copy.deepcopy(role_behaviours.load_knowledge_base())
        for entry in kb: entry['behaviour_verified']=False
        no_evidence=connectivity_engine_v2.build_connectivity_v2({'ip_roles':{position:None for position in PRESETS['4-4-2']}},role_constraints.load_role_catalog(),kb,ROLE_ALIASES)
        self.assertEqual(len(no_evidence['progression_routes']),32)

    def test_compact_ui_uses_one_instruction_phase_and_v2_legend(self):
        index=(ROOT/'web'/'static'/'index.html').read_text(encoding='utf-8')
        app=(ROOT/'web'/'static'/'app.js').read_text(encoding='utf-8')
        self.assertIn('instruction-tab-IP',index)
        self.assertIn('instruction-tab-OOP',index)
        self.assertIn('instruction-panel-OOP" role="tabpanel" aria-labelledby="instruction-tab-OOP" hidden',index)
        self.assertIn('주요 연결',index)
        self.assertIn('전체 연결',index)
        self.assertIn('연결 의존도',index)
        self.assertIn('function setInstructionPhase(phase)',app)
        self.assertIn("linkMode==='all'",app)
        self.assertIn('selectedNode',app)
        self.assertIn('analysis.connectivity_v2?.structural_links',app)

    def test_python_browser_v2_parity_and_legacy_regression(self):
        for name in ('sample_leicester_4231.json','static_parity_fixture_433.json','static_parity_fixture_442.json','static_parity_fixture_3421.json'):
            raw=tactic(name)
            expected=connectivity_engine_v2.build_connectivity_v2(raw,role_constraints.load_role_catalog(),role_behaviours.load_knowledge_base(),ROLE_ALIASES)
            actual=json.loads(subprocess.check_output(['node',str(RUNNER),str(ROOT/name)],cwd=ROOT,text=True,encoding='utf-8'))
            self.assertEqual(actual,expected,name)
        legacy=connectivity_engine.build_connectivity(tactic(),role_constraints.load_role_catalog(),role_behaviours.load_knowledge_base(),ROLE_ALIASES)
        self.assertEqual(len(legacy['edges']),61)
        self.assertEqual(legacy['evidence_completeness'],{'edges_total':61,'semantic_complete':2,'mixed':7,'compatibility_only':4,'evidence_missing':48})

if __name__=='__main__': unittest.main()
