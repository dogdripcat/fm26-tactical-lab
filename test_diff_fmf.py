import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import fmf_diff as f
import fm26lab


def frame(data):
    # Standard single-segment frame with one raw block, no FM-specific fields.
    return f.MAGIC+bytes([32,len(data)])+((len(data)<<3)|1).to_bytes(3,'little')+data

class DiffTests(unittest.TestCase):
    def test_ranges_context_and_counts(self):
        a=b'A'*100; b=a[:40]+b'BC'+a[42:]+b'end'
        r=f.byte_diff(a,b)
        self.assertEqual([(x['start'],x['end_exclusive']) for x in r['ranges']],[(40,42),(100,103)])
        self.assertEqual(r['identical_bytes'],98)
        self.assertEqual(r['changed_bytes'],5)
        self.assertEqual(r['ranges'][0]['a_context']['start'],8)
        self.assertEqual(r['ranges'][0]['a_context']['end_exclusive'],74)
        self.assertEqual(f.byte_diff(b'',b'')['identical_percent'],100)
        self.assertEqual(f.byte_diff(a,a)['ranges'],[])

    def test_embedded_frames(self):
        data=b'prefix'+frame(b'hello')+b'tail'+frame(b'world')
        reports,payloads=f.frames(data)
        self.assertEqual(payloads,{0:b'hello',1:b'world'})
        self.assertEqual(reports[0]['offset'],6)
        self.assertEqual(f.frames(f.MAGIC+b'\x20')[0][0]['status'],'error')

    def test_hashes_strings_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'base.fmf';b=Path(tmp)/'changed.fmf';out=Path(tmp)/'report.json'
            aa=b'header'+frame(b'Centre Forward');bb=b'header'+frame(b'Channel Forward')
            a.write_bytes(aa);b.write_bytes(bb)
            args=argparse.Namespace(a=str(a),b=str(b),out=str(out),label='ST_CFD_to_CHF')
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                f.diff_fmf_cmd(args)
            report=json.loads(out.read_text())
            self.assertEqual(report,json.loads(stdout.getvalue()))
            self.assertTrue(all(s['unchanged'] for s in report['sources']))
            decoded=report['observed']['zstandard']['decoded_comparisons'][0]
            self.assertEqual(decoded['printable_strings']['only_a'],['Centre Forward'])
            self.assertEqual(a.read_bytes(),aa);self.assertEqual(b.read_bytes(),bb)
            for dest in (a,b,out):
                args.out=str(dest)
                with self.assertRaises(SystemExit):f.diff_fmf_cmd(args)
            alias=Path(tmp)/'alias.json';os.link(a,alias);args.out=str(alias)
            with self.assertRaises(SystemExit):f.diff_fmf_cmd(args)
            with patch.object(fm26lab,'init_db',side_effect=AssertionError('DB touched')),patch('sys.argv',['fm26lab.py','diff-fmf','--a',str(a),'--b',str(b)]),contextlib.redirect_stdout(io.StringIO()):
                fm26lab.main()

    def test_hash_change_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a';p.write_bytes(b'old')
            def change(data):p.write_bytes(b'changed');return [],{}
            with patch.object(f,'frames',side_effect=change),self.assertRaises(ValueError):f.compare_files(p,p)

    def test_missing_decoder_is_reported(self):
        with patch.object(f,'decompress',side_effect=RuntimeError('missing')):
            r,p=f.frames(frame(b'abc'))
        self.assertEqual(r[0]['status'],'error');self.assertEqual(p,{})

if __name__=='__main__':unittest.main()
