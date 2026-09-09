"""Evidence registry view for the role behaviour knowledge base."""
import copy

import role_behaviours


def build_evidence_registry(behaviour_kb):
    """Deduplicate KB evidence into JSON-compatible records with an explicit level."""
    entries = role_behaviours.validate_knowledge_base(behaviour_kb)
    records = {}
    for entry in entries:
        for evidence in entry['evidence']:
            item = copy.deepcopy(evidence)
            item['verification_level'] = item.get('evidence_level') or _level_for_source(item['source_type'])
            records[item['evidence_id']] = item
    return [records[key] for key in sorted(records)]


def _level_for_source(source_type):
    if source_type == 'user_ingame_capture':
        return 'user_ingame_verified'
    if source_type == 'official':
        return 'official_verified'
    return 'unresolved'
