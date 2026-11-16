"""Offline *illustrative* authority kernel. No VLM, no Runware calls, no artistic success.

The real Claude/Codex build MUST implement equivalent behavior at every production
call-site, not just copy these tests. The synthetic fixture is not Kurzgesagt evidence.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

class Blocked(ValueError):
    pass

_ISSUER = object()
_ALLOWED_CONTENT = ('subject','setting','action','visual_role','view','original_prop')
_STYLE_WORDS_IN_CONTENT = re.compile(r'\b(kurzgesagt|vector style|art style|in the style of|shading style|color palette|lineart style|photorealistic style)\b', re.I)


def digest(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()


def _check_required(obj: dict, keys: set, error: str) -> None:
    if not keys.issubset(obj) or any(obj[k] in (None,'',[]) for k in keys):
        raise Blocked(error)


def witness_to_candidate(bundle: dict, proposal: dict) -> dict:
    """Structure genuine source-to-decision transformation; does NOT judge visual truth."""
    _check_required(bundle,{'bundle_id','witnesses','visible_effect','contrasting_evidence'},'MISSING_WITNESS')
    if len(bundle['witnesses']) < 2:
        raise Blocked('INSUFFICIENT_CONTRAST')
    for w in bundle['witnesses']:
        _check_required(w,{'film_sha256','frame_index','visible_description'},'UNANCHORED_WITNESS')
        if len(w['film_sha256']) != 64:
            raise Blocked('BAD_FILM_SHA')
    _check_required(proposal,{'decision_id','conditions','invariants','adaptations','exceptions','operation_ids','expected_visible_effect','what_may_vary','excluded_source_specifics'},'INCOMPLETE_STYLE_DECISION')
    if not proposal['operation_ids']:
        raise Blocked('NO_PRODUCING_OPERATION')
    if not isinstance(proposal['conditions'],dict):
        raise Blocked('INVALID_STYLE_CONDITION')
    if any(not isinstance(x,str) for x in proposal['operation_ids']):
        raise Blocked('INVALID_OPERATION')
    # Uniquely source-specific terms must be declared and absent from the reusable rule.
    symbolic = json.dumps({k:proposal[k] for k in ('conditions','invariants','adaptations','expected_visible_effect')},ensure_ascii=False).lower()
    for term in proposal['excluded_source_specifics']:
        if term.lower() in symbolic:
            raise Blocked('SOURCE_SPECIFIC_STYLE_LEAK')
    return {'bundle_hash':digest(bundle),'candidate':proposal,'candidate_sha':digest(proposal),'status':'STYLE_CANDIDATE_NOT_QUALIFIED'}


@dataclass(frozen=True)
class CompiledImageJob:
    logical_payload: dict
    trace: dict
    logical_sha256: str
    _issuer: object

    def __post_init__(self):
        if self._issuer is not _ISSUER:
            raise Blocked('DIRECT_JOB_CONSTRUCTION_FORBIDDEN')


class StyleProgramCompiler:
    """Only frozen skill clauses become aesthetic text; typed original slots supply content."""
    def compile(self, brief: dict, skill: dict, scene: dict, provider: dict) -> CompiledImageJob:
        _check_required(brief,{'brief_id','subject','setting','action','visual_role','view'},'CONTENT_BRIEF_INCOMPLETE')
        for field in _ALLOWED_CONTENT:
            if field in brief:
                if not isinstance(brief[field],str):
                    raise Blocked('CONTENT_MUST_BE_TEXT')
                if _STYLE_WORDS_IN_CONTENT.search(brief[field]):
                    raise Blocked('STYLE_INJECTION_IN_CONTENT')
        _check_required(skill,{'skill_id','version','status','clauses','decisions','allowed_operations'},'STYLE_SKILL_MISSING')
        if skill['status'] not in ('CANDIDATE_EXPERIMENT','QUALIFIED'):
            raise Blocked('SKILL_STATUS_DISALLOWED')
        _check_required(scene,{'required_decision_ids','operation_id','output_contract'},'SCENE_ART_PLAN_MISSING')
        if 'reference_images' not in scene: raise Blocked('SCENE_REFERENCE_LIST_MISSING')
        if scene['operation_id'] not in skill['allowed_operations']:
            raise Blocked('UNAPPROVED_OPERATION')
        _check_required(provider,{'model_air_id','max_prompt_chars','max_reference_images','supported_operations'},'PROVIDER_UNKNOWN')
        if scene['operation_id'] not in provider['supported_operations']:
            raise Blocked('PROVIDER_UNSUPPORTED_OPERATION')
        # Only explicitly required decisions and their declared dependencies control
        # the call. A merely matching, unrelated clause must not contaminate art.
        eligible={}
        for decision in skill['decisions']:
            if any(brief.get(k)!=v for k,v in decision.get('when',{}).items()):
                continue
            _check_required(decision,{'id','clause_ids','operation_id','evidence_ids','visual_prediction'},'STYLE_DECISION_INCOMPLETE')
            if decision['operation_id']==scene['operation_id']:
                eligible[decision['id']]=decision
        required_ids=set(scene['required_decision_ids'])
        if not required_ids or not required_ids.issubset(eligible):
            raise Blocked('MISSING_REQUIRED_STYLE_DECISION')
        decision_ids=set()
        def visit(decision_id):
            if decision_id in decision_ids: return
            if decision_id not in eligible: raise Blocked('MISSING_STYLE_DEPENDENCY')
            decision_ids.add(decision_id)
            for dep in eligible[decision_id].get('depends_on',[]): visit(dep)
        for x in sorted(required_ids): visit(x)
        selected=[]
        for x in sorted(decision_ids): selected.extend(eligible[x]['clause_ids'])
        clause_lookup={c['id']:c for c in skill['clauses']}
        text_parts=[f"Original subject: {brief['subject']}",f"Original setting: {brief['setting']}",f"Original action: {brief['action']}"]
        clause_trace=[]
        unique=[]
        for x in selected:
            if x not in unique: unique.append(x)
        for cid in sorted(unique,key=lambda x:(clause_lookup.get(x,{}).get('priority',999),x)):
            if cid not in clause_lookup: raise Blocked('MISSING_PROMPT_CLAUSE')
            clause=clause_lookup[cid]
            _check_required(clause,{'id','template','priority'},'INCOMPLETE_PROMPT_CLAUSE')
            template=clause['template']
            keys=set(re.findall(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}',template))
            if keys-set(_ALLOWED_CONTENT): raise Blocked('UNAPPROVED_TEMPLATE_SLOT')
            if re.search(r'\$\{[^}]*\}',template) and not keys:
                raise Blocked('UNAPPROVED_TEMPLATE_SLOT')
            result=template
            for key in keys:
                if key not in brief: raise Blocked('MISSING_CONTENT_SLOT')
                result=result.replace('${'+key+'}',brief[key])
            if '${' in result: raise Blocked('UNRESOLVED_TEMPLATE_SLOT')
            text_parts.append(result)
            clause_trace.append({'id':cid,'template_hash':digest(template),'rendered_hash':digest(result)})
        if not unique: raise Blocked('EMPTY_STYLE_PROMPT')
        refs=scene['reference_images']
        if len(refs)>provider['max_reference_images']:
            raise Blocked('PROVIDER_REF_LIMIT')
        ref_roles=[]
        allowed_shas=set(skill.get('authorized_reference_sha256s',[]))
        for r in refs:
            _check_required(r,{'id','role','sha256','approved'},'BAD_REFERENCE')
            if len(r['sha256'])!=64 or not r['approved']: raise Blocked('UNAPPROVED_REFERENCE')
            if r['role']=='learned_style' and r['sha256'] not in allowed_shas:
                raise Blocked('UNPINNED_STYLE_REFERENCE')
            ref_roles.append({'id':r['id'],'role':r['role'],'sha256':r['sha256']})
        required_roles=set(skill.get('required_reference_roles',[]))
        if not required_roles.issubset({r['role'] for r in ref_roles}):
            raise Blocked('REQUIRED_STYLE_REFERENCE_MISSING')
        if scene.get('requires_identity') and not any(r['role']=='canonical_identity' for r in refs):
            raise Blocked('CHARACTER_IDENTITY_REFERENCE_MISSING')
        output=scene['output_contract']
        _check_required(output,{'width','height','format','asset_kind'},'OUTPUT_CONTRACT_MISSING')
        w,h=output['width'],output['height']
        if not isinstance(w,int) or not isinstance(h,int) or w<=0 or h<=0: raise Blocked('INVALID_DIMENSION')
        if provider.get('size_multiple') and (w%provider['size_multiple'] or h%provider['size_multiple']):
            raise Blocked('PROVIDER_DIMENSION_MULTIPLE')
        text='\n'.join(text_parts)
        if len(text)>provider['max_prompt_chars']: raise Blocked('PROMPT_LIMIT')
        payload={'model':provider['model_air_id'],'operation_id':scene['operation_id'],'positivePrompt':text,
                 'referenceRoles':ref_roles,'width':w,'height':h,'outputFormat':output['format']}
        trace={'content_hash':digest(brief),'skill_hash':digest(skill),'skill_id':skill['skill_id'],
               'version':skill['version'],'selected_decisions':sorted(decision_ids),
               'clause_trace':clause_trace,'authority':{'content':'original_brief','aesthetic':'frozen_skill','technical':'provider'},
               'output_contract_hash':digest(output)}
        return CompiledImageJob(payload,trace,digest({'payload':payload,'trace':trace}),_ISSUER)


class OfflineStyleImageGateway:
    """No network. Shape of sole paid gateway; the real app MUST enforce same contract."""
    def submit(self, job:CompiledImageJob) -> dict:
        if not isinstance(job,CompiledImageJob) or job._issuer is not _ISSUER:
            raise Blocked('RAW_PROMPT_GATEWAY_BYPASS')
        if digest({'payload':job.logical_payload,'trace':job.trace})!=job.logical_sha256:
            raise Blocked('COMPILED_JOB_MUTATED')
        return {'OFFLINE_ONLY':True,'logical_sha256':job.logical_sha256,'positivePrompt':job.logical_payload['positivePrompt'],
                'model':job.logical_payload['model'],'generated_images':0}
