"""R3 F13 + R3-C02/C03/C04/C06 — skill-owned motion / camera / attention / world / audio-cue event program.

Ownership (recorded per numeric parameter in `parameter_ownership`):
  * DIRECTOR_BRIEF — original narrative content: WHICH actors exist, WHERE they are placed and go, WHEN events / attention beats
    happen and on WHOM. A director value is labelled with its exact `shot_plan` path; the brief may NOT carry style magnitudes or timing
    grammar (an `emphasis`, easing or coefficient in the brief is refused: DIRECTOR_SUPPLIED_STYLE_PARAMETER).
  * SKILL_DECISION — HOW things move: method and every method parameter (holds, anticipation/overshoot ratio AND span, attention
    mechanism, transition/hold/release frames and magnitude, per-depth parallax coefficients, cue offsets). Each comes from the
    source-derived decision branch that owns the track; a missing parameter is MOTION_PARAMETER_UNOWNED — there is no default.
  * DEFINITIONAL — values that are true by construction, not taste (actors sit on the camera's reference plane: coefficient 1.0).

Methods are dispatched EXHAUSTIVELY per track (TRACK_METHOD_PARAMS); an unknown or track-inappropriate method is
UNSUPPORTED_METHOD_FOR_TRACK — never a catch-all ease. Coordinates go through ONE ShotCoordinateSpace (vme.render.coords).
"""
from __future__ import annotations

from ..util import Blocked, digest
from .coords import ShotCoordinateSpace, check_on_canvas, complete_keys

# per-track method contracts: method -> required numeric parameters (all must be supplied by the owning skill branch)
TRACK_METHOD_PARAMS: dict[str, dict[str, tuple]] = {
    "ACTOR_ACTING": {"EASE_IN_OUT": (), "HOLD_THEN_MOVE": ("hold_ratio",),
                     "ANTICIPATE_OVERSHOOT": ("hold_ratio", "anticipation_ratio", "anticipation_span", "overshoot_ratio", "overshoot_span")},
    "CAMERA": {"EASE_IN_OUT": (), "HOLD_THEN_MOVE": ("hold_ratio",)},
    "ATTENTION": {"DIM_OTHERS": ("transition_frames", "hold_frames", "release_frames", "magnitude"),
                  "LOCAL_HIGHLIGHT": ("transition_frames", "hold_frames", "release_frames", "magnitude"),
                  "LOCAL_SCALE": ("transition_frames", "hold_frames", "release_frames", "magnitude")},
    "WORLD": {"PARALLAX_LAYERS": ("layer_coefficients",)},
    "AUDIO": {"CUE_ON_EVENT": ("cue_offset_frames",)},
}
METHODS = tuple(sorted({m for d in TRACK_METHOD_PARAMS.values() for m in d} | {"STEPPED_REDRAW"}))
KEYFRAME_METHODS = ("EASE_IN_OUT", "HOLD_THEN_MOVE", "ANTICIPATE_OVERSHOOT")
TRACK_OPS = {"ACTOR_ACTING": "op.motion_actor_track", "CAMERA": "op.camera_attention", "ATTENTION": "op.attention_focus",
             "WORLD": "op.world_motion", "AUDIO": "op.audio_cue"}
CHOICE_FOR_TRACK = {"ACTOR_ACTING": "{actor}:acting", "CAMERA": "camera:depth", "ATTENTION": "attention:focus", "WORLD": "world:motion",
                    "AUDIO": "audio_timing"}
DIRECTOR_STYLE_FIELDS = ("emphasis", "easing", "method", "hold_ratio", "parallax", "parallax_factor", "coefficient", "magnitude")


def validate_motion_program(mp: dict | None) -> list[str]:
    """Writer-side + runtime contract check. Returns problems (empty = executable)."""
    if not isinstance(mp, dict):
        return ["MOTION_PROGRAM_MISSING"]
    tk, m = mp.get("track_kind"), mp.get("method")
    if tk not in TRACK_METHOD_PARAMS:
        return [f"MOTION_TRACK_KIND_UNKNOWN:{tk}"]
    if m not in TRACK_METHOD_PARAMS[tk]:
        return [f"UNSUPPORTED_METHOD_FOR_TRACK:{tk}:{m}"]
    probs = []
    for p in TRACK_METHOD_PARAMS[tk][m]:
        v = mp.get(p)
        if p == "layer_coefficients":
            if not isinstance(v, dict) or not v or not all(isinstance(x, (int, float)) and 0 <= x <= 2 for x in v.values()):
                probs.append(f"MOTION_PARAMETER_UNOWNED:{tk}.{p}")
        elif not isinstance(v, (int, float)) or isinstance(v, bool):
            probs.append(f"MOTION_PARAMETER_UNOWNED:{tk}.{p}")
    for p in ("hold_ratio", "anticipation_ratio", "anticipation_span", "overshoot_ratio", "overshoot_span"):
        if p in TRACK_METHOD_PARAMS[tk][m] and isinstance(mp.get(p), (int, float)) and not 0 <= mp[p] <= 1:
            probs.append(f"MOTION_PARAMETER_OUT_OF_RANGE:{tk}.{p}")
    return probs


