import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import fm26lab as f
import tactic_analysis as a

class AnalysisTests(unittest.TestCase):
    def analyze(self,t,obs=None):return a.analyze_evidence(t,f.ROLE_DICTIONARY,f.ROLE_ALIASES,obs)

    def test_thirteen_and_unknown(self):
        r=self.analyze({'ip_formation':'unknown','ip_roles':{'ST':'unknown'}})
        self.assertEqual(len(r['areas']),13)
        for area in r['areas']:
            self.assertIsNone(area['score'])
            self.assertEqual(area['status'],'insufficient_evidence')
            self.assertEqual(area['expected_structure']['status'],'unknown')
            self.assertEqual(area['observed_structure']['facts'],[])
            self.assertEqual(area['confidence']['level'],'none')
        self.assertEqual(r['areas'][0]['configured_structure']['facts'][0]['value'],'unknown')

    def test_phase_independence(self):
        t={'ip_roles':{'ST':'CFwd'},'oop_roles':{'ST':'CFwd'},'ip_formation':'4231','oop_formation':'433'}
        r=self.analyze(t);changed=copy.deepcopy(t);changed['ip_roles']['ST']='IF'
        rr=self.analyze(changed)
        self.assertEqual([x for x in r['areas'] if x['phase']=='OOP'],[x for x in rr['areas'] if x['phase']=='OOP'])
        ip=r['areas'][0]['configured_structure']['facts'][-1]
        self.assertEqual((ip['raw_value'],ip['value']),('CFwd','CHF'))
        oop=next(x for x in r['areas'] if x['phase']=='OOP')['configured_structure']['facts'][-1]
        self.assertEqual(oop['value'],'CFwd')
        self.assertFalse(oop['name_verified'])

    def test_no_heuristics_or_behaviour(self):
        with patch.object(f,'diagnose',side_effect=AssertionError('legacy called')),patch.object(f,'prof',side_effect=AssertionError('weights called')):
            r=self.analyze({'ip_roles':{'ST':'CFD','LB':'AWB'},'team_instructions':{'tempo':'high'}})
        for area in r['areas']:self.assertEqual(area['expected_structure']['facts'],[])
        self.assertEqual(r['unassigned_configuration']['team_instructions'],{'tempo':'high'})
        self.assertTrue(all(not row['behaviour_verified'] for row in f.ROLE_DICTIONARY))
        self.assertEqual(sum(row['name_verified'] for row in f.ROLE_DICTIONARY),12)

    def test_observed_separation(self):
        observation={'area':'box_entries','phase':'IP','match_id':'match-1','source':'user video review','metric':'box entrants','value':3}
        r=self.analyze({'ip_roles':{'ST':'CHF'}},[observation])
        box=next(x for x in r['areas'] if x['area']=='box_entries')
        self.assertEqual(box['observed_structure']['facts'][0]['value'],3)
        self.assertEqual(box['expected_structure']['facts'],[])
        self.assertEqual(box['status'],'observations_available')
        self.assertTrue(all(not x['observed_structure']['facts'] for x in r['areas'] if x['area']!='box_entries'))
        unknown=copy.deepcopy(observation);unknown['value']='unknown'
        self.assertEqual(self.analyze({},[unknown])['areas'][5]['observed_structure']['status'],'unknown')
        bad=copy.deepcopy(observation);bad['phase']='OOP'
        with self.assertRaises(ValueError):self.analyze({},[bad])
        with self.assertRaises(ValueError):self.analyze({},[{'area':'box_entries','phase':'IP'}])

    def test_readonly_cli_json_and_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'t.json';db=root/'t.db';out=root/'report.json'
            t={'ip_roles':{'ST':'CFwd'},'oop_roles':{'ST':'unknown'}}
            src.write_text(json.dumps(t),encoding='utf-8')
            with contextlib.closing(sqlite3.connect(db)) as con:
                con.execute('CREATE TABLE tactics (id INTEGER, tactic_json TEXT)')
                con.execute('INSERT INTO tactics VALUES (1,?)',(json.dumps(t),));con.commit()
            before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in (src,db)]
            for argv in (['--file',str(src),'--out',str(out)],['--tactic','1']):
                with patch.object(f,'DB_PATH',db),patch.object(f,'init_db',side_effect=AssertionError('DB init')),patch('sys.argv',['fm26lab.py','analyze-tactic']+argv),contextlib.redirect_stdout(io.StringIO()) as stdout:
                    f.main()
                self.assertEqual(len(json.loads(stdout.getvalue())['areas']),13)
            self.assertEqual(before,[hashlib.sha256(p.read_bytes()).hexdigest() for p in (src,db)])
            self.assertEqual(json.loads(out.read_text())['areas'][0]['configured_structure']['facts'][0]['value'],'CHF')
            for dest in (src,db,out):
                with patch('sys.argv',['fm26lab.py','analyze-tactic','--file',str(src),'--out',str(dest)]),self.assertRaises(SystemExit):f.main()

    def test_input_preserved_and_gpt_boundary(self):
        t={'ip_roles':{'ST':'CFwd'}};before=copy.deepcopy(t)
        r=self.analyze(t);self.assertEqual(t,before)
        context=a.explanation_context(r)
        self.assertNotIn('deterministic_diagnostic',context)
        context['report']['areas'].clear();self.assertEqual(len(r['areas']),13)

if __name__=='__main__':unittest.main()
