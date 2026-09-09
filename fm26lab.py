#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FM26 Tactical Lab v0.2.1
Backend-first Football Manager 2026 tactical analysis prototype.

- No GUI
- SQLite local database
- Tactic versions
- Match logging
- Deterministic tactical diagnostics
- OpenAI Responses API feedback (optional)
"""

from __future__ import annotations

import argparse
import tactic_analysis
import role_evidence_importer
import role_master_baseline
import compatibility_candidates
import role_evidence_planning
import role_behaviours
import role_constraints
import evidence_request_manifest
import current_tactic_evidence_sufficiency
import role_evidence_snapshot
import role_evidence_snapshot_audit
import existing_evidence_package_candidates
from fmf_diff import diff_fmf_cmd
import io
import re
import zipfile
import zlib
import xml.etree.ElementTree as ET
import datetime as dt
import json
import os
import sqlite3
import sys
import tempfile
import shutil
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "fm26lab.db"

# Role verification is user-sourced and phase-specific; no FMF IDs are mapped.
ROLE_DICTIONARY = json.loads((APP_DIR / "roles.json").read_text(encoding="utf-8"))
VERIFIED_ROLES = {(r["phase"], r["ingame_abbr"]): r for r in ROLE_DICTIONARY
                  if r["name_verified"]}
# Compatibility translations only, never canonical in-game abbreviations.
ROLE_ALIASES = {("IP", "CF"): "CFD", ("IP", "WF"): "WFD", ("IP", "BPGK"): "BGK", ("IP", "CFwd"): "CHF"}
# CFwd -> CHF is explicitly confirmed by the user; CFwd stays a legacy token.
IP_ROLES = {abbr for phase, abbr in VERIFIED_ROLES if phase == "IP"}
OOP_ROLES = {abbr for phase, abbr in VERIFIED_ROLES if phase == "OOP"}


def canonical_role(phase: str, token: Any) -> Optional[str]:
    if not isinstance(token, str):
        return None
    candidate = ROLE_ALIASES.get((phase, token), token)
    return candidate if (phase, candidate) in VERIFIED_ROLES else None


def canonicalize_tactic(t: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize in-memory reads/writes; preserve source files and unknown tokens."""
    out = dict(t)
    for phase, key in (("IP", "ip_roles"), ("OOP", "oop_roles")):
        if isinstance(t.get(key), dict):
            out[key] = {pos: canonical_role(phase, token) or token
                        for pos, token in t[key].items()}
    return out


def validate_role_evidence_command(args: argparse.Namespace) -> None:
    catalog = role_evidence_importer.role_constraints.load_role_catalog()
    kb = role_evidence_importer.role_behaviours.load_knowledge_base()
    reports = []
    for filename in args.file:
        result = role_evidence_importer.validate_role_evidence(json.loads(Path(filename).read_text(encoding="utf-8-sig")), catalog, kb)
        reports.append(role_evidence_importer.public_report(result))
        if not result["valid"]:
            print(json.dumps({"valid": False, "packages": reports}, ensure_ascii=False, indent=2)); raise SystemExit(1)
        catalog, kb = result["_catalog"], result["_behaviour_kb"]
    print(json.dumps({"valid": True, "packages": reports}, ensure_ascii=False, indent=2))


