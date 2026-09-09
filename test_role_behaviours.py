import copy
import json
from pathlib import Path
import tempfile
import unittest
import role_behaviours as kb
import tactic_analysis as analysis
import fm26lab


def fixture():
    # Artificial schema fixture; not a claim about any Football Manager role.
    return [{'role':'TEST_ONLY','phase':'IP','behaviour_verified':True,
             'behaviours':[{'behaviour_id':'test-item','category':'passing','claim':'Schema fixture only',
                            'conditions':[],'evidence_ids':['test-source'],'verification':'verified'}],
             'relationships':[], 'evidence':[{'evidence_id':'test-source','source_type':'test_fixture',
                'title':'Synthetic validation data','source':'unit-test','accessed':'2026-09-07','notes':'Not game evidence'}]}]

class BehaviourTests(unittest.TestCase):
    def test_load_scoped_production_kb(self):
        data=kb.load_knowledge_base()
        self.assertEqual(len(data),12)
        self.assertEqual({(r['phase'],r['role']) for r in data},set(fm26lab.VERIFIED_ROLES))
        for r in data:
            if r['role'] in ('CFD','WFD','AM','IF','DLP','BBP','WB','IWB','CB','BGK'):
                self.assertTrue(r['behaviour_verified'])
                continue
            self.assertFalse(r['behaviour_verified'])
            for field in ('behaviours','relationships','evidence'):self.assertEqual(r[field],[])

    def test_individual_and_role_gates(self):
        data=fixture()
        other=copy.deepcopy(data[0]['behaviours'][0]);other.update(behaviour_id='not-verified',verification='unverified')
        data[0]['behaviours'].append(other)
        self.assertEqual([b['behaviour_id'] for b in kb.verified_behaviours(data,'TEST_ONLY','IP')],['test-item'])
        self.assertEqual(kb.verified_behaviours(data,'TEST_ONLY','OOP'),[])
        data[0]['behaviour_verified']=False
        self.assertEqual(kb.verified_behaviours(data,'TEST_ONLY','IP'),[])

    def test_validation_rejects_bad_evidence(self):
        for mutation in ('missing','dangling','date','duplicate','category','enabled_empty'):
            data=fixture()
            if mutation=='missing':data[0]['behaviours'][0]['evidence_ids']=[]
            if mutation=='dangling':data[0]['behaviours'][0]['evidence_ids']=['absent']
            if mutation=='date':data[0]['evidence'][0]['accessed']='not-a-date'
            if mutation=='duplicate':data.append(copy.deepcopy(data[0]))
            if mutation=='category':data[0]['behaviours'][0]['category']='invented'
            if mutation=='enabled_empty':data[0]['behaviours']=[]
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):kb.validate_knowledge_base(data)

    def test_file_loading_and_copy(self):
        data=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'kb.json';p.write_text(json.dumps(data));before=p.read_bytes()
            loaded=kb.load_knowledge_base(p);loaded.clear()
            self.assertEqual(p.read_bytes(),before)
            p.write_text('{broken')
            with self.assertRaises(ValueError):kb.load_knowledge_base(p)

    def test_analysis_blocks_unverified_behaviour(self):
        data=fixture();data[0]['behaviour_verified']=False
        dictionary=[{'phase':'IP','ingame_abbr':'TEST_ONLY','name_verified':True,'behaviour_verified':True}]
        r=analysis.analyze_evidence({'ip_roles':{'ST':'TEST_ONLY'}},dictionary,{},behaviour_kb=data)
        for area in r['areas']:
            self.assertEqual(area['expected_structure']['facts'],[])
            self.assertEqual(area['expected_structure']['status'],'unknown')
        self.assertFalse(r['areas'][0]['configured_structure']['facts'][0]['behaviour_verified'])
        self.assertFalse(r['behaviour_knowledge_base']['expected_generation_enabled'])
        # Schema-only release does not infer effects even for an enabled synthetic item.
        data[0]['behaviour_verified']=True
        r=analysis.analyze_evidence({'ip_roles':{'ST':'TEST_ONLY'}},dictionary,{},behaviour_kb=data)
        self.assertTrue(all(not x['expected_structure']['facts'] for x in r['areas']))

if __name__=='__main__':unittest.main()
