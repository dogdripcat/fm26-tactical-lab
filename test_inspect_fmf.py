import argparse
import contextlib
import gzip
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import zlib

import fm26lab


class InspectFmfTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "전술.fmf"

    def inspect(self, data):
        self.source.write_bytes(data)
        before = self.source.stat().st_mtime_ns
        result = fm26lab.inspect_fmf_file(str(self.source))
        self.assertEqual(self.source.read_bytes(), data)
        self.assertEqual(self.source.stat().st_mtime_ns, before)
        return result

    def command(self, out):
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            fm26lab.inspect_fmf_cmd(argparse.Namespace(file=str(self.source), out=out))
        return json.loads(stdout.getvalue())

    def test_binary_metadata_strings(self):
        data = b"\x00\xffHello\x00World!\x00" + bytes(range(256))
        report = self.inspect(data)
        self.assertEqual(report["size_bytes"], len(data))
        self.assertEqual(report["magic_bytes"]["hex"], data[:16].hex(" "))
        self.assertEqual(report["first_256_bytes_hex"], data[:256].hex(" "))
        self.assertEqual(report["printable_strings"][0], {"offset": 2, "text": "Hello"})
        self.assertFalse(report["text"]["utf8_valid"])

    def test_empty_and_short(self):
        for data in (b"", b"x", b"\x78"):
            with self.subTest(data=data):
                report = self.inspect(data)
                self.assertEqual(report["size_bytes"], len(data))
                self.assertFalse(report["compression"]["zlib"]["header_match"])
                self.assertFalse(report["text"]["json_valid"])

    def test_text(self):
        cases = [(b'\xef\xbb\xbf{"name":"test"}', True, False),
                 ('<tactic>한글</tactic>'.encode(), False, True),
                 ('한글 text'.encode(), False, False),
                 (b'{bad json}', False, False), (b'NaN', False, False),
                 (b'<unclosed>', False, False)]
        for data, is_json, is_xml in cases:
            with self.subTest(data=data):
                report = self.inspect(data)["text"]
                self.assertTrue(report["utf8_text"])
                self.assertEqual(report["json_valid"], is_json)
                self.assertEqual(report["xml_valid"], is_xml)
        self.assertFalse(self.inspect(b"\x00abc")["text"]["utf8_text"])

    def test_xml_entities_skipped(self):
        report = self.inspect(b'<!DOCTYPE x [<!ENTITY a "test">]><x>&a;</x>')
        self.assertEqual(report["text"]["xml_status"], "skipped_dtd_or_entity")

    def test_compressed_streams(self):
        for name, encode in (("gzip", gzip.compress), ("zlib", zlib.compress)):
            data = encode(b"tactic sample")
            with self.subTest(name=name):
                report = self.inspect(data)["compression"][name]
                self.assertEqual(report["status"], "valid_first_stream")
                self.assertEqual(report["decoded_bytes_observed"], 13)
                self.assertEqual(self.inspect(data[:-2])["compression"][name]["status"], "incomplete_stream")
                self.assertEqual(self.inspect(data + b"tail")["compression"][name]["trailing_bytes"], 4)
                damaged = data[:-1] + bytes([data[-1] ^ 255])
                self.assertEqual(self.inspect(damaged)["compression"][name]["status"], "invalid_or_dictionary_required")

    def test_decompression_limit(self):
        data = zlib.compress(b"x" * (8 * 1024 * 1024 + 1))
        self.assertEqual(self.inspect(data)["compression"]["zlib"]["status"], "output_limit_exceeded")

    def test_zip(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("../tactic.xml", "<tactic/>")
        result = self.inspect(buffer.getvalue())["compression"]["zip"]
        self.assertTrue(result["directory_readable"])
        self.assertEqual(result["members"][0]["name"], "../tactic.xml")
        self.assertEqual(list(self.root.iterdir()), [self.source])
        self.assertFalse(self.inspect(b"PK\x03\x04broken")["compression"]["zip"]["directory_readable"])

    def test_complete_json_output(self):
        self.source.write_bytes(b"sample")
        out = self.root / "report.json"
        report = self.command(str(out))
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")), report)
        with self.assertRaises(SystemExit):
            self.command(str(out))

    def test_protect_source_and_hardlink(self):
        self.source.write_bytes(b"original")
        alias = self.root / "alias.json"
        os.link(self.source, alias)
        for out in (self.source, alias, self.root / "other.fmf"):
            with self.subTest(out=out), self.assertRaises(SystemExit):
                self.command(str(out))
        self.assertEqual(self.source.read_bytes(), b"original")

    def test_missing_and_directory(self):
        for path in (self.source, self.root):
            with self.subTest(path=path), self.assertRaises(SystemExit):
                fm26lab.inspect_fmf_cmd(argparse.Namespace(file=str(path), out=None))

    def test_cli_no_database(self):
        self.source.write_bytes(b"sample")
        with patch.object(sys, "argv", ["fm26lab.py", "inspect-fmf", "--file", str(self.source)]), \
                patch.object(fm26lab, "init_db", side_effect=AssertionError("DB accessed")), \
                contextlib.redirect_stdout(io.StringIO()):
            fm26lab.main()
        result = subprocess.run([sys.executable, str(Path(fm26lab.__file__)),
                                 "inspect-fmf", "--file", str(self.source),
                                 "--out", str(self.root / "cli.json")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["size_bytes"], 6)


if __name__ == "__main__":
    unittest.main()
