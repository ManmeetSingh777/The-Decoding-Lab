"""R3 F13 — skill-owned motion / camera / attention / world / audio-cue event program.

The DIRECTED shot plan (original content) says WHERE actors and the camera go and WHEN events happen. HOW they move — hold,
anticipation, overshoot, easing, stepped redraw, cue placement — is owned by a source-derived decision branch whose `motion_program`
was authored through the guarded writer. Every track records its owner decision/branch; a required track without an owning
decision is BLOCKED (`MOTION_TRACK_UNOWNED`) — there is no default linear interpolation and no WHOLE_STATE_SWAP-only acting.
Removing or changing the owning decision changes the time-coded keyframes (local ablation), which tests assert.
"""
from __future__ import annotations

from ..util import Blocked, digest

METHODS = ("EASE_IN_OUT", "HOLD_THEN_MOVE", "ANTICIPATE_OVERSHOOT", "STEPPED_REDRAW", "CUE_ON_EVENT")
TRACK_OPS = {"ACTOR_ACTING": "op.motion_actor_track", "CAMERA": "op.camera_attention", "ATTENTION": "op.attention_focus",
             "WORLD": "op.world_motion", "AUDIO": "op.audio_cue"}
CHOICE_FOR_TRACK = {"ACTOR_ACTING": "{actor}:acting", "CAMERA": "camera:depth", "ATTENTION": "attention:focus", "WORLD": "world:motion",
                    "AUDIO": "audio_timing"}


def _owner(decisions: list[dict], plan: dict, track: str, actor: str | None) -> tuple[dict, dict]:
    from ..style.coverage import owns
    cid = CHOICE_FOR_TRACK[track].format(actor=actor)
    choice = next((c for c in plan["choices"] if c["choice_id"] == cid), None)
    if choice is None:
        raise Blocked("MOTION_CHOICE_NOT_PLANNED", f"{cid}: the original scope does not declare this motion need")
    op = TRACK_OPS[track]
    for d in decisions:
        if d.get("status") == "RESEARCH_ONLY" or not owns(d, cid, choice["dimensions"]):
            continue
        for b in d.get("branches", []):
            if op in b.get("operation_node_ids", []) and all(str(choice["conditions"].get(k)) == str(v) for k, v in b["when"].items()) \
                    and set(choice["conditions"]) <= set(b["when"]):
                mp = b.get("motion_program") or {}
                if mp.get("track_kind") != track or mp.get("method") not in METHODS:
                    raise Blocked("MOTION_PROGRAM_INVALID", f"{d['decision_id']}: {mp}")
                return d, b
    raise Blocked("MOTION_TRACK_UNOWNED", f"{track} for {actor or 'scene'}: no source-derived decision owns {cid} (no default motion)")


def _segment_keys(k0: dict, k1: dict, prop: str, mp: dict) -> list[dict]:
    """Expand one directed segment with the learned timing method into explicit keyframes (with per-segment easing)."""
    f0, f1 = int(k0["frame"]), int(k1["frame"])
    v0, v1 = float(k0[prop]), float(k1[prop])
    dur = max(1, f1 - f0)
    m = mp["method"]
    if m == "STEPPED_REDRAW":
        return [{"frame": f1 - 1, prop: v0, "easing": "hold"}, {"frame": f1, prop: v1, "easing": "hold"}]
    if m == "HOLD_THEN_MOVE":
        h = f0 + max(1, int(dur * float(mp.get("hold_ratio", 0.25))))
        return [{"frame": h, prop: v0, "easing": "hold"}, {"frame": f1, prop: v1, "easing": "ease_in_out"}]
    if m == "ANTICIPATE_OVERSHOOT":
        delta = v1 - v0
        h = f0 + max(1, int(dur * float(mp.get("hold_ratio", 0.0))))
        a = min(f1 - 2, h + max(1, int(dur * 0.2)))
        o = max(a + 1, f1 - max(1, int(dur * 0.15)))
        return [{"frame": h, prop: v0, "easing": "hold"},
                {"frame": a, prop: v0 - delta * float(mp.get("anticipation_ratio", 0.1)), "easing": "ease_in_out"},
                {"frame": o, prop: v1 + delta * float(mp.get("overshoot_ratio", 0.08)), "easing": "ease_in_out"},
                {"frame": f1, prop: v1, "easing": "ease_in_out"}]
    return [{"frame": f1, prop: v1, "easing": "ease_in_out"}]


