"""Browser presentation formats evaluator output without inventing tactical states."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import connectivity_qualitative_evaluator as qualitative
from test_connectivity_engine_v2 import PRESETS, position_only, v2
from test_connectivity_qualitative_evaluator import edge, fixture, node

ROOT=Path(__file__).resolve().parent
RUNNER=ROOT/'web'/'static'/'js'/'connectivity_evaluation_presentation_runner.mjs'

def present(graph, evaluation=None):
    payload={"connectivity_v2":graph,"connectivity_evaluation":evaluation or qualitative.evaluate_connectivity_v2(graph)}
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',suffix='.json',delete=False) as handle:
        json.dump(payload,handle); path=Path(handle.name)
    try:
        return json.loads(subprocess.check_output(['node',str(RUNNER),str(path)],cwd=ROOT,text=True,encoding='utf-8'))
    finally:
        path.unlink(missing_ok=True)

class ConnectivityEvaluationPresenterTests(unittest.TestCase):
    def test_summary_continuity_regions_and_limitations_are_user_facing(self):
        result=present(v2())
        self.assertIn('구조적 연결',result['summary'])
        self.assertEqual(result['continuity'],'점유한 각 라인 사이에 전진 연결이 이어집니다.')
        self.assertEqual([item['title'] for item in result['regions']],['왼쪽','중앙','오른쪽'])
        self.assertTrue(result['limitations'])
        self.assertNotIn('16',result['summary'])
        self.assertNotIn('semantic_complete',json.dumps(result,ensure_ascii=False))

    def test_dependency_bottleneck_and_shared_connector_use_distinct_wording(self):
        bridge=fixture([node('DC','centre',1),node('MC','centre',2),node('ST','centre',3,'forward')],[edge('DC','MC'),edge('MC','ST')])
        result=present(bridge)
        self.assertTrue(any('완결된 전진 경로가 남지 않습니다' in item['text'] for item in result['dependency']))
        evaluation=qualitative.evaluate_connectivity_v2(bridge)
        evaluation['connector_dependency']=[]; evaluation['structural_bottlenecks']=[]
        bridge['bottlenecks']=[{'node_id':'MC','status':'shared_progression_connector'}]
        shared=present(bridge,evaluation)
        self.assertEqual(shared['shared'][0]['text'],'MC 위치는 여러 전진 경로가 이 연결점을 공유합니다.')
        self.assertNotIn('의존',shared['shared'][0]['text'])

    def test_support_dead_end_isolation_and_role_adjustment_wording(self):
        no_recycle=fixture([node('DC','centre',1),node('MC','centre',2),node('ST','centre',3,'forward')],[edge('DC','MC'),edge('MC','ST')])
        result=present(no_recycle)
        self.assertIn('순환할 선택지가 제한적',result['support'])
        self.assertEqual(result['deadEnds'],[])
        sample=present(v2())
        self.assertTrue(sample['roleAdjustments'])
        self.assertTrue(all('근거' in item['text'] for item in sample['roleAdjustments']))

    def test_all_seven_presets_and_synthetic_cases_have_no_score_or_raw_route_headline(self):
        for name,positions in PRESETS.items():
            with self.subTest(name=name):
                result=present(position_only(positions))
                self.assertTrue(result['summary'])
                self.assertNotIn('전진 경로  ',result['summary'])
                self.assertNotIn('score',result)
        no_route=fixture([node('DC','centre',1),node('MC','centre',2),node('ST','centre',3,'forward')],[edge('DC','MC','support'),edge('MC','DC','backward')])
        self.assertIn('완결 경로가 현재 확인되지 않습니다',present(no_route)['summary'])
        wide=fixture([node('DL','left',1),node('ML','left',2),node('ST','left',3,'forward')],[edge('DL','ML'),edge('ML','ST')])
        self.assertEqual(next(item for item in present(wide)['regions'] if item['region']=='centre')['primary'],'완결 경로 미확인')

    def test_static_ui_consumes_presenter_and_preserves_pitch_controls(self):
        app=(ROOT/'web'/'static'/'app.js').read_text(encoding='utf-8')
        index=(ROOT/'web'/'static'/'index.html').read_text(encoding='utf-8')
        self.assertIn('presentConnectivityEvaluation(analysis.connectivity_evaluation,analysis.connectivity_v2)',app)
        self.assertIn('selectedRegionEdges()',app)
        self.assertIn('show-primary',index); self.assertIn('show-all',index)
        self.assertIn('역할에 따른 보정',index); self.assertIn('근거 및 한계',index)

if __name__=='__main__': unittest.main()
