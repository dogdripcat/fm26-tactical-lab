"""Read-only semantic readiness derived from explicitly mapped behaviour facts."""
from collections import defaultdict

import role_behaviours
import role_knowledge_coverage


GROUPS = ('send', 'receive', 'space', 'movement')


def build_analysis_readiness(catalog, behaviour_kb):
    coverage = role_knowledge_coverage.build_coverage_report(catalog, behaviour_kb)
    semantics = defaultdict(lambda: {group: [] for group in GROUPS})
    for record in role_behaviours.behaviour_records(behaviour_kb, catalog):
        if not record['role_internal_id']:
            continue
        for group in GROUPS:
            semantics[record['role_internal_id']][group].extend(record['connectivity_semantics'][group])
    output = []
    for role in coverage['roles']:
        groups = semantics[role['internal_id']]
        readiness = {}
        for group, facts in groups.items():
            if not facts:
                readiness[group] = 'unknown'
            elif any(item.get('coverage') == 'partial' for item in facts):
                readiness[group] = 'partial'
            else:
                readiness[group] = 'verified'
        output.append({
            'role_internal_id': role['internal_id'],
            'overall': role['status'],
            'analysis_readiness': {'connectivity': readiness},
        })
    return output
