"""REAL evidence → production choice → conditional decision → immutable skill version (repair R08, R09, R15, R21).

Chain: source witnesses + contrasts (persisted VLM records) → observed relation (answer facts with witness ids) →
PRODUCTION CHOICE (identity = the producer decision a reverse plan needs, e.g. `hero:face+view`, plus the investigated
phenomenon — NOT the dimension tags) → conditional branches → registered operation → OWNED prompt clause derived
verbatim from the evidenced branch action → skill-owned EXEMPLAR reference bytes (role, hash, consent) →
content-addressed immutable skill version + atomic CURRENT pointer → deterministic compile.

Two findings in the same category (same dimension tags, even the same condition) are different decisions whenever they
are different production choices or different phenomena. Re-answering the SAME choice never silently overwrites: a
changed construction action for the same condition+operation is kept in `contradictions` with both witness sets.

What this module does NOT claim: that the evidenced relation is visually true or that the clause will make good art.
Every decision carries visual_truth = UNVERIFIED_UNTIL_ORIGINAL_ART_REVIEW.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Callable

from ..util import Blocked, atomic_write_bytes, atomic_write_json, digest, now_iso, read_json, sha256_bytes
from ..investigation.evidence import Witness, WitnessBundle
from ..skills.operators import OPERATORS
from ..skills.skill import write_skill, skill_hash
from .decisions import witness_to_decision

SLOT_PLACEHOLDERS = {"{subject}": "${subject}", "{setting}": "${setting}", "{original_prop}": "${original_prop}"}


def json_key(d: dict) -> str:
    return json.dumps(d, sort_keys=True)


def production_choice_id(owned_key: str, phenomenon: str) -> str:
    """Semantic identity of a production choice: the producer decision it owns + the investigated phenomenon (R09)."""
    if not owned_key:
        raise Blocked("PRODUCTION_CHOICE_WITHOUT_OWNER_KEY")
    return "PC-" + digest({"owns": owned_key, "phenomenon": " ".join(str(phenomenon).lower().split())})[:16]


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


REFERENCE_MODES = ("REQUIRED", "TEXT_ONLY_DEMONSTRATED", "NOT_APPLICABLE")
CHARACTER_OPS = ("op.canonical_character", "op.face_view_state", "op.hand_prop_contact", "op.guided_pose_edit")


def authorize_answer(store, question: dict, answer: dict, *, authorized_submission_manifest: dict, registered_ops: dict,
                     allowed_ops: list[str]) -> set[str]:
    """R3 F04/F10 — the central write-site guard. Returns the locally authorized witness ids or raises the exact root cause.

    * Only STYLE_CONDITIONS questions (a locally built envelope) may publish a skill-bearing decision.
    * Cited witnesses must be a subset of what the LOCAL submission journal says was actually sent for this exact request — never the
      model's own `answer_evidence_ids` — and must match that manifest's source film, frame index (PTS) and crop region.
    * The answer must be sufficient to control a REGISTERED producing operator.
    """
    from ..vision.protocol import assess_sufficiency
    if question.get("owner_stage") != "STYLE_CONDITIONS":
        raise Blocked("EARLY_STAGE_CANNOT_PUBLISH_SKILL", f"{question.get('owner_stage')} answers create observations only")
    man = authorized_submission_manifest or {}
    allowed = set(man.get("submitted_witness_ids") or [])
    if not allowed:
        raise Blocked("NO_ACTUAL_SUBMISSION_MANIFEST", question.get("question_id", "?"))
    cited = {w for f in answer.get("SOURCE_VISIBLE_FACTS") or [] for w in (f.get("witness_ids") or [])}
    if not cited:
        raise Blocked("UNCITED_ARTISTIC_CLAIM", question.get("question_id", "?"))
    if cited - allowed:
        raise Blocked("UNSENT_WITNESS_CITATION", str(sorted(cited - allowed)[:5]))
    by_wid = {m["witness_id"]: m for m in man.get("byte_manifest") or []}
    for wid in sorted(cited):
        w = store.get("Witness", wid)
        m = by_wid[wid]
        if w is None:
            raise Blocked("CITED_WITNESS_NOT_IN_STORE", wid)
        if w["film_sha256"] != m["source_sha256"]:
            raise Blocked("WRONG_SOURCE_WITNESS", wid)
        if int(w["frame_start"]) != int(m["frame_index"]):
            raise Blocked("WRONG_PTS_WITNESS", f"{wid}: witness frame {w['frame_start']} != sent frame {m['frame_index']}")
        if (w.get("evidence_kind") == "NATIVE_CROP") != bool(m.get("region")) or (m.get("region") and w.get("region") != m["region"]):
            raise Blocked("UNSEEN_CROP_OR_WRONG_REGION", wid)
    bad_ops = [b.get("operation_id") for b in answer.get("BRANCHES") or [] if b.get("operation_id") not in registered_ops]
    if bad_ops:
        raise Blocked("UNREGISTERED_OPERATOR", str(bad_ops))
    proof = assess_sufficiency(answer, producing_operator=allowed_ops, known_witness_ids=allowed)
    if proof["verdict"] != "SUFFICIENT_FOR_PRODUCING_CHOICE":
        raise Blocked("INSUFFICIENT_FOR_PRODUCING_CHOICE", ";".join(proof["reasons"]))
    return allowed


def _reference_policy(b: dict, did: str, allowed: set[str], authority) -> tuple[dict, str | None]:
    """Explicit per-branch conditioning policy. A missing/unknown policy is UNKNOWN (fail closed), never 'not required'."""
    pol = b.get("reference_policy")
    if not isinstance(pol, dict) or pol.get("mode") not in REFERENCE_MODES:
        return {"mode": "UNKNOWN"}, "REFERENCE_POLICY_UNKNOWN"
    mode = pol["mode"]
    if mode == "REQUIRED":
        roles = [r for r in pol.get("roles") or [] if isinstance(r, dict)]
        if not roles:
            return {"mode": mode, "roles": []}, "REQUIRED_REF_WITHOUT_ROLES"
        if any(r.get("witness_id") not in allowed for r in roles):
            return {"mode": mode, "roles": roles}, "REQUIRED_REF_UNSEEN"
        names = [r.get("role") for r in roles]
        if len(set(names)) != len(names) or not all(names):
            return {"mode": mode, "roles": roles}, "AMBIGUOUS_REFERENCE_ROLES"
        return {"mode": mode, "roles": [{"role": r["role"], "witness_id": r["witness_id"]} for r in roles]}, None
    if mode == "TEXT_ONLY_DEMONSTRATED":
        if authority is None or not authority.text_only_transfer(did, {k: str(v) for k, v in (b.get("when") or {}).items()},
                                                                  b.get("construction_action", "")):
            return {"mode": mode}, "TEXT_ONLY_NOT_PROVEN"
        return {"mode": mode}, None
    if not str(pol.get("reason", "")).strip():
        return {"mode": mode}, "NOT_APPLICABLE_UNJUSTIFIED"
    return {"mode": mode, "reason": pol["reason"]}, None


def author_decision(store, question: dict, answer: dict, *, dims: list[str], registered_ops: dict, required_branches: list[dict],
                    decision_id: str, owned_choice_ids: list[str], phenomenon: str, authorized_submission_manifest: dict) -> dict:
    """Build/extend ONE production-choice decision ONLY from an authorized, sufficient STYLE_CONDITIONS answer (R3 F10)."""
    from ..state.authority import AuthorityRegistry
    allowed_ops = sorted({o for r in required_branches for o in r["operation_ids"]}) or \
        sorted({b.get("operation_id") for b in answer.get("BRANCHES") or [] if b.get("operation_id")})
    authorized = authorize_answer(store, question, answer, authorized_submission_manifest=authorized_submission_manifest,
                                  registered_ops=registered_ops, allowed_ops=allowed_ops)
    authority = AuthorityRegistry(store)
    rel_ids = register_relations_from_answer(store, question, answer, dims)
    cited = sorted({w for f in answer.get("SOURCE_VISIBLE_FACTS") or [] for w in f.get("witness_ids", [])})
    contrast = [w for w in question.get("observed_contrast_with_witness_ids", []) if w not in cited]
    wrecs = [store.get("Witness", w) for w in cited + contrast]
    wrecs = [w for w in wrecs if w]
    # an AUDIO_SIGNAL witness is evidence only with the full frame it coincides with: attach that parent as context, but ONLY when the
    # local submission manifest shows it was actually sent in this request (never pulled in from the store unseen)
    # The same holds for a NATIVE_CROP and its full-frame parent (R3-C07/C08: crops reach the bundle only with their context).
    have = {w["witness_id"] for w in wrecs}
    for w in list(wrecs):
        par = w.get("parent_full_frame_witness") if w.get("evidence_kind") in ("AUDIO_SIGNAL", "NATIVE_CROP") else None
        if par and par not in have and par in authorized:
            pw = store.get("Witness", par)
            if pw:
                wrecs.append(pw)
                have.add(par)
                contrast.append(par)
        elif par and par not in have and w["witness_id"] not in cited:
            wrecs.remove(w)                       # uncited contrast whose frame context was not sent: excluded, not imported
            contrast.remove(w["witness_id"])
    if not wrecs:
        raise Blocked("NO_EVIDENCE_FOR_DECISION", question["question_id"])
    bundle = WitnessBundle(f"WB-{question['question_id']}", question["question_id"], answer.get("CONSTRUCTION_EXPLANATION", ""),
                           [Witness(**{k: v for k, v in w.items() if k in Witness.__dataclass_fields__}) for w in wrecs],
                           contrasting_witness_ids=contrast)
    did = decision_id
    prev = store.get("ConditionalVisualDecision", did)
    branches, policy_problems = [], []
    seen_keys: dict = {}
    for i, b in enumerate(answer.get("BRANCHES") or []):
        op = b.get("operation_id")
        when = {k: str(v) for k, v in (b.get("when") or {}).items()}
        key = (json_key(when), op)
        if key in seen_keys and seen_keys[key] != b.get("construction_action", ""):
            raise Blocked("CONFLICTING_EQUALLY_APPLICABLE_BRANCHES", f"{did}: {when} / {op}")
        seen_keys[key] = b.get("construction_action", "")
        pol, problem = _reference_policy(b, did, authorized, authority)
        if problem:
            policy_problems.append({"when": when, "operation": op, "problem": problem})
        # one DISTINCT role per declared reference role, each bound to ITS witness (never sorted(wids)[0] for every role)
        roles = [{"role_id": f"exemplar:{did}:{digest([when, op, r['role']])[:8]}", "role": r["role"], "witness_id": r["witness_id"]}
                 for r in pol.get("roles", [])]
        mandatory = [r["role_id"] for r in roles] if pol["mode"] == "REQUIRED" else []
        mp = b.get("MOTION_PROGRAM") if isinstance(b.get("MOTION_PROGRAM"), dict) else None
        from ..render.motion_program import TRACK_OPS, validate_motion_program
        if op in TRACK_OPS.values():      # R3-C04: a motion branch must carry EVERY parameter of its track/method contract
            mprobs = validate_motion_program(mp)
            if mprobs:
                policy_problems.append({"when": when, "operation": op, "problem": "MOTION_PROGRAM_INCOMPLETE:" + ";".join(mprobs)})
        branches.append({"when": when, "construction_action": b.get("construction_action", ""), "clause_ids": [],
                         "reference_role_ids": [r["role_id"] for r in roles], "mandatory_reference_role_ids": mandatory,
                         "reference_policy": {**pol, "role_bindings": roles}, "motion_program": mp,
                         "operation_node_ids": [op] if op else [], "priority": 10 + i, "witness_ids": cited})
    contradictions = list((prev or {}).get("contradictions", []))
    superseded = list((prev or {}).get("superseded_branches", []))
    reopened = bool(prev) and str(prev.get("research_only_reason", "")).startswith("REOPENED_BY_HUMAN")
    if reopened:   # a human art rejection REJECTED the earlier action: it is superseded (kept with its review), not a contradiction
        reopened_keys = {(json_key(b["when"]), tuple(b["operation_node_ids"])) for b in branches}
        for b in prev["branches"]:
            if (json_key(b["when"]), tuple(b["operation_node_ids"])) in reopened_keys:
                superseded.append({**b, "superseded_by_review": prev["research_only_reason"].split(":", 1)[1],
                                   "defects": prev.get("reopened_defects", []), "at": now_iso()})
            else:
                branches.append(dict(b))
    elif prev:   # same production choice re-answered: keep earlier branches; conflicting actions are retained, not overwritten
        new_keys = {(json_key(b["when"]), tuple(b["operation_node_ids"])): b for b in branches}
        for b in prev["branches"]:
            k = (json_key(b["when"]), tuple(b["operation_node_ids"]))
            if k not in new_keys:
                branches.append(dict(b))
            elif new_keys[k]["construction_action"] != b["construction_action"]:
                contradictions.append({"condition": b["when"], "operation": list(k[1]), "earlier_action": b["construction_action"],
                                       "earlier_witness_ids": b.get("witness_ids", []), "later_action": new_keys[k]["construction_action"],
                                       "later_witness_ids": cited, "from_question": question["question_id"], "at": now_iso(),
                                       "status": "OPEN_NEEDS_DISCRIMINATING_EVIDENCE"})
    for i, b in enumerate(branches):
        b["priority"] = 10 + i
        op = b["operation_node_ids"][0] if b["operation_node_ids"] else None
        b["clause_ids"] = [f"K-{did}-{i}@{op.split('.')[-1]}"] if op else []
    # R3 F05: ONE branch must own the FULL required condition tuple; a branch that omits an axis counts only with a human-reviewed
    # invariance for that axis (authority registry, >=2 witnesses) — never by combining disjoint partial branches.
    def covers(br, rb):
        if not set(br["operation_node_ids"]) & set(rb["operation_ids"]):
            return False
        for k, v in rb["conditions"].items():
            if k in br["when"]:
                if br["when"][k] != str(v):
                    return False
            elif not authority.invariance(did, k):
                return False
        return all(k in rb["conditions"] for k in br["when"])
    missing = [rb for rb in required_branches if not any(covers(br, rb) for br in branches)]
    proposal = {"decision_id": did, "version": int((prev or {}).get("version", 0)) + 1,
                "target_quality": question.get("exact_artistic_unknown", ""),
                "branches": [{k: v for k, v in b.items() if k != "witness_ids"} for b in branches],
                "invariant_visual_relation": answer.get("INVARIANT") or answer.get("CONSTRUCTION_EXPLANATION", ""),
                "adaptive_visual_choices": list(answer.get("ADAPTS_WITH") or []), "exceptions": list(answer.get("WHEN_NOT_APPLICABLE") or []),
                "creative_freedom": list(answer.get("CREATIVE_FREEDOM") or []), "dependencies": [],
                "forbidden_source_specific_copies": list(answer.get("FORBIDDEN_SOURCE_SPECIFIC") or []),
                "observed_relation_ids": sorted(set(rel_ids) | set((prev or {}).get("observed_relation_ids", []))),
                "expected_visible_effect": answer.get("WHY_THE_DECISION_MATTERS", ""),
                "uncertainty": list(answer.get("REMAINING_UNKNOWN") or []), "dimension_tags": sorted(dims),
                "origin_type": "CROSS_SOURCE_INFERRED" if len(bundle.films) > 1 else "SOURCE_OBSERVED"}
    d = witness_to_decision(bundle, proposal, registered_operators=registered_ops, substitutes=None).to_dict()
    for b, src in zip(d["branches"], branches):
        b["witness_ids"] = src.get("witness_ids", cited)
    if prev:
        d["evidence_frame_ids"] = sorted(set(d["evidence_frame_ids"]) | set(prev.get("evidence_frame_ids", [])))
    if missing and d["status"] != "RESEARCH_ONLY":
        d["status"], d["research_only_reason"] = "RESEARCH_ONLY", f"BRANCHES_MISSING_FOR:{missing}"
    if any(c["status"].startswith("OPEN") for c in contradictions) and d["status"] != "RESEARCH_ONLY":
        d["status"], d["research_only_reason"] = "RESEARCH_ONLY", "OPEN_CONTRADICTION_NEEDS_DISCRIMINATING_EVIDENCE"
    if policy_problems and d["status"] != "RESEARCH_ONLY":
        d["status"], d["research_only_reason"] = "RESEARCH_ONLY", f"REFERENCE_POLICY:{policy_problems[0]['problem']}"
    if any("op.audio_cue" in b["operation_node_ids"] for b in branches) and d["status"] != "RESEARCH_ONLY":
        studied = [x for x in store.list("SourceAudioStudy") if x.get("status") == "AUDIO_SIGNAL_STUDIED_LOCALLY"
                   and x["film_sha256"] in {w["film_sha256"] for w in wrecs}]
        if not studied or not any(w.get("evidence_kind") == "AUDIO_SIGNAL" for w in wrecs):
            d["status"], d["research_only_reason"] = "RESEARCH_ONLY", "AUDIO_UNSTUDIED (no local source-audio witness)"
    if any(set(b["operation_node_ids"]) & set(CHARACTER_OPS) for b in branches) and d["status"] != "RESEARCH_ONLY":
        films = {w["film_sha256"] for w in wrecs}
        ok = [x for x in store.list("CharacterArtDossier") if x.get("status") == "VALIDATED" and set(x.get("films", [])) & films]
        if not ok:                                   # Addendum 29: no character rule before a source-first drawn-entity study
            d["status"], d["research_only_reason"] = "RESEARCH_ONLY", "CHARACTER_SOURCE_STUDY_MISSING"
        else:
            d["character_dossier_ids"] = sorted(x["dossier_id"] for x in ok)
    exemplars = [w["witness_id"] for w in wrecs if w["witness_id"] in cited]
    d.update(visual_truth="UNVERIFIED_UNTIL_ORIGINAL_ART_REVIEW", authored_from_question=question["question_id"],
             evidence_origin=wrecs[0].get("evidence_origin", "UNKNOWN"), authored_at=now_iso(),
             owned_choice_ids=sorted(set(owned_choice_ids) | set((prev or {}).get("owned_choice_ids", []))),
             phenomenon=phenomenon, identity_basis="PRODUCTION_CHOICE+PHENOMENON (not dimension tags)",
             contradictions=contradictions, superseded_branches=superseded, exemplar_witness_ids=exemplars,
             reference_required=any(b["mandatory_reference_role_ids"] for b in branches), reference_policy_problems=policy_problems,
             authorized_witness_ids=sorted(authorized), source_art_review="UNREVIEWED (candidate until a human SOURCE_ART_REVIEW)",
             revision_of=(prev or {}).get("research_only_reason") if reopened else None,
             claim_state=("UNRESOLVED" if d["status"] == "RESEARCH_ONLY" else "METHOD_CANDIDATE"),
             observed_vs_inferred={"observed": [f.get("relation") for f in answer.get("SOURCE_VISIBLE_FACTS") or []],
                                   "inferred_mechanism": answer.get("CONSTRUCTION_EXPLANATION", ""),
                                   "answer_status": answer.get("answer_status")})
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


ExemplarLoader = Callable[[str], tuple[bytes, dict]]     # witness_id -> (png bytes, provenance)
ConsentLookup = Callable[[str, str], dict | None]        # (film_sha, exemplar image sha) -> consent record or None


def _package_references(staging: Path, usable: list[dict], exemplar_loader: ExemplarLoader | None,
                        consent_for: ConsentLookup | None) -> tuple[list[dict], list[dict]]:
    """Exemplar bytes for every branch reference role: immutable file named by content hash, role, witness, consent."""
    refs, problems = [], []
    for d in usable:
        for br in d["branches"]:
            bind = {r["role_id"]: r for r in (br.get("reference_policy") or {}).get("role_bindings", [])}
            for role in br.get("reference_role_ids", []):
                mandatory = role in (br.get("mandatory_reference_role_ids") or [])
                rb = bind.get(role)
                if rb is None:   # legacy role without a declared witness binding
                    wids = br.get("witness_ids") or d.get("exemplar_witness_ids") or []
                    rb = {"witness_id": sorted(wids)[0] if wids else None, "role": "legacy"}
                if not rb.get("witness_id") or exemplar_loader is None:
                    problems.append({"role": role, "decision_id": d["decision_id"], "mandatory": mandatory, "reason": "NO_EXEMPLAR_SOURCE"})
                    continue
                wid = rb["witness_id"]
                try:
                    png, prov = exemplar_loader(wid)
                except Blocked as b:
                    problems.append({"role": role, "decision_id": d["decision_id"], "mandatory": mandatory, "reason": b.code})
                    continue
                sha = sha256_bytes(png)
                atomic_write_bytes(staging / "references" / f"{sha}.png", png)
                consent = consent_for(prov["film_sha256"], sha) if consent_for and prov.get("film_sha256") else None
                refs.append({"ref_id": f"ref-{sha[:16]}-{digest(role)[:6]}", "role": role, "semantic_role": rb.get("role"), "sha256": sha,
                             "path": f"{sha}.png",
                             "approved": bool(consent), "mandatory": mandatory, "decision_id": d["decision_id"], "branch_when": br["when"],
                             "source_witness_id": wid, "source_film_sha256": prov.get("film_sha256"), "evidence_kind": prov.get("evidence_kind"),
                             "frame_index": prov.get("frame_index"), "region": prov.get("region"),
                             "license": "THIRD_PARTY_SOURCE_FRAME: local study only; provider upload requires recorded consent",
                             "consent": consent or {"status": "MISSING", "needed": "vme reference consent --film-sha <sha> --by <human>"},
                             "applicability": br["when"], "exceptions": d.get("exceptions", []), "priority": br.get("priority", 100)})
    return refs, problems


def author_skill(folder: str | Path, decisions: list[dict], *, skill_id: str, version: str, evidence_origin: str,
                 output_contracts: dict, exemplar_loader: ExemplarLoader | None = None, consent_for: ConsentLookup | None = None) -> dict:
    """Write a complete skill folder: decisions + per-operation templates + exemplar references + recipe DAG."""
    usable = [json.loads(json.dumps(d)) for d in decisions if d["status"] != "RESEARCH_ONLY"]
    if not usable:
        raise Blocked("NO_EXECUTABLE_DECISIONS")
    folder = Path(folder)
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
                     "allowed_content_slots": sorted(set(re.findall(r"\$\{([a-z_]+)\}", tmpl))),
                     "reference_roles": list(br.get("reference_role_ids", [])), "operation_id": op, "origin_type": d["origin_type"],
                     "derivation": {"decision_id": d["decision_id"], "branch_index": bi, "field": "construction_action",
                                    "observed_relation_ids": d["observed_relation_ids"]}})
                derivations.append({"clause_id": cid, "decision_id": d["decision_id"], "branch": br["when"],
                                    "owned_choice_ids": d.get("owned_choice_ids", []),
                                    "witness_ids": d["evidence_frame_ids"], "relations": d["observed_relation_ids"],
                                    "reference_roles": br.get("reference_role_ids", [])})
                if cid not in br["clause_ids"]:
                    br["clause_ids"].append(cid)
    refs, ref_problems = _package_references(folder, usable, exemplar_loader, consent_for)
    ops_present = sorted({op for d in usable for br in d["branches"] for op in br["operation_node_ids"]})
    nodes: list[dict] = []
    order = ["op.whole_scene", "op.world_plate", "op.canonical_character", "op.face_view_state", "op.hand_prop_contact", "op.region_edit"]
    for op in [o for o in order if o in ops_present]:
        nid = "n_" + op.split(".")[-1]
        decs_for = sorted({d["decision_id"] for d in usable for br in d["branches"] if op in br["operation_node_ids"]})
        nodes.append({"id": nid, "operator": op, "decisions": decs_for,
                      "inputs": ["brief"] + (["approved canonical"] if OPERATORS[op]["identity_reference_required"] else []),
                      "outputs": OPERATORS[op]["outputs"], "depends_on": [n["id"] for n in nodes if n["operator"] == "op.canonical_character"]
                      if OPERATORS[op]["identity_reference_required"] else [],
                      "requires_identity": OPERATORS[op]["identity_reference_required"],
                      "output_contract": output_contracts.get(op) or output_contracts["op.whole_scene"]})
    nodes.append({"id": "n_states_swap", "operator": "op.composite", "decisions": [], "inputs": ["approved states"],
                  "outputs": ["WHOLE_SCENE"], "depends_on": [n["id"] for n in nodes], "layer_method": "WHOLE_STATE_SWAP"})
    nodes.append({"id": "n_motion", "operator": "op.motion_render", "decisions": [], "inputs": ["approved pack"], "outputs": ["MP4"],
                  "depends_on": ["n_states_swap"]})
    manifest = {"skill_id": skill_id, "version": version, "status": "CANDIDATE_EXPERIMENT", "claim_state": "METHOD_CANDIDATE",
                "synthetic": False, "evidence_origin": evidence_origin, "reference_overflow_policy": "BLOCK", "provider_parameters": {},
                "entrypoint": "vme.skills.runtime:execute", "visual_truth": "UNVERIFIED_UNTIL_ORIGINAL_ART_REVIEW",
                "reference_packaging_problems": ref_problems,
                "label": ("SIMULATED-TRANSPORT EVIDENCE — wiring drill, not learned style" if evidence_origin != "REAL_VLM"
                          else "Evidence-authored candidate skill; artistic quality unproven")}
    md = (f"# {skill_id} {version}\n\nAuthored by vme.style.authoring from persisted evidence ({evidence_origin}).\n"
          f"Decisions: {[d['decision_id'] for d in usable]}\nRecipe: recipes/main.json. This Markdown has no production authority.\n")
    h = write_skill(folder, manifest=manifest, decisions=usable, templates=templates, references=refs,
                    recipes={"main": {"recipe_id": "main", "nodes": nodes}}, skill_md=md)
    return {"folder": str(folder), "skill_hash": h, "derivations": derivations, "nodes": [n["id"] for n in nodes],
            "references": [{k: r[k] for k in ("role", "sha256", "approved", "mandatory", "source_witness_id", "decision_id")} for r in refs],
            "reference_problems": ref_problems,
            "research_only_excluded": [d["decision_id"] for d in decisions if d["status"] == "RESEARCH_ONLY"]}


def publish_skill_version(skill_root: str | Path, decisions: list[dict], **kw) -> dict:
    """Immutable content-addressed version (R21): author into a fresh staging dir, hash, move to versions/<hash16>
    (never rewritten), then atomically repoint CURRENT.json. Older versions stay byte-identical and stale clause
    files cannot leak because every version folder is written from scratch."""
    root = Path(skill_root)
    staging = root / "staging" / digest([now_iso(), kw.get("version"), [d["decision_id"] for d in decisions]])[:12]
    if staging.exists():
        shutil.rmtree(staging)
    res = author_skill(staging, decisions, **kw)
    final = root / "versions" / res["skill_hash"][:16]
    if final.exists():
        if skill_hash(final) != res["skill_hash"]:
            raise Blocked("IMMUTABLE_SKILL_VERSION_CORRUPTED", str(final))
        shutil.rmtree(staging)
    else:
        final.parent.mkdir(parents=True, exist_ok=True)
        staging.rename(final)
    prev = read_json(root / "CURRENT.json") if (root / "CURRENT.json").exists() else None
    hist = (prev or {}).get("history", []) + ([prev["skill_hash"]] if prev and prev["skill_hash"] != res["skill_hash"] else [])
    atomic_write_json(root / "CURRENT.json", {"skill_hash": res["skill_hash"], "folder": str(final), "version": kw.get("version"),
                                              "published_at": now_iso(), "history": hist})
    return {**res, "folder": str(final)}


def current_skill(skill_root: str | Path) -> dict | None:
    p = Path(skill_root) / "CURRENT.json"
    return read_json(p) if p.exists() else None


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
