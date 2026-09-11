"""Qualitative Connectivity v2 is deterministic, scoreless, and topology read-only."""
import copy
import json
from pathlib import Path
import subprocess
import unittest

import connectivity_qualitative_evaluator as qualitative
from test_connectivity_engine_v2 import PRESETS, position_only, v2, tactic

ROOT=Path(__file__).resolve().parent
RUNNER=ROOT/'web'/'static'/'js'/'qualitative_parity_runner.mjs'

def node(node_id, lane, vertical, band=None):
    return {"node_id":node_id,"configured_position":node_id,"lateral_slot":lane,"vertical_index":vertical,"vertical_band":band or ("forward" if vertical==3 else "midfield")}

def edge(source,target,direction='forward'):
    return {"link_id":f"{source}->{target}","source":source,"target":target,"direction":direction,"role_modifiers":[]}

def fixture(nodes,links):
    routes=qualitative._routes_from_graph(nodes,links)
    return {"nodes":nodes,"structural_links":links,"progression_routes":routes,"role_modifiers":[]}

def contains_key(value,key):
    if isinstance(value,dict): return key in value or any(contains_key(item,key) for item in value.values())
    if isinstance(value,list): return any(contains_key(item,key) for item in value)
    return False

class QualitativeEvaluatorTests(unittest.TestCase):
    def test_line_continuity_and_pipeline_safe_output(self):
        result=qualitative.evaluate_connectivity_v2(v2())
        self.assertEqual(result['line_continuity']['status'],'continuous')
        self.assertEqual(result['progression']['status'],'complete_route_present')
        self.assertFalse(contains_key(result,'score'))

    def test_route_family_deduplicates_raw_defender_variants(self):
        result=qualitative.evaluate_connectivity_v2(v2())
        self.assertLess(result['debug']['distinct_route_family_count'],result['debug']['raw_route_count'])
        self.assertTrue(all('origin_region' in family and 'major_connectors' in family for family in result['route_diversity']['families']))

    def test_shared_connector_is_not_automatically_a_bottleneck(self):
        nodes=[node('DL','left',1),node('DR','right',1),node('DC','centre',1),node('MC','centre',2),node('MC2','centre',2),node('ST','centre',3,'forward')]
        graph=fixture(nodes,[edge('DL','MC'),edge('DR','MC'),edge('MC','ST'),edge('DC','MC2'),edge('MC2','ST')])
        result=qualitative.evaluate_connectivity_v2(graph)
        mc=next(item for item in result['connector_dependency'] if item['node_id']=='MC')
        self.assertEqual(mc['impact'],'removes_one_alternative')
        self.assertNotIn('MC',{item['node_id'] for item in result['structural_bottlenecks']})

    def test_true_bottleneck_requires_route_survival_loss(self):
        graph=fixture([node('DC','centre',1),node('MC','centre',2),node('ST','centre',3,'forward')],[edge('DC','MC'),edge('MC','ST')])
        result=qualitative.evaluate_connectivity_v2(graph)
        mc=next(item for item in result['connector_dependency'] if item['node_id']=='MC')
        self.assertEqual(mc['impact'],'all_complete_progression_removed')
        self.assertEqual(mc['classification'],'critical_structural_bridge')
        self.assertEqual(result['structural_bottlenecks'],[mc])

    def test_support_recycle_and_dead_end_safeguards(self):
        graph=fixture([node('DC','centre',1),node('MC','centre',2),node('ST','centre',3,'forward')],[edge('DC','MC'),edge('MC','ST')])
        result=qualitative.evaluate_connectivity_v2(graph)
        self.assertEqual(next(item for item in result['support_recycle']['nodes'] if item['node_id']=='MC')['status'],'fallback_not_detected')
        self.assertEqual(result['dead_ends'],[])
        self.assertNotIn('ST',{item['node_id'] for item in result['dead_ends']})

    def test_cross_region_access_and_isolation_are_contextual(self):
        nodes=[node('DL','left',1),node('ML','left',2),node('ST','left',3,'forward'),node('RISO','right',2)]
        result=qualitative.evaluate_connectivity_v2(fixture(nodes,[edge('DL','ML'),edge('ML','ST')]))
        self.assertEqual(result['cross_region_access']['left_to_centre']['status'],'access_not_detected')
        self.assertEqual(result['cross_region_access']['right_to_centre']['status'],'access_not_detected')
        self.assertIn('RISO',{item['node_id'] for item in result['isolated_nodes']})
        self.assertNotIn('ST',{item['node_id'] for item in result['isolated_nodes']})

    def test_all_eight_synthetic_topology_fixtures(self):
        fixtures={
            'A': fixture([node('DC','centre',1),node('MC','centre',2),node('ST','centre',3,'forward')],[edge('DC','MC'),edge('MC','ST')]),
            'B': fixture([node('DL','left',1),node('ML','left',2),node('ST','left',3,'forward'),node('RISO','right',2)],[edge('DL','ML'),edge('ML','ST')]),
            'C': fixture([node('DL','left',1),node('DR','right',1),node('MC','centre',2),node('ST','centre',3,'forward')],[edge('DL','MC'),edge('DR','MC'),edge('MC','ST')]),
            'D': fixture([node('DL','left',1),node('ML','left',2),node('SL','left',3,'forward'),node('DR','right',1),node('MR','right',2),node('SR','right',3,'forward')],[edge('DL','ML'),edge('ML','SL'),edge('DR','MR'),edge('MR','SR')]),
            'E': fixture([node('DC','centre',1),node('MC','centre',2),node('ST','centre',3,'forward')],[edge('DC','MC','support'),edge('MC','DC','backward')]),
            'F': fixture([node('DC','centre',1),node('MC','centre',2),node('ST','centre',3,'forward')],[edge('DC','MC'),edge('MC','ST')]),
            'G': fixture([node('DL','left',1),node('ML','left',2),node('ST','left',3,'forward')],[edge('DL','ML'),edge('ML','ST')]),
            'H': fixture([node('DC','centre',1),node('MC','centre',2),node('ST','centre',3,'forward')],[edge('DC','MC'),edge('MC','ST')]),
        }
        results={name:qualitative.evaluate_connectivity_v2(graph) for name,graph in fixtures.items()}
        self.assertEqual(results['A']['structural_bottlenecks'][0]['node_id'],'MC')
        self.assertIn('RISO',{item['node_id'] for item in results['B']['isolated_nodes']})
        self.assertEqual(next(item for item in results['C']['connector_dependency'] if item['node_id']=='MC')['impact'],'all_complete_progression_removed')
        self.assertEqual(results['D']['regional_connectivity']['left']['status'],'complete_route_present')
        self.assertEqual(results['D']['regional_connectivity']['right']['status'],'complete_route_present')
        self.assertEqual(results['E']['progression']['status'],'no_complete_route_detected')
        self.assertEqual(next(item for item in results['F']['support_recycle']['nodes'] if item['node_id']=='MC')['status'],'fallback_not_detected')
        self.assertEqual(results['G']['cross_region_access']['left_to_centre']['status'],'access_not_detected')
        self.assertEqual(results['H']['regional_connectivity']['left']['status'],'no_complete_regional_route_detected')
        self.assertEqual(results['H']['regional_connectivity']['right']['status'],'no_complete_regional_route_detected')

    def test_evidence_absence_cannot_change_baseline_qualitative_topology(self):
        first=qualitative.evaluate_connectivity_v2(v2())
        no_modifiers=copy.deepcopy(v2())
        no_modifiers['role_modifiers']=[]
        for item in no_modifiers['structural_links']: item['role_modifiers']=[]
        second=qualitative.evaluate_connectivity_v2(no_modifiers)
        for key in ('line_continuity','progression','route_diversity','regional_connectivity','cross_region_access','support_recycle','connector_dependency','structural_bottlenecks','dead_ends','isolated_nodes','debug'):
            self.assertEqual(first[key],second[key])

    def test_all_seven_presets_keep_topology_and_receive_no_formation_rank(self):
        for name,positions in PRESETS.items():
            with self.subTest(name=name):
                graph=position_only(positions); before=json.dumps(graph['structural_links'],sort_keys=True)
                result=qualitative.evaluate_connectivity_v2(graph)
                self.assertEqual(result['line_continuity']['status'],'continuous')
                self.assertEqual(json.dumps(graph['structural_links'],sort_keys=True),before)
                self.assertFalse({'score','grade','ranking'} & set(result))

    def test_python_browser_parity_and_legacy_v2_regression(self):
        for name in ('sample_leicester_4231.json','static_parity_fixture_433.json','static_parity_fixture_442.json','static_parity_fixture_3421.json'):
            raw=tactic(name); expected_v2=v2() if name=='sample_leicester_4231.json' else __import__('connectivity_engine_v2').build_connectivity_v2(raw, __import__('role_constraints').load_role_catalog(), __import__('role_behaviours').load_knowledge_base(), __import__('fm26lab').ROLE_ALIASES)
            expected={'connectivity_v2':expected_v2,'connectivity_evaluation':qualitative.evaluate_connectivity_v2(expected_v2)}
            actual=json.loads(subprocess.check_output(['node',str(RUNNER),str(ROOT/name)],cwd=ROOT,text=True,encoding='utf-8'))
            self.assertEqual(actual,expected,name)
        self.assertEqual(len(v2()['structural_links']),38)

if __name__=='__main__': unittest.main()
