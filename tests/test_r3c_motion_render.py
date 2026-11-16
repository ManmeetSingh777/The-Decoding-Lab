"""R3-C02/C03/C04/C06 — independent oracles for coordinates, targeted attention, per-depth world layers and cue layers.

Expected values are computed HERE by hand from the plan → render transform, never by re-running the compiler; renders go through the
real Remotion renderer and pixels are read back from the MP4 at exact frames.
"""
from __future__ import annotations

import subprocess

import numpy as np
import pytest
from PIL import Image

from vme.reference.probe import require_tool
from vme.util import Blocked

FULL = {"hold_ratio": 0.2, "anticipation_ratio": 0.1, "anticipation_span": 0.2, "overshoot_ratio": 0.1, "overshoot_span": 0.15,
        "cue_offset_frames": 0, "transition_frames": 4, "hold_frames": 10, "release_frames": 4, "magnitude": 0.5}


def _scope_decs(actors, *, attention=None, world=None, coeffs=None, acting="EASE_IN_OUT", props=()):
    from vme.style.coverage import OriginalScope, reverse_plan
    subj = [{"id": a, "kind": "character", "subject_kind": "biped", "actions": ["move"]} for a in actors] + \
           [{"id": p, "kind": "prop", "subject_kind": "object", "actions": ["drift"]} for p in props]
    scope = OriginalScope(scope_id="S", subjects=subj, world={"kind": "space", "layers": bool(world)},
                          camera={"moves": True, "attention_beats": bool(attention)}, audio_cues=[{"event_id": "e1"}])
    plan = reverse_plan(scope)
    cond = {c["choice_id"]: c["conditions"] for c in plan["choices"]}
    dims = {c["choice_id"]: c["dimensions"] for c in plan["choices"]}

    def mk(did, owns, op, kind, m, **extra):
        return {"decision_id": did, "status": "EXECUTABLE_CANDIDATE", "owned_choice_ids": [owns], "dimension_tags": dims[owns],
                "branches": [{"when": cond[owns], "operation_node_ids": [op], "motion_program": {"track_kind": kind, "method": m, **FULL, **extra}}]}
    decs = [mk(f"PC-act-{a}", f"{a}:acting", "op.motion_actor_track", "ACTOR_ACTING", acting) for a in list(actors) + list(props)
            if f"{a}:acting" in cond]
    decs += [mk("PC-cam", "camera:depth", "op.camera_attention", "CAMERA", "EASE_IN_OUT"),
             mk("PC-aud", "audio_timing", "op.audio_cue", "AUDIO", "CUE_ON_EVENT")]
    if attention:
        decs.append(mk("PC-att", "attention:focus", "op.attention_focus", "ATTENTION", attention))
    if world:
        decs.append(mk("PC-wld", "world:motion", "op.world_motion", "WORLD", "PARALLAX_LAYERS", layer_coefficients=coeffs))
    return scope, decs


def _program(scope, decs, sp, W, H):
    from vme.render.motion_program import compile_event_program
    return compile_event_program(decisions=decs, scope=scope, brief={"shot_plan": sp}, pack={"states": {}}, width=W, height=H)


def _png(path, w, h, rgb):
    Image.new("RGB", (int(w), int(h)), rgb).save(path)
    return str(path)


