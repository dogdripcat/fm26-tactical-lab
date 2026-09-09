import copy
import unittest
import fm26lab as f
import tactic_analysis as a
import role_behaviours as kb

class IngameTests(unittest.TestCase):
    def test_individual_claims_and_instruction_separation(self):
        data=kb.load_knowledge_base()
        for role in ('AM','IF'):
            entry=next(r for r in data if r['role']==role)
            self.assertEqual(len(entry['behaviours']),5)
            self.assertTrue(all(b['verification']=='user_ingame_verified' for b in entry['behaviours']))
            self.assertEqual(entry['evidence'][0]['source_type'],'user_ingame_capture')
            self.assertEqual(entry['relationships'],[])
        entry=next(r for r in data if r['role']=='IF')
        self.assertEqual(entry['player_instructions'][0]['name_ko'],'더욱 앞으로 전진하라')
        self.assertFalse(any('더욱 앞으로' in b['claim'] for b in entry['behaviours']))

    def test_expected_only_no_combination(self):
        r=a.analyze_evidence({'ip_roles':{'AMC':'AM','AML':'IF'},'oop_roles':{'AMC':'AM'}},f.ROLE_DICTIONARY,f.ROLE_ALIASES)
        expected=[e for area in r['areas'] for e in area['expected_structure']['facts']]
        self.assertEqual(len(expected),6)
        self.assertEqual({e['role'] for e in expected},{'AM','IF'})
        self.assertTrue(all(e['verification']=='user_ingame_verified' for e in expected))
        self.assertFalse(any('더욱 앞으로' in e['claim'] for e in expected))
        for area in r['areas']:
            self.assertEqual(area['observed_structure']['facts'],[])
            if area['phase']=='OOP' or area['area']=='space_overlap':self.assertEqual(area['expected_structure']['facts'],[])
            self.assertIsNone(area['score'])

    def test_individual_gate_and_provenance(self):
        data=kb.load_knowledge_base();entry=next(r for r in data if r['role']=='AM')
        next(b for b in entry['behaviours'] if b['category']=='ball_receiving')['verification']='unverified'
        report=a.analyze_evidence({'ip_roles':{'AMC':'AM'}},f.ROLE_DICTIONARY,f.ROLE_ALIASES,behaviour_kb=data)
        ids=[e['behaviour_id'] for area in report['areas'] for e in area['expected_structure']['facts']]
        self.assertNotIn('AM_IP_RECEIVE_BETWEEN_LINES',ids)
        entry['evidence'][0]['source_type']='unverified'
        with self.assertRaises(ValueError):kb.validate_knowledge_base(data)

if __name__=='__main__':unittest.main()
