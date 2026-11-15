"""Visual-model completeness (Addendum 27 §1, §3, §6): coverage ledger, reverse construction planner,
completeness investigator and `review_visual_model_completeness`.

The 18 dimensions and 6 relation seeds are SEARCH dimensions, not answers. Unknown phenomena
become dynamic extensions. The review finds multiple gaps, then routes ONE question at a time.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field

from ..util import Blocked, digest, new_id, now_iso

DIMENSIONS = ("WHOLE_FRAME_LANGUAGE", "ORIGINAL_SUBJECT_DESIGN", "CHARACTER_WHOLE_DESIGN", "CHARACTER_FACE_ACTING",
              "CHARACTER_BODY_HAND_CONTACT", "SHAPE_SURFACE_DETAIL", "COLOUR_RELATIONS", "MATERIAL_LIGHT_FINISH",
              "WORLD_ASSEMBLY", "SUBJECT_WORLD_INTEGRATION", "DEPTH_VIEWPOINT", "ART_STATE_TRANSFORMATION", "MOTION_ACTING",
              "SIMULTANEOUS_CHOREOGRAPHY", "TRANSITIONS_VISUAL_GRAMMAR", "GRAPHICS_EXPLANATORY_VISUALS", "VISUAL_AUDIO_TIMING",
              "FINISH_AND_READABILITY")
DIM_STATUSES = ("RELEVANT_SUPPORTED", "RELEVANT_UNKNOWN", "NOT_VISIBLE", "NOT_APPLICABLE_WITH_REASON", "PENDING_SOURCE", "CONTRADICTED")
REL_STATUSES = ("SUPPORTED", "UNKNOWN", "CONTRADICTED", "NOT_APPLICABLE_WITH_REASON")
RELATION_SEEDS = {
    "part_to_whole": ("ORIGINAL_SUBJECT_DESIGN", "SHAPE_SURFACE_DETAIL", "MATERIAL_LIGHT_FINISH", "WORLD_ASSEMBLY"),
    "identity_over_states": ("CHARACTER_WHOLE_DESIGN", "CHARACTER_FACE_ACTING", "ART_STATE_TRANSFORMATION", "MATERIAL_LIGHT_FINISH"),
    "depth_and_attention": ("SUBJECT_WORLD_INTEGRATION", "DEPTH_VIEWPOINT", "FINISH_AND_READABILITY"),
    "concurrent_action": ("MOTION_ACTING", "SIMULTANEOUS_CHOREOGRAPHY", "CHARACTER_BODY_HAND_CONTACT"),
    "transition_between_worlds": ("TRANSITIONS_VISUAL_GRAMMAR", "ART_STATE_TRANSFORMATION", "WORLD_ASSEMBLY"),
    "cross_subject_identity": ("WHOLE_FRAME_LANGUAGE", "ORIGINAL_SUBJECT_DESIGN", "CHARACTER_WHOLE_DESIGN"),
}
GAP_ORDER = ("MISSING_SOURCE", "CONTRADICTED", "MISSING_DECISION", "MISSING_JOINT_DECISION", "MISSING_OPERATION",
             "PROMPT_AUTHORITY")
REVIEW_STATES = ("READY_FOR_ORIGINAL_IMAGE_TRIAL", "BLOCKED_MISSING_SOURCE", "BLOCKED_MISSING_STYLE_DECISION",
                 "BLOCKED_MISSING_OPERATION", "BLOCKED_PROMPT_AUTHORITY", "PARTIAL_CAPABILITY_ONLY", "ARTISTIC_QUALITY_UNPROVEN")


def new_ledger(scope_id: str, sequence_ids: list[str]) -> dict:
    return {"record_type": "VisualModelCoverageLedger", "scope_id": scope_id, "sequence_ids": list(sequence_ids),
            "dimensions": [], "relations": [], "extensions": [], "open_gaps": [], "frame_coverage_state": "NOT_STARTED"}


def set_dimension(ledger: dict, dimension: str, status: str, *, evidence: list, why_relevant: str,
                  missing_decisions: list | None = None, production_consumers: list | None = None,
                  connected_dimensions: list | None = None, inapplicability_reason: str | None = None) -> dict:
    if status not in DIM_STATUSES:
        raise Blocked("BAD_DIMENSION_STATUS", status)
    if status == "NOT_APPLICABLE_WITH_REASON" and not inapplicability_reason:
        raise Blocked("NOT_APPLICABLE_NEEDS_REASON", dimension)
    entry = {"dimension": dimension, "status": status, "evidence": evidence, "why_relevant": why_relevant,
             "missing_decisions": missing_decisions or [], "production_consumers": production_consumers or [],
             "connected_dimensions": connected_dimensions or [], "inapplicability_reason": inapplicability_reason}
    target = ledger["dimensions"] if dimension in DIMENSIONS else ledger["extensions"]
    target[:] = [e for e in target if e["dimension"] != dimension] + [entry]
    return entry


def add_extension(ledger: dict, phenomenon: str, *, evidence: list, why_relevant: str, connected: list) -> dict:
    """A visible phenomenon outside the 18 dimensions gets its own entry; never forced into a category."""
    name = "EXT_" + "".join(ch if ch.isalnum() else "_" for ch in phenomenon.upper())[:48]
    if name in DIMENSIONS:
        raise Blocked("EXTENSION_SHADOWS_DIMENSION")
    return set_dimension(ledger, name, "RELEVANT_UNKNOWN", evidence=evidence, why_relevant=why_relevant,
                         missing_decisions=[f"decision for {phenomenon}"], connected_dimensions=connected)


def set_relation(ledger: dict, relation_id: str, participants: list, status: str, *, evidence: list,
                 producing_effect: str, missing_decisions: list | None = None) -> dict:
    if status not in REL_STATUSES:
        raise Blocked("BAD_RELATION_STATUS", status)
    if status == "SUPPORTED" and not evidence:
        raise Blocked("SUPPORTED_RELATION_WITHOUT_WITNESS", relation_id)   # R10: no empty-evidence joint support
    e = {"relation_id": relation_id, "participants": sorted(participants), "evidence": evidence, "status": status,
         "producing_effect": producing_effect, "missing_decisions": missing_decisions or []}
    ledger["relations"][:] = [r for r in ledger["relations"] if r["relation_id"] != relation_id] + [e]
    return e


# ---- reverse construction -----------------------------------------------------------------
@dataclass
class OriginalScope:
    scope_id: str
    subjects: list            # [{id, kind: character|object|world, role, view, view_changes, face_visible, actions, contact_props, lighting_changes}]
    world: dict               # {kind, layers, lighting}
    camera: dict = field(default_factory=dict)    # {moves: [...], scale_change: bool}
    events: list = field(default_factory=list)    # [{id, actors, kind}]
    transitions: list = field(default_factory=list)
    graphics: bool = False
    audio_cues: bool = False
    salient_features: list = field(default_factory=list)  # [{feature, dimensions, salience}]

    def to_dict(self) -> dict:
        return asdict(self)


def reverse_plan(scope: OriginalScope) -> dict:
    """Finished original frame/event → required assets, appearance choices, joint choices and operations."""
    choices, joints, assets = [], [], []

    def need(cid, dims, asset, op, salience="HIGH", conditions=None):
        choices.append({"choice_id": cid, "dimensions": list(dims), "asset": asset, "operation_kind": op,
                        "salience": salience, "conditions": conditions or dict(envc)})

    w = scope.world or {}
    envc = {"environment": w.get("kind")} if w.get("kind") else {}
    for d in ("WHOLE_FRAME_LANGUAGE", "FINISH_AND_READABILITY"):
        need(f"frame:{d}", [d], "whole_scene", "whole_scene", conditions=envc)
    assets.append({"asset": "whole_scene", "kind": "WHOLE_SCENE"})
    need("world:assembly", ["WORLD_ASSEMBLY"], "whole_scene", "whole_scene", conditions={"environment": w.get("kind")})
    need("world:colour", ["COLOUR_RELATIONS"], "whole_scene", "whole_scene", conditions=envc)
    need("world:material_light", ["MATERIAL_LIGHT_FINISH"], "whole_scene", "whole_scene", conditions=envc)
    if w.get("layers"):
        assets.append({"asset": "world_layers", "kind": "LAYER"})
        need("world:layers", ["WORLD_ASSEMBLY", "DEPTH_VIEWPOINT"], "world_layers", "layer_extract")
        joints.append({"joint_id": "world_layers+viewpoint", "dimensions": ["WORLD_ASSEMBLY", "DEPTH_VIEWPOINT"], "seed": "depth_and_attention"})
    if any(s.get("kind") == "character" for s in scope.subjects):
        # separate clean world plate so a separately produced actor is never duplicated over a scene that contains it (R18)
        assets.append({"asset": "world_plate", "kind": "WORLD_PLATE"})
        need("world:clean_plate", ["WORLD_ASSEMBLY"], "world_plate", "world_plate", conditions={"environment": w.get("kind")})
    for s in scope.subjects:
        sid = s["id"]
        cond = {k: s[k] for k in ("view", "role") if s.get(k)}
        cond["subject_kind"] = s.get("subject_kind", s.get("kind"))
        if s.get("kind") == "character":
            assets.append({"asset": f"{sid}:canonical", "kind": "CHARACTER_CANONICAL"})
            need(f"{sid}:whole_design", ["CHARACTER_WHOLE_DESIGN"], f"{sid}:canonical", "canonical_character", conditions=cond)
            need(f"{sid}:integration", ["SUBJECT_WORLD_INTEGRATION"], "whole_scene", "whole_scene", conditions=cond)
            joints.append({"joint_id": f"{sid}:character+world", "dimensions": ["CHARACTER_WHOLE_DESIGN", "SUBJECT_WORLD_INTEGRATION"],
                           "seed": "cross_subject_identity"})
            if s.get("face_visible"):
                need(f"{sid}:face", ["CHARACTER_FACE_ACTING"], f"{sid}:canonical", "canonical_character", conditions=cond)
            if s.get("view_changes"):
                assets.append({"asset": f"{sid}:view_state", "kind": "CHARACTER_STATE"})
                need(f"{sid}:view_state", ["DEPTH_VIEWPOINT", "ART_STATE_TRANSFORMATION"], f"{sid}:view_state", "guided_pose_edit",
                     conditions={**cond, "view": s["view_changes"][-1]})
                if s.get("face_visible"):
                    joints.append({"joint_id": f"{sid}:face+view", "dimensions": ["CHARACTER_FACE_ACTING", "DEPTH_VIEWPOINT"],
                                   "seed": "identity_over_states"})
                    if s.get("lighting_changes") or w.get("lighting") == "directional":
                        joints.append({"joint_id": f"{sid}:face+view+light",
                                       "dimensions": ["CHARACTER_FACE_ACTING", "DEPTH_VIEWPOINT", "MATERIAL_LIGHT_FINISH"],
                                       "seed": "identity_over_states"})
            for prop in s.get("contact_props", []):
                assets.append({"asset": f"{sid}:grip:{prop}", "kind": "CHARACTER_STATE"})
                need(f"{sid}:grip:{prop}", ["CHARACTER_BODY_HAND_CONTACT"], f"{sid}:grip:{prop}", "guided_pose_edit",
                     conditions={**cond, "action": "grip"})
                joints.append({"joint_id": f"{sid}:contact+light", "dimensions": ["CHARACTER_BODY_HAND_CONTACT", "MATERIAL_LIGHT_FINISH"],
                               "seed": "concurrent_action"})
            if s.get("actions"):
                need(f"{sid}:acting", ["MOTION_ACTING"], f"{sid}:canonical", "motion_render", conditions=cond)
        else:
            assets.append({"asset": f"{sid}:object", "kind": "PROP"})
            need(f"{sid}:design", ["ORIGINAL_SUBJECT_DESIGN", "SHAPE_SURFACE_DETAIL"], f"{sid}:object", "whole_scene", conditions=cond)
            joints.append({"joint_id": f"{sid}:part_to_whole", "dimensions": ["ORIGINAL_SUBJECT_DESIGN", "MATERIAL_LIGHT_FINISH"],
                           "seed": "part_to_whole"})
    cam = scope.camera or {}
    if cam.get("moves"):
        need("camera:depth", ["DEPTH_VIEWPOINT"], "world_layers", "motion_render")
        if cam.get("scale_change"):
            need("camera:state_change", ["ART_STATE_TRANSFORMATION", "DEPTH_VIEWPOINT"], "whole_scene", "whole_scene")
            joints.append({"joint_id": "camera+art_states", "dimensions": ["DEPTH_VIEWPOINT", "ART_STATE_TRANSFORMATION"],
                           "seed": "transition_between_worlds"})
    if len({a for e in scope.events for a in e.get("actors", [])}) > 1:
        need("events:choreography", ["SIMULTANEOUS_CHOREOGRAPHY"], "scene_graph", "motion_render")
    if scope.transitions:
        need("transitions", ["TRANSITIONS_VISUAL_GRAMMAR"], "scene_graph", "motion_render")
    if scope.graphics:
        need("graphics", ["GRAPHICS_EXPLANATORY_VISUALS"], "graphics_layer", "layer_extract", salience="MEDIUM")
    if scope.audio_cues:
        need("audio_timing", ["VISUAL_AUDIO_TIMING"], "scene_graph", "motion_render", salience="MEDIUM")
    for f in scope.salient_features:
        need(f"salient:{f['feature']}", f["dimensions"], f.get("asset", "whole_scene"), f.get("operation", "whole_scene"),
             salience=f.get("salience", "HIGH"))
    required_dims = sorted({d for c in choices for d in c["dimensions"]})
    return {"scope_id": scope.scope_id, "assets": assets, "choices": choices, "joint_choices": joints,
            "required_dimensions": required_dims, "plan_sha": digest([choices, joints])}


# ---- investigator -------------------------------------------------------------------------
def owns(d: dict, key: str, dims) -> bool:
    """Production-choice ownership (R10). Evidence-authored decisions own ONLY the choice/joint ids they declare;
    sharing a dimension tag is never ownership. Legacy fixture decisions (no `owned_choice_ids`) fall back to the
    dimension cover and are labelled CATEGORY_LEVEL_LEGACY in coverage traces."""
    if d.get("status") == "RESEARCH_ONLY":
        return False
    if "owned_choice_ids" in d:
        return key in d["owned_choice_ids"] and set(dims) <= set(d.get("dimension_tags", []))
    return set(dims) <= set(d.get("dimension_tags", []))


def _owner_for(choice: dict, decisions: list[dict], registered_ops: dict) -> tuple[str | None, str | None]:
    """Return (decision_id, problem) where problem in {None, MISSING_DECISION, MISSING_OPERATION}."""
    cands = [d for d in decisions if owns(d, choice["choice_id"], choice["dimensions"])]
    if not cands:
        return None, "MISSING_DECISION"
    for d in cands:
        for br in d.get("branches", []):
            when = br.get("when", {})
            # Unknown predicates must not be ignored: that made an action=grip
            # branch qualify a view=profile requirement (vacuous all([])).
            if when and all(k in choice["conditions"] and str(choice["conditions"][k]) == str(v)
                            for k, v in when.items()):
                ops = br.get("operation_node_ids", [])
                if ops and all(o in registered_ops for o in ops):
                    return d["decision_id"], None
                return d["decision_id"], "MISSING_OPERATION"
    return cands[0]["decision_id"], "MISSING_DECISION"  # no branch for these conditions


class VisualModelCompletenessInvestigator:
    def __init__(self, registered_ops: dict):
        self.ops = registered_ops

    def investigate(self, ledger: dict, plan: dict, decisions: list[dict], *, unexplained_phenomena: list | None = None) -> list[dict]:
        gaps: list[dict] = []

        def gap(kind, what, dims, salience="HIGH", **kw):
            gaps.append({"gap_id": f"G{len(gaps):03d}_{kind}", "kind": kind, "what": what, "dimensions": sorted(dims),
                         "salience": salience, **kw})

        if ledger["frame_coverage_state"] in ("NOT_STARTED", "PARTIAL", "NEEDS_REINSPECTION"):
            gap("MISSING_SOURCE", f"selected-frame coverage is {ledger['frame_coverage_state']}", [], source_scope="frames")
        by_dim = {e["dimension"]: e for e in ledger["dimensions"] + ledger["extensions"]}
        req = set(plan["required_dimensions"])
        for d in DIMENSIONS:
            e = by_dim.get(d)
            if d in req and e is None:
                gap("MISSING_SOURCE", f"{d} required by scope but never investigated", [d])
                continue
            if e is None:
                continue
            st = e["status"]
            if st == "NOT_APPLICABLE_WITH_REASON" and d in req:
                gap("CONTRADICTED", f"{d} marked not applicable but the original scope requires it ({e.get('inapplicability_reason')})", [d])
            elif st in ("NOT_VISIBLE", "PENDING_SOURCE") and d in req:
                gap("MISSING_SOURCE", f"{d} {st} in selected sources but required by scope", [d])
            elif st == "RELEVANT_UNKNOWN":
                gap("MISSING_DECISION", f"{d} relevant but unknown: {e.get('missing_decisions')}", [d])
            elif st == "CONTRADICTED":
                gap("CONTRADICTED", f"{d} evidence contradicts current model", [d])
            elif st == "RELEVANT_SUPPORTED":
                cons = e.get("production_consumers", [])
                if not cons or any(c not in self.ops for c in cons):
                    gap("MISSING_OPERATION", f"{d} SOURCE_SUPPORTED / OPERATION_MISSING ({cons})", [d])
        for e in ledger["extensions"]:
            if e["status"] == "RELEVANT_UNKNOWN":
                gap("MISSING_DECISION", f"extension {e['dimension']}: {e['why_relevant']}", [e["dimension"]] + e.get("connected_dimensions", []))
        for ph in unexplained_phenomena or []:
            ext = add_extension(ledger, ph["phenomenon"], evidence=ph.get("evidence", []), why_relevant=ph["why"],
                                connected=ph.get("connected", []))
            gap("MISSING_DECISION", f"new phenomenon {ext['dimension']}", [ext["dimension"]], extension=True)
        # relationship sweep: each joint choice needs a SUPPORTED relation AND one decision owning all its dimensions
        rels = ledger["relations"]
        for j in plan["joint_choices"]:
            dims = set(j["dimensions"])
            rel_ok = any(r["status"] == "SUPPORTED" and dims <= set(r["participants"]) and r.get("evidence") for r in rels)
            owner = [d for d in decisions if owns(d, j["joint_id"], dims)]
            if not rel_ok or not owner:
                gap("MISSING_JOINT_DECISION", f"no {'supported relation' if not rel_ok else 'joint decision'} for {j['joint_id']}",
                    dims, joint_id=j["joint_id"], seed=j["seed"],
                    individually_supported=all(by_dim.get(x, {}).get("status") == "RELEVANT_SUPPORTED" for x in dims))
        # reverse construction: every high-salience appearance choice must have an owner + operation
        for c in plan["choices"]:
            did, prob = _owner_for(c, decisions, self.ops)
            if prob:
                gap(prob, f"appearance choice {c['choice_id']} has no {'owning decision' if prob == 'MISSING_DECISION' else 'registered operation'}",
                    c["dimensions"], salience=c["salience"], choice_id=c["choice_id"], decision_id=did, conditions=c["conditions"])
        return _dedupe(gaps)


def _dedupe(gaps: list[dict]) -> list[dict]:
    seen, out = set(), []
    for g in gaps:
        k = (g["kind"], tuple(g["dimensions"]), g.get("joint_id"), g.get("choice_id"))
        if k not in seen:
            seen.add(k)
            out.append(g)
    return out


def cluster_gaps(gaps: list[dict]) -> list[list[str]]:
    """Connected components over shared dimensions (dependency clustering, §6 step 6)."""
    parent = {g["gap_id"]: g["gap_id"] for g in gaps}

    def f(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i, a in enumerate(gaps):
        for b in gaps[i + 1:]:
            if set(a["dimensions"]) & set(b["dimensions"]):
                parent[f(a["gap_id"])] = f(b["gap_id"])
    comps: dict[str, list] = {}
    for g in gaps:
        comps.setdefault(f(g["gap_id"]), []).append(g["gap_id"])
    return sorted(comps.values(), key=len, reverse=True)


def choose_controlling_gap(gaps: list[dict]) -> dict | None:
    high = [g for g in gaps if g["salience"] == "HIGH"] or gaps
    if not high:
        return None
    return sorted(high, key=lambda g: (GAP_ORDER.index(g["kind"]), -len(g["dimensions"]), g["gap_id"]))[0]


def dynamic_question_ticket(g: dict, ledger: dict) -> dict:
    ev = []
    for e in ledger["dimensions"] + ledger["extensions"]:
        if e["dimension"] in g["dimensions"]:
            ev.extend(e.get("evidence", []))
    for r in ledger["relations"]:
        if set(g["dimensions"]) & set(r["participants"]):
            ev.extend(r.get("evidence", []))
    dims = " + ".join(g["dimensions"]) or "source frames"
    if g["kind"] == "MISSING_JOINT_DECISION":
        q = (f"In the witnessed frames, how do {dims} change TOGETHER for {g.get('joint_id')} — which choice must the producer "
             f"make jointly (rather than per category) so a new subject keeps the quality, and which operation renders it?")
        effects = ["joint branch added to one decision owning all dimensions → single guided edit carries it",
                   "relation shown to be independent → separate decisions remain, relation marked NOT_APPLICABLE_WITH_REASON"]
    elif g["kind"] == "MISSING_OPERATION":
        q = f"Which provider-supported operation can construct the supported {dims} decision for a new subject, with what inputs and output asset?"
        effects = ["registered operation found → decision becomes EXECUTABLE_CANDIDATE", "none exists → capability NOT_READY"]
    elif g["kind"] == "MISSING_SOURCE":
        q = f"Which exact source frames/crops/contrasts must be inspected to observe {dims} before any decision is written?"
        effects = ["evidence found → ledger entry RELEVANT_SUPPORTED/UNKNOWN with witnesses", "absent in corpus → expand sources or NOT_READY"]
    elif g["kind"] == "CONTRADICTED":
        q = f"Which witness resolves the contradiction for {dims} between the ledger status and the original scope's requirement?"
        effects = ["scope genuinely needs it → reinvestigate", "scope does not need it → correct scope with reason"]
    else:
        q = (f"For the new original subject under {g.get('conditions') or 'the scope conditions'}, what choice must the producer make "
             f"about {dims} to obtain the witnessed quality, and how do unlike witnesses constrain it?")
        effects = ["choice invariant → one branch/clause", "choice adapts → conditional branches with distinct clauses/references"]
    return {"question_id": new_id("dq"), "blocking_gap_id": g["gap_id"], "missing_artistic_decision": g["what"],
            "source_evidence_to_inspect": ev, "actual_question": q, "possible_answer_effects": effects,
            "next_action": f"resolve {g['gap_id']} then recompute the COMPLETE coverage review"}


def review_visual_model_completeness(ledger: dict, scope: OriginalScope, decisions: list[dict], registered_ops: dict, *,
                                     prompt_authority_ok: bool = True, unexplained_phenomena: list | None = None,
                                     provenance_report_id: str | None = None) -> dict:
    plan = reverse_plan(scope)
    inv = VisualModelCompletenessInvestigator(registered_ops)
    gaps = inv.investigate(ledger, plan, decisions, unexplained_phenomena=unexplained_phenomena)
    if not prompt_authority_ok:
        gaps.append({"gap_id": f"G{len(gaps):03d}_PROMPT_AUTHORITY", "kind": "PROMPT_AUTHORITY", "what": "prompt authority audit failed",
                     "dimensions": [], "salience": "HIGH"})
    ledger["open_gaps"] = [g["gap_id"] + ": " + g["what"] for g in gaps]
    ctrl = choose_controlling_gap(gaps)
    high = [g for g in gaps if g["salience"] == "HIGH"]
    if not gaps:
        state = "READY_FOR_ORIGINAL_IMAGE_TRIAL"
    elif not high:
        state = "PARTIAL_CAPABILITY_ONLY"
    else:
        assert ctrl is not None
        k = ctrl["kind"]
        state = {"MISSING_SOURCE": "BLOCKED_MISSING_SOURCE", "CONTRADICTED": "BLOCKED_MISSING_SOURCE",
                 "MISSING_DECISION": "BLOCKED_MISSING_STYLE_DECISION", "MISSING_JOINT_DECISION": "BLOCKED_MISSING_STYLE_DECISION",
                 "MISSING_OPERATION": "BLOCKED_MISSING_OPERATION", "PROMPT_AUTHORITY": "BLOCKED_PROMPT_AUTHORITY"}[k]
    ticket = dynamic_question_ticket(ctrl, ledger) if ctrl else None
    review = {"record_type": "CoverageReview", "scope_id": scope.scope_id, "coverage_ledger_id": digest(ledger)[:16],
              "state": state, "gaps": [g["gap_id"] + ": " + g["what"] for g in gaps],
              "next_question_id": ticket["question_id"] if ticket else None,
              "image_trial_ready": state == "READY_FOR_ORIGINAL_IMAGE_TRIAL", "provenance_report_id": provenance_report_id}
    return {"review": review, "gap_details": gaps, "clusters": cluster_gaps(gaps), "controlling_gap": ctrl,
            "question_ticket": ticket, "reverse_plan": plan, "artistic_quality": "ARTISTIC_QUALITY_UNPROVEN",
            "scope_claim": "SCOPE_COVERED_WITH_KNOWN_LIMITS" if state == "READY_FOR_ORIGINAL_IMAGE_TRIAL" else state,
            "reviewed_at": now_iso()}
