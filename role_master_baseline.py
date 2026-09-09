"""Master manifest and read-only integrity checks for user-verified FM26 role identity data."""
import copy
import json
from pathlib import Path

import role_behaviours
import role_connectivity_readiness
import role_constraints
import role_knowledge_coverage


MANIFEST_PATH = Path(__file__).resolve().parent / "data" / "role_source_manifest.json"


def build_manifest(catalog, kb):
    coverage = {row['internal_id']: row for row in role_knowledge_coverage.build_coverage_report(catalog, kb)['roles']}
    resolved = {row['internal_id']: row for row in role_constraints.resolve_catalog(catalog, kb)}
    output = []
    for role in catalog:
        row = resolved[role['internal_id']]
        missing = []
        if coverage[role['internal_id']]['status'] == 'identity_only': missing.append('behaviour_evidence')
        if role.get('ambiguity', {}).get('status') == 'unresolved': missing.append('identity_ambiguity')
        output.append({
            'role_internal_id': role['internal_id'], 'phase': role['phase'], 'role_name_ko': role['role_name_ko'],
            'role_families': copy.deepcopy(role['role_families']),
            'identity_verification': 'user_ingame_verified', 'availability_verification': 'user_ingame_verified',
            'behaviour_verification': coverage[role['internal_id']]['status'],
            'abbr_verification': role['display_abbr_verification'],
            'evidence_ids': [item['evidence_id'] for item in row['evidence']], 'missing_fields': missing,
        })
    return output


def write_manifest(path=MANIFEST_PATH):
    catalog = role_constraints.load_role_catalog(); kb = role_behaviours.load_knowledge_base()
    Path(path).write_text(json.dumps(build_manifest(catalog, kb), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def validate_master_baseline(catalog, kb, manifest):
    errors = []
    catalog = role_constraints.validate_role_catalog(catalog); kb = role_behaviours.validate_knowledge_base(kb)
    by_id = {item['role_internal_id']: item for item in manifest}
    catalog_ids = {item['internal_id'] for item in catalog}
    if len(manifest) != len(by_id): errors.append('duplicate manifest role_internal_id')
    for role in catalog:
        item = by_id.get(role['internal_id'])
        if item is None: errors.append('catalog role missing from manifest: '+role['internal_id']); continue
        for key, actual in (('phase', role['phase']), ('role_name_ko', role['role_name_ko']), ('role_families', role['role_families']), ('abbr_verification', role['display_abbr_verification'])):
            if item.get(key) != actual: errors.append('manifest mismatch '+key+': '+role['internal_id'])
    for internal_id in by_id:
        if internal_id not in catalog_ids: errors.append('manifest references unknown catalog role: '+internal_id)
    for role in catalog:
        for constraint in role['formation_constraints']:
            if constraint['comparison'] != 'eq' or constraint['value'] != 3: errors.append('non-exact three-CB constraint')
    return {'valid': not errors, 'errors': errors, 'catalog_roles': len(catalog), 'master_manifest_roles': len(manifest)}


def knowledge_matrix(catalog, kb, manifest):
    report = role_knowledge_coverage.build_coverage_report(catalog, kb)
    readiness = {item['role_internal_id']: item['analysis_readiness']['connectivity'] for item in role_connectivity_readiness.build_analysis_readiness(catalog, kb)}
    roles = []
    for role in catalog:
        roles.append({'identity': role['internal_id'], 'phase': role['phase'], 'role_families': role['role_families'], 'available_starting_positions': role['available_starting_positions'], 'formation_constraints': role['formation_constraints'], 'abbreviation_status': role['display_abbr_verification'], 'behaviour_coverage': next(x['status'] for x in report['roles'] if x['internal_id']==role['internal_id']), 'semantic_coverage': readiness[role['internal_id']]})
    return {'catalog_roles': len(catalog), 'master_manifest_roles': len(manifest), 'identity_verified': len(catalog), 'availability_verified': len(catalog), 'behaviour_partial': report['partial'], 'behaviour_verified': report['verified'], 'identity_only': report['identity_only'], 'unresolved': report['unresolved'], 'with_semantics': sum(any(value != 'unknown' for value in item['semantic_coverage'].values()) for item in roles), 'without_semantics': sum(all(value == 'unknown' for value in item['semantic_coverage'].values()) for item in roles), 'by_phase': report['by_phase'], 'by_role_family': report['by_role_family'], 'discrepancies': validate_master_baseline(catalog, kb, manifest)['errors'], 'roles': roles}