def _frame(mp4, k, W, H):
    ff = require_tool("ffmpeg")
    out = subprocess.run([ff, "-v", "error", "-i", str(mp4), "-vf", f"select=eq(n\\,{k})", "-fps_mode", "passthrough", "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    return np.frombuffer(out.stdout, dtype=np.uint8).reshape(H, W, 3).astype(int)


def _bbox(img, rgb, tol=60):
    m = (np.abs(img - np.array(rgb)).sum(axis=2) < tol)
    ys, xs = np.nonzero(m)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(xs) else None


def _render(tmp_path, scene, assets, name):
    from vme.render.renderer import render_video, REMOTION_DIR
    if not (REMOTION_DIR / "node_modules" / "remotion").exists():
        pytest.skip("remotion not installed")
    out = tmp_path / f"{name}.mp4"
    render_video(scene, assets, out, diagnostic_label="DIAGNOSTIC_NOT_APPROVED")
    return out


# ------------------------------------------------------------------------------------------------ C02 coordinates (numeric)
@pytest.mark.req("R3-C02")
@pytest.mark.parametrize("pw,ph,W,H", [(1280, 720, 320, 180), (1920, 1080, 1536, 864)])
def test_every_coordinate_maps_through_one_transform(pw, ph, W, H):
    sx, sy = W / pw, H / ph
    scope, decs = _scope_decs(["hero"])
    sp = {"frames": 60, "plan_width": pw, "plan_height": ph,
          "actors": [{"id": "hero", "x": pw * 0.3, "y": ph * 0.2, "w": pw * 0.1, "h": ph * 0.2, "z": 1,
                      "keyframes": [{"frame": 0, "x": pw * 0.3, "y": ph * 0.2}, {"frame": 59, "x": pw * 0.5, "y": ph * 0.4}]}],
          "camera": [{"frame": 0, "x": 0, "y": 0, "scale": 1}, {"frame": 59, "x": pw * 0.05, "y": ph * 0.02, "scale": 1}]}
    p = _program(scope, decs, sp, W, H)
    g = p["actor_geometry_px"]["hero"]
    assert (g["x"], g["y"], g["w"], g["h"]) == pytest.approx((pw * 0.3 * sx, ph * 0.2 * sy, pw * 0.1 * sx, ph * 0.2 * sy))
    hero = next(t for t in p["tracks"] if t["kind"] == "ACTOR_ACTING")
    assert (hero["keyframes"][0]["x"], hero["keyframes"][0]["y"]) == pytest.approx((pw * 0.3 * sx, ph * 0.2 * sy))
    assert (hero["keyframes"][-1]["x"], hero["keyframes"][-1]["y"]) == pytest.approx((pw * 0.5 * sx, ph * 0.4 * sy))
    cam = next(t for t in p["tracks"] if t["kind"] == "CAMERA")
    assert (cam["keyframes"][-1]["x"], cam["keyframes"][-1]["y"]) == pytest.approx((pw * 0.05 * sx, ph * 0.02 * sy))


@pytest.mark.req("R3-C02")
def test_the_shipped_moth_example_maps_y():
    scope, decs = _scope_decs(["moth"])
    sp = {"frames": 60, "plan_width": 1280, "plan_height": 720,
          "actors": [{"id": "moth", "x": 820, "y": 80, "w": 320, "h": 320, "z": 3,
                      "keyframes": [{"frame": 0, "x": 900, "y": 60}, {"frame": 30, "x": 760, "y": 140}, {"frame": 59, "x": 700, "y": 100}]}]}
    p = _program(scope, decs, sp, 320, 180)
    k = next(t for t in p["tracks"] if t["kind"] == "ACTOR_ACTING")["keyframes"]
    assert [(x["frame"], x["x"], x["y"]) for x in k] == [(0, 225.0, 15.0), (30, 190.0, 35.0), (59, 175.0, 25.0)]


@pytest.mark.req("R3-C02")
def test_aspect_mismatch_is_refused_unless_axes_are_declared_independent():
    scope, decs = _scope_decs(["hero"])
    sp = {"frames": 30, "plan_width": 1280, "plan_height": 720,
          "actors": [{"id": "hero", "x": 100, "y": 90, "w": 100, "h": 90, "z": 1, "keyframes": []}]}
    with pytest.raises(Blocked) as e:
        _program(scope, decs, sp, 320, 240)
    assert e.value.code == "ASPECT_RATIO_MISMATCH"
    p = _program(scope, decs, dict(sp, aspect_policy="INDEPENDENT_AXES"), 320, 240)
    assert p["actor_geometry_px"]["hero"] == pytest.approx({"x": 25.0, "y": 30.0, "w": 25.0, "h": 30.0, "z": 1})
    with pytest.raises(Blocked) as e:
        _program(scope, decs, {k: v for k, v in sp.items() if k != "plan_height"}, 320, 180)
    assert e.value.code == "COORDINATE_SPACE_UNDECLARED"


@pytest.mark.req("R3-C02")
def test_actor_driven_off_canvas_is_refused():
    scope, decs = _scope_decs(["hero"])
    sp = {"frames": 30, "plan_width": 1280, "plan_height": 720,
          "actors": [{"id": "hero", "x": 100, "y": 90, "w": 100, "h": 90, "z": 1, "keyframes": [{"frame": 0, "x": 100}, {"frame": 29, "x": 1400}]}]}
    with pytest.raises(Blocked) as e:
        _program(scope, decs, sp, 320, 180)
    assert e.value.code == "ACTOR_OUTSIDE_CANVAS"


# ------------------------------------------------------------------------------------------------ C02 coordinates (rendered pixels)
@pytest.mark.req("R3-C02")
def test_rendered_pixels_match_the_hand_computed_transform(tmp_path):
    from vme.render.motion_program import apply_program
    W, H = 320, 180                                   # plan 1280x720 -> factor 0.25 on BOTH axes
    scope, decs = _scope_decs(["red"])
    sp = {"frames": 61, "plan_width": 1280, "plan_height": 720,
          "actors": [{"id": "red", "x": 400, "y": 240, "w": 160, "h": 160, "z": 1,
                      "keyframes": [{"frame": 0, "x": 400, "y": 240}, {"frame": 60, "x": 800, "y": 360}]}]}
    p = _program(scope, decs, sp, W, H)
    scene = apply_program({"width": W, "height": H, "fps": 30, "durationInFrames": 61, "background": "#000000",
                           "layers": [{"id": "red", "src": "red.png", "x": 0, "y": 0, "w": 0, "h": 0, "z": 1}]}, p)
    mp4 = _render(tmp_path, scene, {"red.png": _png(tmp_path / "red.png", 40, 40, (255, 0, 0))}, "coords")
    for k, (ex, ey) in {0: (100, 60), 30: (150, 75), 60: (200, 90)}.items():   # cubic in-out passes exactly through its midpoint
        bb = _bbox(_frame(mp4, k, W, H), (255, 0, 0))
        assert bb is not None and abs(bb[0] - ex) <= 2 and abs(bb[1] - ey) <= 2 and abs(bb[2] - (ex + 40)) <= 2 and abs(bb[3] - (ey + 40)) <= 2, (k, bb)


# ------------------------------------------------------------------------------------------------ C03 targeted attention
def _two_actor_attention(tmp_path, mech, beats, name):
    from vme.render.motion_program import apply_program
    W, H = 320, 180
    scope, decs = _scope_decs(["a", "b"], attention=mech)
    sp = {"frames": 50, "plan_width": 1280, "plan_height": 720, "attention_directed_by": "test author",
          "actors": [{"id": "a", "x": 160, "y": 240, "w": 320, "h": 240, "z": 1, "keyframes": []},
                     {"id": "b", "x": 800, "y": 240, "w": 320, "h": 240, "z": 2, "keyframes": []}],
          "attention_beats": beats}
    p = _program(scope, decs, sp, W, H)
    scene = apply_program({"width": W, "height": H, "fps": 30, "durationInFrames": 50, "background": "#000000",
                           "layers": [{"id": "a", "src": "a.png", "x": 0, "y": 0, "w": 0, "h": 0, "z": 1},
                                      {"id": "b", "src": "b.png", "x": 0, "y": 0, "w": 0, "h": 0, "z": 2}]}, p)
    mp4 = _render(tmp_path, scene, {"a.png": _png(tmp_path / "a.png", 80, 60, (120, 60, 60)),
                                    "b.png": _png(tmp_path / "b.png", 80, 60, (60, 120, 60))}, name)
    reg = lambda img, x: img[65:115, x:x + 70].mean()      # interior of a (x 40..120) and b (x 200..280), plan/4
    return p, scene, mp4, (lambda k: (reg(_frame(mp4, k, W, H), 45), reg(_frame(mp4, k, W, H), 205)))


@pytest.mark.req("R3-C03")
def test_dim_others_switches_saliency_between_actors_with_camera_held(tmp_path):
    p, scene, mp4, lum = _two_actor_attention(tmp_path, "DIM_OTHERS", [{"frame": 5, "targets": ["a"]}, {"frame": 26, "targets": ["b"]}], "dim")
    a0, b0 = lum(0)
    a1, b1 = lum(12)                    # beat 1 holds frames 9..19: b dimmed to (1-0.5), a untouched
    a2, b2 = lum(33)                    # beat 2 holds frames 30..40: a dimmed, b restored
    assert abs(a1 - a0) < 3 and b1 < 0.65 * b0
    assert abs(b2 - b0) < 3 and a2 < 0.65 * a0
    assert len(scene["camera"]["keyframes"]) == 1                                   # framing held fixed (local mechanism)
    att = next(t for t in p["tracks"] if t["kind"] == "ATTENTION")
    assert [bt["affected_layers"] for bt in att["beats"]] == [["b"], ["a"]] and att["camera_framing_changed"] is False


@pytest.mark.req("R3-C03")
def test_a_different_mechanism_changes_the_target_pixels_not_all_pixels(tmp_path):
    p, scene, mp4, lum = _two_actor_attention(tmp_path, "LOCAL_HIGHLIGHT", [{"frame": 5, "targets": ["a"]}], "hi")
    a0, b0 = lum(0)
    a1, b1 = lum(12)
    assert a1 > 1.3 * a0 and abs(b1 - b0) < 3                                       # only the target brightens


@pytest.mark.req("R3-C03")
def test_wrong_target_unknown_mechanism_and_director_emphasis_are_refused():
    scope, decs = _scope_decs(["a", "b"], attention="DIM_OTHERS")
    base = {"frames": 50, "plan_width": 1280, "plan_height": 720,
            "actors": [{"id": "a", "x": 160, "y": 240, "w": 320, "h": 240, "z": 1, "keyframes": []},
                       {"id": "b", "x": 800, "y": 240, "w": 320, "h": 240, "z": 2, "keyframes": []}]}
    for beats, code in (([{"frame": 5, "targets": ["ghost"]}], "ATTENTION_TARGET_UNMAPPED"),
                        ([{"frame": 5, "targets": ["a"], "emphasis": 0.04}], "DIRECTOR_SUPPLIED_STYLE_PARAMETER"),
                        ([{"frame": 5, "targets": ["a"]}, {"frame": 10, "targets": ["b"]}], "ATTENTION_BEATS_OVERLAP")):
        with pytest.raises(Blocked) as e:
            _program(scope, decs, dict(base, attention_beats=beats), 320, 180)
        assert e.value.code == code
    scope, decs = _scope_decs(["a", "b"], attention="HOLD_THEN_MOVE")             # a timing method is not an attention mechanism
    with pytest.raises(Blocked) as e:
        _program(scope, decs, dict(base, attention_beats=[{"frame": 5, "targets": ["a"]}]), 320, 180)
    assert e.value.code == "UNSUPPORTED_METHOD_FOR_TRACK"


# ------------------------------------------------------------------------------------------------ C04 world depth / methods
@pytest.mark.req("R3-C04")
def test_three_world_depths_move_by_their_own_source_coefficients(tmp_path):
    from vme.render.motion_program import apply_program
    W, H = 320, 180
    scope, decs = _scope_decs(["hero"], world=True, coeffs={"far": 0.2, "mid": 0.5, "near": 1.0})
    sp = {"frames": 31, "plan_width": 1280, "plan_height": 720, "camera_directed_by": "test",
          "world_layers": [{"id": "far", "depth": "far"}, {"id": "mid", "depth": "mid"}, {"id": "near", "depth": "near"}],
          "actors": [{"id": "hero", "x": 1100, "y": 560, "w": 80, "h": 80, "z": 5, "keyframes": [{"frame": 0, "x": 1100}, {"frame": 30, "x": 1120}]}],
          "camera": [{"frame": 0, "x": 0, "y": 0, "scale": 1}, {"frame": 30, "x": 160, "y": 0, "scale": 1}]}   # 160 plan = 40 px
    p = _program(scope, decs, sp, W, H)
    assert p["layer_camera_coefficients"] == {"hero": 1.0, "far": 0.2, "mid": 0.5, "near": 1.0}
    own = {(r["actor"], r["parameter"]): r for r in p["parameter_ownership"] if r["track"] == "WORLD"}
    assert own[("far", "camera_coefficient")]["owner"] == "PC-wld" and own[("hero", "camera_coefficient")]["owner_kind"] == "DEFINITIONAL"

    def stripe(name, x, rgb):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))               # transparent: only the stripe is visible
        for yy in range(H):
            for xx in range(x, x + 10):
                img.putpixel((xx, yy), (*rgb, 255))
        img.save(tmp_path / name)
        return str(tmp_path / name)
    layers = [{"id": "far", "src": "far.png", "x": 0, "y": 0, "w": W, "h": H, "z": -3},
              {"id": "mid", "src": "mid.png", "x": 0, "y": 0, "w": W, "h": H, "z": -2},
              {"id": "near", "src": "near.png", "x": 0, "y": 0, "w": W, "h": H, "z": -1},
              {"id": "hero", "src": "hero.png", "x": 0, "y": 0, "w": 0, "h": 0, "z": 5}]
    scene = apply_program({"width": W, "height": H, "fps": 30, "durationInFrames": 31, "background": "#000000", "layers": layers}, p)
    mp4 = _render(tmp_path, scene, {"far.png": stripe("far.png", 100, (255, 0, 0)), "mid.png": stripe("mid.png", 150, (0, 255, 0)),
                                    "near.png": stripe("near.png", 200, (0, 0, 255)), "hero.png": _png(tmp_path / "hero.png", 20, 20, (255, 255, 0))},
                  "world")
    end = _frame(mp4, 30, W, H)
    for rgb, x0, k in (((255, 0, 0), 100, 0.2), ((0, 255, 0), 150, 0.5), ((0, 0, 255), 200, 1.0)):
        bb = _bbox(end[:60], rgb)                                                  # top band (hero is at the bottom right)
        assert bb is not None and abs(bb[0] - (x0 - 40 * k)) <= 2, (rgb, bb)
    assert all(f"WORLD:{x}" in scene["consumed_tracks"] for x in ("far", "mid", "near"))