def import_role_evidence_command(args: argparse.Namespace) -> None:
    if not args.apply:
        raise SystemExit("import-role-evidence requires --apply; use validate-role-evidence for dry-run")
    packages = [json.loads(Path(filename).read_text(encoding="utf-8-sig")) for filename in args.file]
    result = role_evidence_importer.apply_role_evidence_packages(
        packages, role_evidence_importer.role_constraints.DEFAULT_PATH,
        role_evidence_importer.role_behaviours.DEFAULT_PATH,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


def validate_role_master_baseline_command(_: argparse.Namespace) -> None:
    catalog = role_master_baseline.role_constraints.load_role_catalog()
    kb = role_master_baseline.role_behaviours.load_knowledge_base()
    manifest = json.loads(role_master_baseline.MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    result = role_master_baseline.validate_master_baseline(catalog, kb, manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]: raise SystemExit(1)


def compatibility_readiness_command(_: argparse.Namespace) -> None:
    """Read-only development status; this does not evaluate compatibility."""
    print(json.dumps(compatibility_candidates.compatibility_candidate_readiness(), ensure_ascii=False, indent=2))


def role_evidence_coverage_plan_command(args: argparse.Namespace) -> None:
    """Read-only coverage planning; it does not write or apply knowledge."""
    source = Path(args.file) if args.file else APP_DIR / "sample_leicester_4231.json"
    tactic = json.loads(source.read_text(encoding="utf-8-sig"))
    report = role_evidence_planning.build_role_evidence_collection_plan(
        tactic, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), ROLE_ALIASES,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


def evidence_request_manifest_command(args: argparse.Namespace) -> None:
    """Read-only manifest that prevents requesting already-recorded evidence again."""
    source = Path(args.file) if args.file else APP_DIR / "sample_leicester_4231.json"
    tactic = json.loads(source.read_text(encoding="utf-8-sig"))
    report = evidence_request_manifest.build_evidence_request_manifest(
        tactic, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), ROLE_ALIASES,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


def current_tactic_evidence_sufficiency_command(args: argparse.Namespace) -> None:
    """Read-only evidence capability report for the tactic's configured IP roles."""
    source = Path(args.file) if args.file else APP_DIR / "sample_leicester_4231.json"
    tactic = json.loads(source.read_text(encoding="utf-8-sig"))
    report = current_tactic_evidence_sufficiency.build_current_tactic_evidence_sufficiency(
        tactic, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(), ROLE_ALIASES,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


def export_role_evidence_snapshot_command(args: argparse.Namespace) -> None:
    """Export a derived snapshot; no catalog, KB, or analysis data is modified."""
    target = Path(args.out) if args.out else APP_DIR / "data" / "role_evidence_snapshot.json"
    report = role_evidence_snapshot.write_role_evidence_snapshot(
        target, role_constraints.load_role_catalog(), role_behaviours.load_knowledge_base(),
    )
    print(json.dumps({"output": str(target), **report}, ensure_ascii=False, indent=2))


def audit_role_evidence_snapshot_command(args: argparse.Namespace) -> None:
    """Read-only comparison of a derived snapshot with catalog and KB source data."""
    source = Path(args.file) if args.file else APP_DIR / "data" / "role_evidence_snapshot.json"
    print(json.dumps(role_evidence_snapshot_audit.load_and_audit(source), ensure_ascii=False, indent=2))


def existing_evidence_package_candidates_command(args: argparse.Namespace) -> None:
    """Read-only candidate report; it never writes evidence packages or source data."""
    source = Path(args.file) if args.file else APP_DIR / "data" / "role_evidence_snapshot.json"
    print(json.dumps(existing_evidence_package_candidates.load_existing_evidence_package_candidates(source), ensure_ascii=False, indent=2))


FORMATIONS = {"4231", "433", "442", "4141", "541", "352", "343", "442D", "custom"}

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")


def now_iso() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with connect() as con:
        con.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS tactics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version TEXT NOT NULL,
            created_at TEXT NOT NULL,
            ip_formation TEXT NOT NULL,
            oop_formation TEXT NOT NULL,
            play_style TEXT,
            tactic_json TEXT NOT NULL,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            played_at TEXT NOT NULL,
            tactic_id INTEGER NOT NULL,
            opponent TEXT NOT NULL,
            venue TEXT NOT NULL CHECK (venue IN ('home','away','neutral')),
            opp_formation TEXT,
            opp_block TEXT,
            gf INTEGER NOT NULL,
            ga INTEGER NOT NULL,
            xg_for REAL,
            xg_against REAL,
            shots_for INTEGER,
            shots_against INTEGER,
            sot_for INTEGER,
            sot_against INTEGER,
            possession REAL,
            striker_shots INTEGER,
            striker_goals INTEGER,
            striker_rating REAL,
            notes TEXT,
            FOREIGN KEY(tactic_id) REFERENCES tactics(id)
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            tactic_id INTEGER,
            match_id INTEGER,
            source TEXT NOT NULL,
            question TEXT,
            response TEXT NOT NULL,
            context_json TEXT,
            FOREIGN KEY(tactic_id) REFERENCES tactics(id),
            FOREIGN KEY(match_id) REFERENCES matches(id)
        );

        CREATE TABLE IF NOT EXISTS weight_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            version TEXT NOT NULL UNIQUE,
            weights_json TEXT NOT NULL,
            note TEXT
        );

        CREATE TABLE IF NOT EXISTS tactic_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            parent_tactic_id INTEGER NOT NULL,
            child_tactic_id INTEGER NOT NULL,
            diff_json TEXT NOT NULL,
            note TEXT,
            FOREIGN KEY(parent_tactic_id) REFERENCES tactics(id),
            FOREIGN KEY(child_tactic_id) REFERENCES tactics(id)
        );
        """)
        row = con.execute("SELECT COUNT(*) AS n FROM weight_versions").fetchone()
        if row["n"] == 0:
            con.execute(
                "INSERT INTO weight_versions(created_at,version,weights_json,note) VALUES (?,?,?,?)",
                (now_iso(), "0.1", json.dumps(default_weights(), ensure_ascii=False), "Initial heuristic weights")
            )
    print(f"[OK] DB ready: {DB_PATH}")


def default_weights() -> Dict[str, float]:
    return {
        "attack_width": 1.0,
        "central_creation": 1.0,
        "striker_service": 1.0,
        "box_penetration": 1.0,
        "rest_defence": 1.0,
        "press_structure": 1.0,
        "midfield_matchup": 1.0,
        "low_block_attack": 1.0,
        "transition_threat": 1.0,
    }


def read_json(path: str) -> Dict[str, Any]:
    return canonicalize_tactic(json.loads(Path(path).read_text(encoding="utf-8")))


def validate_tactic(t: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    for key in ("ip_formation", "oop_formation"):
        f = str(t.get(key, "custom"))
        if f not in FORMATIONS:
            warnings.append(f"{key}='{f}' is not in built-in formation list; treated as custom.")

    for phase, phase_key in (("IP", "ip_roles"), ("OOP", "oop_roles")):
        roles = t.get(phase_key, {})
        if not isinstance(roles, dict):
            warnings.append(f"{phase_key} must be an object/dict.")
            continue
        for pos, role in roles.items():
            canonical = canonical_role(phase, role)
            if role and canonical is None:
                warnings.append(f"{phase_key}.{pos}={role!r}: unverified; stored unchanged, excluded from role-specific calculations.")
            elif canonical and canonical != role:
                warnings.append(f"{phase_key}.{pos}={role!r}: legacy alias -> {canonical}; not a canonical in-game abbreviation.")
    return warnings


def tactic_add(args: argparse.Namespace) -> None:
    t = read_json(args.file)
    warnings = validate_tactic(t)
    t = canonicalize_tactic(t)
    name = args.name or t.get("name") or "Unnamed tactic"
    version = args.version or t.get("version") or "v1"
    ipf = str(t.get("ip_formation", "custom"))
    oopf = str(t.get("oop_formation", "custom"))
    style = t.get("play_style")
    notes = t.get("notes", "")

    with connect() as con:
        cur = con.execute("""
            INSERT INTO tactics(name,version,created_at,ip_formation,oop_formation,play_style,tactic_json,notes)
            VALUES (?,?,?,?,?,?,?,?)
        """, (name, version, now_iso(), ipf, oopf, style, json.dumps(t, ensure_ascii=False), notes))
        tid = cur.lastrowid

    print(f"[OK] tactic saved: id={tid}, {name} {version}")
    for w in warnings:
        print(f"[WARN] {w}")


def tactic_list(_: argparse.Namespace) -> None:
    with connect() as con:
        rows = con.execute("""
            SELECT id,name,version,ip_formation,oop_formation,play_style,created_at
            FROM tactics ORDER BY id DESC
        """).fetchall()
    if not rows:
        print("No tactics saved.")
        return
    print("ID | NAME | VER | IP | OOP | PLAY STYLE | CREATED")
    for r in rows:
        print(f"{r['id']} | {r['name']} | {r['version']} | {r['ip_formation']} | "
              f"{r['oop_formation']} | {r['play_style'] or '-'} | {r['created_at']}")


def tactic_show(args: argparse.Namespace) -> None:
    t = get_tactic(args.id)
    print(json.dumps(t, ensure_ascii=False, indent=2))


def get_tactic(tactic_id: int) -> Dict[str, Any]:
    with connect() as con:
        r = con.execute("SELECT * FROM tactics WHERE id=?", (tactic_id,)).fetchone()
    if not r:
        raise SystemExit(f"Tactic id={tactic_id} not found.")
    data = canonicalize_tactic(json.loads(r["tactic_json"]))
    data["_db"] = {k: r[k] for k in r.keys() if k != "tactic_json"}
    return data



def _strip_db_meta(t: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(t)
    out.pop("_db", None)
    return out


def json_diff(a: Any, b: Any, path: str = "") -> List[Dict[str, Any]]:
    """Return human-readable recursive differences between two JSON-like values."""
    changes: List[Dict[str, Any]] = []
    if isinstance(a, dict) and isinstance(b, dict):
        keys = sorted(set(a) | set(b))
        for key in keys:
            p = f"{path}.{key}" if path else key
            if key not in a:
                changes.append({"path": p, "type": "added", "before": None, "after": b[key]})
            elif key not in b:
                changes.append({"path": p, "type": "removed", "before": a[key], "after": None})
            else:
                changes.extend(json_diff(a[key], b[key], p))
        return changes
    if isinstance(a, list) and isinstance(b, list):
        if a != b:
            changes.append({"path": path, "type": "changed", "before": a, "after": b})
        return changes
    if a != b:
        changes.append({"path": path, "type": "changed", "before": a, "after": b})
    return changes


def tactic_diff_cmd(args: argparse.Namespace) -> None:
    a = _strip_db_meta(get_tactic(args.a))
    b = _strip_db_meta(get_tactic(args.b))
    changes = json_diff(a, b)
    out = {
        "from_tactic_id": args.a,
        "to_tactic_id": args.b,
        "change_count": len(changes),
        "changes": changes,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


def tactic_clone(args: argparse.Namespace) -> None:
    parent = get_tactic(args.from_id)
    data = _strip_db_meta(parent)

    if args.patch:
        patch = read_json(args.patch)
        # Shallow/deep merge for dictionaries.
        def merge(base: Dict[str, Any], upd: Dict[str, Any]) -> Dict[str, Any]:
            out = dict(base)
            for k, v in upd.items():
                if isinstance(v, dict) and isinstance(out.get(k), dict):
                    out[k] = merge(out[k], v)
                else:
                    out[k] = v
            return out
        data = merge(data, patch)

    data["version"] = args.version
    if args.name:
        data["name"] = args.name

    warnings = validate_tactic(data)
    data = canonicalize_tactic(data)
    with connect() as con:
        cur = con.execute("""
            INSERT INTO tactics(name,version,created_at,ip_formation,oop_formation,play_style,tactic_json,notes)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            data.get("name", parent["_db"]["name"]),
            args.version,
            now_iso(),
            str(data.get("ip_formation", "custom")),
            str(data.get("oop_formation", "custom")),
            data.get("play_style"),
            json.dumps(data, ensure_ascii=False),
            args.note or data.get("notes", "")
        ))
        child_id = cur.lastrowid
        changes = json_diff(_strip_db_meta(parent), data)
        con.execute("""
            INSERT INTO tactic_changes(created_at,parent_tactic_id,child_tactic_id,diff_json,note)
            VALUES (?,?,?,?,?)
        """, (now_iso(), args.from_id, child_id, json.dumps(changes, ensure_ascii=False), args.note or ""))

    print(f"[OK] cloned tactic: {args.from_id} -> {child_id} ({args.version})")
    if changes:
        print(f"[OK] recorded {len(changes)} change(s):")
        for c in changes:
            print(f"  - {c['path']}: {c['before']} -> {c['after']}")
    else:
        print("[INFO] No tactical changes detected; version-only clone.")
    for w in warnings:
        print(f"[WARN] {w}")


