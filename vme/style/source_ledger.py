"""R3 F11 + Addendum 29 — source-first character study and the two SEPARATE coverage ledgers.

1. `validate_character_art_study` — a CharacterArtDossier is valid only if it studies the DRAWN entity (study_basis
   SOURCE_FIRST_DRAWN_ENTITY) across every Add.29 relation field, each OBSERVED with a construction-grade relation and impact, or UNKNOWN
   with the precise next witness; every cited witness must be one actually submitted (local manifest); identity across ≥2 drawings and
   a contrasting example are mandatory. Anatomy words are tags, never geometry generators: generic-anatomy-only text is refused.
2. `source_art_ledger` — per selected scene: frames sent / identity-bound, typed per-frame observations, witnesses, native inspections,
   phenomena, character entities and dossiers, open gaps. A frame hash alone carries ZERO art coverage. A scene is
   NEEDS_SOURCE_REINSPECTION while any consequential gap lacks action. Source-art TRUTH stays UNREVIEWED without a human review.
3. `production_coverage_ledger` — new-production choices → owner decision/skill clause/reference roles/operator/consumer. It can never
   claim source study, and an image clause never counts as a motion rule.
"""
from __future__ import annotations

import json
import re

from ..util import Blocked, digest, is_vague_statement, now_iso

CHAR_FIELDS = ("whole_design", "outer_contour_and_taper", "negative_spaces", "visual_piece_junctions", "fills_edges_materials",
               "lighting_and_shadows", "view_and_pose_redraws", "contact_and_occlusion", "world_integration")
SCOPE_CLASSES = ("STYLE_INVARIANT_CANDIDATE", "CONDITIONAL_STYLE_RULE", "CHARACTER_IDENTITY_RULE", "SHOT_OR_EVENT_RULE",
                 "UNKNOWN_OR_CONTRADICTED")
_GENERIC_ANATOMY = re.compile(r"\b(tubes?|tubular|cylinders?|cylindrical|stick (arms?|limbs?)|mittens?|generic (hands?|faces?|skeleton)|"
                              r"standard (human|anatomy)|skeletons?|bone rig|default shading|stock faces?|sausage limbs?)\b", re.I)


def validate_character_art_study(dossier: dict, authorized: set[str]) -> list[str]:
    """Returns the list of problems (empty = construction-grade source-first study). Never raises on content problems."""
    p: list[str] = []
    if dossier.get("study_basis") != "SOURCE_FIRST_DRAWN_ENTITY":
        p.append("GENERIC_ANATOMY_TEMPLATE_FORBIDDEN")
    fields = dossier.get("fields") or {}
    for f in CHAR_FIELDS:
        part = fields.get(f)
        if not isinstance(part, dict):
            p.append(f"MISSING_CHARACTER_ART_RELATION:{f}")
            continue
        ids = set(part.get("witness_ids") or [])
        if not ids or not ids <= authorized:
            p.append(f"CHARACTER_ART_WITHOUT_SUBMITTED_WITNESS:{f}")
        st = part.get("state")
        if st == "OBSERVED":
            rel, imp = str(part.get("visible_relation", "")), str(part.get("reconstruction_impact", ""))
            if not rel.strip() or not imp.strip() or is_vague_statement(rel):
                p.append(f"CHARACTER_ART_NOT_CONSTRUCTION_GRADE:{f}")
            if _GENERIC_ANATOMY.search(rel) or _GENERIC_ANATOMY.search(imp):
                p.append(f"GENERIC_ANATOMY_SUBSTITUTED_FOR_DRAWN_FORM:{f}")
        elif st == "UNKNOWN":
            if not str(part.get("precise_next_witness", "")).strip():
                p.append(f"CHARACTER_ART_UNKNOWN_WITHOUT_TARGET:{f}")
        else:
            p.append(f"CHARACTER_ART_STATE_UNKNOWN:{f}")
    ident = dossier.get("identity_across_drawings") or []
    if not ident or not any(len(set(x.get("witness_ids") or []) & authorized) >= 2 for x in ident if isinstance(x, dict)):
        p.append("NO_MULTI_STATE_IDENTITY_PROOF")
    contrast = dossier.get("contrasting_examples") or []
    if not contrast or not any(set(x.get("witness_ids") or []) & authorized for x in contrast if isinstance(x, dict)):
        p.append("NO_CHARACTER_CONTRAST")
    if dossier.get("scope_class") not in SCOPE_CLASSES:
        p.append("CHARACTER_RULE_SCOPE_UNCLASSIFIED")
    return p