@pytest.mark.req("R3-C04")
def test_world_layer_without_a_coefficient_and_cue_on_event_keyframes_are_refused():
    from vme.render.motion_program import _segment_keys
    scope, decs = _scope_decs(["hero"], world=True, coeffs={"far": 0.2})
    sp = {"frames": 31, "plan_width": 1280, "plan_height": 720, "world_layers": [{"id": "near", "depth": "near"}],
          "actors": [{"id": "hero", "x": 100, "y": 90, "w": 80, "h": 80, "z": 5, "keyframes": [{"frame": 0, "x": 100}, {"frame": 30, "x": 120}]}],
          "camera": [{"frame": 0, "x": 0, "y": 0, "scale": 1}, {"frame": 30, "x": 160, "y": 0, "scale": 1}]}
    with pytest.raises(Blocked) as e:
        _program(scope, decs, sp, 320, 180)
    assert e.value.code == "WORLD_LAYER_UNOWNED"
    with pytest.raises(Blocked) as e:
        _segment_keys({"frame": 0, "x": 0.0}, {"frame": 30, "x": 1.0}, "x", {"method": "CUE_ON_EVENT"})
    assert e.value.code == "UNSUPPORTED_METHOD_FOR_TRACK"
    a = _segment_keys({"frame": 0, "x": 0.0}, {"frame": 30, "x": 1.0}, "x", {"method": "EASE_IN_OUT"})
    h = _segment_keys({"frame": 0, "x": 0.0}, {"frame": 30, "x": 1.0}, "x", {"method": "HOLD_THEN_MOVE", "hold_ratio": 0.5})
    assert a != h                                                                   # each method is its own dispatch


