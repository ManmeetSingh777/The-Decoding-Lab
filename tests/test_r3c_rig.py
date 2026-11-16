"""R3-C05 — part-level route: source-derived topology/limits, contact and planted-foot invariants, refusal without real part assets."""
from __future__ import annotations

import math

import pytest

from vme.util import Blocked

RIG = {"actor_id": "keeper", "source_derivation": {"dossier_id": "CD-1"},
       "allowed_transitions": [["reach", "grip"]],
       "parts": [{"id": "torso", "parent": None, "pivot": [0, 0], "rest_angle": 0, "min_angle": -10, "max_angle": 10, "z": 1},
                 {"id": "upper_arm", "parent": "torso", "pivot": [10, -30], "rest_angle": 0, "min_angle": -80, "max_angle": 80, "z": 2},
                 {"id": "forearm", "parent": "upper_arm", "pivot": [30, 0], "rest_angle": 0, "min_angle": 0, "max_angle": 120, "z": 3},
                 {"id": "foot", "parent": "torso", "pivot": [0, 60], "rest_angle": 0, "min_angle": -20, "max_angle": 20, "z": 0}]}
ASSETS = {p["id"]: {"approved": True, "origin": "SOURCE_DERIVED_COMPONENT", "sha256": p["id"] * 4} for p in RIG["parts"]}


def _hand(angles, root):
    from vme.render.rig import anchor_world, validate_rig
    return anchor_world(validate_rig(RIG), angles, root, "forearm", (25, 0))


def _poses():
    # the arm rotates while the prop is carried with the hand: the prop anchor is defined independently as the hand target
    return [{"frame": f, "root": [100, 100], "angles": {"upper_arm": -10 * i, "forearm": 20 + 5 * i}, "state": "reach" if f < 20 else "grip"}
            for i, f in enumerate(range(0, 40, 10))]


@pytest.mark.req("R3-C05")
def test_hand_grips_a_moving_prop_without_breaking_contact():
    from vme.render.rig import compile_rig_program
    poses = _poses()
    prop = {p["frame"]: list(_hand(p["angles"], tuple(p["root"]))) for p in poses}        # independent oracle: where the prop handle is
    prog = compile_rig_program(RIG, poses, contacts=[{"part": "forearm", "local": [25, 0], "prop_anchor": prop, "frames": [0, 30]}], assets=ASSETS)
    assert all(c["error_px"] < 0.01 for c in prog["checks"] if c["kind"] == "CONTACT") and prog["front_back_order"][0] == "foot"
    moved = {f: [x + (3 if f == 20 else 0), y] for f, (x, y) in prop.items()}           # the prop moves without the hand: contact breaks
    with pytest.raises(Blocked) as e:
        compile_rig_program(RIG, poses, contacts=[{"part": "forearm", "local": [25, 0], "prop_anchor": moved, "frames": [0, 30]}], assets=ASSETS)
    assert e.value.code == "CONTACT_BROKEN"


@pytest.mark.req("R3-C05")
def test_planted_foot_during_a_weight_shift_must_not_slide():
    from vme.render.rig import compile_rig_program
    shift = [{"frame": f, "root": [100, 100], "angles": {"torso": 2 * i, "foot": -2 * i}, "state": "reach"} for i, f in enumerate(range(0, 30, 10))]
    with pytest.raises(Blocked) as e:                       # rotating the torso about its pivot moves the foot pivot: it slides
        compile_rig_program(RIG, shift, planted=[{"part": "foot", "local": [0, 0], "frames": [0, 20]}], assets=ASSETS)
    assert e.value.code == "PLANTED_FOOT_SLIDES"
    still = [{"frame": f, "root": [100, 100], "angles": {"upper_arm": 5 * i}, "state": "reach"} for i, f in enumerate(range(0, 30, 10))]
    p = compile_rig_program(RIG, still, planted=[{"part": "foot", "local": [0, 0], "frames": [0, 20]}], assets=ASSETS)
    assert max(c["slide_px"] for c in p["checks"]) == 0


@pytest.mark.req("R3-C05")
def test_source_limits_transitions_and_derivation_are_enforced():
    from vme.render.rig import compile_rig_program
    with pytest.raises(Blocked) as e:
        compile_rig_program(RIG, [{"frame": 0, "root": [0, 0], "angles": {"forearm": 150}}], assets=ASSETS)
    assert e.value.code == "POSE_EXCEEDS_SOURCE_LIMIT"
    with pytest.raises(Blocked) as e:
        compile_rig_program(RIG, [{"frame": 0, "root": [0, 0], "angles": {}, "state": "grip"}, {"frame": 5, "root": [0, 0], "angles": {}, "state": "reach"}],
                            assets=ASSETS)
    assert e.value.code == "STATE_TRANSITION_NOT_ALLOWED"
    with pytest.raises(Blocked) as e:
        compile_rig_program({**RIG, "source_derivation": {}}, _poses(), assets=ASSETS)
    assert e.value.code == "RIG_NOT_SOURCE_DERIVED"


@pytest.mark.req("R3-C05")
def test_without_approved_source_derived_part_assets_the_route_refuses():
    from vme.render.rig import compile_rig_program
    with pytest.raises(Blocked) as e:
        compile_rig_program(RIG, _poses())
    assert e.value.code == "PART_RIG_ASSETS_UNAVAILABLE"
    gen = {**ASSETS, "forearm": {"approved": True, "origin": "GENERIC_TUBE_LIMB", "sha256": "x"}}
    with pytest.raises(Blocked) as e:
        compile_rig_program(RIG, _poses(), assets=gen)
    assert e.value.code == "PART_RIG_ASSETS_UNAVAILABLE" and "forearm" in e.value.detail
