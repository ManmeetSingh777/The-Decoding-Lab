"""Loop/test helpers on top of `synthetic` (all SYNTHETIC; nothing here is a source observation)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from ..util import sha256_bytes, atomic_write_json
from .synthetic import (SYN, OBSERVED_RELATIONS, SKILL_ID, synthetic_witnesses, synthetic_brief, synthetic_decisions,
                        build_synthetic_skill, make_clip, make_sixth_clip, colour_classifier_factory, fixture_caps)

__all__ = ["SYN", "OBSERVED_RELATIONS", "SKILL_ID", "synthetic_witnesses", "synthetic_brief", "synthetic_decisions",
           "build_synthetic_skill", "make_clip", "make_sixth_clip", "colour_classifier_factory", "fixture_caps",
           "FIXTURE_REVIEWER", "SYNTHETIC_BASE_FILMS", "index_and_loader", "synthetic_candidates", "synthetic_bundle", "synthetic_gaps",
           "synthetic_problem", "fixture_answer", "face_view_proposal_from_answer", "complete_ledger_and_scope", "synthetic_shot_actions",
           "fixture_layer_pack", "fixture_scene_from_pack", "holdout_brief", "synthetic_output_review"]

FIXTURE_REVIEWER = "TEST_FIXTURE_HUMAN_SIMULATION"
SYNTHETIC_BASE_FILMS = [f"SYNTHETIC_BASE_FILM_{i}_" + str(i) * 42 for i in range(1, 6)]


def index_and_loader(clip, out_dir):
    from ..reference.probe import probe_source
    from ..reference.frame_index import index_every_frame, read_index
    from ..reference.frames import retrieve_frame
    p = probe_source(clip)
    s = index_every_frame(clip, p.sha256, out_dir, width=p.width, height=p.height, stream_duration_s=p.stream_duration_s,
                          metadata_nb_frames=p.metadata_nb_frames)
    idx = read_index(s.index_path)
    cache: dict = {}

    def loader(rec):
        k = rec["presentation_index"]
        if k not in cache:
            fr = retrieve_frame(clip, rec)
            cache[k] = {"png": fr.png_bytes, "png_sha": fr.png_sha256, "raw_sha": fr.raw_sha256, "w": fr.width, "h": fr.height,
                        "scale": 1.0}
        return cache[k]
    return idx, loader


def _cand(film, cid, a, b, roles, opps, stmt, **kw):
    proof = {o: f"{SYN} frames {a}-{b}: {o.replace('_', ' ')} visible in relation to the surrounding world" for o in opps}
    return {"film_sha": film, "candidate_id": cid, "start_frame_index": a, "end_frame_index_inclusive": b, "start_pts": a / 60,
            "end_pts": b / 60, "actual_frame_count": b - a + 1, "key_witness_frame_ids": [a, (a + b) // 2, b],
            "whole_visual_quality_statement": stmt, "selection_role_candidates": roles, "observer": "SYNTHETIC_FIXTURE",
            "opportunities": opps, "visible_proof_for_each_opportunity": proof, **kw}


def synthetic_candidates() -> list:
    F = SYNTHETIC_BASE_FILMS
    S = lambda t: f"{SYN} {t}"
    c = []
    classes = ["biped", "creature", None, "mascot", "biped_child"]
    for i, f in enumerate(F):
        n = i + 1
        if n != 3:  # film 3 deliberately has no character candidate (ROLE_SUBSTITUTION drill, ADD25-S03)
            c.append(_cand(f, f"F{n}-C1", 100, 460, ["C"], ["character_shape", "body_face_relation"] + (["hand_prop"] if n in (1, 4) else []) +
                           (["whole_body_acting"] if n == 5 else []),
                           S("focal actor silhouette stays separate from the layered setting while face and hands change together"),
                           actor_class=classes[i], observer_rank=1))
        c.append(_cand(f, f"F{n}-W1", 1200, 1700, ["W"], ["complete_world", "integrated_object_artwork"] + (["colour_material_finish"] if n % 2 else []),
                       S("near mid far structures repeat one construction system while the focal region carries denser internal divisions"),
                       observer_rank=2))
        c.append(_cand(f, f"F{n}-T1", 2400, 2900, ["T"], ["viewpoint", "spatial_transformation"] + (["state_substitution"] if n in (2, 5) else []) +
                       (["choreographed_coexistence"] if n == 4 else []),
                       S("camera reframes while foreground and background art states change together and a new world is revealed"),
                       observer_rank=2, event_start_frame=2380 if n == 2 else None))
        c.append(_cand(f, f"F{n}-W2", 3300, 3700, ["W", "T"], ["complete_world", "viewpoint"],
                       S("environment shown again while the camera drifts; overlaps the earlier world role"), observer_rank=5))
    c.append(_cand(F[0], "F1-C1-dup", 120, 470, ["C"], ["character_shape"],
                   S("near-identical interval to F1-C1, focal actor silhouette against setting"), observer_rank=3))
    c.append(_cand(F[1], "F2-vague", 5000, 5100, ["W"], ["complete_world"], "beautiful vibrant dynamic", observer_rank=0))
    c.append(_cand(F[3], "F4-sponsor", 6000, 6300, ["W"], ["complete_world"],
                   S("sponsor segment layout with product shot against plain background while text changes"), observer_rank=0,
                   content_label="SPONSOR"))
    return c


def synthetic_bundle():
    from ..investigation.evidence import WitnessBundle
    w = synthetic_witnesses()
    return WitnessBundle("WB-SYN-01", None, OBSERVED_RELATIONS["R-SYN-02"]["relation"], list(w.values()),
                         contrasting_witness_ids=["W-SYN-B01", "W-SYN-C01"],
                         unobservables=["studio production method"], competing_explanations=["rigid rotation of a flat cutout"])


def _crit(**lv):
    from ..investigation.gaps import CRITERIA
    return {k: {"level": lv.get(k, "MEDIUM"), "reason": f"{SYN} {k} judged from cited original/source witnesses ({lv.get(k, 'MEDIUM')})"}
            for k in CRITERIA}


def synthetic_gaps() -> list:
    def G(gid, sym, area, crit, deps, locus="skill_input"):
        return {"gap_id": gid, "run_id": "SYN", "visual_symptom": f"{SYN} {sym}", "affected_original_outputs": ["OUT-SYN-BASE-01"],
                "source_witness_ids": ["W-SYN-A01", "W-SYN-B01"], "scope_and_salience": "focal region dominates attention",
                "candidate_causes": [{"cause": "missing view-dependent redraw decision", "discriminating_check": "compile with/without D-SYN-FACE-VIEW"},
                                     {"cause": "provider ignores identity reference", "discriminating_check": "same request with stronger anchor"}],
                "expected_visual_signature": f"{SYN} {area} relation visibly present in new original art", "implementation_locus": locus,
                "criteria": crit, "area": area, "depends_on": deps}
    return [
        G("G-SYN-FACE", "face turn of the original actor reads as a rotated flat cutout relative to the source redraw", "character",
          _crit(salience="HIGH", breadth="HIGH", upstream_position="HIGH", method_likelihood="MEDIUM", leverage_per_cost="HIGH", interaction="HIGH"),
          ["G-SYN-VIEW", "G-SYN-WORLD"]),
        G("G-SYN-WORLD", "setting objects look like separate icons instead of one constructed system around the actor", "world",
          _crit(salience="HIGH", breadth="HIGH", upstream_position="MEDIUM", method_likelihood="MEDIUM", leverage_per_cost="MEDIUM", interaction="HIGH"),
          ["G-SYN-FACE"]),
        G("G-SYN-GRIP", "hand and prop drawn separately so the grip floats against the handle", "character",
          _crit(salience="HIGH", breadth="MEDIUM", upstream_position="MEDIUM", method_likelihood="HIGH", leverage_per_cost="MEDIUM", interaction="MEDIUM"),
          ["G-SYN-FACE"]),
        G("G-SYN-VIEW", "viewpoint change leaves background layers unchanged while the actor turns", "viewpoint_or_motion",
          _crit(salience="MEDIUM", breadth="MEDIUM", upstream_position="MEDIUM", method_likelihood="MEDIUM", leverage_per_cost="MEDIUM", interaction="HIGH"),
          ["G-SYN-FACE"]),
        G("G-SYN-MICRO", "one highlight is slightly displaced compared with the source treatment while everything else matches", "other",
          _crit(salience="LOW", breadth="LOW", upstream_position="LOW", method_likelihood="HIGH", leverage_per_cost="LOW", interaction="LOW"), []),
    ]


def synthetic_problem() -> dict:
    return {"cluster_id": "CL-SYN-01", "version": 1, "original_output_id_or_initial_reference_only": "INITIAL_REFERENCE_ONLY",
            "reference_full_frame_ids": ["W-SYN-A01"], "affected_original_subject_classes": ["biped", "creature"],
            "high_impact_visible_difference": f"{SYN} the source actor's three-quarter turn redraws near/far facial features and shoulder silhouette while our baseline rotates a flat face",
            "whole_scene_consequence": "focal actor loses identity and appeal at the moment of attention",
            "connected_artistic_relations": ["near/far facial features", "head contour", "shoulder silhouette", "identity masses"],
            "competing_explanations": [{"claim": "features are redrawn as one coherent state"}, {"claim": "a flat face cutout is rigidly rotated"}],
            "latest_unresolved_uncertainties": [{"kind": "RESOLUTION_INSUFFICIENT", "what": "face-turn region only seen at thumbnail scale"}],
            "expected_original_visual_improvement": "new actor's 3/4 state shows redrawn near/far features with retained identity masses",
            "next_required_producer_decision_id": "D-SYN-FACE-VIEW", "required_conditions": {"view": "three_quarter"},
            "source_evidence_version": "ev1"}


def fixture_answer(q) -> dict:
    """SYNTHETIC answerer standing in for an authorized VLM/human answer. Labelled; never real evidence.
    R3 F04: it may cite ONLY the witnesses the question actually supplied (never self-added ids)."""
    a = _fixture_answer_raw(q)
    planned = set(getattr(q, "observed_contrast_with_witness_ids", []) or [])
    if a.get("SOURCE_VISIBLE_FACTS"):
        facts = []
        for f in a["SOURCE_VISIBLE_FACTS"]:
            ids = [w for w in f["witness_ids"] if w in planned] or sorted(planned)[:1]
            if ids:
                facts.append({**f, "witness_ids": ids})
        a["SOURCE_VISIBLE_FACTS"] = facts
    a["answer_evidence_ids"] = sorted({w for f in a.get("SOURCE_VISIBLE_FACTS") or [] for w in f["witness_ids"]})
    return a


def _fixture_answer_raw(q) -> dict:
    base = {"answer_status": "UNKNOWN", "answerer": "SYNTHETIC_FIXTURE",
            **{k: None for k in ("SOURCE_VISIBLE_FACTS", "IMPORTANT_LINKED_CHANGES", "CONSTRUCTION_EXPLANATION", "WHY_THE_DECISION_MATTERS",
                                 "WHEN_APPLICABLE", "WHEN_NOT_APPLICABLE", "ACTUAL_PRODUCING_OPERATION",
                                 "WHERE_IT_ENTERS_COMPILED_REQUEST", "REMAINING_UNKNOWN")}}
    rel = OBSERVED_RELATIONS["R-SYN-02"]["relation"]
    common = {"IMPORTANT_LINKED_CHANGES": ["head contour", "shoulder silhouette", "near/far features"],
              "WHY_THE_DECISION_MATTERS": "focal actor keeps identity while turning", "ACTUAL_PRODUCING_OPERATION": {"operation_id": "op.face_view_state"},
              "WHERE_IT_ENTERS_COMPILED_REQUEST": {"decision": "D-SYN-FACE-VIEW", "clause": "K-SYN-FACE-01", "operator": "op.face_view_state"},
              "REMAINING_UNKNOWN": ["behaviour for profile view"], "answer_evidence_ids": ["W-SYN-A02", "W-SYN-A03"]}
    if q.owner_stage == "SOURCE_OBSERVATION":
        return {**base, **common, "answer_status": "OBSERVED",
                "SOURCE_VISIBLE_FACTS": [{"relation": rel, "witness_ids": ["W-SYN-A01", "W-SYN-A03"]}],
                "CONSTRUCTION_EXPLANATION": "near and far facial features are redrawn together with the head contour while identity masses stay; not a rigid rotation",
                "WHEN_APPLICABLE": {"view": "three_quarter"}, "WHEN_NOT_APPLICABLE": ["distant figures"]}
    if q.owner_stage == "CAUSE_INFERENCE":
        return {**base, **common, "answer_status": "INFERRED",
                "SOURCE_VISIBLE_FACTS": [{"relation": rel, "witness_ids": ["W-SYN-A02"]},
                                         {"relation": "unlike creature also keeps silhouette masses joined at visible boundaries while turning",
                                          "witness_ids": ["W-SYN-B01"]}],
                "CONSTRUCTION_EXPLANATION": "the turn is a coordinated redraw of near/far features with shoulder silhouette, which the cutout explanation cannot produce",
                "WHEN_APPLICABLE": {"view": "three_quarter"}, "WHEN_NOT_APPLICABLE": ["explanatory diagram"]}
    if q.owner_stage == "STYLE_CONDITIONS":
        return {**base, **common, "answer_status": "INFERRED",
                "SOURCE_VISIBLE_FACTS": [{"relation": rel, "witness_ids": ["W-SYN-A02"]},
                                         {"relation": "exception: diagram uses fewer internal divisions", "witness_ids": ["W-SYN-C01"]}],
                "CONSTRUCTION_EXPLANATION": "for oblique three quarter views redraw near and far facial features, head contour and shoulder silhouette together; front views redraw head contour with identity masses retained",
                "WHEN_APPLICABLE": {"view": ["three_quarter", "front"]}, "WHEN_NOT_APPLICABLE": ["distant figures simplify facial features"]}
    return base


def face_view_proposal_from_answer(ans: dict) -> dict:
    """The answer's construction explanation becomes the decision's branch actions (T3→T4)."""
    return {"decision_id": "D-SYN-FACE-VIEW", "version": 2, "target_quality": "face identity across view",
            "dimension_tags": ["CHARACTER_FACE_ACTING", "DEPTH_VIEWPOINT", "ART_STATE_TRANSFORMATION", "MATERIAL_LIGHT_FINISH"],
            "branches": [
                {"when": {"view": "three_quarter"}, "construction_action": "near far facial features, head contour and shoulder silhouette redrawn together",
                 "clause_ids": ["K-SYN-FACE-01"], "reference_role_ids": [], "operation_node_ids": ["op.face_view_state", "op.canonical_character"], "priority": 15},
                {"when": {"view": "front"}, "construction_action": "front head contour with identity masses retained",
                 "clause_ids": ["K-SYN-FACE-02"], "reference_role_ids": [], "operation_node_ids": ["op.face_view_state", "op.canonical_character"], "priority": 15}],
            "invariant_visual_relation": OBSERVED_RELATIONS["R-SYN-02"]["relation"], "adaptive_visual_choices": ["head design per actor"],
            "exceptions": list(ans.get("WHEN_NOT_APPLICABLE") or ["distant figures"]), "observed_relation_ids": ["R-SYN-02"],
            "origin_type": "SOURCE_OBSERVED", "dependencies": ["D-SYN-CHAR-WHOLE"], "expected_visible_effect": "redrawn turn keeps identity masses",
            "creative_freedom": ["original head shape", "costume"], "forbidden_source_specific_copies": ["orange jacket"]}


def complete_ledger_and_scope(*, lighting: str = "directional", include_contact: bool = True):
    from ..style.coverage import OriginalScope, new_ledger, reverse_plan, set_dimension, set_relation, DIMENSIONS
    scope = OriginalScope("SCOPE-SYN-01", subjects=[{"id": "explorer", "kind": "character", "subject_kind": "biped", "role": "focal",
                                                     "view": "three_quarter", "view_changes": ["front"], "face_visible": True,
                                                     "contact_props": ["chamber_handle"] if include_contact else [], "lighting_changes": False}],
                          world={"kind": "underwater", "layers": True, "lighting": lighting})
    plan = reverse_plan(scope)
    L = new_ledger("SCOPE-SYN-01", ["SYN_seq_A", "SYN_seq_B"])
    L["frame_coverage_state"] = "ALL_TARGET_FRAMES_SEEN"
    ev = [{"source_hash": "SYNTHETIC_SHA", "sequence_id": "SYN_seq_A", "frame_start": 100, "frame_end": 112, "evidence_kind": "SYNTHETIC_FIXTURE"}]
    cons = {"CHARACTER_FACE_ACTING": ["op.face_view_state"], "CHARACTER_BODY_HAND_CONTACT": ["op.hand_prop_contact"],
            "CHARACTER_WHOLE_DESIGN": ["op.canonical_character"], "DEPTH_VIEWPOINT": ["op.face_view_state", "op.layer_extract"],
            "ART_STATE_TRANSFORMATION": ["op.face_view_state"]}
    for d in DIMENSIONS:
        if d in plan["required_dimensions"]:
            set_dimension(L, d, "RELEVANT_SUPPORTED", evidence=ev, why_relevant=f"{SYN} visible in fixture sequence",
                          production_consumers=cons.get(d, ["op.whole_scene"]))
        else:
            set_dimension(L, d, "NOT_APPLICABLE_WITH_REASON", evidence=[], why_relevant="not in this still-art scope",
                          inapplicability_reason="scope is a still-art image trial without this phenomenon")
    for j in plan["joint_choices"]:
        set_relation(L, j["joint_id"], j["dimensions"], "SUPPORTED", evidence=ev, producing_effect=f"{SYN} joint choice owned by one decision")
    return L, scope


def synthetic_shot_actions() -> list:
    return [{"actor": "explorer", "event_id": "e1", "view": "front", "expression": "surprise"},
            {"actor": "explorer", "event_id": "e2", "contact_prop": "chamber_handle", "hand_side": "right", "gesture": "reach"},
            {"actor": "explorer", "event_id": "e3", "moves_part": "near_arm"}]


def fixture_layer_pack(out_dir, *, canonical_path, canonical_sha, states: dict) -> dict:
    """Local real-pixel layer extraction from the (fixture) canonical raster + local clean plate. Wiring only."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    can = Image.open(canonical_path).convert("RGBA")
    W, H = can.size
    x0, y0, w, h = W // 2, H // 3, W // 4, H // 4
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, w - 1, h - 1], fill=255)
    part = can.crop((x0, y0, x0 + w, y0 + h))
    part.putalpha(mask)
    pp, mp = out / "layer_near_arm.png", out / "mask_near_arm.png"
    part.save(pp)
    mask.save(mp)
    arr = np.asarray(can).copy()
    region = arr[y0:y0 + h, x0:x0 + w]
    fill = arr[max(0, y0 - 4):y0, x0:x0 + w].reshape(-1, 4).mean(axis=0) if y0 >= 4 else np.array([60, 60, 60, 255])
    m = np.asarray(mask) > 0
    region[m] = fill.astype(np.uint8)
    region[..., 3] = 255
    arr[y0:y0 + h, x0:x0 + w] = region
    cp = out / "clean_plate.png"
    Image.fromarray(arr, "RGBA").save(cp)
    layers = [
        {"layer_id": "L-bg", "owner": "explorer", "body_part": "torso", "side": "center", "image_path": str(cp),
         "image_sha256": sha256_bytes(cp.read_bytes()), "mode": "OPAQUE", "mask_path": None, "mask_sha256": None, "local_origin": [0, 0],
         "pivot": [0, 0], "natural_size": [W, H], "z": 0, "parent": None, "parent_scale_applied": False, "occluded_fill": None, "moves": False},
        {"layer_id": "L-near-arm", "owner": "explorer", "body_part": "near_hand", "side": "right", "image_path": str(pp),
         "image_sha256": sha256_bytes(pp.read_bytes()), "mode": "RGBA", "mask_path": str(mp), "mask_sha256": sha256_bytes(mp.read_bytes()),
         "local_origin": [x0, y0], "pivot": [w // 2, 0], "natural_size": [w, h], "z": 2, "parent": None, "parent_scale_applied": False,
         "occluded_fill": str(cp), "moves": True, "motion_range_px": [0, 30], "source_composite_sha256": canonical_sha},
    ]
    st = [{"state_id": k, "path": v["image"], "width": W, "height": H, "identity_reference_sha256": v["identity_ref"]} for k, v in states.items()]
    pack = {"pack_id": "PACK-SYN-explorer", "canonical": {"path": canonical_path, "sha256": canonical_sha, "width": W, "height": H},
            "view": "three_quarter", "layers": layers, "states": st, "clean_plate": str(cp), "check_motion_holes": True,
            "contacts": [{"contact_id": "C-grip", "required_order": ["torso", "near_hand"], "hand_anchor_world": [100, 100],
                          "prop_anchor_world": [101, 99], "approved_hand_prop_state": states.get("n4_grip", {}).get("image")}],
            "label": "FIXTURE_ONLY_NOT_ART_QUALIFICATION"}
    pack["pack_path"] = str(out / "pack.json")
    atomic_write_json(out / "pack.json", pack)
    return pack


def fixture_scene_from_pack(pack: dict):
    W, H = 640, 360
    cw = pack["canonical"]["width"]
    s = H / pack["canonical"]["height"]
    arm = next(l for l in pack["layers"] if l["layer_id"] == "L-near-arm")
    view = next((x for x in pack["states"] if x["state_id"] == "n3_view"), None)
    scene = {"width": W, "height": H, "fps": 30, "durationInFrames": 60, "background": "#101418",
             "camera": {"keyframes": [{"frame": 0, "x": 0, "y": 0, "scale": 1.0}, {"frame": 59, "x": 10, "y": 0, "scale": 1.04}]},
             "layers": [
                 {"id": "plate", "src": "clean_plate.png", "x": 0, "y": 0, "w": round(cw * s), "h": H, "z": 0},
                 {"id": "actor", "src": "canonical.png", "x": round(cw * s) + 10, "y": 0, "w": round(cw * s * 0.9), "h": round(H * 0.9), "z": 1,
                  "states": [{"from_frame": 30, "to_frame": 59, "src": "view_state.png"}] if view else []},
                 {"id": "arm", "src": "layer_near_arm.png", "x": round(arm["local_origin"][0] * s), "y": round(arm["local_origin"][1] * s),
                  "w": round(arm["natural_size"][0] * s), "h": round(arm["natural_size"][1] * s), "z": 2, "pivot": [10, 0],
                  "keyframes": [{"frame": 0, "rotation": 0, "y": round(arm["local_origin"][1] * s)},
                                {"frame": 59, "rotation": 25, "y": round(arm["local_origin"][1] * s) + 30}]}],
             "events": [{"id": "ev-arm", "kind": "part_motion", "layer": "arm"}]}
    assets = {"clean_plate.png": pack["clean_plate"], "canonical.png": pack["canonical"]["path"], "layer_near_arm.png": arm["image_path"]}
    if view:
        assets["view_state.png"] = view["path"]
    return scene, assets


def holdout_brief() -> dict:
    return synthetic_brief(brief_id="BRIEF-SYN-UNSEEN-01", shot_id="holdout-01", pool="unseen_transfer",
                           subjects=[{"id": "tidal_creature", "noun": "tidal creature", "subject_kind": "creature", "role": "focal",
                                      "content_attributes": []}],
                           actions=["drifts past a cracked greenhouse pane"], world={"setting": "abandoned orbital greenhouse", "environment": "interior"},
                           visual_focus="creature against greenhouse ribs", camera_or_view_requirement="front",
                           slots={"subject": "tidal creature", "setting": "abandoned orbital greenhouse", "action": "drifts past a cracked pane",
                                  "visual_role": "focal", "view": "front", "subject_kind": "creature", "environment": "interior",
                                  "original_prop": "cracked greenhouse pane"})


def synthetic_output_review(output_sha: str) -> dict:
    return {"output_id": output_sha, "reviewer": "SYNTHETIC_FIXTURE_REVIEW",
            "findings": [{"symptom": f"{SYN} transfer output: a background creature needs a simplified-but-identity-preserving treatment that no branch covers",
                          "attributed_stage": "STYLE_CONDITIONS", "decision_id": "D-SYN-CHAR-WHOLE",
                          "required_conditions": {"subject_kind": "creature", "role": "background"}, "output_id": output_sha}]}
