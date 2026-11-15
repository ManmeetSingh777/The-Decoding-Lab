"""Deterministic skill-exclusive StyleProgramCompiler → immutable CompiledImageJob (spec 15 §3, 09 E, 11, ADD25 §4.2).

Only frozen/pinned skill clauses produce aesthetic text; typed brief slots supply content;
provider capabilities supply the technical envelope. There is no free-text style input,
no post-compile "polish" step and no raw-prompt entry point. A missing decision returns a
ResearchTicket (MISSING_STYLE_DECISION) instead of filler.
"""
from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..util import Blocked, canonical_json, digest, new_id, now_iso, sha256_file
from ..skills.operators import get_operator, provider_supports
from ..skills.skill import COMPILABLE_STATUSES, load_skill
from ..style.provenance import interface_two_audit, style_authority_report
from .brief import CONTENT_SLOTS, OriginalContentBrief, brief_hash, validate_brief

COMPILER_VERSION = "style-program-compiler/1"
_ISSUER = object()
_SLOT = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
CONDITION_TO_SLOT = {"subject_kind": "subject_kind", "role": "visual_role", "view": "view", "material": "material",
                     "scale": "scale", "action": "action", "environment": "environment"}
SCENE_PLAN_FIELDS = ("plan_id", "brief_id", "skill_id", "skill_hash", "recipe_id", "required_art_ops", "dependency_graph",
                     "style_decision_ids", "character_anchor_ids", "image_reference_roles", "asset_output_specs",
                     "motion_state_needs", "conditions")
CONTENT_LABELS = (("subject", "Original subject"), ("setting", "Original setting"), ("action", "Required original action"),
                  ("view", "Required view"), ("original_prop", "Original prop"))


@dataclass(frozen=True)
class CompiledImageJob:
    job_id: str
    logical_payload: dict           # exact provider-visible fields (taskUUID assigned only at submission)
    reference_images: tuple         # ((role, sha256, data_uri), ...) — actual bytes, not just IDs
    trace: dict
    inputs: dict                    # everything required to deterministically recompile
    synthetic: bool
    baseline_only: bool
    logical_sha256: str
    _issuer: object

    def __post_init__(self):
        if self._issuer is not _ISSUER:
            raise Blocked("DIRECT_JOB_CONSTRUCTION_FORBIDDEN", "only StyleProgramCompiler issues jobs")


def issued_by_compiler(job: Any) -> bool:
    return isinstance(job, CompiledImageJob) and job._issuer is _ISSUER


def research_ticket(code: str, *, missing_decision: str | None, affected_state: str, question: str,
                    candidate_frames: list | None = None, reason: str = "") -> Blocked:
    t = {"ticket_id": new_id("rt"), "kind": code, "missing_art_decision": missing_decision,
         "affected_scene_state": affected_state, "required_source_question": question,
         "candidate_reference_frames": candidate_frames or [], "reason_for_block": reason or code, "created_at": now_iso()}
    return Blocked(code, reason or question, ticket=t, missing_decision=missing_decision)


def build_scene_art_plan(brief: OriginalContentBrief, skill: dict, recipe_id: str) -> dict:
    """SceneArtPlan produced FROM resolved skill recipe + brief. Has no aesthetic text field."""
    if recipe_id not in skill["recipes"]:
        raise Blocked("UNKNOWN_RECIPE", recipe_id)
    rec = skill["recipes"][recipe_id]
    nodes = rec["nodes"]
    conditions = {k: brief.slots[s] for k, s in CONDITION_TO_SLOT.items() if s in brief.slots}
    anchors = [s["identity_asset_id"] for s in brief.subjects if s.get("identity_asset_id")]
    plan = {"plan_id": f"sap_{digest([brief.brief_id, skill['skill_hash'], recipe_id])[:16]}", "brief_id": brief.brief_id,
            "skill_id": skill["skill_id"], "skill_hash": skill["skill_hash"], "recipe_id": recipe_id,
            "required_art_ops": [{"node_id": n["id"], "operator": n["operator"], "decisions": n.get("decisions", []),
                                  "outputs": n.get("outputs", [])} for n in nodes],
            "dependency_graph": {n["id"]: n.get("depends_on", []) for n in nodes},
            "style_decision_ids": sorted({d for n in nodes for d in n.get("decisions", [])}),
            "character_anchor_ids": anchors,
            "image_reference_roles": sorted({r for n in nodes for r in n.get("reference_roles", [])}),
            "asset_output_specs": {n["id"]: n.get("output_contract", {}) for n in nodes},
            "motion_state_needs": list(brief.animation_requirements), "conditions": conditions}
    return plan


