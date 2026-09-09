"""Schema and fail-closed access for role behaviour evidence; no football rules."""
import copy
import datetime
import json
from urllib.parse import urlparse
from pathlib import Path

CATEGORIES = frozenset(('position_occupancy','ball_receiving','runs','link_play',
                       'dribbling','passing','goal_threat','width','defensive_transition','role_classification','key_attribute','chance_creation','role_description','player_requirement'))
VERIFICATIONS = frozenset(('unverified','verified','official','user_ingame_verified','rejected'))
EVIDENCE_LEVELS = frozenset(('user_ingame_verified', 'official_verified', 'experimental', 'community_report', 'unresolved'))
SOURCE_KINDS = frozenset(('user_ingame', 'official', 'experimental', 'community_report', 'unresolved'))
BEHAVIOUR_COVERAGE = frozenset(('verified', 'partial'))
DEFAULT_PATH = Path(__file__).resolve().with_name('role_behaviours.json')


def _require(ok, message):
    if not ok: raise ValueError('Role behaviour KB: '+message)


def _text(value):
    return isinstance(value,str) and bool(value.strip())


def validate_knowledge_base(data):
    _require(isinstance(data,list),'root must be an array')
    roles=set()
    for entry in data:
        _require(isinstance(entry,dict),'role entry must be an object')
        _require({'role','phase','behaviours','relationships','evidence','behaviour_verified'} <= entry.keys(),'missing role fields')
        _require(entry.get('role_internal_id') is None or _text(entry['role_internal_id']), 'invalid role_internal_id')
        _require(entry.get('coverage_status', 'partial') in BEHAVIOUR_COVERAGE, 'invalid coverage status')
        _require(_text(entry['role']) and entry['phase'] in ('IP','OOP'),'invalid role/phase')
        key=(entry['phase'],entry['role'])
        _require(key not in roles,'duplicate role/phase');roles.add(key)
        _require(type(entry['behaviour_verified']) is bool,'behaviour_verified must be boolean')
        for field in ('behaviours','relationships','evidence'):
            _require(isinstance(entry[field],list),field+' must be an array')
        # Relationships are reserved for a future evidence-backed schema, never executed.
        _require(all(isinstance(r,dict) for r in entry['relationships']),'relationships must contain objects')
        evidence_ids=set()
        for ev in entry['evidence']:
            _require(isinstance(ev,dict),'evidence must be an object')
            _require({'evidence_id','source_type','title','source','accessed','notes'} <= ev.keys(),'missing evidence fields')
            _require(all(_text(ev[k]) for k in ('evidence_id','source_type','title','source','accessed')),'empty evidence identity/source')
            _require(isinstance(ev['notes'],str),'notes must be text')
            if 'evidence_level' in ev:
                _require(ev['evidence_level'] in EVIDENCE_LEVELS, 'invalid evidence level')
            try: datetime.date.fromisoformat(ev['accessed'])
            except (TypeError,ValueError): raise ValueError('Role behaviour KB: accessed must be YYYY-MM-DD')
            _require(ev['evidence_id'] not in evidence_ids,'duplicate evidence ID')
            evidence_ids.add(ev['evidence_id'])
        ids=set()
        for behaviour in entry['behaviours']:
            _require(isinstance(behaviour,dict),'behaviour must be an object')
            _require({'behaviour_id','category','claim','conditions','evidence_ids','verification'} <= behaviour.keys(),'missing behaviour fields')
            _require(_text(behaviour['behaviour_id']) and _text(behaviour['claim']),'empty behaviour ID/claim')
            _require(behaviour['behaviour_id'] not in ids,'duplicate behaviour ID');ids.add(behaviour['behaviour_id'])
            _require(isinstance(behaviour['category'],str) and behaviour['category'] in CATEGORIES,'invalid category')
            _require(isinstance(behaviour['verification'],str) and behaviour['verification'] in VERIFICATIONS,'invalid verification')
            _require(isinstance(behaviour['conditions'],list) and all(isinstance(c,dict) or _text(c) for c in behaviour['conditions']),'conditions must be an array of objects or nonempty tokens')
            refs=behaviour['evidence_ids']
            _require(isinstance(refs,list) and bool(refs) and all(_text(x) for x in refs),'every behaviour requires evidence IDs')
            _require(len(set(refs))==len(refs) and set(refs)<=evidence_ids,'duplicate or unresolved evidence references')
            if behaviour['verification']=='user_ingame_verified':
                _require(all(e['source_type']=='user_ingame_capture' for e in entry['evidence'] if e['evidence_id'] in refs),'user-ingame verification requires user capture evidence')
            if behaviour['verification']=='official':
                sources=[e for e in entry['evidence'] if e['evidence_id'] in refs]
                _require(all(e['source_type']=='official' and urlparse(e['source']).scheme=='https' and urlparse(e['source']).hostname=='www.footballmanager.com' for e in sources),'official claims require Football Manager official source references')
            semantics = behaviour.get('connectivity_semantics')
            if semantics is not None:
                _require(isinstance(semantics, dict), 'connectivity_semantics must be an object')
                _require(set(semantics) <= {'send', 'receive', 'space', 'movement'}, 'invalid connectivity semantics key')
                for group, items in semantics.items():
                    _require(isinstance(items, list), 'invalid connectivity semantics value')
                    for semantic in items:
                        _require(isinstance(semantic, dict), 'connectivity semantic must be an object')
                        _require({'semantic_id', 'evidence_ids', 'verification'} <= semantic.keys(), 'missing connectivity semantic fields')
                        _require(_text(semantic['semantic_id']), 'invalid semantic ID')
                        refs = semantic['evidence_ids']
                        _require(isinstance(refs, list) and bool(refs) and set(refs) <= evidence_ids, 'unresolved semantic evidence')
                        _require(semantic['verification'] in VERIFICATIONS, 'invalid semantic verification')
                        _require(semantic.get('coverage', 'verified') in ('verified', 'partial'), 'invalid semantic coverage')
            for field in ('role_internal_id', 'behaviour_type', 'description_ko', 'source_kind', 'limitations'):
                if field in behaviour:
                    if field == 'limitations':
                        _require(isinstance(behaviour[field], list) and all(_text(item) for item in behaviour[field]), 'invalid limitations')
                    else:
                        _require(_text(behaviour[field]), 'invalid extended behaviour field')
            if 'source_kind' in behaviour:
                _require(behaviour['source_kind'] in SOURCE_KINDS, 'invalid source kind')
        instructions=entry.get('player_instructions',[])
        _require(isinstance(instructions,list),'player_instructions must be an array')
        instruction_ids=set()
        for instruction in instructions:
            _require(isinstance(instruction,dict) and {'instruction_id','name_ko','phase','evidence_ids','verification'}<=instruction.keys(),'missing player instruction fields')
            _require(_text(instruction['instruction_id']) and _text(instruction['name_ko']),'invalid player instruction identity')
            _require(instruction['instruction_id'] not in instruction_ids,'duplicate player instruction ID')
            instruction_ids.add(instruction['instruction_id'])
            _require(instruction['phase']==entry['phase'],'player instruction phase mismatch')
            _require(instruction['verification'] in VERIFICATIONS,'invalid instruction verification')
            refs=instruction['evidence_ids']
            _require(isinstance(refs,list) and bool(refs) and all(_text(x) for x in refs),'instruction requires evidence')
            _require(set(refs)<=evidence_ids,'unresolved instruction evidence')
            if instruction['verification']=='user_ingame_verified':
                _require(all(e['source_type']=='user_ingame_capture' for e in entry['evidence'] if e['evidence_id'] in refs),'instruction requires user capture evidence')
        _require(not entry['behaviour_verified'] or any(b['verification'] in ('verified','official','user_ingame_verified') for b in entry['behaviours']),
                 'enabled role requires at least one individually verified behaviour')
    return copy.deepcopy(data)