def _expand(keys: list[dict], props: tuple, mp: dict) -> list[dict]:
    keys = sorted(keys, key=lambda k: k["frame"])
    out = [dict(keys[0])]
    for k0, k1 in zip(keys, keys[1:]):
        merged: dict[int, dict] = {}
        for prop in props:
            if prop in k0 and prop in k1:
                for kk in _segment_keys(k0, k1, prop, mp):
                    merged.setdefault(kk["frame"], {"frame": kk["frame"]}).update({prop: kk[prop], "easing": kk["easing"]})
        for f in sorted(merged):
            out.append(merged[f])
    return out


def compile_event_program(*, decisions: list[dict], scope, brief: dict, pack: dict, width: int, height: int, scale: float) -> dict:
    from ..style.coverage import reverse_plan
    plan = reverse_plan(scope)
    sp = brief["shot_plan"]
    n = int(sp["frames"])
    tracks, contacts = [], []
    for a in sp["actors"]:
        keys = [dict(k, x=k["x"] * scale) if "x" in k else dict(k) for k in a.get("keyframes", [])]
        if len(keys) > 1:
            d, b = _owner(decisions, plan, "ACTOR_ACTING", a["id"])
            tracks.append({"kind": "ACTOR_ACTING", "actor_id": a["id"], "owner_decision_id": d["decision_id"], "branch_when": b["when"],
                           "method": b["motion_program"]["method"], "interpolation_or_redraw_method": b["motion_program"]["method"],
                           "start_frame": int(keys[0]["frame"]), "end_frame": min(n - 1, int(keys[-1]["frame"])),
                           "keyframes": _expand(keys, ("x", "y", "rotation", "scale"), b["motion_program"])})
        states = [e for e in sp.get("events", []) if e.get("actor", a["id"]) == a["id"] and e.get("state")]
        for e in states:
            st_ = pack["states"].get(f"{a['id']}:{e['state']}") or pack["states"].get(e["state"])
            if st_ is None:
                raise Blocked("EVENT_STATE_NOT_PRODUCED", str(e))
            tracks.append({"kind": "ACTOR_DRAWING_STATE", "actor_id": a["id"], "owner_decision_id": (st_.get("clause_ids") or ["?"])[0].split("-")[1]
                           if st_.get("clause_ids") else None, "clause_ids": st_.get("clause_ids"), "method": "STEPPED_REDRAW",
                           "interpolation_or_redraw_method": "APPROVED_REDRAWN_STATE", "start_frame": int(e["from"]),
                           "end_frame": int(e["to"]), "state": e["state"], "asset_sha256": st_["sha256"]})
            if "grip" in e["state"]:
                contacts.append({"owner_actor_id": a["id"], "event_id": e.get("event_id"), "state": e["state"],
                                 "world_anchor_or_prop_id": (st_.get("contact") or {}).get("prop"), "occlusion_and_grip_state_sha": st_["sha256"],
                                 "hand_side": (st_.get("contact") or {}).get("hand_side"), "owner_clause_ids": st_.get("clause_ids")})
    cam = sp.get("camera") or []
    if len(cam) > 1:
        d, b = _owner(decisions, plan, "CAMERA", None)
        tracks.append({"kind": "CAMERA", "owner_decision_id": d["decision_id"], "branch_when": b["when"], "method": b["motion_program"]["method"],
                       "interpolation_or_redraw_method": b["motion_program"]["method"], "start_frame": int(cam[0]["frame"]),
                       "end_frame": min(n - 1, int(cam[-1]["frame"])), "keyframes": _expand(cam, ("x", "y", "scale"), b["motion_program"])})
    if sp.get("attention_beats"):
        d, b = _owner(decisions, plan, "ATTENTION", None)
        keys = []
        for beat in sp["attention_beats"]:
            f = int(beat["frame"])
            keys += [{"frame": max(0, f - 1), "scale": 1.0}, {"frame": min(n - 1, f + 8), "scale": 1.0 + float(beat.get("emphasis", 0.04))},
                     {"frame": min(n - 1, f + 20), "scale": 1.0}]
        tracks.append({"kind": "ATTENTION", "owner_decision_id": d["decision_id"], "branch_when": b["when"], "method": b["motion_program"]["method"],
                       "interpolation_or_redraw_method": b["motion_program"]["method"], "start_frame": keys[0]["frame"], "end_frame": keys[-1]["frame"],
                       "targets": [x.get("actor") for x in sp["attention_beats"]], "keyframes": _expand(keys, ("scale",), b["motion_program"])})
    if len(cam) > 1 and (scope.world or {}).get("layers"):
        d, b = _owner(decisions, plan, "WORLD", None)
        keys = [{"frame": int(k["frame"]), "x": -0.5 * float(k.get("x", 0))} for k in cam]
        tracks.append({"kind": "WORLD", "owner_decision_id": d["decision_id"], "branch_when": b["when"], "method": b["motion_program"]["method"],
                       "interpolation_or_redraw_method": b["motion_program"]["method"], "start_frame": keys[0]["frame"], "end_frame": keys[-1]["frame"],
                       "parallax_factor": 0.5, "keyframes": _expand(keys, ("x",), b["motion_program"])})
    cues = []
    if (sp.get("audio") or {}).get("required"):
        d, b = _owner(decisions, plan, "AUDIO", None)
        for e in sp.get("events", []):
            cues.append({"frame": int(e["from"]), "event_id": e.get("event_id"), "kind": "EVENT_CUE"})
        for c in sp["audio"].get("cues", []):
            cues.append({"frame": int(c["frame"]), "event_id": c.get("event_id"), "kind": c.get("kind", "DIRECTED_CUE")})
        cues = sorted({c["frame"]: c for c in cues}.values(), key=lambda c: c["frame"])
        tracks.append({"kind": "AUDIO", "owner_decision_id": d["decision_id"], "branch_when": b["when"], "method": b["motion_program"]["method"],
                       "interpolation_or_redraw_method": b["motion_program"]["method"], "start_frame": cues[0]["frame"] if cues else 0,
                       "end_frame": cues[-1]["frame"] if cues else 0, "cues": cues})
    for t in tracks:
        if not 0 <= t["start_frame"] <= t["end_frame"] < n:
            raise Blocked("TRACK_OUTSIDE_SCENE_TIMEBASE", f"{t['kind']} {t['start_frame']}..{t['end_frame']} of {n}")
    prog = {"tracks": tracks, "contacts": contacts, "audio_cues": cues, "frames": n,
            "expected_independent_motion": any(t["kind"] in ("ACTOR_ACTING", "CAMERA", "WORLD") for t in tracks)}
    prog["program_sha"] = digest(prog)
    return prog


def apply_program(scene: dict, prog: dict) -> dict:
    """Consume the program in the Remotion scene graph: actor/world/camera keyframes with per-segment easing."""
    by_actor = {t["actor_id"]: t for t in prog["tracks"] if t["kind"] == "ACTOR_ACTING"}
    for lay in scene["layers"]:
        if lay["id"] in by_actor:
            lay["keyframes"] = by_actor[lay["id"]]["keyframes"]
        if lay["id"] == "world":
            w = next((t for t in prog["tracks"] if t["kind"] == "WORLD"), None)
            if w:
                lay["keyframes"] = w["keyframes"]
    cam = next((t for t in prog["tracks"] if t["kind"] == "CAMERA"), None)
    att = next((t for t in prog["tracks"] if t["kind"] == "ATTENTION"), None)
    scene["camera"] = {"keyframes": cam["keyframes"] if cam else [{"frame": 0, "x": 0, "y": 0, "scale": 1.0}]}
    if att:
        scene["attention"] = {"keyframes": att["keyframes"]}
    scene["motion_contract"] = {"expected_independent_motion": prog["expected_independent_motion"], "program_sha": prog["program_sha"]}
    scene["event_program_sha"] = prog["program_sha"]
    return scene
