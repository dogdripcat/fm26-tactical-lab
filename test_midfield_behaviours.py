import unittest
import fm26lab as f
import tactic_analysis as a
import role_behaviours as kb

class MidfieldTests(unittest.TestCase):
    def test_data_and_instruction(self):
        rows={r['role']:r for r in kb.load_knowledge_base()}
        self.assertEqual(len(rows['BBP']['behaviours']),5)
        self.assertEqual(len(rows['DLP']['behaviours']),6)
        for role in ('DLP','BBP'):
            r=rows[role]
            self.assertEqual(r['evidence'][0]['source_type'],'user_ingame_capture')
            self.assertTrue(all(b['verification']=='user_ingame_verified' for b in r['behaviours']))
            self.assertEqual(r['relationships'],[])
        self.assertEqual(rows['DLP']['player_instructions'][0]['name_ko'],'더 모험적으로 플레이하라')
        self.assertFalse(any('모험' in b['claim'] for b in rows['DLP']['behaviours']))

    def test_expected_separate_and_no_stronger_claims(self):
        report=a.analyze_evidence({'ip_roles':{'DML':'DLP','DMR':'BBP','AMC':'AM'}},f.ROLE_DICTIONARY,f.ROLE_ALIASES)
        expected=[e for area in report['areas'] for e in area['expected_structure']['facts'] if e['role'] in ('DLP','BBP')]
        self.assertEqual(len(expected),7)
        self.assertFalse(any('TAG_' in e['behaviour_id'] for e in expected))
        self.assertFalse(any('항상' in e['claim'] or '모험' in e['claim'] or '충돌' in e['claim'] for e in expected))
        requirement=next(e for e in expected if e['behaviour_id']=='DLP_IP_DEFENSIVE_REQUIREMENT')
        self.assertEqual(requirement['category'],'player_requirement')
        for area in report['areas']:
            self.assertEqual(area['observed_structure']['facts'],[])
            self.assertIsNone(area['score'])
            if area['phase']=='OOP' or area['area']=='space_overlap':self.assertEqual(area['expected_structure']['facts'],[])

    def test_gates(self):
        for role in ('DLP','BBP'):
            data=kb.load_knowledge_base();row=next(r for r in data if r['role']==role)
            row['behaviour_verified']=False
            report=a.analyze_evidence({'ip_roles':{'DML':role}},f.ROLE_DICTIONARY,f.ROLE_ALIASES,behaviour_kb=data)
            self.assertTrue(all(not x['expected_structure']['facts'] for x in report['areas']))
            row['behaviour_verified']=True
            target=next(b for b in row['behaviours'] if b['category']!='role_classification');target['verification']='unverified'
            report=a.analyze_evidence({'ip_roles':{'DML':role}},f.ROLE_DICTIONARY,f.ROLE_ALIASES,behaviour_kb=data)
            self.assertNotIn(target['behaviour_id'],[e['behaviour_id'] for x in report['areas'] for e in x['expected_structure']['facts']])
            report=a.analyze_evidence({'oop_roles':{'DML':role}},f.ROLE_DICTIONARY,f.ROLE_ALIASES)
            self.assertTrue(all(not x['expected_structure']['facts'] for x in report['areas']))

if __name__=='__main__':unittest.main()