def load_knowledge_base(path=DEFAULT_PATH):
    return validate_knowledge_base(json.loads(Path(path).read_text(encoding='utf-8-sig')))


def verified_behaviours(data,role,phase):
    """Evidence presence is not verification; both explicit gates must pass."""
    entries=validate_knowledge_base(data)
    for entry in entries:
        if entry['role']==role and entry['phase']==phase and entry['behaviour_verified']:
            return [b for b in entry['behaviours'] if b['verification'] in ('verified','official','user_ingame_verified')]
    return []


def behaviour_records(data, catalog=None):
    """Return JSON-ready v2 behaviour records without mutating legacy KB input.

    Legacy fields remain authoritative.  The extended fields make future
    screenshot-derived facts explicit, but never assign connectivity semantics.
    """
    entries = validate_knowledge_base(data)
    reference_ids = {}
    if catalog is not None:
        for role in catalog:
            reference = role.get('role_behaviour_ref')
            if reference:
                reference_ids[(reference.get('phase'), reference.get('role'))] = role['internal_id']
    records = []
    for entry in entries:
        internal_id = entry.get('role_internal_id') or reference_ids.get((entry['phase'], entry['role']))
        for behaviour in entry['behaviours']:
            evidence = [item for item in entry['evidence'] if item['evidence_id'] in behaviour['evidence_ids']]
            source_kind = behaviour.get('source_kind') or _source_kind(evidence, behaviour['verification'])
            records.append({
                'behaviour_id': behaviour['behaviour_id'],
                'role_internal_id': behaviour.get('role_internal_id') or internal_id,
                'phase': entry['phase'],
                'behaviour_type': behaviour.get('behaviour_type', behaviour['category']),
                'description_ko': behaviour.get('description_ko', behaviour['claim']),
                'source_kind': source_kind,
                'verification': behaviour['verification'],
                'evidence_ids': copy.deepcopy(behaviour['evidence_ids']),
                'connectivity_semantics': _complete_semantics(behaviour.get('connectivity_semantics', {})),
                'limitations': copy.deepcopy(behaviour.get('limitations', [])),
            })
    return records


def _complete_semantics(value):
    return {group: copy.deepcopy(value.get(group, [])) for group in ('send', 'receive', 'space', 'movement')}


def _source_kind(evidence, verification):
    declared = {item.get('evidence_level') for item in evidence if item.get('evidence_level')}
    if len(declared) == 1:
        return {'user_ingame_verified': 'user_ingame', 'official_verified': 'official'}.get(declared.pop(), 'unresolved')
    if verification == 'user_ingame_verified' and evidence and all(item['source_type'] == 'user_ingame_capture' for item in evidence):
        return 'user_ingame'
    if verification == 'official' and evidence and all(item['source_type'] == 'official' for item in evidence):
        return 'official'
    return 'unresolved'
