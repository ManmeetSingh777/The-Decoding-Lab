"""Educational deterministic compiler core. No model calls, no source-film claims.

Implements a narrow, testable rule: only immutable skill clauses specify style;
brief controls content; no LLM may append aesthetic words during production.
"""
import hashlib
import json
from typing import Any


class CompileBlocked(ValueError):
    pass


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def compile_request(brief: dict, skill: dict, scene: dict, provider: dict, *, fixture_mode=False) -> dict:
    required_brief = {'brief_id','subject','action','scene_id'}
    if not required_brief.issubset(brief):
        raise CompileBlocked('ORIGINAL_BRIEF_INCOMPLETE')
    if skill.get('state') not in ({'FIXTURE_ONLY'} if fixture_mode else {'CANDIDATE_EXPERIMENT','QUALIFIED'}):
        raise CompileBlocked('SKILL_NOT_ELIGIBLE')
    if not skill.get('version') or not skill.get('style_clauses'):
        raise CompileBlocked('STYLE_SKILL_ABSENT')
    if not provider.get('model_id') or not provider.get('max_prompt_chars'):
        raise CompileBlocked('PROVIDER_CAPABILITY_UNKNOWN')
    if scene.get('scene_id') != brief['scene_id']:
        raise CompileBlocked('SCENE_BRIEF_MISMATCH')
    keys = set(scene.get('conditions', {}))
    used = []
    for clause in skill['style_clauses']:
        if any(scene['conditions'].get(k) != v for k,v in clause.get('when',{}).items()):
            continue
        if not clause.get('template') or not clause.get('id') or not clause.get('operation_id'):
            raise CompileBlocked('STYLE_CLAUSE_INCOMPLETE')
        if not set(clause.get('when',{})).issubset(keys):
            raise CompileBlocked('UNMATCHED_CONDITION')
        if '{' in clause['template'] or '}' in clause['template']:
            raise CompileBlocked('UNDECLARED_STYLE_TEMPLATE_VARIABLE')
        used.append(clause)
    required = set(scene.get('required_style_clause_ids', []))
    selected = {x['id'] for x in used}
    if not required or not required.issubset(selected):
        raise CompileBlocked('REQUIRED_STYLE_CLAUSE_UNCOVERED')
    text_parts = [f"Original subject: {brief['subject']}", f"Required original action: {brief['action']}"]
    text_parts.extend(x['template'] for x in sorted(used, key=lambda x: x.get('priority',100)))
    # No runtime string expansion besides original-brief fields. All aesthetic text
    # is copied, in deterministic order, directly from skill-owned templates.
    positive = '\n'.join(text_parts)
    if len(positive) > provider['max_prompt_chars']:
        raise CompileBlocked('PROMPT_LIMIT_EXCEEDED')
    output = {
        'brief_sha256': canonical_hash(brief),
        'skill_sha256': canonical_hash(skill),
        'scene_sha256': canonical_hash(scene),
        'model_id': provider['model_id'],
        'route': scene.get('route','whole_scene'),
        'positivePrompt': positive,
        'style_provenance': [{'id':x['id'], 'operation_id':x['operation_id']} for x in used],
        'authorities': {'content':'OriginalBrief','style':'FrozenSkill','technical':'ProviderCapabilities'},
        'no_model_call': True,
    }
    output['request_sha256'] = canonical_hash(output)
    return output