@pytest.mark.req("R3-C04")
@pytest.mark.parametrize("drop", ["hold_ratio", "anticipation_span", "overshoot_span"])
def test_every_method_parameter_must_be_source_owned(drop):
    from vme.render.motion_program import validate_motion_program
    mp = {"track_kind": "ACTOR_ACTING", "method": "ANTICIPATE_OVERSHOOT", **{k: FULL[k] for k in
          ("hold_ratio", "anticipation_ratio", "anticipation_span", "overshoot_ratio", "overshoot_span")}}
    assert validate_motion_program(mp) == []
    del mp[drop]
    assert validate_motion_program(mp) == [f"MOTION_PARAMETER_UNOWNED:ACTOR_ACTING.{drop}"]


@pytest.mark.req("R3-C04")
def test_still_camera_with_an_independently_moving_world_object(tmp_path):
    scope, decs = _scope_decs(["hero"], world=True, coeffs={"far": 0.2}, props=("balloon",))
    sp = {"frames": 31, "plan_width": 1280, "plan_height": 720,
          "world_layers": [{"id": "balloon", "depth": "far", "x": 0, "y": 0, "w": 1280, "h": 720,
                            "keyframes": [{"frame": 0, "x": 0, "y": 0}, {"frame": 30, "x": 0, "y": -80}]}],
          "actors": [{"id": "hero", "x": 100, "y": 90, "w": 80, "h": 80, "z": 5, "keyframes": []}],
          "camera": [{"frame": 0, "x": 0, "y": 0, "scale": 1}]}
    p = _program(scope, decs, sp, 320, 180)
    w = next(t for t in p["tracks"] if t["kind"] == "WORLD")
    assert [x["layer_id"] for x in w["layers"]] == ["balloon"] and w["layers"][0]["keyframes"][-1]["y"] == pytest.approx(-20.0)
    assert not any(t["kind"] == "CAMERA" for t in p["tracks"])                     # camera did not move: object motion is its own


# ------------------------------------------------------------------------------------------------ C06 coinciding cue layers
@pytest.mark.req("R3-C06")
def test_coinciding_semantic_cues_are_all_kept_with_ids():
    scope, decs = _scope_decs(["a"])
    sp = {"frames": 40, "plan_width": 1280, "plan_height": 720,
          "actors": [{"id": "a", "x": 100, "y": 90, "w": 80, "h": 80, "z": 1, "keyframes": []}],
          "events": [{"event_id": "impact", "actor": "a", "from": 20, "to": 25}],
          "audio": {"required": True, "cues": [{"frame": 20, "kind": "NARRATION_ACCENT", "event_id": "impact", "layer": "NARRATION"},
                                               {"frame": 20, "kind": "MUSIC_HIT", "event_id": "impact", "layer": "MUSIC"}]}}
    p = _program(scope, decs, sp, 320, 180)
    at20 = sorted(c["cue_id"] for c in p["audio_cues"] if c["frame"] == 20)
    assert at20 == ["EVENT_ONSET:impact", "MUSIC_HIT:impact:20", "NARRATION_ACCENT:impact:20"]
    assert {c["layer"] for c in p["audio_cues"]} == {"SFX", "MUSIC", "NARRATION"}
