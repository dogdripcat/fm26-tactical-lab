import copy
import unittest
import fm26lab as f
import role_behaviours as kb
import tactic_analysis as a

class OfficialTests(unittest.TestCase):
    def analyze(self,t,data=None,obs=None):return a.analyze_evidence(t,f.ROLE_DICTIONARY,f.ROLE_ALIASES,obs,behaviour_kb=data)

    def test_cfd_classification_attributes_no_movement(self):
        entry=next(r for r in kb.load_knowledge_base() if r['role']=='CFD')
        self.assertGreaterEqual(len(entry['behaviours']),6)
        self.assertTrue({'role_classification','goal_threat','key_attribute'} <= {b['category'] for b in entry['behaviours']})
        self.assertEqual({b['attribute'] for b in entry['behaviours'] if 'attribute' in b},{'Off the Ball','Acceleration','Composure','Finishing'})
        report=self.analyze({'ip_roles':{'ST':'CFD'}})
        self.assertTrue(all(not x['expected_structure']['facts'] for x in report['areas']))
        self.assertGreaterEqual(len(report['role_knowledge'][0]['items']),6)

    def test_wfd_expected_not_observed(self):
        report=self.analyze({'ip_roles':{'AMR':'WF'}})
        areas={x['area']:x for x in report['areas']}
        self.assertEqual(areas['width']['expected_structure']['facts'][0]['behaviour_id'],'WFD_IP_MAINTAIN_WIDTH')
        self.assertEqual(areas['width']['confidence']['level'],'official_role_description')
        self.assertTrue(areas['depth']['expected_structure']['facts'])
        self.assertTrue(areas['box_entries']['expected_structure']['facts'])
        self.assertTrue(areas['central_buildup']['expected_structure']['facts'])
        evidence={e['evidence_id'] for e in report['knowledge_evidence']}
        for area in report['areas']:
            self.assertEqual(area['observed_structure']['facts'],[])
            self.assertIsNone(area['score'])
            for fact in area['expected_structure']['facts']:
                self.assertTrue(set(fact['evidence_ids'])<=evidence)
        obs=[dict(area='width',phase='IP',match_id='test',source='review',metric='test',value=1)]
        with_obs=self.analyze({'ip_roles':{'AMR':'WFD'}},obs=obs)
        self.assertEqual(next(x for x in with_obs['areas'] if x['area']=='width')['observed_structure']['facts'][0]['value'],1)

    def test_verification_and_conditions_block(self):
        for kind in ('role','individual','conditions'):
            data=kb.load_knowledge_base();r=next(x for x in data if x['role']=='WFD')
            if kind=='role':r['behaviour_verified']=False
            if kind=='individual':
                r['behaviour_verified']=False
                for b in r['behaviours']:b['verification']='unverified'
            if kind=='conditions':
                for b in r['behaviours']:b['conditions']=['unconfirmed_condition']
            report=self.analyze({'ip_roles':{'AMR':'WFD'}},data)
            self.assertTrue(all(not x['expected_structure']['facts'] for x in report['areas']))
        data=kb.load_knowledge_base();r=next(x for x in data if x['role']=='WFD')
        next(b for b in r['behaviours'] if b['category']=='width')['verification']='unverified'
        self.assertFalse(next(x for x in self.analyze({'ip_roles':{'AMR':'WFD'}},data)['areas'] if x['area']=='width')['expected_structure']['facts'])

    def test_other_roles_and_oop_unchanged(self):
        for r in kb.load_knowledge_base():
            if r['role'] not in ('CFD','WFD','AM','IF','DLP','BBP','WB','IWB','CB','BGK'):
                self.assertFalse(r['behaviour_verified']);self.assertEqual(r['behaviours'],[]);self.assertEqual(r['evidence'],[])
        report=self.analyze({'oop_roles':{'AMR':'WFD'},'ip_roles':{'ST':'CHF'}})
        self.assertTrue(all(not x['expected_structure']['facts'] for x in report['areas']))

    def test_official_requires_official_source(self):
        data=kb.load_knowledge_base();r=next(x for x in data if x['role']=='WFD')
        r['evidence'][0]['source']='https://example.com'
        with self.assertRaises(ValueError):kb.validate_knowledge_base(data)

if __name__=='__main__':unittest.main()