def change_history(args: argparse.Namespace) -> None:
    with connect() as con:
        rows = con.execute("""
            SELECT tc.*, p.name AS parent_name, p.version AS parent_ver,
                   c.name AS child_name, c.version AS child_ver
            FROM tactic_changes tc
            JOIN tactics p ON p.id=tc.parent_tactic_id
            JOIN tactics c ON c.id=tc.child_tactic_id
            ORDER BY tc.id DESC LIMIT ?
        """, (args.limit,)).fetchall()
    if not rows:
        print("No tactic change history.")
        return
    for r in rows:
        changes = json.loads(r["diff_json"])
        print(f"#{r['id']} {r['parent_name']} {r['parent_ver']} -> {r['child_ver']} "
              f"({len(changes)} changes) {r['created_at']}")
        for c in changes:
            print(f"   {c['path']}: {c['before']} -> {c['after']}")


def self_test(_: argparse.Namespace) -> None:
    """Run a non-network smoke test in a temporary database."""
    global DB_PATH
    original_db = DB_PATH
    temp_dir = Path(tempfile.mkdtemp(prefix="fm26lab_test_"))
    DB_PATH = temp_dir / "test.db"
    try:
        init_db()

        sample_path = APP_DIR / "sample_leicester_4231.json"
        sample = read_json(str(sample_path))
        assert not [w for w in validate_tactic(sample) if "must be" in w]

        with connect() as con:
            cur = con.execute("""
                INSERT INTO tactics(name,version,created_at,ip_formation,oop_formation,play_style,tactic_json,notes)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                sample.get("name","Sample"), "self-test", now_iso(),
                sample.get("ip_formation","4231"), sample.get("oop_formation","4231"),
                sample.get("play_style"), json.dumps(sample, ensure_ascii=False), "self-test"
            ))
            tid = cur.lastrowid
            con.execute("""
                INSERT INTO matches(
                    played_at,tactic_id,opponent,venue,opp_formation,opp_block,gf,ga,
                    xg_for,xg_against,shots_for,shots_against,sot_for,sot_against,
                    possession,striker_shots,striker_goals,striker_rating,notes
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                now_iso(), tid, "Test FC", "away", "433", "mid", 0, 4,
                0.73, 2.23, 9, 19, 0, 9, 40.0, 1, 0, 6.2, "self-test"
            ))

        t = get_tactic(tid)
        result = diagnose(t, "433", "away", "mid", "stronger")
        assert isinstance(result.get("overall"), int)
        assert 0 <= result["overall"] <= 100
        assert "스트라이커 공급" in result["metrics"]

        agg = aggregate_matches(latest_matches(tid, 5))
        assert agg["sample"] == 1
        assert agg["W-D-L"] == "0-0-1"

        print("[PASS] database initialization")
        print("[PASS] tactic JSON validation/loading")
        print("[PASS] match logging")
        print("[PASS] deterministic tactical diagnosis")
        print("[PASS] recent-match aggregation")
        print("[PASS] Python core runtime")
        print("[OK] FM26 Tactical Lab v0.2.1 core self-test passed.")
    finally:
        DB_PATH = original_db
        shutil.rmtree(temp_dir, ignore_errors=True)