def _decision_of_clause(cid: str | None) -> str | None:
    """Clause ids are K-<decision_id>-<branch>@<op>; decision ids themselves contain '-' (PC-<hex>)."""
    if not cid or not cid.startswith("K-") or "@" not in cid:
        return None
    return cid[2:].split("@", 1)[0].rsplit("-", 1)[0]


def _owner(decisions: list[dict], plan: dict, track: str, actor: str | None) -> tuple[dict, dict]:
    from ..style.coverage import owns
    cid = CHOICE_FOR_TRACK[track].format(actor=actor)
    choice = next((c for c in plan["choices"] if c["choice_id"] == cid), None)
    if choice is None:
        raise Blocked("MOTION_CHOICE_NOT_PLANNED", f"{cid}: the original scope does not declare this motion need")
    op = TRACK_OPS[track]
    hits: list[tuple[dict, dict]] = []
    for d in decisions:
        if d.get("status") == "RESEARCH_ONLY" or not owns(d, cid, choice["dimensions"]):
            continue
        for b in d.get("branches", []):
            if op in b.get("operation_node_ids", []) and all(str(choice["conditions"].get(k)) == str(v) for k, v in b["when"].items()) \
                    and set(choice["conditions"]) <= set(b["when"]):
                mp = b.get("motion_program") or {}
                if mp.get("track_kind") != track:
                    raise Blocked("MOTION_PROGRAM_INVALID", f"{d['decision_id']}: track_kind {mp.get('track_kind')} != {track}")
                probs = validate_motion_program(mp)
                if probs:
                    code = probs[0].split(":", 1)[0]
                    raise Blocked(code if code in ("UNSUPPORTED_METHOD_FOR_TRACK", "MOTION_PARAMETER_UNOWNED", "MOTION_PARAMETER_OUT_OF_RANGE")
                                  else "MOTION_PROGRAM_INVALID", f"{d['decision_id']}: {probs}")
                hits.append((d, b))
    if not hits:
        raise Blocked("MOTION_TRACK_UNOWNED", f"{track} for {actor or 'scene'}: no source-derived decision owns {cid} (no default motion)")
    progs = {digest({k: v for k, v in h[1]["motion_program"].items() if k not in ("rationale", "witness_ids")}) for h in hits}
    if len(progs) > 1:
        # equally applicable owners prescribing different timing: never resolved by list order (R3 refusal discipline)
        raise Blocked("CONFLICTING_MOTION_OWNERS", f"{track} for {actor or 'scene'}: " +
                      ", ".join(f"{d['decision_id']}={b['motion_program'].get('method')}" for d, b in hits))
    d, b = hits[0]
    b = dict(b, co_owner_decision_ids=sorted({h[0]["decision_id"] for h in hits} - {d["decision_id"]}))
    return d, b


def _segment_keys(k0: dict, k1: dict, prop: str, mp: dict) -> list[dict]:
    """Expand one directed segment with the learned timing method into explicit keyframes. EXHAUSTIVE: only keyframe methods."""
    f0, f1 = int(k0["frame"]), int(k1["frame"])
    v0, v1 = float(k0[prop]), float(k1[prop])
    dur = max(1, f1 - f0)
    m = mp.get("method")
    if m == "EASE_IN_OUT":
        return [{"frame": f1, prop: v1, "easing": "ease_in_out"}]
    if m == "HOLD_THEN_MOVE":
        h = f0 + max(1, int(dur * float(mp["hold_ratio"])))
        return [{"frame": h, prop: v0, "easing": "hold"}, {"frame": f1, prop: v1, "easing": "ease_in_out"}]
    if m == "ANTICIPATE_OVERSHOOT":
        delta = v1 - v0
        h = f0 + max(1, int(dur * float(mp["hold_ratio"])))
        a = min(f1 - 2, h + max(1, int(dur * float(mp["anticipation_span"]))))
        o = max(a + 1, f1 - max(1, int(dur * float(mp["overshoot_span"]))))
        return [{"frame": h, prop: v0, "easing": "hold"},
                {"frame": a, prop: v0 - delta * float(mp["anticipation_ratio"]), "easing": "ease_in_out"},
                {"frame": o, prop: v1 + delta * float(mp["overshoot_ratio"]), "easing": "ease_in_out"},
                {"frame": f1, prop: v1, "easing": "ease_in_out"}]
    raise Blocked("UNSUPPORTED_METHOD_FOR_TRACK", f"{m} is not a keyframe interpolation method")


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