def character_state_inventory(entity_id: str, frames: list[tuple]) -> list[dict]:
    """R3-C09: distinct OBSERVED states of one drawn entity, in time order, from the committed per-frame records
    [(seq, frame_index, region, observation)]. A new state starts when the drawing-state ids, contact, face/view or occlusion signature
    changes, or a new drawing is reported for this entity. Hard cases (contact / occlusion / redraw / face-view) are flagged."""
    from ..vision.contracts import _addressing
    inv: list[dict] = []
    last = None
    for seq, k, reg, o in sorted(frames, key=lambda x: (x[0], x[1])):
        rels = [r for r in o.get("visible_design_relations") or [] if isinstance(r, dict) and entity_id in (r.get("entity_ids") or [entity_id])]
        dims = {d for r in rels for d in r.get("dimensions") or []}
        text = " ".join(str(r.get("relation", "")).lower() for r in rels)
        contact = "CHARACTER_BODY_HAND_CONTACT" in dims or ("grip" in text or "contact" in text)
        face = bool(dims & {"CHARACTER_FACE_ACTING", "DEPTH_VIEWPOINT"})
        occl = any(w in text for w in ("occlud", "behind", "in front", "overlap"))
        redraw = any(isinstance(c, dict) and c.get("kind") == "INFERRED_NEW_DRAWING" and entity_id in (c.get("entity_ids") or [entity_id])
                     for c in o.get("changed_since_prior_frame") or [])
        ids = tuple(sorted(str(x) for x in o.get("persistent_state_ids") or [] if str(x).startswith(entity_id)))
        sig = (ids, contact, face, occl)
        if last is None or sig != last or redraw:
            inv.append({"state_id": f"{entity_id}#S{len(inv)}", "signature": {"drawing_state_ids": list(ids), "contact": contact, "face_view": face,
                                                                             "occlusion": occl, "starts_with_redraw": redraw},
                        "sequence_id": seq, "frames": [], "regions": [], "hard_case": contact or occl or redraw or face,
                        "contact_substantive": _addressing(o.get("character_face_limb_contact_state")) == "SUBSTANTIVE"})
            last = sig
        inv[-1]["frames"].append(k)
        inv[-1]["regions"].append(reg)
    return inv