def match_add(args: argparse.Namespace) -> None:
    _ = get_tactic(args.tactic)
    with connect() as con:
        cur = con.execute("""
            INSERT INTO matches(
                played_at,tactic_id,opponent,venue,opp_formation,opp_block,gf,ga,
                xg_for,xg_against,shots_for,shots_against,sot_for,sot_against,
                possession,striker_shots,striker_goals,striker_rating,notes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            args.date or now_iso(),
            args.tactic, args.opponent, args.venue, args.opp_formation, args.opp_block,
            args.gf, args.ga, args.xg_for, args.xg_against,
            args.shots_for, args.shots_against, args.sot_for, args.sot_against,
            args.possession, args.striker_shots, args.striker_goals, args.striker_rating,
            args.notes or ""
        ))
        mid = cur.lastrowid
    print(f"[OK] match saved: id={mid} {args.opponent} {args.gf}-{args.ga}")


def match_list(args: argparse.Namespace) -> None:
    q = """
        SELECT m.*, t.name AS tactic_name, t.version AS tactic_version
        FROM matches m JOIN tactics t ON t.id=m.tactic_id
    """
    params: List[Any] = []
    if args.tactic:
        q += " WHERE m.tactic_id=?"
        params.append(args.tactic)
    q += " ORDER BY m.id DESC LIMIT ?"
    params.append(args.limit)
    with connect() as con:
        rows = con.execute(q, params).fetchall()
    if not rows:
        print("No matches saved.")
        return
    for r in rows:
        xg = "-" if r["xg_for"] is None else f"{r['xg_for']:.2f}-{(r['xg_against'] or 0):.2f}"
        print(
            f"#{r['id']} {r['played_at']} | {r['opponent']} | {r['venue']} | "
            f"{r['gf']}-{r['ga']} | xG {xg} | tactic {r['tactic_name']} {r['tactic_version']}"
        )


def latest_matches(tactic_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    with connect() as con:
        rows = con.execute("""
            SELECT * FROM matches WHERE tactic_id=?
            ORDER BY id DESC LIMIT ?
        """, (tactic_id, limit)).fetchall()
    return [dict(r) for r in rows]


_LEGACY_ROLE_PROFILES: Dict[str, Dict[str, float]] = {
    "CF":   {"goal": 9, "link": 6, "run": 7, "width": 0, "create": 4},
    "CFwd": {"goal": 9, "link": 3, "run": 10, "width": 2, "create": 2},
    "P":    {"goal":10, "link": 1, "run": 8, "width": 0, "create": 1},
    "DLF":  {"goal": 5, "link":10, "run": 3, "width": 0, "create": 7},
    "F9":   {"goal": 4, "link":10, "run": 4, "width": 1, "create": 8},
    "TF":   {"goal": 7, "link": 8, "run": 3, "width": 0, "create": 5},

    "AM":   {"create":6, "run":6, "width":1},
    "AP":   {"create":10,"run":3, "width":1},
    "SS":   {"create":3, "run":10,"width":1},
    "FR":   {"create":8, "run":7, "width":2},

    "W":    {"width":10,"create":7,"goal":3,"run":5},
    "IW":   {"width":5, "create":7,"goal":6,"run":6},
    "IF":   {"width":3, "create":4,"goal":9,"run":9},
    "PW":   {"width":7, "create":10,"goal":3,"run":4},
    "WF":   {"width":9, "create":4,"goal":9,"run":9},

    "DLP":  {"hold":7,"create":9,"run":2},
    "DM":   {"hold":10,"create":4,"run":1},
    "HB":   {"hold":10,"create":4,"run":1},
    "BBM":  {"hold":5,"create":4,"run":9},
    "BBP":  {"hold":5,"create":8,"run":9},
    "CM":   {"hold":6,"create":5,"run":5},
    "MP":   {"hold":5,"create":9,"run":4},
    "WCM":  {"hold":5,"create":5,"run":7,"width":6},

    "FB":   {"width":5,"hold":8,"run":4},
    "WB":   {"width":9,"hold":5,"run":8},
    "IWB":  {"width":2,"hold":7,"run":6},
    "IFB":  {"width":1,"hold":10,"run":2},
    "PWB":  {"width":5,"hold":5,"run":7,"create":8},
    "AWB":  {"width":10,"hold":3,"run":10},
}


# Keep old numbers as heuristic weights, not verified game mechanics.
# Alias confirmation alone does not activate previously quarantined CFwd weights.
ROLE_PROFILES = {canonical: weights for token, weights in _LEGACY_ROLE_PROFILES.items()
                 if token != "CFwd" and (canonical := canonical_role("IP", token)) is not None}


def prof(role_name: Optional[str]) -> Dict[str, float]:
    return ROLE_PROFILES.get(canonical_role("IP", role_name), {})


def getv(d: Dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(d.get(key, default))
    except (TypeError, ValueError):
        return default


def clamp(n: float) -> int:
    return max(0, min(100, round(n)))


def diagnose(t: Dict[str, Any], opponent_formation: str = "433",
             venue: str = "home", opp_block: str = "mid",
             opp_strength: str = "equal") -> Dict[str, Any]:

    ip = {pos: canonical_role("IP", token)
          for pos, token in t.get("ip_roles", {}).items()}
    ti = t.get("team_instructions", {})

    st = prof(ip.get("ST"))
    am = prof(ip.get("AMC"))
    lw = prof(ip.get("AML"))
    rw = prof(ip.get("AMR"))
    dm1 = prof(ip.get("DML") or ip.get("DM1") or ip.get("MCL"))
    dm2 = prof(ip.get("DMR") or ip.get("DM2") or ip.get("MCR"))
    lb = prof(ip.get("LB") or ip.get("DL"))
    rb = prof(ip.get("RB") or ip.get("DR"))

    width = (getv(lw,"width",5)+getv(rw,"width",5)+getv(lb,"width",5)+getv(rb,"width",5))/4*10
    creation = (getv(am,"create",5)+getv(lw,"create",5)+getv(rw,"create",5)+
                getv(dm1,"create",5)+getv(dm2,"create",5))/5*10
    penetration = (getv(st,"run",5)+getv(am,"run",5)+getv(lw,"run",5)+
                   getv(rw,"run",5)+getv(dm1,"run",5)+getv(dm2,"run",5))/6*10
    rest = (getv(dm1,"hold",6)+getv(dm2,"hold",6)+getv(lb,"hold",6)+getv(rb,"hold",6))/4*10

    service = (
        getv(st,"link",5)*0.18 +
        getv(am,"create",5)*0.30 +
        getv(lw,"create",5)*0.15 +
        getv(rw,"create",5)*0.15 +
        getv(dm1,"create",5)*0.11 +
        getv(dm2,"create",5)*0.11
    ) * 10

    press = 58.0
    risk = 32.0

    press_line = str(ti.get("press_line", "mid"))
    def_line = str(ti.get("defensive_line", "normal"))
    pressing = str(ti.get("pressing", "normal"))
    transition = str(ti.get("defensive_transition", "balanced"))
    tempo = str(ti.get("tempo", "normal"))
    play_style = str(t.get("play_style") or ti.get("play_style") or "balanced")

    if press_line == "mid": press += 5
    if press_line == "high": press += 10
    if pressing in ("more", "더 자주"): press += 8
    if transition in ("counterpress", "역압박"): press += 7

    if def_line in ("high", "높게"): risk += 15
    if press_line == "mid" and def_line in ("high", "높게"): risk += 5
    if pressing in ("more", "더 자주"): risk += 6
    if transition in ("counterpress", "역압박"): risk += 7

    if ip.get("LB") in ("WB",): risk += 5
    if ip.get("RB") in ("WB",): risk += 5
    risk -= ((getv(dm1,"hold",6)+getv(dm2,"hold",6))-12)*1.8

    midfield = 58.0
    warnings: List[Dict[str,str]] = [
        {"title": "역할 검증", "detail": message} for message in validate_tactic(t)
    ]
    suggestions: List[str] = []

    if opponent_formation == "433":
        midfield -= 7
        if ip.get("AMC") in ("AM",): midfield += 3
        if ip.get("DML") == "DLP" or ip.get("DMR") == "DLP": midfield += 2
        if ip.get("RB") == "IWB" or ip.get("LB") == "IWB": midfield += 4
        warnings.append({
            "title":"4-3-3 중원 상성",
            "detail":"상대 3미드필더가 2DM과 AMC 사이 연결을 끊으면 스트라이커가 고립될 수 있습니다."
        })
    elif opponent_formation == "352":
        midfield -= 6
    elif opponent_formation == "442":
        midfield += 7

    if opp_strength == "stronger":
        midfield -= 8
        press -= 4
        risk += 8
    elif opp_strength == "weaker":
        midfield += 8
        risk -= 3

    low_block = width*0.28 + creation*0.34 + penetration*0.18 + service*0.20
    transition_threat = getv(st,"run",5)*4 + (getv(lw,"run",5)+getv(rw,"run",5))*2.5 + (getv(dm1,"run",5)+getv(dm2,"run",5))*0.5

    if venue == "home" and opp_block == "low":
        low_block -= 6
        transition_threat -= 8
        warnings.append({
            "title":"홈 저블록",
            "detail":"원정에서 생기던 뒷공간이 줄어들어 같은 역할 조합도 전환 위협이 감소할 수 있습니다."
        })
    if venue == "away" and opp_block == "high":
        transition_threat += 10
    if opp_block == "low":
        low_block -= 4
        transition_threat -= 6
    elif opp_block == "high":
        transition_threat += 8

    if tempo in ("high","높게"):
        penetration += 5
        creation -= 2
        risk += 3
    elif tempo in ("low","낮게"):
        creation += 4
        penetration -= 5

    if play_style in ("공격형","attack"):
        penetration += 6
        risk += 6
    elif play_style in ("지배형","control"):
        creation += 5
        midfield += 3

    # Common complementary/overlap rules
    if ip.get("AML") == "IF" and ip.get("LB") in ("WB",):
        width += 5
        warnings.append({
            "title":"왼쪽 상호보완",
            "detail":"IF의 안쪽 침투와 WB의 바깥 폭 확보는 구조적으로 상호보완적입니다."
        })
    if ip.get("AML") == "IF" and ip.get("LB") == "IWB":
        width -= 7
    if ip.get("AMR") == "IF" and ip.get("RB") == "IWB":
        width -= 7
    if ip.get("AMR") == "WFD" and ip.get("RB") == "IWB":
        rest += 3
        warnings.append({
            "title":"오른쪽 비대칭",
            "detail":"WFD가 높은 폭/침투를 제공하고 IWB가 안쪽을 보충하는 조합은 역할 중복이 비교적 적습니다."
        })

    central_goal_roles = sum([
        getv(st,"goal",5), getv(lw,"goal",5), getv(rw,"goal",5), getv(am,"run",5)
    ])
    if central_goal_roles >= 32 and width < 60:
        low_block -= 8
        warnings.append({
            "title":"중앙 혼잡 가능성",
            "detail":"골 위협 역할이 많고 폭 점수가 낮아지면 낮은 블록 상대로 박스 앞 공간이 혼잡해질 수 있습니다."
        })

    rest_score = clamp(rest - risk*0.28)
    press_score = clamp(press - risk*0.18)

    metrics = {
        "중앙 전개": clamp((creation + service + midfield) / 3),
        "스트라이커 공급": clamp(service),
        "박스 침투": clamp(penetration),
        "폭 확보": clamp(width),
        "낮은 블록 공략": clamp(low_block),
        "전환 위협": clamp(transition_threat),
        "레스트 디펜스": rest_score,
        "압박 구조": press_score,
        "중원 상성": clamp(midfield),
    }

    overall = sum(metrics.values()) / len(metrics)
    overall = clamp(overall)

    if risk > 62:
        warnings.append({
            "title":"수비 전환 위험",
            "detail":"높은 수비 라인, 적극적 압박, 역압박이 겹치면 압박이 풀렸을 때 뒷공간 위험이 커질 수 있습니다."
        })
        suggestions.append("강팀 원정에서는 수비 라인을 한 단계 낮추는 단일 변경을 우선 테스트하십시오.")

    if metrics["스트라이커 공급"] < 60:
        warnings.append({
            "title":"스트라이커 공급 부족",
            "detail":"ST 역할 자체보다 AMC/측면/중원의 공급 경로를 먼저 점검할 가치가 있습니다."
        })
        suggestions.append("스트라이커 역할 변경 전에 AMC와 측면 창조 역할 중 하나만 바꾸어 3경기 비교하십시오.")

    if opponent_formation == "433" and metrics["중원 상성"] < 55:
        suggestions.append("4-3-3 상대에서는 AMC 연결과 IWB의 중원 보조를 우선 점검하십시오.")

    if venue == "home" and opp_block == "low" and metrics["낮은 블록 공략"] < 65:
        suggestions.append("홈 저블록에서는 전방 역할을 더 공격적으로 만드는 것보다 폭/창조 경로를 하나씩 조정하십시오.")

    if not suggestions:
        suggestions.append("구조적 대수술보다 3~5경기 표본으로 현재 조합을 검증하십시오.")

    return {
        "overall": overall,
        "metrics": metrics,
        "warnings": warnings,
        "suggestions": suggestions,
        "assumptions": {
            "opponent_formation": opponent_formation,
            "venue": venue,
            "opp_block": opp_block,
            "opp_strength": opp_strength,
        },
        "disclaimer": "This is a transparent heuristic diagnostic, not the hidden FM26 match-engine formula."
    }


def aggregate_matches(matches: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not matches:
        return {"sample": 0}

    def avg(key: str) -> Optional[float]:
        vals = [m[key] for m in matches if m.get(key) is not None]
        return round(sum(vals)/len(vals), 3) if vals else None

    wins = sum(1 for m in matches if m["gf"] > m["ga"])
    draws = sum(1 for m in matches if m["gf"] == m["ga"])
    losses = len(matches) - wins - draws
    return {
        "sample": len(matches),
        "W-D-L": f"{wins}-{draws}-{losses}",
        "goals_for_avg": avg("gf"),
        "goals_against_avg": avg("ga"),
        "xg_for_avg": avg("xg_for"),
        "xg_against_avg": avg("xg_against"),
        "shots_for_avg": avg("shots_for"),
        "shots_against_avg": avg("shots_against"),
        "sot_for_avg": avg("sot_for"),
        "sot_against_avg": avg("sot_against"),
        "possession_avg": avg("possession"),
        "striker_shots_avg": avg("striker_shots"),
        "striker_goals_avg": avg("striker_goals"),
        "striker_rating_avg": avg("striker_rating"),
    }


def analyze(args: argparse.Namespace) -> None:
    t = get_tactic(args.tactic)
    result = diagnose(
        t,
        opponent_formation=args.opp_formation,
        venue=args.venue,
        opp_block=args.opp_block,
        opp_strength=args.opp_strength,
    )
    matches = latest_matches(args.tactic, args.last)
    result["recent_matches"] = aggregate_matches(matches)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def build_context(tactic_id: int, last: int, question: str,
                  opp_formation: Optional[str] = None,
                  venue: Optional[str] = None,
                  opp_block: Optional[str] = None,
                  opp_strength: Optional[str] = None) -> Dict[str, Any]:
    t = get_tactic(tactic_id)
    matches = latest_matches(tactic_id, last)
    diag = diagnose(
        t,
        opponent_formation=opp_formation or "433",
        venue=venue or "home",
        opp_block=opp_block or "mid",
        opp_strength=opp_strength or "equal",
    )
    return {
        "app": "FM26 Tactical Lab v0.2.1",
        "question": question,
        "tactic": t,
        "deterministic_diagnostic": diag,
        "recent_matches": matches,
        "recent_aggregate": aggregate_matches(matches),
        "analysis_rules": [
            "Use FM26 terminology only.",
            "Do not use FM24 duty terminology.",
            "Separate in-possession and out-of-possession logic.",
            "Do not claim the heuristic score is an official match-engine value.",
            "Prefer the user's saved match data over generic web/game assumptions.",
            "Recommend at most two changes, ideally one, and state the test metric.",
            "Distinguish structural problem from one-match variance.",
        ],
    }


def extract_response_text(data: Dict[str, Any]) -> str:
    # Responses API usually returns output[].content[].text for output_text items.
    texts: List[str] = []
    for item in data.get("output", []):
        for c in item.get("content", []) if isinstance(item, dict) else []:
            if isinstance(c, dict):
                if c.get("type") == "output_text" and isinstance(c.get("text"), str):
                    texts.append(c["text"])
                elif isinstance(c.get("text"), str):
                    texts.append(c["text"])
    if texts:
        return "\n".join(texts).strip()
    if isinstance(data.get("output_text"), str):
        return data["output_text"].strip()
    return json.dumps(data, ensure_ascii=False, indent=2)


def call_openai(context: Dict[str, Any], model: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit(
            "OPENAI_API_KEY is not set.\n"
            "Windows CMD example:\n"
            "  setx OPENAI_API_KEY \"YOUR_KEY\"\n"
            "Then open a new terminal and run again."
        )

    system_text = (
        "You are the analysis module of FM26 Tactical Lab. "
        "Answer in Korean. Use only Football Manager 2026 concepts supplied in the context. "
        "Do not invent UI labels or hidden match-engine mechanics. "
        "Treat deterministic scores as heuristic indicators, not official values. "
        "Ground conclusions first in the user's saved match data. "
        "Give: conclusion, evidence, likely causes in priority order, one minimal change, "
        "risk/side effect, and a 3-match test plan."
    )

    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_text}]
            },
            {
                "role": "user",
                "content": [{
                    "type": "input_text",
                    "text": json.dumps(context, ensure_ascii=False)
                }]
            }
        ]
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"OpenAI API HTTP {e.code}\n{body}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Network error: {e}")

    return extract_response_text(data)


def gpt_feedback(args: argparse.Namespace) -> None:
    context = build_context(
        args.tactic, args.last, args.question,
        args.opp_formation, args.venue, args.opp_block, args.opp_strength
    )
    response = call_openai(context, args.model)
    print("\n=== GPT FEEDBACK ===\n")
    print(response)

    with connect() as con:
        con.execute("""
            INSERT INTO feedback(created_at,tactic_id,match_id,source,question,response,context_json)
            VALUES (?,?,?,?,?,?,?)
        """, (
            now_iso(), args.tactic, None, f"openai:{args.model}", args.question,
            response, json.dumps(context, ensure_ascii=False)
        ))
    print("\n[OK] feedback saved to local DB.")


def compare(args: argparse.Namespace) -> None:
    a = get_tactic(args.a)
    b = get_tactic(args.b)
    aa = aggregate_matches(latest_matches(args.a, args.last))
    bb = aggregate_matches(latest_matches(args.b, args.last))
    out = {
        "tactic_A": {"id": args.a, "name": a["_db"]["name"], "version": a["_db"]["version"], "results": aa},
        "tactic_B": {"id": args.b, "name": b["_db"]["name"], "version": b["_db"]["version"], "results": bb},
        "note": "Comparison is descriptive. Small samples can be noisy.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


def interactive() -> None:
    init_db()
    while True:
        print("""
FM26 Tactical Lab v0.2.1
1) 전술 목록
2) 최근 경기 목록
3) 전술 분석
4) GPT 피드백
5) 전술 변경 이력
6) 코어 자가진단
7) 종료
""")
        choice = input("선택> ").strip()
        try:
            if choice == "1":
                tactic_list(argparse.Namespace())
            elif choice == "2":
                tactic_id = input("전술 ID(전체는 엔터)> ").strip()
                match_list(argparse.Namespace(tactic=int(tactic_id) if tactic_id else None, limit=20))
            elif choice == "3":
                tid = int(input("전술 ID> "))
                opp = input("상대 포메이션 [433]> ").strip() or "433"
                venue = input("home/away [home]> ").strip() or "home"
                block = input("상대 블록 low/mid/high [mid]> ").strip() or "mid"
                strength = input("상대 전력 weaker/equal/stronger [equal]> ").strip() or "equal"
                analyze(argparse.Namespace(
                    tactic=tid, opp_formation=opp, venue=venue,
                    opp_block=block, opp_strength=strength, last=5
                ))
            elif choice == "4":
                tid = int(input("전술 ID> "))
                q = input("질문> ").strip()
                gpt_feedback(argparse.Namespace(
                    tactic=tid, last=5, question=q, model=DEFAULT_MODEL,
                    opp_formation=None, venue=None, opp_block=None, opp_strength=None
                ))
            elif choice == "5":
                change_history(argparse.Namespace(limit=20))
            elif choice == "6":
                self_test(argparse.Namespace())
            elif choice == "7":
                return
            else:
                print("잘못된 선택입니다.")
        except Exception as e:
            print(f"[ERROR] {e}")


def inspect_fmf_file(path: str) -> Dict[str, Any]:
    """Observe bytes only; no FM-specific format or role interpretation."""
    source = Path(path).resolve(strict=True)
    with source.open("rb") as stream:
        data = stream.read()
    compression: Dict[str, Any] = {}
    zip_magic = data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"))
    compression["zip"] = {"header_match": zip_magic, "directory_readable": False}
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            compression["zip"].update(directory_readable=True, members=[
                {"name": item.filename, "size_bytes": item.file_size,
                 "compressed_size_bytes": item.compress_size}
                for item in archive.infolist()
            ])
    except (zipfile.BadZipFile, OSError, ValueError) as exc:
        if zip_magic:
            compression["zip"]["error"] = str(exc)

    zlib_header = (len(data) >= 2 and data[0] & 15 == 8
                   and data[0] >> 4 <= 7 and int.from_bytes(data[:2], "big") % 31 == 0)
    for name, matched, window in (("gzip", data.startswith(b"\x1f\x8b"), 31),
                                   ("zlib", zlib_header, 15)):
        result: Dict[str, Any] = {"header_match": matched, "status": "no_header_match"}
        if matched:
            # Bound decompression; never write or recursively unpack payloads.
            limit = 8 * 1024 * 1024
            result["output_limit_bytes"] = limit
            try:
                decoder = zlib.decompressobj(window)
                payload = decoder.decompress(data, limit + 1)
                result["status"] = ("output_limit_exceeded" if len(payload) > limit
                                    else "valid_first_stream" if decoder.eof else "incomplete_stream")
                result["decoded_bytes_observed"] = len(payload)
                if decoder.eof:
                    result["trailing_bytes"] = len(decoder.unused_data)
            except zlib.error as exc:
                result.update(status="invalid_or_dictionary_required", error=str(exc))
        compression[name] = result

    text_info: Dict[str, Any] = {"utf8_valid": False, "utf8_text": False,
                                 "json_valid": False, "xml_valid": False}
    try:
        decoded = data.decode("utf-8-sig")
        text_info["utf8_valid"] = True
        text_info["utf8_text"] = bool(decoded) and all(
            ch.isprintable() or ch in "\r\n\t" for ch in decoded)
        try:
            def reject_constant(value: str) -> None:
                raise ValueError("Non-standard JSON constant: " + value)
            json.loads(decoded, parse_constant=reject_constant)
            text_info["json_valid"] = True
        except (ValueError, RecursionError):
            pass
        if "<!DOCTYPE" in decoded.upper() or "<!ENTITY" in decoded.upper():
            text_info["xml_status"] = "skipped_dtd_or_entity"
        else:
            try:
                ET.fromstring(decoded)
                text_info["xml_valid"] = True
            except (ET.ParseError, ValueError, RecursionError):
                pass
    except UnicodeDecodeError:
        pass

    return {
        "file": str(source), "size_bytes": len(data),
        "magic_bytes": {"length": min(16, len(data)), "hex": data[:16].hex(" ")},
        "first_256_bytes_hex": data[:256].hex(" "),
        "printable_strings": [{"offset": m.start(), "text": m.group().decode("ascii")}
                              for m in re.finditer(rb"[\x20-\x7e]{4,}", data)],
        "compression": compression, "text": text_info,
        "scope": {
            "strings": "All ASCII printable runs of at least 4 bytes; offsets are zero-based.",
            "text": "Whole original file only; UTF-8/BOM, strict JSON, XML without DTD/entities.",
            "compression": "ZIP directory only (no member CRC check); GZIP/ZLIB first stream at offset 0, up to 8 MiB output.",
            "limitations": "No embedded stream search, recursive extraction, FMF decoding, or tactical/role mapping. Entire input is read into memory."
        }
    }


def inspect_fmf_cmd(args: argparse.Namespace) -> None:
    try:
        source = Path(args.file).resolve(strict=True)
        destination = Path(args.out).resolve() if args.out else None
        if destination is not None:
            if destination == source or (destination.exists() and destination.samefile(source)):
                raise ValueError("Report output must not be the input file or an alias of it.")
            if destination.suffix.lower() == ".fmf":
                raise ValueError("Report output must not use the .fmf extension.")
        report = inspect_fmf_file(str(source))
        serialized = json.dumps(report, ensure_ascii=True, indent=2)
        if destination is not None:
            # Exclusive creation also protects existing files and aliases from overwrites.
            with destination.open("x", encoding="utf-8") as stream:
                stream.write(serialized + "\n")
        print(serialized)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"inspect-fmf: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fm26lab", description="FM26 Tactical Lab v0.2.1")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("analyze-tactic", help="Evidence-only IP/OOP tactical analysis")
    inputs = s.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--file")
    inputs.add_argument("--tactic", type=int)
    s.add_argument("--observations", help="JSON array of sourced match observations")
    s.add_argument("--out")
    s.set_defaults(func=lambda a: tactic_analysis.run(a, DB_PATH, ROLE_DICTIONARY, ROLE_ALIASES))

    s = sub.add_parser("diff-fmf", help="Read-only byte comparison with embedded Zstandard inspection")
    s.add_argument("--a", required=True)
    s.add_argument("--b", required=True)
    s.add_argument("--label")
    s.add_argument("--out")
    s.set_defaults(func=diff_fmf_cmd)

    s = sub.add_parser("inspect-fmf", help="Read-only byte exploration; not an FMF parser")
    s.add_argument("--file", required=True)
    s.add_argument("--out", help="Save complete JSON report to a new file")
    s.set_defaults(func=inspect_fmf_cmd)

    s = sub.add_parser("init")
    s.set_defaults(func=lambda a: init_db())

    s = sub.add_parser("tactic-add")
    s.add_argument("--file", required=True)
    s.add_argument("--name")
    s.add_argument("--version")
    s.set_defaults(func=tactic_add)

    s = sub.add_parser("tactic-list")
    s.set_defaults(func=tactic_list)

    s = sub.add_parser("tactic-show")
    s.add_argument("--id", type=int, required=True)
    s.set_defaults(func=tactic_show)

    s = sub.add_parser("match-add")
    s.add_argument("--tactic", type=int, required=True)
    s.add_argument("--opponent", required=True)
    s.add_argument("--venue", choices=["home","away","neutral"], required=True)
    s.add_argument("--opp-formation", default="custom")
    s.add_argument("--opp-block", choices=["low","mid","high"], default="mid")
    s.add_argument("--gf", type=int, required=True)
    s.add_argument("--ga", type=int, required=True)
    s.add_argument("--xg-for", type=float)
    s.add_argument("--xg-against", type=float)
    s.add_argument("--shots-for", type=int)
    s.add_argument("--shots-against", type=int)
    s.add_argument("--sot-for", type=int)
    s.add_argument("--sot-against", type=int)
    s.add_argument("--possession", type=float)
    s.add_argument("--striker-shots", type=int)
    s.add_argument("--striker-goals", type=int)
    s.add_argument("--striker-rating", type=float)
    s.add_argument("--date")
    s.add_argument("--notes")
    s.set_defaults(func=match_add)

    s = sub.add_parser("match-list")
    s.add_argument("--tactic", type=int)
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=match_list)

    s = sub.add_parser("analyze")
    s.add_argument("--tactic", type=int, required=True)
    s.add_argument("--opp-formation", default="433")
    s.add_argument("--venue", choices=["home","away","neutral"], default="home")
    s.add_argument("--opp-block", choices=["low","mid","high"], default="mid")
    s.add_argument("--opp-strength", choices=["weaker","equal","stronger"], default="equal")
    s.add_argument("--last", type=int, default=5)
    s.set_defaults(func=analyze)

    s = sub.add_parser("gpt")
    s.add_argument("--tactic", type=int, required=True)
    s.add_argument("--question", required=True)
    s.add_argument("--last", type=int, default=5)
    s.add_argument("--model", default=DEFAULT_MODEL)
    s.add_argument("--opp-formation")
    s.add_argument("--venue", choices=["home","away","neutral"])
    s.add_argument("--opp-block", choices=["low","mid","high"])
    s.add_argument("--opp-strength", choices=["weaker","equal","stronger"])
    s.set_defaults(func=gpt_feedback)

    s = sub.add_parser("compare")
    s.add_argument("--a", type=int, required=True)
    s.add_argument("--b", type=int, required=True)
    s.add_argument("--last", type=int, default=5)
    s.set_defaults(func=compare)

    s = sub.add_parser("tactic-diff")
    s.add_argument("--a", type=int, required=True)
    s.add_argument("--b", type=int, required=True)
    s.set_defaults(func=tactic_diff_cmd)

    s = sub.add_parser("tactic-clone")
    s.add_argument("--from-id", type=int, required=True)
    s.add_argument("--version", required=True)
    s.add_argument("--name")
    s.add_argument("--patch", help="JSON file containing only fields to change")
    s.add_argument("--note")
    s.set_defaults(func=tactic_clone)

    s = sub.add_parser("change-history")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=change_history)

    s = sub.add_parser("self-test")
    s.set_defaults(func=self_test)

    s = sub.add_parser("validate-role-evidence")
    s.add_argument("--file", required=True, action="append", help="Reviewed role evidence package JSON; repeat for atomic batch")
    s.set_defaults(func=validate_role_evidence_command)

    s = sub.add_parser("import-role-evidence")
    s.add_argument("--file", required=True, action="append", help="Reviewed role evidence package JSON; repeat for atomic batch")
    s.add_argument("--apply", action="store_true", help="Write only after full validation succeeds")
    s.set_defaults(func=import_role_evidence_command)

    s = sub.add_parser("validate-role-master-baseline")
    s.set_defaults(func=validate_role_master_baseline_command)

    s = sub.add_parser("compatibility-readiness", help="Read-only compatibility candidate/rule-evidence readiness")
    s.set_defaults(func=compatibility_readiness_command)

    s = sub.add_parser("role-evidence-coverage-plan", help="Read-only role evidence collection plan")
    s.add_argument("--file", help="Tactic JSON; defaults to sample_leicester_4231.json")
    s.set_defaults(func=role_evidence_coverage_plan_command)

    s = sub.add_parser("evidence-request-manifest", help="Read-only request manifest excluding existing evidence")
    s.add_argument("--file", help="Tactic JSON; defaults to sample_leicester_4231.json")
    s.set_defaults(func=evidence_request_manifest_command)

    s = sub.add_parser("current-tactic-evidence-sufficiency", help="Read-only evidence sufficiency report")
    s.add_argument("--file", help="Tactic JSON; defaults to sample_leicester_4231.json")
    s.set_defaults(func=current_tactic_evidence_sufficiency_command)

    s = sub.add_parser("export-role-evidence-snapshot", help="Export read-only role evidence database snapshot")
    s.add_argument("--out", help="Output JSON path; defaults to data/role_evidence_snapshot.json")
    s.set_defaults(func=export_role_evidence_snapshot_command)

    s = sub.add_parser("audit-role-evidence-snapshot", help="Audit a snapshot against current role source data")
    s.add_argument("--file", help="Snapshot JSON; defaults to data/role_evidence_snapshot.json")
    s.set_defaults(func=audit_role_evidence_snapshot_command)

    s = sub.add_parser("existing-user-evidence-package-candidates", help="Read-only candidates from existing explicit evidence")
    s.add_argument("--file", help="Snapshot JSON; defaults to data/role_evidence_snapshot.json")
    s.set_defaults(func=existing_evidence_package_candidates_command)

    s = sub.add_parser("interactive")
    s.set_defaults(func=lambda a: interactive())

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.cmd:
        interactive()
        return
    if args.cmd not in ("init", "inspect-fmf", "diff-fmf", "analyze-tactic", "validate-role-evidence", "import-role-evidence", "validate-role-master-baseline", "compatibility-readiness", "role-evidence-coverage-plan", "evidence-request-manifest", "current-tactic-evidence-sufficiency", "export-role-evidence-snapshot", "audit-role-evidence-snapshot", "existing-user-evidence-package-candidates"):
        init_db()
    args.func(args)


if __name__ == "__main__":
    main()