def _refuse_director_style(obj: dict, path: str) -> None:
    bad = [k for k in obj if k in DIRECTOR_STYLE_FIELDS]
    if bad:
        raise Blocked("DIRECTOR_SUPPLIED_STYLE_PARAMETER", f"{path}: {bad} — style timing/magnitude must come from a source-owned skill branch")


def _track(kind, d, b, **kw) -> dict:
    mp = b["motion_program"]
    return {"kind": kind, "owner_decision_id": d["decision_id"], "co_owner_decision_ids": b["co_owner_decision_ids"], "branch_when": b["when"],
            "method": mp["method"], "interpolation_or_redraw_method": mp["method"], **kw}


def compile_event_program(*, decisions: list[dict], scope, brief: dict, pack: dict, width: int, height: int,
                          scale: float | None = None) -> dict:
    from ..style.coverage import reverse_plan
    plan = reverse_plan(scope)
    sp = brief["shot_plan"]
    n = int(sp["frames"])
    space = ShotCoordinateSpace.from_shot_plan(sp, width, height)
    if scale is not None and abs(float(scale) - space.sx) > 1e-9:
        raise Blocked("COORDINATE_SCALE_CONFLICT", f"caller scale {scale} != shot coordinate space sx {space.sx}")
    own: list[dict] = []

    def owned(track, actor, param, value, kind, owner, path=None):
        own.append({"track": track, "actor": actor, "parameter": param, "value": value, "owner_kind": kind, "owner": owner, "path": path})

    tracks: list[dict] = []
    contacts: list[dict] = []
    geometry: dict[str, dict] = {}
    for i, a in enumerate(sp["actors"]):
        _refuse_director_style(a, f"shot_plan.actors[{i}]")
        box = space.box(a)
        geometry[a["id"]] = {**box, "z": int(a["z"])}
        for p in ("x", "y", "w", "h"):
            owned("ACTOR_PLACEMENT", a["id"], p, box[p], "DIRECTOR_BRIEF", a.get("directed_by"), f"shot_plan.actors[{i}].{p}")
        raw = a.get("keyframes", [])
        for j, k in enumerate(raw):
            _refuse_director_style(k, f"shot_plan.actors[{i}].keyframes[{j}]")
        keys = complete_keys([space.key(k) for k in raw], box, ("x", "y"))
        check_on_canvas(space, box, keys, a["id"])
        if len(keys) > 1:
            d, b = _owner(decisions, plan, "ACTOR_ACTING", a["id"])
            mp = b["motion_program"]
            for p in TRACK_METHOD_PARAMS["ACTOR_ACTING"][mp["method"]]:
                owned("ACTOR_ACTING", a["id"], p, mp[p], "SKILL_DECISION", d["decision_id"])
            exp = _expand(keys, ("x", "y", "rotation", "scale"), mp)
            check_on_canvas(space, box, complete_keys(exp, box, ("x", "y")), a["id"])
            tracks.append(_track("ACTOR_ACTING", d, b, actor_id=a["id"], start_frame=int(keys[0]["frame"]),
                                 end_frame=min(n - 1, int(keys[-1]["frame"])), keyframes=exp))
        for e in [e for e in sp.get("events", []) if e.get("actor", a["id"]) == a["id"] and e.get("state")]:
            st_ = pack["states"].get(f"{a['id']}:{e['state']}") or pack["states"].get(e["state"])
            if st_ is None:
                raise Blocked("EVENT_STATE_NOT_PRODUCED", str(e))
            tracks.append({"kind": "ACTOR_DRAWING_STATE", "actor_id": a["id"], "owner_decision_id": _decision_of_clause((st_.get("clause_ids") or [None])[0]),
                           "clause_ids": st_.get("clause_ids"), "method": "STEPPED_REDRAW", "interpolation_or_redraw_method": "APPROVED_REDRAWN_STATE",
                           "start_frame": int(e["from"]), "end_frame": int(e["to"]), "state": e["state"], "asset_sha256": st_["sha256"]})
            if "grip" in e["state"]:
                act = next((x for x in sp.get("actions", []) if x.get("event_id") == e.get("event_id")), {})
                anchor = act.get("contact_anchor")
                contacts.append({"owner_actor_id": a["id"], "event_id": e.get("event_id"), "state": e["state"],
                                 "world_anchor_or_prop_id": (st_.get("contact") or {}).get("prop"), "occlusion_and_grip_state_sha": st_["sha256"],
                                 "hand_side": (st_.get("contact") or {}).get("hand_side"), "owner_clause_ids": st_.get("clause_ids"),
                                 "contact_anchor_px": space.key({"x": anchor["x"], "y": anchor["y"]}) if anchor else None})
    actor_ids = [a["id"] for a in sp["actors"]]
    cam_raw = sp.get("camera") or []
    cam = [space.key(k) for k in cam_raw]
    cam_track = None
    if len(cam) > 1:
        d, b = _owner(decisions, plan, "CAMERA", None)
        mp = b["motion_program"]
        for p in TRACK_METHOD_PARAMS["CAMERA"][mp["method"]]:
            owned("CAMERA", None, p, mp[p], "SKILL_DECISION", d["decision_id"])
        for j, k in enumerate(cam_raw):
            _refuse_director_style(k, f"shot_plan.camera[{j}]")
            for p in ("x", "y", "scale"):
                if p in k:
                    owned("CAMERA_PATH", None, p, k[p], "DIRECTOR_BRIEF", sp.get("camera_directed_by"), f"shot_plan.camera[{j}].{p}")
        cam_track = _track("CAMERA", d, b, start_frame=int(cam[0]["frame"]), end_frame=min(n - 1, int(cam[-1]["frame"])),
                           keyframes=_expand(complete_keys(cam, {"x": 0.0, "y": 0.0, "scale": 1.0}, ("x", "y", "scale")), ("x", "y", "scale"), mp))
        tracks.append(cam_track)
    # ---- R3-C03 attention: typed beats executed per target layer by the skill-owned mechanism ----------------------------------
    beats = sp.get("attention_beats") or []
    layer_attention: dict[str, list[dict]] = {}
    if beats:
        d, b = _owner(decisions, plan, "ATTENTION", None)
        mp = b["motion_program"]
        mech = mp["method"]
        t, hd, r, mag = int(mp["transition_frames"]), int(mp["hold_frames"]), int(mp["release_frames"]), float(mp["magnitude"])
        for p in TRACK_METHOD_PARAMS["ATTENTION"][mech]:
            owned("ATTENTION", None, p, mp[p], "SKILL_DECISION", d["decision_id"])
        typed, last_end = [], -1
        for j, beat in enumerate(sorted(beats, key=lambda x: int(x["frame"]))):
            _refuse_director_style(beat, f"shot_plan.attention_beats[{j}]")
            tgt = beat.get("targets") or ([beat["actor"]] if beat.get("actor") else [])
            if not tgt or any(x not in actor_ids for x in tgt):
                raise Blocked("ATTENTION_TARGET_UNMAPPED", f"beat {j}: {tgt} not among rendered actor layers {actor_ids}")
            on = int(beat["frame"])
            end = on + t + hd + r
            if end > n - 1:
                raise Blocked("TRACK_OUTSIDE_SCENE_TIMEBASE", f"attention beat {j} ends at {end} >= {n}")
            if on <= last_end:
                raise Blocked("ATTENTION_BEATS_OVERLAP", f"beat {j} at {on} starts before the previous beat released ({last_end})")
            last_end = end
            owned("ATTENTION_BEAT", None, "frame", on, "DIRECTOR_BRIEF", sp.get("attention_directed_by"), f"shot_plan.attention_beats[{j}].frame")
            owned("ATTENTION_BEAT", None, "targets", tgt, "DIRECTOR_BRIEF", sp.get("attention_directed_by"), f"shot_plan.attention_beats[{j}].targets")
            affected = [x for x in actor_ids if x not in tgt] if mech == "DIM_OTHERS" else list(tgt)
            prop, peak = {"DIM_OTHERS": ("brightness", 1.0 - mag), "LOCAL_HIGHLIGHT": ("brightness", 1.0 + mag),
                          "LOCAL_SCALE": ("scale", 1.0 + mag)}[mech]
            for lid in affected:
                layer_attention.setdefault(lid, []).extend([
                    {"frame": on, prop: 1.0, "easing": "hold"}, {"frame": on + t, prop: peak, "easing": "ease_in_out"},
                    {"frame": on + t + hd, prop: peak, "easing": "hold"}, {"frame": end, prop: 1.0, "easing": "ease_in_out"}])
            typed.append({"beat_id": f"beat{j}", "targets": tgt, "mechanism": mech, "scope": "LOCAL", "onset": on, "hold_from": on + t,
                          "release_from": on + t + hd, "end": end, "affected_layers": affected, "property": prop, "peak": peak,
                          "concurrent_events": [e.get("event_id") for e in sp.get("events", []) if int(e["from"]) <= on <= int(e["to"])]})
        tracks.append(_track("ATTENTION", d, b, start_frame=typed[0]["onset"], end_frame=typed[-1]["end"], beats=typed,
                             targets=[x for bt in typed for x in bt["targets"]], layer_keyframes=layer_attention,
                             camera_framing_changed=False))
    # ---- R3-C04 world: per-depth layers with skill-owned camera coefficients; actors are on the reference plane (definitional) ---
    world_layers = sp.get("world_layers") or []
    layer_coeff: dict[str, float] = {a: 1.0 for a in actor_ids}
    for a in actor_ids:
        owned("WORLD", a, "camera_coefficient", 1.0, "DEFINITIONAL", "actors sit on the camera reference plane")
    if world_layers and (len(cam) > 1 or any(w.get("keyframes") for w in world_layers)):
        d, b = _owner(decisions, plan, "WORLD", None)
        coeffs = b["motion_program"]["layer_coefficients"]
        wl_out = []
        for j, wl in enumerate(world_layers):
            _refuse_director_style(wl, f"shot_plan.world_layers[{j}]")
            if wl.get("depth") not in coeffs:
                raise Blocked("WORLD_LAYER_UNOWNED", f"world layer {wl.get('id')} depth {wl.get('depth')} has no source-owned camera coefficient")
            k = float(coeffs[wl["depth"]])
            layer_coeff[wl["id"]] = k
            owned("WORLD", wl["id"], "camera_coefficient", k, "SKILL_DECISION", d["decision_id"])
            wkeys = None
            if wl.get("keyframes"):
                box = space.box({"x": wl.get("x", 0), "y": wl.get("y", 0), "w": wl.get("w", sp["plan_width"]), "h": wl.get("h", sp["plan_height"])})
                ks = complete_keys([space.key(x) for x in wl["keyframes"]], box, ("x", "y"))
                ad, ab = _owner(decisions, plan, "ACTOR_ACTING", wl["id"]) if any(c["choice_id"] == f"{wl['id']}:acting" for c in plan["choices"]) \
                    else (None, None)
                if ad is None:
                    raise Blocked("MOTION_TRACK_UNOWNED", f"world object {wl['id']} moves but no decision owns {wl['id']}:acting")
                wkeys = _expand(ks, ("x", "y"), ab["motion_program"])
            wl_out.append({"layer_id": wl["id"], "depth": wl["depth"], "camera_coefficient": k, "keyframes": wkeys})
        tracks.append(_track("WORLD", d, b, start_frame=0, end_frame=n - 1, layers=wl_out, layer_coefficients=dict(coeffs),
                             parallax_owner=d["decision_id"]))
    elif world_layers:
        for wl in world_layers:
            layer_coeff[wl["id"]] = None                                     # static camera, static world: no coefficient is consumed
    # ---- R3-C06 audio cues: every semantic cue is kept (cue ids), coinciding cues are NOT merged ------------------------------
    cues: list[dict] = []
    if (sp.get("audio") or {}).get("required"):
        d, b = _owner(decisions, plan, "AUDIO", None)
        off = int(b["motion_program"]["cue_offset_frames"])
        owned("AUDIO", None, "cue_offset_frames", off, "SKILL_DECISION", d["decision_id"])
        for e in sp.get("events", []):
            cues.append({"cue_id": f"EVENT_ONSET:{e.get('event_id')}", "frame": int(e["from"]) + off, "event_id": e.get("event_id"),
                         "kind": "EVENT_CUE", "layer": "SFX"})
        for j, c in enumerate(sp["audio"].get("cues", [])):
            _refuse_director_style(c, f"shot_plan.audio.cues[{j}]")
            cues.append({"cue_id": f"{c.get('kind', 'DIRECTED_CUE')}:{c.get('event_id') or j}:{int(c['frame'])}", "frame": int(c["frame"]),
                         "event_id": c.get("event_id"), "kind": c.get("kind", "DIRECTED_CUE"), "layer": c.get("layer", "SFX")})
        ids = [c["cue_id"] for c in cues]
        if len(ids) != len(set(ids)):
            raise Blocked("DUPLICATE_CUE_ID", str(sorted({i for i in ids if ids.count(i) > 1})))
        cues.sort(key=lambda c: (c["frame"], c["cue_id"]))
        tracks.append(_track("AUDIO", d, b, start_frame=cues[0]["frame"] if cues else 0, end_frame=cues[-1]["frame"] if cues else 0, cues=cues))
    for t_ in tracks:
        if not 0 <= t_["start_frame"] <= t_["end_frame"] < n:
            raise Blocked("TRACK_OUTSIDE_SCENE_TIMEBASE", f"{t_['kind']} {t_['start_frame']}..{t_['end_frame']} of {n}")
    prog = {"tracks": tracks, "contacts": contacts, "audio_cues": cues, "frames": n, "coordinate_space": space.to_dict(),
            "actor_geometry_px": geometry, "layer_camera_coefficients": layer_coeff, "parameter_ownership": own,
            "expected_independent_motion": any(t_["kind"] in ("ACTOR_ACTING", "CAMERA", "WORLD") for t_ in tracks)}
    prog["program_sha"] = digest(prog)
    return prog