def validate_scene_plan(plan: dict) -> None:
    extra = set(plan) - set(SCENE_PLAN_FIELDS)
    if extra:
        raise Blocked("SCENE_PLAN_HAS_UNOWNED_FIELDS", f"{sorted(extra)} (no free aesthetic field allowed)")


def _escape(v: str) -> str:
    return re.sub(r"[\r\n{}$]", " ", v).strip()


def _select_branch(decision: dict, conditions: dict, operator: str | None = None) -> dict | None:
    ok = []
    for br in decision.get("branches", []):
        if operator and operator not in br.get("operation_node_ids", []):
            continue
        when = br.get("when", {})
        if all(k in conditions and str(conditions[k]) == str(v) for k, v in when.items()):
            ok.append(br)
    return sorted(ok, key=lambda b: (b.get("priority", 100), canonical_json(b["when"])))[0] if ok else None


class StyleProgramCompiler:
    """compile(brief, pinned skill, recipe node, capabilities) → CompiledImageJob | Blocked(ticket)."""

    def __init__(self, *, clause_renderer=None):
        # clause_renderer is injectable ONLY so tests can simulate a compiler bug; the self-check catches it.
        self._render_clause = clause_renderer or self._default_render

    @staticmethod
    def _default_render(template: str, slots: dict) -> str:
        keys = set(_SLOT.findall(template))
        bad = keys - set(CONTENT_SLOTS)
        if bad:
            raise Blocked("UNAPPROVED_TEMPLATE_SLOT", str(sorted(bad)))
        if re.search(r"\$\{[^}]*\}", template) and not keys:
            raise Blocked("UNAPPROVED_TEMPLATE_SLOT")
        out = template
        for k in keys:
            if k not in slots:
                raise Blocked("MISSING_CONTENT_SLOT", k)
            out = out.replace("${" + k + "}", _escape(slots[k]))
        if "${" in out:
            raise Blocked("UNRESOLVED_TEMPLATE_SLOT")
        return out

    def compile(self, raw_brief: dict, skill_folder: str | Path, *, pinned_skill_hash: str, recipe_id: str, node_id: str,
                caps: dict, identity_assets: dict | None = None, output_contract: dict | None = None) -> CompiledImageJob:
        brief = validate_brief(raw_brief)
        skill = load_skill(skill_folder)
        if skill["skill_hash"] != pinned_skill_hash:
            raise Blocked("SKILL_NOT_PINNED", f"pinned {pinned_skill_hash[:12]} != loaded {skill['skill_hash'][:12]}")
        if skill["status"] not in COMPILABLE_STATUSES:
            raise Blocked("SKILL_STATUS_DISALLOWED", skill["status"])
        plan = build_scene_art_plan(brief, skill, recipe_id)
        validate_scene_plan(plan)
        node = next((n for n in skill["recipes"][recipe_id]["nodes"] if n["id"] == node_id), None)
        if node is None:
            raise Blocked("UNKNOWN_RECIPE_NODE", node_id)
        op = get_operator(node["operator"])
        if op["backend"] != "provider":
            raise Blocked("NOT_A_PROVIDER_OPERATION", node["operator"])
        missing_caps = provider_supports(node["operator"], caps)
        if missing_caps:
            raise Blocked("UNSUPPORTED_PROVIDER_OPERATION", f"{node['operator']} needs {missing_caps}")
        conditions = plan["conditions"]
        decisions = {d["decision_id"]: d for d in skill["decisions"]}
        selected: dict[str, dict] = {}

        def resolve(did: str, chain: tuple = ()) -> None:
            if did in selected:
                return
            if did in chain:
                raise Blocked("DECISION_DEPENDENCY_CYCLE", did)
            d = decisions.get(did)
            if d is None or d.get("status") == "RESEARCH_ONLY":
                raise research_ticket("MISSING_STYLE_DECISION", missing_decision=did, affected_state=node_id,
                                      question=f"Which source-grounded conditional decision governs {did} for {conditions}?",
                                      reason="required decision absent or RESEARCH_ONLY")
            br = _select_branch(d, conditions, node["operator"])
            if br is None:
                raise research_ticket("MISSING_STYLE_DECISION", missing_decision=did, affected_state=node_id,
                                      question=f"Decision {did} has no branch for conditions {conditions}; which visible "
                                               f"construction applies for this subject/view/action?",
                                      reason="UNMATCHED_CONDITION")
            if node["operator"] not in br.get("operation_node_ids", []):
                raise Blocked("BRANCH_OPERATION_MISMATCH", f"{did} branch does not produce via {node['operator']}")
            selected[did] = {"decision": d, "branch": br}
            for dep in d.get("dependencies", []):
                resolve(dep, chain + (did,))

        req = node.get("decisions", [])
        if not req:
            raise research_ticket("MISSING_STYLE_DECISION", missing_decision=None, affected_state=node_id,
                                  question="recipe node lists no style decisions", reason="EMPTY_STYLE_PROGRAM")
        for did in sorted(req):
            resolve(did)
        clause_by_id = {c["id"]: c for c in skill["clauses"]}
        clause_ids = []
        for did in sorted(selected):
            for_op = [cid for cid in selected[did]["branch"]["clause_ids"]
                      if clause_by_id.get(cid, {}).get("operation_id") == node["operator"]]
            missing_here = [cid for cid in selected[did]["branch"]["clause_ids"] if cid not in clause_by_id]
            if missing_here:
                raise Blocked("MISSING_PROMPT_CLAUSE", str(missing_here))
            if not for_op:
                raise research_ticket("MISSING_STYLE_DECISION", missing_decision=did, affected_state=node_id,
                                      question=f"Decision {did} has no skill clause for operation {node['operator']}",
                                      reason="NO_CLAUSE_FOR_OPERATION")
            for cid in for_op:
                if cid not in clause_ids:
                    clause_ids.append(cid)
        segs: list[dict] = []
        for key, label in CONTENT_LABELS:
            if key in brief.slots:
                segs.append({"authority": "CONTENT", "brief_field_path": f"slots.{key}", "text": f"{label}: {_escape(brief.slots[key])}"})
        style_segs = []
        for cid in clause_ids:
            c = clause_by_id.get(cid)
            if c is None:
                raise Blocked("MISSING_PROMPT_CLAUSE", cid)
            if c.get("operation_id") != node["operator"]:
                raise Blocked("CLAUSE_OPERATION_MISMATCH", cid)
            style_segs.append((c.get("priority", 100), cid, c))
        for _, cid, c in sorted(style_segs, key=lambda x: (x[0], x[1])):
            segs.append({"authority": "STYLE", "clause_id": cid, "skill_decision_id": c["decision_id"],
                         "skill_hash": skill["skill_hash"], "template_sha": digest(c["template"]),
                         "text": self._render_clause(c["template"], brief.slots)})
        # identity + references (actual bytes)
        identity_assets = identity_assets or {}
        refs: list[tuple] = []
        ref_trace = []
        needs_identity = op["identity_reference_required"] or node.get("requires_identity")
        if needs_identity:
            anchors = [a for a in plan["character_anchor_ids"] if a in identity_assets]
            if not anchors:
                raise Blocked("CHARACTER_IDENTITY_REFERENCE_MISSING", "pose/view edit requires approved canonical image bytes")
            for a in anchors:
                ia = identity_assets[a]
                if not ia.get("approved"):
                    raise Blocked("IDENTITY_NOT_APPROVED", a)
                p = Path(ia["path"])
                if sha256_file(p) != ia["sha256"]:
                    raise Blocked("IDENTITY_BYTES_CHANGED", a)
                refs.append(("canonical_identity", ia["sha256"], "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()))
                ref_trace.append({"role": "canonical_identity", "sha256": ia["sha256"], "asset_id": a, "authority": "APPROVED_IDENTITY"})
        wanted_roles = []
        for did in sorted(selected):
            for r in selected[did]["branch"].get("reference_role_ids", []):
                if r not in wanted_roles:
                    wanted_roles.append(r)
        source_shas = []
        for role in wanted_roles:
            cands = [r for r in skill["references"] if r["role"] == role and r.get("approved")]
            if not cands:
                raise Blocked("REQUIRED_STYLE_REFERENCE_MISSING", role)
            r = sorted(cands, key=lambda x: (x.get("priority", 100), x["ref_id"]))[0]
            p = Path(skill["folder"]) / "references" / r["path"]
            refs.append((role, r["sha256"], "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()))
            ref_trace.append({"role": role, "sha256": r["sha256"], "ref_id": r["ref_id"], "authority": "SKILL_REFERENCE",
                              "source_witness_id": r.get("source_witness_id"), "source_film_sha256": r.get("source_film_sha256")})
            if r.get("source_film_sha256"):
                source_shas.append(r["source_film_sha256"])
        stages = [{"stage": 1, "operator": node["operator"], "reference_count": len(refs)}]
        max_refs = int(caps.get("max_reference_images", 0))
        if len(refs) > max_refs:
            if skill["reference_overflow_policy"] == "STAGED_EDIT" and "imageEdit" in caps.get("supported_capabilities", []):
                stages = [{"stage": 1, "operator": node["operator"], "reference_count": max_refs, "refs": [r[1] for r in refs[:max_refs]]},
                          {"stage": 2, "operator": "op.region_edit", "reference_count": len(refs) - max_refs + 1,
                           "refs": ["<stage1_output>"] + [r[1] for r in refs[max_refs:]],
                           "note": "remaining required references applied by a staged guided edit, never dropped"}]
                refs_stage1 = refs[:max_refs]
            else:
                raise Blocked("PROVIDER_REF_LIMIT", f"{len(refs)} required references > provider max {max_refs}")
        else:
            refs_stage1 = refs
        # negatives
        neg_trace, negative_text = [], None
        negs = [c for c in skill["negative_clauses"] if c["decision_id"] in selected and c.get("operation_id") == node["operator"]]
        if negs:
            if caps.get("supports_negative_prompt"):
                negative_text = "\n".join(self._render_clause(c["template"], brief.slots) for c in sorted(negs, key=lambda c: (c.get("priority", 100), c["id"])))
                neg_trace = [{"clause_id": c["id"], "sent": True} for c in negs]
            else:
                hi = [c["id"] for c in negs if c.get("high_impact")]
                if hi:
                    raise Blocked("NEGATIVE_UNREPRESENTABLE", f"provider has no negative prompt for high-impact {hi}")
                neg_trace = [{"clause_id": c["id"], "sent": False, "reason": "provider has no negative prompt field"} for c in negs]
        # output contract
        oc = output_contract or node.get("output_contract") or {}
        for k in ("width", "height", "format", "asset_kind"):
            if k not in oc:
                raise Blocked("OUTPUT_CONTRACT_MISSING", k)
        w, h = oc["width"], oc["height"]
        mult = caps.get("dimension_multiple", 1)
        if not (caps["min_dimension"] <= w <= caps["max_dimension"] and caps["min_dimension"] <= h <= caps["max_dimension"]):
            raise Blocked("PROVIDER_DIMENSION_RANGE", f"{w}x{h}")
        if w % mult or h % mult:
            raise Blocked("PROVIDER_DIMENSION_MULTIPLE", f"{w}x{h} not multiple of {mult}")
        if oc["format"] not in caps.get("output_formats", []):
            raise Blocked("PROVIDER_OUTPUT_FORMAT", oc["format"])
        prompt = "\n".join(s["text"] for s in segs)
        if len(prompt) > caps["max_prompt_chars"]:
            raise Blocked("PROMPT_LIMIT", f"{len(prompt)} > {caps['max_prompt_chars']} (never truncated)")
        payload = {"taskType": "imageInference", "model": caps["model_air_id"], "positivePrompt": prompt,
                   "width": w, "height": h, "numberResults": 1, "outputType": caps.get("output_type", "base64Data"),
                   "outputFormat": oc["format"], "includeCost": True}
        ownership = {"includeCost": "TECHNICAL:cost_reporting", "taskType": "TECHNICAL:provider_adapter", "model": "TECHNICAL:user_confirmed_model_air_id",
                     "positivePrompt": "SEGMENTS", "width": "TECHNICAL:output_contract", "height": "TECHNICAL:output_contract",
                     "numberResults": "TECHNICAL:fixed", "outputType": "TECHNICAL:provider_caps", "outputFormat": "TECHNICAL:output_contract"}
        if refs_stage1:
            payload["inputs"] = {"referenceImages": [r[2] for r in refs_stage1]}
            ownership["inputs"] = "SKILL_REFERENCE_ROLES+APPROVED_IDENTITY"
        if negative_text is not None:
            payload["negativePrompt"] = negative_text
            ownership["negativePrompt"] = "SKILL_NEGATIVE_CLAUSES"
        for k, v in sorted(skill["provider_parameters"].items()):
            if k not in caps.get("allowed_parameters", []):
                raise Blocked("UNSUPPORTED_PROVIDER_PARAMETER", k)
            payload[k] = v
            ownership[k] = f"SKILL_PROVIDER_PARAMETER:{skill['skill_hash'][:12]}"
        # Self-check: every selected clause's rendered text must be present in the provider-visible payload.
        dropped = [s["clause_id"] for s in segs if s["authority"] == "STYLE" and s["text"] not in prompt]
        expected = [cid for cid in clause_ids]
        present = [s["clause_id"] for s in segs if s["authority"] == "STYLE"]
        if dropped or present != [x[1] for x in sorted(style_segs, key=lambda x: (x[0], x[1]))] or set(present) != set(expected):
            raise Blocked("SELECTED_CLAUSE_DROPPED_FROM_PAYLOAD", str(dropped or sorted(set(expected) - set(present))))
        correct_prompt = "\n".join(s["text"] if s["authority"] != "STYLE" else
                                   self._default_render(clause_by_id[s["clause_id"]]["template"], brief.slots) for s in segs)
        for s in segs:
            if s["authority"] == "STYLE":
                c = clause_by_id[s["clause_id"]]
                if s["text"] != self._default_render(c["template"], brief.slots):
                    raise Blocked("SELECTED_CLAUSE_ALTERED_IN_PAYLOAD", s["clause_id"],
                                  expected=self._default_render(c["template"], brief.slots), actual=s["text"],
                                  payload_prompt_before=correct_prompt, payload_prompt_after=prompt)
        audit = interface_two_audit(payload, ownership, segs)
        if not audit["ok"]:
            raise Blocked("PROMPT_AUTHORITY_VIOLATION", str(audit["problems"][:3]))
        eligible_not_selected = []
        for did, d in decisions.items():
            if did in selected or d.get("status") == "RESEARCH_ONLY":
                continue
            br = _select_branch(d, conditions, node["operator"])
            if br and node["operator"] in br.get("operation_node_ids", []) and d.get("must_apply_when_matching"):
                eligible_not_selected.append(did)
        sar = style_authority_report(
            "pending", controlled=[f"{did}:{selected[did]['branch'].get('clause_ids')}" for did in sorted(selected)],
            missing_from_skill=[], not_compiled=eligible_not_selected, outside_authority=[],
            model_inventions=[d["decision_id"] for d in skill["decisions"] if d.get("status") == "RESEARCH_ONLY"],
            ungoverned_output=[], content_choices=[f"slots.{k}" for k in sorted(brief.slots)])
        if eligible_not_selected:
            raise Blocked("SKILL_PRESENT_BUT_NOT_COMPILED", str(eligible_not_selected))
        trace = {"compiler_version": COMPILER_VERSION, "brief_id": brief.brief_id, "brief_hash": brief_hash(brief),
                 "skill_id": skill["skill_id"], "skill_version": skill["version"], "skill_hash": skill["skill_hash"],
                 "skill_status": skill["status"], "recipe_id": recipe_id, "node_id": node_id, "operator": node["operator"],
                 "selected_decisions": sorted(selected),
                 "selected_branches": {did: selected[did]["branch"]["when"] for did in sorted(selected)},
                 "clause_ids": [s["clause_id"] for s in segs if s["authority"] == "STYLE"], "segments": segs,
                 "reference_trace": ref_trace, "stages": stages, "negative_trace": neg_trace, "field_ownership": ownership,
                 "interface_two_audit": audit, "scene_art_plan": plan, "scene_art_plan_sha": digest(plan),
                 "caps_snapshot_id": caps.get("snapshot_id"), "caps_sha": digest(caps), "conditions": conditions,
                 "requires_source_upload_consent_for": sorted(set(source_shas)),
                 "authority": {"style": "frozen_skill_clauses", "content": "original_brief_slots",
                               "identity": "approved_identity_assets", "technical": "provider_capabilities"},
                 "style_authority_report": sar, "skill_present_but_not_compiled": eligible_not_selected,
                 "runtime_style_invention_prohibited": True,
                 "skill_evidence_origin": skill["manifest"].get("evidence_origin", "SYNTHETIC_FIXTURE" if skill["synthetic"] else "REAL_VLM")}
        inputs = {"brief": raw_brief, "skill_folder": str(skill_folder), "pinned_skill_hash": pinned_skill_hash,
                  "recipe_id": recipe_id, "node_id": node_id, "caps": caps,
                  "identity_assets": {k: {kk: vv for kk, vv in v.items()} for k, v in identity_assets.items()},
                  "output_contract": output_contract}
        logical = {"payload": payload, "refs": [(r[0], r[1]) for r in refs_stage1], "trace_core": {
            k: trace[k] for k in ("brief_hash", "skill_hash", "selected_decisions", "clause_ids", "node_id", "caps_sha")}}
        lsha = digest(logical)
        trace["style_authority_report"]["job_id"] = f"job_{lsha[:20]}"
        return CompiledImageJob(f"job_{lsha[:20]}", payload, tuple(refs_stage1), trace, inputs,
                                bool(skill["synthetic"]), False, lsha, _ISSUER)

    def compile_baseline(self, raw_brief: dict, *, caps: dict, output_contract: dict) -> CompiledImageJob:
        """BASELINE_ONLY: explicit unspecialised comparison path; never promotable as learned style (11, 15 §6)."""
        brief = validate_brief(raw_brief)
        segs = [{"authority": "CONTENT", "brief_field_path": f"slots.{k}", "text": f"{label}: {_escape(brief.slots[k])}"}
                for k, label in CONTENT_LABELS if k in brief.slots]
        prompt = "\n".join(s["text"] for s in segs)
        oc = output_contract
        payload = {"taskType": "imageInference", "model": caps["model_air_id"], "positivePrompt": prompt, "width": oc["width"],
                   "height": oc["height"], "numberResults": 1, "outputType": caps.get("output_type", "base64Data"),
                   "outputFormat": oc["format"], "includeCost": True}
        trace = {"compiler_version": COMPILER_VERSION, "mode": "BASELINE_ONLY", "brief_hash": brief_hash(brief), "segments": segs,
                 "selected_decisions": [], "clause_ids": [], "promotable": False, "caps_sha": digest(caps)}
        lsha = digest({"payload": payload, "baseline": True})
        return CompiledImageJob(f"baseline_{lsha[:20]}", payload, tuple(), trace,
                                {"brief": raw_brief, "caps": caps, "output_contract": output_contract, "baseline": True},
                                False, True, lsha, _ISSUER)


def recompile(job: CompiledImageJob) -> CompiledImageJob:
    """Deterministic recompilation from the job's own pinned inputs (used by the gateway as a tamper check)."""
    c = StyleProgramCompiler()
    i = job.inputs
    if i.get("baseline"):
        return c.compile_baseline(i["brief"], caps=i["caps"], output_contract=i["output_contract"])
    return c.compile(i["brief"], i["skill_folder"], pinned_skill_hash=i["pinned_skill_hash"], recipe_id=i["recipe_id"],
                     node_id=i["node_id"], caps=i["caps"], identity_assets=i["identity_assets"], output_contract=i["output_contract"])


def payload_diff(a: dict, b: dict) -> dict:
    keys = sorted(set(a) | set(b))
    out: dict[str, Any] = {}
    for k in keys:
        if a.get(k) != b.get(k):
            if k == "positivePrompt":
                la, lb = (a.get(k) or "").split("\n"), (b.get(k) or "").split("\n")
                out[k] = {"removed": [x for x in la if x not in lb], "added": [x for x in lb if x not in la]}
            elif k == "inputs":
                out[k] = {"before_refs": len((a.get(k) or {}).get("referenceImages", [])),
                          "after_refs": len((b.get(k) or {}).get("referenceImages", []))}
            else:
                out[k] = {"before": a.get(k), "after": b.get(k)}
    return out
