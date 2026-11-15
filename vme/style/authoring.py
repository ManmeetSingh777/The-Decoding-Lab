"""REAL evidence → conditional decision → skill authoring (audit P0-3, task item 5).

Chain: source witnesses + contrasts (persisted VLM records) → visual design relation (answer facts, registered
as ObservedRelation with witness ids) → conditional production choice (answer BRANCHES) → branch/exception →
registered provider/edit operation → OWNED prompt clause whose text is DERIVED VERBATIM from the evidenced
branch action (no other aesthetic authority) → versioned skill folder + hash → deterministic compile.

What this module does NOT claim: that the evidenced relation is visually true or that the clause will make
good art. Every decision carries visual_truth = UNVERIFIED_UNTIL_ORIGINAL_ART_REVIEW. Lexical overlap is a
lint only; the structural derivation edge (clause == branch action) is what is enforced.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..util import Blocked, digest, now_iso
from ..investigation.evidence import Witness, WitnessBundle
from ..skills.operators import OPERATORS
from ..skills.skill import write_skill, skill_hash
from .decisions import witness_to_decision

SLOT_PLACEHOLDERS = {"{subject}": "${subject}", "{setting}": "${setting}", "{original_prop}": "${original_prop}"}


def json_key(d: dict) -> str:
    import json as _j
    return _j.dumps(d, sort_keys=True)


def decision_id_for(dims: list[str]) -> str:
    return "D-" + digest(sorted(dims))[:10]


def register_relations_from_answer(store, question: dict, answer: dict, dims: list[str]) -> list[str]:
    """Answer facts that cite real witnesses become ObservedRelation records (joint dims = the question's dims)."""
    ids = []
    for i, f in enumerate(answer.get("SOURCE_VISIBLE_FACTS") or []):
        wids = f.get("witness_ids") or []
        if not wids:
            continue
        rid = f"R-{question['question_id']}-{i}"
        ws = [store.get("Witness", w) for w in wids]
        if any(w is None for w in ws):
            raise Blocked("ANSWER_CITES_UNKNOWN_WITNESS", str(wids))
        films = {w["film_sha256"] for w in ws}
        store.put("ObservedRelation", rid, {"relation_id": rid, "relation": f["relation"], "witness_ids": wids, "dimensions": sorted(dims),
                                            "origin_type": "SOURCE_OBSERVED" if len(films) == 1 else "CROSS_SOURCE_INFERRED",
                                            "evidence_origin": ws[0].get("evidence_origin", "UNKNOWN"),
                                            "from_question": question["question_id"], "at": now_iso()})
        ids.append(rid)
    return ids


def author_decision(store, question: dict, answer: dict, *, dims: list[str], registered_ops: dict, required_branches: list[dict]) -> dict:
    """Build a ConditionalVisualDecision ONLY from the evidenced answer; unknowns stay RESEARCH_ONLY."""
    rel_ids = register_relations_from_answer(store, question, answer, dims)
    cited = sorted({w for f in answer.get("SOURCE_VISIBLE_FACTS") or [] for w in f.get("witness_ids", [])})
    contrast = [w for w in question.get("observed_contrast_with_witness_ids", []) if w not in cited]
    wrecs = [store.get("Witness", w) for w in cited + contrast]
    wrecs = [w for w in wrecs if w]
    if not wrecs:
        raise Blocked("NO_EVIDENCE_FOR_DECISION", question["question_id"])
    bundle = WitnessBundle(f"WB-{question['question_id']}", question["question_id"], answer.get("CONSTRUCTION_EXPLANATION", ""),
                           [Witness(**{k: v for k, v in w.items() if k in Witness.__dataclass_fields__}) for w in wrecs],
                           contrasting_witness_ids=contrast)
    did = decision_id_for(dims)
    prev = store.get("ConditionalVisualDecision", did)
    branches = []
    for i, b in enumerate(answer.get("BRANCHES") or []):
        op = b.get("operation_id")
        branches.append({"when": {k: str(v) for k, v in (b.get("when") or {}).items()}, "construction_action": b.get("construction_action", ""),
                         "clause_ids": [f"K-{did}-{i}@{op.split('.')[-1]}"] if op else [], "reference_role_ids": [],
                         "operation_node_ids": [op] if op else [], "priority": 10 + i})
    if prev:   # merge: branches evidenced by earlier answers stay unless re-answered for the same condition+operation
        keyset = {(json_key(b["when"]), tuple(b["operation_node_ids"])) for b in branches}
        for b in prev["branches"]:
            if (json_key(b["when"]), tuple(b["operation_node_ids"])) not in keyset:
                branches.append({**b, "clause_ids": [c for c in b["clause_ids"] if c.startswith(f"K-{did}-")][:1]})
        for i, b in enumerate(branches):
            b["priority"] = 10 + i
            op = b["operation_node_ids"][0] if b["operation_node_ids"] else None
            b["clause_ids"] = [f"K-{did}-{i}@{op.split('.')[-1]}"] if op else []
    missing = [rb for rb in required_branches if not any(all(br["when"].get(k) == str(v) for k, v in rb["conditions"].items())
                                                         and set(br["operation_node_ids"]) & set(rb["operation_ids"]) for br in branches)]
    proposal = {"decision_id": did, "version": int((store.get("ConditionalVisualDecision", did) or {}).get("version", 0)) + 1,
                "target_quality": question.get("exact_artistic_unknown", ""), "branches": branches,
                "invariant_visual_relation": answer.get("INVARIANT") or answer.get("CONSTRUCTION_EXPLANATION", ""),
                "adaptive_visual_choices": list(answer.get("ADAPTS_WITH") or []), "exceptions": list(answer.get("WHEN_NOT_APPLICABLE") or []),
                "creative_freedom": list(answer.get("CREATIVE_FREEDOM") or []), "dependencies": [],
                "forbidden_source_specific_copies": list(answer.get("FORBIDDEN_SOURCE_SPECIFIC") or []),
                "observed_relation_ids": sorted(set(rel_ids) | set((prev or {}).get("observed_relation_ids", []))), "expected_visible_effect": answer.get("WHY_THE_DECISION_MATTERS", ""),
                "uncertainty": list(answer.get("REMAINING_UNKNOWN") or []), "dimension_tags": sorted(dims),
                "origin_type": "CROSS_SOURCE_INFERRED" if len(bundle.films) > 1 else "SOURCE_OBSERVED"}
    d = witness_to_decision(bundle, proposal, registered_operators=registered_ops, substitutes=None).to_dict()
    if prev:
        d["evidence_frame_ids"] = sorted(set(d["evidence_frame_ids"]) | set(prev.get("evidence_frame_ids", [])))
    if missing and d["status"] != "RESEARCH_ONLY":
        d["status"], d["research_only_reason"] = "RESEARCH_ONLY", f"BRANCHES_MISSING_FOR:{missing}"
    d.update(visual_truth="UNVERIFIED_UNTIL_ORIGINAL_ART_REVIEW", authored_from_question=question["question_id"],
             evidence_origin=wrecs[0].get("evidence_origin", "UNKNOWN"), authored_at=now_iso())
    store.put("ConditionalVisualDecision", did, d)
    return d


def derive_clause_template(construction_action: str) -> str:
    """Structural derivation: the clause IS the evidenced branch action with content placeholders bound to slots."""
    t = construction_action.strip()
    for k, v in SLOT_PLACEHOLDERS.items():
        t = t.replace(k, v)
    if re.search(r"(?<!\$)\{[a-z_]+\}", t):
        raise Blocked("UNKNOWN_PLACEHOLDER_IN_ACTION", t[:80])
    return t


def author_skill(folder: str | Path, decisions: list[dict], *, skill_id: str, version: str, evidence_origin: str,
                 output_contracts: dict) -> dict:
    """Write a real skill folder: decisions.json + per-operation templates + recipe DAG, all derived from decisions."""
    usable = [d for d in decisions if d["status"] != "RESEARCH_ONLY"]
    if not usable:
        raise Blocked("NO_EXECUTABLE_DECISIONS")
    templates: dict = {}
    derivations = []
    for d in usable:
        for bi, br in enumerate(d["branches"]):
            for op in br["operation_node_ids"]:
                if op not in OPERATORS:
                    raise Blocked("UNKNOWN_OPERATOR", op)
                if OPERATORS[op]["backend"] != "provider":
                    continue
                cid = f"K-{d['decision_id']}-{bi}@{op.split('.')[-1]}"
                tmpl = derive_clause_template(br["construction_action"])
                templates.setdefault(op.split(".")[-1], {"clauses": [], "negative_clauses": []})["clauses"].append(
                    {"id": cid, "decision_id": d["decision_id"], "priority": br.get("priority", 100), "template": tmpl,
                     "allowed_content_slots": sorted(set(re.findall(r"\$\{([a-z_]+)\}", tmpl))), "reference_roles": [],
                     "operation_id": op, "origin_type": d["origin_type"],
                     "derivation": {"decision_id": d["decision_id"], "branch_index": bi, "field": "construction_action",
                                    "observed_relation_ids": d["observed_relation_ids"]}})
                derivations.append({"clause_id": cid, "decision_id": d["decision_id"], "branch": br["when"],
                                    "witness_ids": d["evidence_frame_ids"], "relations": d["observed_relation_ids"]})
                if cid not in br["clause_ids"]:
                    br["clause_ids"].append(cid)
    ops_present = sorted({op for d in usable for br in d["branches"] for op in br["operation_node_ids"]})
    nodes: list[dict] = []
    order = ["op.whole_scene", "op.canonical_character", "op.face_view_state", "op.hand_prop_contact", "op.region_edit"]
    for op in [o for o in order if o in ops_present]:
        nid = "n_" + op.split(".")[-1]
        nodes.append({"id": nid, "operator": op, "decisions": sorted({d["decision_id"] for d in usable for br in d["branches"]
                                                                      if op in br["operation_node_ids"]}),
                      "inputs": ["brief"] + (["approved canonical"] if OPERATORS[op]["identity_reference_required"] else []),
                      "outputs": OPERATORS[op]["outputs"], "depends_on": [n["id"] for n in nodes if n["operator"] == "op.canonical_character"]
                      if OPERATORS[op]["identity_reference_required"] else [],
                      "requires_identity": OPERATORS[op]["identity_reference_required"], "output_contract": output_contracts[op]})
    nodes.append({"id": "n_states_swap", "operator": "op.composite", "decisions": [], "inputs": ["approved states"],
                  "outputs": ["WHOLE_SCENE"], "depends_on": [n["id"] for n in nodes], "layer_method": "WHOLE_STATE_SWAP"})
    nodes.append({"id": "n_motion", "operator": "op.motion_render", "decisions": [], "inputs": ["approved pack"], "outputs": ["MP4"],
                  "depends_on": ["n_states_swap"]})
    manifest = {"skill_id": skill_id, "version": version, "status": "CANDIDATE_EXPERIMENT", "claim_state": "METHOD_CANDIDATE",
                "synthetic": False, "evidence_origin": evidence_origin, "reference_overflow_policy": "BLOCK", "provider_parameters": {},
                "entrypoint": "vme.skills.runtime:execute", "visual_truth": "UNVERIFIED_UNTIL_ORIGINAL_ART_REVIEW",
                "label": ("SIMULATED-TRANSPORT EVIDENCE — wiring drill, not learned style" if evidence_origin != "REAL_VLM"
                          else "Evidence-authored candidate skill; artistic quality unproven")}
    md = (f"# {skill_id} {version}\n\nAuthored by vme.style.authoring from persisted evidence ({evidence_origin}).\n"
          f"Decisions: {[d['decision_id'] for d in usable]}\nRecipe: recipes/main.json. This Markdown has no production authority.\n")
    h = write_skill(folder, manifest=manifest, decisions=usable, templates=templates, references=[], recipes={"main": {"recipe_id": "main",
                    "nodes": nodes}}, skill_md=md)
    return {"folder": str(folder), "skill_hash": h, "derivations": derivations, "nodes": [n["id"] for n in nodes],
            "research_only_excluded": [d["decision_id"] for d in decisions if d["status"] == "RESEARCH_ONLY"]}


def verify_structural_derivation(folder: str | Path) -> dict:
    """Interface I (REAL path): each clause template must equal the derived form of its cited branch action."""
    from ..skills.skill import load_skill
    sk = load_skill(folder)
    by = {d["decision_id"]: d for d in sk["decisions"]}
    bad = []
    for c in sk["clauses"]:
        dv = c.get("derivation")
        if not dv:
            bad.append({"clause": c["id"], "reason": "NO_DERIVATION_EDGE"})
            continue
        d = by.get(dv["decision_id"])
        if d is None:
            bad.append({"clause": c["id"], "reason": "DECISION_MISSING"})
            continue
        if derive_clause_template(d["branches"][dv["branch_index"]]["construction_action"]) != c["template"]:
            bad.append({"clause": c["id"], "reason": "CLAUSE_NOT_DERIVED_FROM_EVIDENCED_ACTION"})
        if not d.get("observed_relation_ids") or not d.get("evidence_frame_ids"):
            bad.append({"clause": c["id"], "reason": "DECISION_WITHOUT_EVIDENCE"})
    return {"ok": not bad, "problems": bad, "skill_hash": skill_hash(folder)}
