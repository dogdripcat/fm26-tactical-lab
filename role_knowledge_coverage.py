"""Read-only coverage accounting for the FM26 role behaviour knowledge base."""
from collections import Counter

import role_behaviours
import role_constraints


ANALYSABLE_VERIFICATIONS = frozenset(('verified', 'official', 'user_ingame_verified'))


def build_coverage_report(catalog, behaviour_kb):
    """Return JSON-compatible coverage states; no tactical inference occurs here."""
    catalog = role_constraints.validate_role_catalog(catalog)
    behaviour_kb = role_behaviours.validate_knowledge_base(behaviour_kb)
    by_internal_id = {
        entry.get('role_internal_id'): entry
        for entry in behaviour_kb if entry.get('role_internal_id')
    }
    by_reference = {(entry['phase'], entry['role']): entry for entry in behaviour_kb}
    rows = []
    for role in catalog:
        ambiguity = role.get('ambiguity', {})
        entry = by_internal_id.get(role['internal_id'])
        if entry is None and role['role_behaviour_ref']:
            reference = role['role_behaviour_ref']
            entry = by_reference.get((reference['phase'], reference['role']))
        if ambiguity.get('status') == 'unresolved':
            status = 'unresolved'
        elif not entry:
            status = 'identity_only'
        else:
            facts = [item for item in entry['behaviours'] if item['verification'] in ANALYSABLE_VERIFICATIONS and item['evidence_ids']]
            if not facts:
                status = 'identity_only'
            else:
                status = entry.get('coverage_status', 'partial')
        rows.append({
            'internal_id': role['internal_id'],
            'phase': role['phase'],
            'role_families': list(role['role_families']),
            'status': status,
        })
    status_counts = Counter(row['status'] for row in rows)
    phases = {}
    families = {}
    for phase in ('IP', 'OOP'):
        phase_rows = [row for row in rows if row['phase'] == phase]
        phases[phase] = dict(Counter(row['status'] for row in phase_rows))
        for family in sorted({family for row in phase_rows for family in row['role_families']}):
            family_rows = [row for row in phase_rows if family in row['role_families']]
            families[f'{phase}:{family}'] = dict(Counter(row['status'] for row in family_rows))
    return {
        'total_roles': len(rows),
        'verified': status_counts['verified'],
        'partial': status_counts['partial'],
        'identity_only': status_counts['identity_only'],
        'unresolved': status_counts['unresolved'],
        'by_phase': phases,
        'by_role_family': families,
        'missing_behaviour_roles': [row['internal_id'] for row in rows if row['status'] in ('identity_only', 'unresolved')],
        'roles': rows,
    }
