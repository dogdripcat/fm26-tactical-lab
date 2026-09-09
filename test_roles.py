import argparse
import copy
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import fm26lab as f

class RoleTests(unittest.TestCase):
    def test_dictionary(self):
        self.assertEqual(len(f.VERIFIED_ROLES),12)
        required={'phase','position_group','name_ko','name_en','ingame_abbr','verification','source_note'}
        for row in f.ROLE_DICTIONARY:
            self.assertTrue(required <= row.keys())
            self.assertIn(row['phase'],('IP','OOP'))
            self.assertIn(row['verification'],('verified','official_name_only','unverified'))
            if row['verification']=='unverified':
                self.assertIsNone(row['ingame_abbr'])
        for abbr,name in [('CFD','Centre Forward'),('CHF','Channel Forward'),('WFD','Wide Forward'),('BGK','Ball-Playing Goalkeeper')]:
            self.assertEqual(f.VERIFIED_ROLES['IP',abbr]['name_en'],name)
        self.assertFalse(f.OOP_ROLES)

    def test_alias_and_phase(self):
        for old,new in [('CF','CFD'),('WF','WFD'),('BPGK','BGK'),('CFwd','CHF')]:
            self.assertEqual(f.canonical_role('IP',old),new)
            self.assertIsNone(f.canonical_role('OOP',old))
            self.assertNotIn(('IP',old),f.VERIFIED_ROLES)
        self.assertEqual(f.canonical_role('IP','CFwd'),'CHF')
        self.assertIsNone(f.canonical_role('OOP','CFD'))

    def test_unverified_no_effect(self):
        for token in ['AP','AWB','DM','unknown']:
            self.assertEqual(f.prof(token),{})
            t={'ip_roles':{'ST':token,'AMC':token,'LB':token,'RB':token,'DML':token}}
            other={'ip_roles':dict.fromkeys(t['ip_roles'],'unknown')}
            a,b=f.diagnose(t),f.diagnose(other)
            self.assertEqual(a['metrics'],b['metrics'])
            self.assertEqual(a['overall'],b['overall'])
        self.assertTrue(set(f.ROLE_PROFILES)<=f.IP_ROLES)

    def test_legacy_json_read_only(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'legacy.json'
            original={'ip_roles':{'ST':'CFwd'},'oop_roles':{'ST':'CFwd'},
                      'ip_formation':'4231','oop_formation':'433'}
            source.write_text(json.dumps(original),encoding='utf-8')
            before=source.read_bytes()
            normalized=f.read_json(str(source))
            self.assertEqual(normalized['ip_roles']['ST'],'CHF')
            self.assertEqual(normalized['oop_roles']['ST'],'CFwd')
            self.assertEqual(source.read_bytes(),before)
            self.assertEqual(f.canonicalize_tactic(normalized),normalized)
            a=f.diagnose(original); b=f.diagnose(normalized)
            self.assertEqual(a['metrics'],b['metrics'])

    def test_storage_compatibility(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)
            original_connect = f.connect
            with contextlib.ExitStack() as connections, patch.object(f,'DB_PATH',root/'test.db'),patch.object(f,'DATA_DIR',root), patch.object(f, 'connect', side_effect=lambda: connections.enter_context(contextlib.closing(original_connect()))):
                f.init_db()
                old={'name':'legacy','ip_formation':'4231','oop_formation':'433','ip_roles':{'ST':'CF','AMR':'WF','GK':'BPGK','AML':'CFwd'},'oop_roles':{'ST':'TCF'}}
                with f.connect() as con:
                    import json
                    raw=json.dumps(old)
                    con.execute('INSERT INTO tactics(name,version,created_at,ip_formation,oop_formation,tactic_json) VALUES (?,?,?,?,?,?)',('legacy','v1','now','4231','433',raw))
                saved=f.get_tactic(1)
                self.assertEqual(saved['ip_roles']['AML'],'CHF')
                before=copy.deepcopy(saved)
                f.diagnose(saved)
                self.assertEqual(saved,before)
                f.tactic_clone(argparse.Namespace(from_id=1,patch=None,version='v2',name=None,note=None))
                clone=f.get_tactic(2)
                self.assertEqual(clone['ip_roles'],{'ST':'CFD','AMR':'WFD','GK':'BGK','AML':'CHF'})
                self.assertEqual(clone['oop_roles'],old['oop_roles'])
                with f.connect() as con:
                    self.assertEqual(con.execute('SELECT tactic_json FROM tactics WHERE id=1').fetchone()[0],raw)
                new=copy.deepcopy(old);new['ip_roles']['ST']='CHF'
                src=root/'new.json';src.write_text(json.dumps(new),encoding='utf-8')
                f.tactic_add(argparse.Namespace(file=str(src),name=None,version=None))
                self.assertEqual(f.get_tactic(3)['ip_roles']['ST'],'CHF')
                self.assertEqual(f.get_tactic(3)['ip_roles']['AMR'],'WFD')
                self.assertEqual(f.get_tactic(3)['ip_roles']['AML'],'CHF')
                with f.connect() as con:
                    stored=json.loads(con.execute('SELECT tactic_json FROM tactics WHERE id=3').fetchone()[0])
                    self.assertEqual(stored['ip_roles']['AML'],'CHF')

if __name__=='__main__':unittest.main()
