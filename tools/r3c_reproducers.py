"""R3-C audit reproducers (handoff VME_R3_INDEPENDENT_AUDIT_AND_REPAIR_HANDOFF.md).

Each reproducer exercises the ACTUAL production function named in the audit and reports whether the observed defect is
present. Run once on the pre-repair code (RED_BEFORE) and again on the final code (GREEN_AFTER); the same file, unchanged.
A reproducer that now raises the intended `Blocked` code counts as the defect being CLOSED (fail-closed), any other
exception is reported as ERROR (never silently green).

    python tools/r3c_reproducers.py --out evidence/r3c_baseline/RED_BEFORE.json
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vme.util import Blocked  # noqa: E402

FA = "a" * 64


def _motion_fixture(method="ANTICIPATE_OVERSHOOT"):
    from vme.style.coverage import OriginalScope, reverse_plan
    scope = OriginalScope(scope_id="S", subjects=[{"id": "hero", "kind": "character", "subject_kind": "biped", "actions": ["walk"]},
                                                  {"id": "moth", "kind": "character", "subject_kind": "creature", "actions": ["circle"]}],
                          world={"kind": "space", "layers": True}, camera={"moves": True, "attention_beats": True},
                          audio_cues=[{"event_id": "e1"}])
    plan = reverse_plan(scope)
    cond = {c["choice_id"]: c["conditions"] for c in plan["choices"]}
    dims = {c["choice_id"]: c["dimensions"] for c in plan["choices"]}

    def mk(did, owns, op, kind, m):
        return {"decision_id": did, "status": "EXECUTABLE_CANDIDATE", "owned_choice_ids": [owns], "dimension_tags": dims[owns],
                "branches": [{"when": cond[owns], "operation_node_ids": [op],
                              "motion_program": {"track_kind": kind, "method": m, "hold_ratio": 0.2, "anticipation_ratio": 0.1,
                                                 "overshoot_ratio": 0.1}}]}
    decs = [mk("PC-act", "hero:acting", "op.motion_actor_track", "ACTOR_ACTING", method),
            mk("PC-act-m", "moth:acting", "op.motion_actor_track", "ACTOR_ACTING", method),
            mk("PC-cam", "camera:depth", "op.camera_attention", "CAMERA", "EASE_IN_OUT"),
            mk("PC-att", "attention:focus", "op.attention_focus", "ATTENTION", "HOLD_THEN_MOVE"),
            mk("PC-wld", "world:motion", "op.world_motion", "WORLD", "EASE_IN_OUT"),
            mk("PC-aud", "audio_timing", "op.audio_cue", "AUDIO", "CUE_ON_EVENT")]
    brief = {"shot_plan": {"frames": 60, "fps": 30, "plan_width": 1280, "plan_height": 720,
                           "actors": [{"id": "hero", "x": 200, "y": 180, "w": 480, "h": 480, "z": 1,
                                       "keyframes": [{"frame": 0, "x": 200}, {"frame": 59, "x": 260}]},
                                      {"id": "moth", "x": 820, "y": 80, "w": 320, "h": 320, "z": 2,
                                       "keyframes": [{"frame": 0, "x": 900, "y": 60}, {"frame": 30, "x": 760, "y": 140},
                                                     {"frame": 59, "x": 700, "y": 100}]}],
                           "camera": [{"frame": 0, "x": 0, "y": 0, "scale": 1}, {"frame": 59, "x": 40, "y": 0, "scale": 1.05}],
                           "attention_beats": [{"frame": 15, "actor": "hero"}, {"frame": 25, "actor": "moth"}],
                           "events": [{"event_id": "e1", "actor": "hero", "from": 20, "to": 30},
                                      {"event_id": "e2", "actor": "moth", "from": 20, "to": 40}],
                           "audio": {"required": True, "cues": [{"frame": 20, "kind": "DIRECTED_CUE", "event_id": "e2"}]}}}
    return decs, scope, brief


def _program(decs, scope, brief):
    from vme.render.motion_program import compile_event_program
    return compile_event_program(decisions=decs, scope=scope, brief=brief, pack={"states": {}}, width=320, height=180, scale=0.25)


def c01_stage2_never_executed():
    from vme.fixtures.synthetic import build_synthetic_skill, fixture_caps, synthetic_brief
    from vme.compiler.compiler import StyleProgramCompiler
    from vme.state.workspace import Workspace
    from vme.providers.gateway import StyleImageGateway, OfflineRecordingTransport
    from vme.providers.runware import RunwareAdapter
    from vme.providers.authorization import AuthorizationRegistry
    td = Path(tempfile.mkdtemp(prefix="r3c01_"))
    h = build_synthetic_skill(td / "skill", extra_refs=4, overflow_policy="STAGED_EDIT")
    caps = fixture_caps()
    job = StyleProgramCompiler().compile(synthetic_brief(), td / "skill", pinned_skill_hash=h, recipe_id="character_world",
                                         node_id="n1_scene", caps=caps)
    import base64, hashlib
    # oracle: the exact data-URI bytes of EVERY required reference image (read independently from the skill folder)
    by_sha = {hashlib.sha256(p.read_bytes()).hexdigest(): p for p in (td / "skill" / "references").glob("*.png")}
    required = {hashlib.sha256(("data:image/png;base64," + base64.b64encode(by_sha[r["sha256"]].read_bytes()).decode()).encode())
                .hexdigest() for r in job.trace["reference_trace"]}
    st = Workspace(td / "ws").ensure().store()
    t = OfflineRecordingTransport(td / "rt")
    g = StyleImageGateway(st, td / "art", RunwareAdapter(caps, t, kind="OFFLINE_RECORDING"), AuthorizationRegistry(td / "authz"))
    g.submit(job)
    sent = t.sent_bodies()
    sent_ref_shas = {s for b in sent for s in ((b.get("task") or {}).get("inputs") or {}).get("referenceImages_sha256", [])}
    missing = sorted(required - sent_ref_shas)
    return {"defect_present": bool(missing), "image_requests_sent": len(sent), "required_reference_shas": len(required),
            "never_submitted_reference_shas": len(missing)}


def c02_y_keyframes_not_scaled():
    decs, scope, brief = _motion_fixture()
    p = _program(decs, scope, brief)
    moth = next(t for t in p["tracks"] if t["kind"] == "ACTOR_ACTING" and t["actor_id"] == "moth")
    ys = [k["y"] for k in moth["keyframes"] if "y" in k]
    # oracle: 1280x720 -> 320x180 maps every y by 0.25; the first moth y keyframe (60) must become 15
    first_y = ys[0] if ys else None
    return {"defect_present": first_y != 15.0, "first_moth_y_keyframe": first_y, "expected": 15.0}


def c03_attention_targets_dropped():
    from vme.render.motion_program import apply_program
    decs, scope, brief = _motion_fixture()
    p = _program(decs, scope, brief)
    scene = apply_program({"width": 320, "height": 180, "fps": 30, "durationInFrames": 60, "background": "#000",
                           "layers": [{"id": "hero", "src": "h.png", "x": 50, "y": 45, "w": 120, "h": 120, "z": 1},
                                      {"id": "moth", "src": "m.png", "x": 205, "y": 20, "w": 80, "h": 80, "z": 2}]}, p)
    per_layer = {l["id"]: bool(l.get("attention") or l.get("attentionKeyframes")) for l in scene["layers"]}
    return {"defect_present": not any(per_layer.values()), "per_layer_attention_consumed": per_layer,
            "scene_level_attention_keys": sorted(k for k in scene if "atten" in k.lower())}


def c04_cue_on_event_equals_ease():
    from vme.render.motion_program import _segment_keys
    k0, k1 = {"frame": 0, "x": 0.0}, {"frame": 30, "x": 100.0}
    try:
        a = _segment_keys(k0, k1, "x", {"method": "CUE_ON_EVENT"})
    except Blocked as e:
        return {"defect_present": False, "blocked": e.code}
    b = _segment_keys(k0, k1, "x", {"method": "EASE_IN_OUT"})
    return {"defect_present": a == b, "cue_on_event_keys": a, "ease_keys": b}


def c04_fixed_world_parallax():
    decs, scope, brief = _motion_fixture()
    try:
        p = _program(decs, scope, brief)
    except Blocked as e:
        return {"defect_present": False, "blocked": e.code}
    w = next((t for t in p["tracks"] if t["kind"] == "WORLD"), None)
    owned = bool(w) and w.get("parallax_owner") is not None
    return {"defect_present": bool(w) and not owned, "parallax_factor": (w or {}).get("parallax_factor"),
            "parallax_owner": (w or {}).get("parallax_owner")}


def c06_same_frame_cues_deduplicated():
    decs, scope, brief = _motion_fixture()
    p = _program(decs, scope, brief)
    at20 = [c for c in p["audio_cues"] if c["frame"] == 20]
    # two semantic cues coincide at frame 20 (event e2 onset + directed cue e2 with distinct kinds) plus e1 onset
    return {"defect_present": len(at20) < 3, "cues_at_frame_20": at20}


def _resp(o):
    return {"frame_observations": [o], "packet_transition_graph": {"edges": []}, "boundary_state": {}}


def _minimal_obs():
    return {"frame_id": "f1", "source_sha": FA, "pts_time": 0.5, "request_id": "r", "submitted_image_sha": "i1",
            "active_question_ids": [], "scene_and_world_state": "", "actually_visible_actor_and_object_ids": [],
            "focal_whole_artwork_state": "The red focal circle overlaps a blue circle behind it",
            "visible_design_relations": [{"relation": "The red focal circle overlaps a blue circle behind it"}],
            "character_face_limb_contact_state": None, "visible_layer_depth_attention_state": None,
            "changed_since_prior_frame": [], "no_significant_change_reason": "first frame", "simultaneous_event_links": [],
            "camera_vs_actor_vs_drawing_state": None, "material_finish_or_colour_change": None, "native_detail_followups": [],
            "source_fact_statements": [], "hypothesis_or_uncertainty": None, "confidence_limitations": None,
            "persistent_state_ids": [], "unexplained_phenomena": []}


MAN = [{"frame_id": "f1", "source_sha": FA, "pts_time": 0.5, "image_sha": "i1"}]


def c08_minimal_record_validated():
    from vme.vision.contracts import validate_packet_response
    v = validate_packet_response(_resp(_minimal_obs()), MAN, None, images_actually_sent=1)
    return {"defect_present": v.get("status") == "VALIDATED", "status": v.get("status"), "problems": v.get("problems", [])[:6]}


def c08_null_pts_validated():
    from vme.vision.contracts import validate_packet_response
    o = _minimal_obs()
    o["pts_time"] = None
    v = validate_packet_response(_resp(o), MAN, None, images_actually_sent=1)
    return {"defect_present": not any("PTS" in p for p in v.get("problems", [])), "status": v.get("status"),
            "problems": v.get("problems", [])[:6]}


def c10_single_fact_sufficient():
    from vme.vision.protocol import assess_sufficiency
    ans = {"answer_status": "OBSERVED",
           "SOURCE_VISIBLE_FACTS": [{"relation": "Red body is in front of blue body near the lower left", "witness_ids": ["W1"]}],
           "CONSTRUCTION_EXPLANATION": "The visible overlap indicates one drawing occludes another here",
           "BRANCHES": [{"operation_id": "op.whole_scene", "construction_action": "Draw red in front of blue to express the overlap"}]}
    v = assess_sufficiency(ans, producing_operator="op.whole_scene", known_witness_ids={"W1"})
    return {"defect_present": v["verdict"] == "SUFFICIENT_FOR_PRODUCING_CHOICE", "verdict": v["verdict"], "reasons": v["reasons"]}


def _has(mod, name):
    try:
        m = __import__(mod, fromlist=[name])
        return hasattr(m, name)
    except Exception:
        return False


def missing_capabilities():
    return {
        "C05_part_rig_route": {"defect_present": not _has("vme.render.rig", "compile_rig_program")},
        "C06_transcript_index": {"defect_present": not _has("vme.reference.transcript", "build_audiovisual_event_index")},
        "C07_inspect_range": {"defect_present": not _has("vme.reference.navigator", "inspect_range")},
        "C07_search_events": {"defect_present": not _has("vme.reference.navigator", "search_events")},
        "C09_state_inventory": {"defect_present": not _has("vme.style.source_ledger", "character_state_inventory")},
        "C11_readiness_stages": {"defect_present": not _has("vme.review.qualification", "READINESS_STAGES")},
        "C10_visual_qualification": {"defect_present": not _has("vme.review.visual_qualification", "qualify_branch_output")},
    }


REPRODUCERS = {"C01_stage2_never_executed": c01_stage2_never_executed, "C02_y_keyframes_not_scaled": c02_y_keyframes_not_scaled,
               "C03_attention_targets_dropped": c03_attention_targets_dropped, "C04_cue_on_event_equals_ease": c04_cue_on_event_equals_ease,
               "C04_fixed_world_parallax": c04_fixed_world_parallax, "C06_same_frame_cues_deduplicated": c06_same_frame_cues_deduplicated,
               "C08_minimal_record_validated": c08_minimal_record_validated, "C08_null_pts_validated": c08_null_pts_validated,
               "C10_single_fact_sufficient": c10_single_fact_sufficient}


def run() -> dict:
    out = {}
    for k, fn in REPRODUCERS.items():
        try:
            out[k] = fn()
        except Blocked as e:
            out[k] = {"defect_present": False, "closed_by_block": e.code, "detail": str(e)[:300]}
        except Exception as e:  # noqa: BLE001
            out[k] = {"defect_present": None, "ERROR": repr(e)[:300], "trace": traceback.format_exc()[-1200:]}
    out.update(missing_capabilities())
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import subprocess
    res = {"git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
           "results": run()}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: v.get("defect_present") for k, v in res["results"].items()}, indent=1))