def apply_program(scene: dict, prog: dict) -> dict:
    """Consume EVERY declared track in the Remotion scene graph (pixel units only): actor keyframes, per-layer attention keyframes,
    per-layer camera coefficients (world parallax) and world-object keyframes. A declared track with no consumer is refused."""
    consumed: set = set()
    by_actor = {t["actor_id"]: t for t in prog["tracks"] if t["kind"] == "ACTOR_ACTING"}
    att = next((t for t in prog["tracks"] if t["kind"] == "ATTENTION"), None)
    world = next((t for t in prog["tracks"] if t["kind"] == "WORLD"), None)
    wl = {x["layer_id"]: x for x in (world or {}).get("layers", [])}
    geo = prog.get("actor_geometry_px", {})
    ids = {l["id"] for l in scene["layers"]}
    for lay in scene["layers"]:
        if lay["id"] in geo:
            g = geo[lay["id"]]
            lay.update({"x": g["x"], "y": g["y"], "w": g["w"], "h": g["h"]})
        if lay["id"] in by_actor:
            lay["keyframes"] = by_actor[lay["id"]]["keyframes"]
            consumed.add(("ACTOR_ACTING", lay["id"]))
        if att and lay["id"] in att["layer_keyframes"]:
            lay["attentionKeyframes"] = att["layer_keyframes"][lay["id"]]
            consumed.add(("ATTENTION", lay["id"]))
        k = prog.get("layer_camera_coefficients", {}).get(lay["id"])
        lay["cameraCoefficient"] = 1.0 if k is None else k
        if lay["id"] in wl:
            consumed.add(("WORLD", lay["id"]))
            if wl[lay["id"]]["keyframes"]:
                lay["keyframes"] = wl[lay["id"]]["keyframes"]
    missing = [a for a in by_actor if a not in ids] + ([x for x in att["layer_keyframes"] if x not in ids] if att else []) + \
              [x for x in wl if x not in ids]
    if missing:
        raise Blocked("TRACK_WITHOUT_RENDER_CONSUMER", f"declared tracks target layers absent from the scene: {sorted(set(missing))}")
    cam = next((t for t in prog["tracks"] if t["kind"] == "CAMERA"), None)
    scene["camera"] = {"keyframes": cam["keyframes"] if cam else [{"frame": 0, "x": 0, "y": 0, "scale": 1.0}]}
    scene["units"] = "px"
    scene["coordinate_space"] = prog.get("coordinate_space")
    scene["motion_contract"] = {"expected_independent_motion": prog["expected_independent_motion"], "program_sha": prog["program_sha"]}
    scene["event_program_sha"] = prog["program_sha"]
    scene["consumed_tracks"] = sorted(f"{a}:{b}" for a, b in consumed)
    return scene