def select_study_frames(inventory: list[dict], capacity: int, required: list[dict] | None = None) -> dict:
    """Pick one representative frame per distinct state — hard cases first, then the rest, then chronology — within the image budget.
    Anything not selected is NAMED (state id + exact frames). A required critical state (from the independent auditor) that no
    selected state covers is a MISSING_CRITICAL_STATE with its frames."""
    order = sorted(inventory, key=lambda s: (not s["hard_case"], s["frames"][0]))
    chosen = order[: max(0, capacity)]
    uncovered = [{"state_id": s["state_id"], "frames": s["frames"][:10], "signature": s["signature"]} for s in order[max(0, capacity):]]
    picks = []
    for s in sorted(chosen, key=lambda s: s["frames"][0]):
        mid = s["frames"][len(s["frames"]) // 2]
        picks.append({"state_id": s["state_id"], "frame": mid, "region": s["regions"][s["frames"].index(mid)], "hard_case": s["hard_case"],
                      "sequence_id": s["sequence_id"]})
    covered = {f for s in chosen for f in s["frames"]}
    missing = [{"phenomenon_id": r.get("phenomenon_id"), "kind": r["kind"], "frames": r["frames"]} for r in required or []
               if not any(a in covered for a in range(int(r["frames"][0]), int(r["frames"][1]) + 1))]
    return {"picks": picks, "uncovered_states": uncovered, "missing_critical_states": missing}


def dossier_state_problems(dossier: dict, state_witness: dict[str, str]) -> list[str]:
    """Every state shown to the study must be cited by it (a dossier that ignores an examined state is not a study of it)."""
    cited = {w for part in (_fields(dossier) or {}).values() if isinstance(part, dict) for w in part.get("witness_ids") or []}
    cited |= {w for x in (dossier.get("identity_across_drawings") or []) if isinstance(x, dict) for w in x.get("witness_ids") or []}
    return [f"MISSING_STATE_IN_DOSSIER:{sid}" for sid, wid in sorted(state_witness.items()) if wid not in cited]


def _fields(dossier: dict) -> dict:
    return (dossier.get("study") or {}).get("fields") or dossier.get("fields") or {}


def dossier_open_fields(dossier: dict) -> list[str]:
    return [f for f in CHAR_FIELDS if (_fields(dossier).get(f) or {}).get("state") != "OBSERVED"]


def source_art_ledger(st, ws, run_id: str, intervals: list[tuple], pass_id: str) -> dict:
    """Per-scene certificates for the 15+1 (or drill) intervals. Never unioned with the production ledger."""
    from ..state.authority import AuthorityRegistry
    auth = AuthorityRegistry(st)
    dossiers = [d for d in st.list("CharacterArtDossier")]
    pend = (st.get("PendingNativeFollowups", run_id) or {}).get("pending", [])
    scenes = []
    for film, a, b, seq in intervals:
        rows = st.conn.execute("SELECT frame_index, status, packet_id FROM frame_vision WHERE film_sha256=? AND pass_id=? AND "
                               "frame_index BETWEEN ? AND ?", (film, pass_id, a, b)).fetchall()
        bound = {r[0] for r in rows}
        packets = sorted({r[2] for r in rows})
        obs, entities = [], set()
        for pk in packets:
            f = ws.vision_dir / pass_id / pk / "frames.jsonl"
            if not f.exists():
                continue
            for line in f.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                o = json.loads(line)
                for e in o.get("actually_visible_actor_and_object_ids") or []:
                    entities.add(e if isinstance(e, str) else str((e or {}).get("id")))
                for i, rel in enumerate(o.get("visible_design_relations") or []):
                    if isinstance(rel, dict) and rel.get("relation"):
                        obs.append({"film_sha": film, "selected_scene": seq, "native_pts": o.get("pts_time"), "frame_id": o["frame_id"],
                                    "actor_or_entity_id": (o.get("actually_visible_actor_and_object_ids") or [None])[0],
                                    "drawing_state_id": (o.get("persistent_state_ids") or [None])[0], "event_id": None,
                                    "part_or_relation_id": f"{o['frame_id']}#{i}", "observed_visual_relation": rel["relation"],
                                    "dimensions": rel.get("dimensions"), "temporal_change_or_persistence":
                                        (o.get("changed_since_prior_frame") or [{}])[0].get("what") if o.get("changed_since_prior_frame")
                                        else o.get("no_significant_change_reason"),
                                    "competing_mechanism": o.get("camera_vs_actor_vs_drawing_state"),
                                    "unknown_or_exact_crop": [x.get("reason") for x in o.get("native_detail_followups") or []],
                                    "source_review_status": "UNREVIEWED"})
        natives = st.conn.execute("SELECT COUNT(*) FROM frame_vision WHERE film_sha256=? AND pass_id=? AND frame_index BETWEEN ? AND ?",
                                  (film, f"{run_id}-native", a, b)).fetchone()[0]
        phen = [x for x in st.list("VisualPhenomenon") if any(s["sequence_id"] == seq for s in x.get("sightings", []))]
        dos = [d for d in dossiers if film in d.get("films", []) and d.get("entity_id") in entities]
        open_gaps: list[dict] = []
        missing = [i for i in range(a, b + 1) if i not in bound]
        if missing:
            open_gaps.append({"kind": "TARGET_FRAMES_NOT_IDENTITY_BOUND", "frames": missing[:20], "next": "run the packet(s) covering them"})
        for x in pend:
            if x.get("sequence") == seq:
                open_gaps.append({"kind": "NATIVE_CROP_PENDING", "frame": x["frame"], "region": x["region"], "next": "native follow-up"})
        for x in phen:
            if x.get("status") != "EXPLAINED":
                open_gaps.append({"kind": "UNEXPLAINED_PHENOMENON", "phenomenon_id": x["phenomenon_id"], "next": "P5 reinspection + P4 question"})
        # R3-C08: a frame record is not an inspection. Every bound frame needs an ADEQUATE per-frame verdict; explicit unknowns and
        # phenomena enumerated by the INDEPENDENT auditor but not explained keep the scene open at their exact frames.
        insp = {r["frame_index"]: r for r in st.list("FrameInspection") if r.get("film_sha256") == film and r.get("pass_id") == pass_id
                and a <= int(r["frame_index"]) <= b}
        not_assessed = sorted(i for i in bound if i not in insp)
        if not_assessed:
            open_gaps.append({"kind": "INSPECTION_NOT_ASSESSED", "frames": not_assessed[:20], "next": "re-run the packet(s) under the inspection gate"})
        weak = sorted((i, r) for i, r in insp.items() if r["status"] != "ARTISTIC_INSPECTION_ADEQUATE")
        if weak:
            open_gaps.append({"kind": "ARTISTIC_INSPECTION_INSUFFICIENT", "frames": [i for i, _ in weak][:20],
                              "gaps": sorted({g["gap"] for _, r in weak for g in r["gaps"]}), "next": "targeted native reinspection of those frames"})
        for i, r in sorted(insp.items()):
            for u in r.get("open_unknowns") or []:
                open_gaps.append({"kind": "KNOWN_UNKNOWN", "frame": i, "dimension": u["dimension"], "next": u.get("next_witness")})
        audit = st.get("PhenomenonAudit", f"{run_id}:{seq}")
        if audit is None:
            open_gaps.append({"kind": "INDEPENDENT_AUDIT_NOT_RUN", "next": "run the auditor (local detectors + P5 adversarial sweep)"})
        else:
            for g in audit.get("gaps") or []:
                open_gaps.append({"kind": g["gap"], "phenomenon_id": g.get("phenomenon_id"), "interval": g.get("interval"),
                                  "source": g.get("source"), "next": g.get("next")})
        for e in sorted(entities):
            d = next((d for d in dos if d["entity_id"] == e), None)
            if d is None or d.get("status") != "VALIDATED":
                open_gaps.append({"kind": "CHARACTER_SOURCE_STUDY_MISSING_OR_INVALID", "entity_id": e,
                                  "next": "P2 character_dossier with multi-state + contrast witnesses",
                                  "problems": (d or {}).get("problems")})
            elif dossier_open_fields(d):
                open_gaps.append({"kind": "CHARACTER_STATE_UNEXPLAINED", "entity_id": e, "fields": dossier_open_fields(d),
                                  "next": [(_fields(d).get(f) or {}).get("precise_next_witness") for f in dossier_open_fields(d)]})
        reviewed = [o for o in obs if auth.get("SOURCE_ART_REVIEW", {"frame_id": o["frame_id"]})]
        scenes.append({"selected_scene": seq, "film_sha256": film, "range": [a, b], "target_frames": b - a + 1,
                       "frames_identity_bound": len(bound), "packets": len(packets), "typed_observations": len(obs),
                       "witnesses": len([w for w in st.list("Witness") if w.get("sequence_id") == seq]), "native_inspections": natives,
                       "phenomena": len(phen), "entities": sorted(entities), "dossiers": [d["dossier_id"] for d in dos], "open_gaps": open_gaps,
                       "status": "NEEDS_SOURCE_REINSPECTION" if open_gaps else "SOURCE_INVESTIGATED_UNREVIEWED",
                       "source_art_truth": "SOURCE_ART_REVIEWED" if obs and len(reviewed) == len(obs) else "UNREVIEWED",
                       "observations_sample": obs[:3]})
    led = {"ledger": "SourceArtObservation", "run_id": run_id, "scenes": scenes, "built_at": now_iso(),
           "complete_for_promotion": all(s["status"] != "NEEDS_SOURCE_REINSPECTION" for s in scenes) and bool(scenes),
           "note": "source investigation completeness; independent of ProductionDecisionCoverage"}
    led["ledger_sha"] = digest({k: v for k, v in led.items() if k != "built_at"})
    return led


def production_coverage_ledger(plan: dict, decisions: list[dict], skill: dict | None, scope_id: str) -> dict:
    from .coverage import owns
    rows = []
    clause_by_dec: dict = {}
    if skill:
        for c in skill.get("clauses", []):
            clause_by_dec.setdefault(c["decision_id"], []).append({"clause_id": c["id"], "clause_sha": digest(c["template"]),
                                                                  "operation_id": c["operation_id"]})
    for c in plan["choices"]:
        owner = next((d for d in decisions if owns(d, c["choice_id"], c["dimensions"])), None)
        br = None
        if owner:
            br = next((b for b in owner["branches"] if all(str(c["conditions"].get(k)) == str(v) for k, v in b["when"].items())
                       and all(k in b["when"] for k in c["conditions"])), None)
        rows.append({"original_subject": scope_id, "choice_id": c["choice_id"], "condition_tuple": c["conditions"],
                     "required_output_operation_kind": c["operation_kind"], "owner_decision": (owner or {}).get("decision_id"),
                     "owner_skill_sha": (skill or {}).get("skill_hash"), "branch_operation": (br or {}).get("operation_node_ids"),
                     "clauses": clause_by_dec.get((owner or {}).get("decision_id"), []),
                     "reference_roles": (br or {}).get("reference_role_ids", []), "motion_program": (br or {}).get("motion_program"),
                     "status": "OWNED" if br else "UNOWNED", "reviewer_verdict": "UNREVIEWED"})
    return {"ledger": "ProductionDecisionCoverage", "scope_id": scope_id, "rows": rows,
            "complete": all(r["status"] == "OWNED" for r in rows),
            # R3-C10: ownership is not implementation — no row is visually verified until a VisualQualification exists for it
            "ownership_complete": all(r["status"] == "OWNED" for r in rows), "implementation_verified": False,
            "implementation_status": "OWNED_UNVERIFIED (needs region-aligned ablation on real output + human visual approval)",
            "note": "cannot claim source study; an image clause never counts as a motion rule"}


def sanity_entities(raw) -> list[str]:
    out = []
    for e in raw or []:
        out.append(e if isinstance(e, str) else str((e or {}).get("id")))
    if any(not x or x == "None" for x in out):
        raise Blocked("ENTITY_WITHOUT_STABLE_ID")
    return out
