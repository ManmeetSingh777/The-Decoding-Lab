"""R3-C09 — character study frames are chosen by DISTINCT OBSERVED STATE and hard case, not by chronology."""
from __future__ import annotations

import pytest


def _o(k, *, dims=("WHOLE_FRAME_LANGUAGE",), rel="the coat mass keeps one contour against the sky", ids=("keeper",), redraw=False):
    return {"frame_id": f"f:{k}", "visible_design_relations": [{"relation": rel, "dimensions": list(dims), "entity_ids": ["keeper"]}],
            "persistent_state_ids": list(ids), "changed_since_prior_frame": ([{"kind": "INFERRED_NEW_DRAWING", "entity_ids": ["keeper"],
                                                                               "what": "head redrawn to front"}] if redraw else []),
            "character_face_limb_contact_state": {"not_applicable": "no hand visible in this frame at all"}}


def _scene(grip_at=230, turn_at=None, n=260):
    frames = []
    for k in range(n):
        if grip_at is not None and grip_at <= k < grip_at + 10:
            o = _o(k, dims=("CHARACTER_BODY_HAND_CONTACT",), rel="the right hand grips the lantern handle in front of the coat")
        elif turn_at is not None and k == turn_at:
            o = _o(k, dims=("CHARACTER_FACE_ACTING",), rel="the far eye is hidden behind the redrawn nose", redraw=True)
        else:
            o = _o(k)
        frames.append(("S1", k, None, o))
    return frames


@pytest.mark.req("R3-C09")
def test_a_late_grip_after_frame_200_is_a_distinct_state_and_is_selected():
    from vme.style.source_ledger import character_state_inventory, select_study_frames
    inv = character_state_inventory("keeper", _scene())
    grip = [s for s in inv if s["signature"]["contact"]]
    assert grip and grip[0]["frames"][0] == 230 and grip[0]["hard_case"]
    sel = select_study_frames(inv, 2, [])
    assert any(230 <= p["frame"] < 240 for p in sel["picks"])            # chronology would have taken frames 0..2


@pytest.mark.req("R3-C09")
def test_states_beyond_capacity_are_named_never_dropped():
    from vme.style.source_ledger import character_state_inventory, select_study_frames
    inv = character_state_inventory("keeper", _scene(turn_at=100))
    sel = select_study_frames(inv, 1, [])
    assert sel["picks"][0]["hard_case"] and len(sel["uncovered_states"]) == len(inv) - 1
    assert all(u["frames"] for u in sel["uncovered_states"])


@pytest.mark.req("R3-C09")
def test_an_auditor_critical_state_the_inventory_never_saw_is_missing():
    from vme.style.source_ledger import character_state_inventory, select_study_frames
    inv = character_state_inventory("keeper", _scene(grip_at=None))
    sel = select_study_frames(inv, 5, [{"phenomenon_id": "ADV:grip", "kind": "HAND_CONTACT", "frames": [300, 305]}])
    assert sel["missing_critical_states"] == [{"phenomenon_id": "ADV:grip", "kind": "HAND_CONTACT", "frames": [300, 305]}]


@pytest.mark.req("R3-C09")
def test_a_dossier_that_omits_a_shown_face_state_fails_closed():
    from vme.style.source_ledger import dossier_state_problems
    dossier = {"fields": {"whole_design": {"witness_ids": ["W-1"]}, "view_and_pose_redraws": {"witness_ids": ["W-1"]}},
               "identity_across_drawings": [{"witness_ids": ["W-1"]}]}
    assert dossier_state_problems(dossier, {"keeper#S0": "W-1", "keeper#S1": "W-2"}) == ["MISSING_STATE_IN_DOSSIER:keeper#S1"]
    dossier["fields"]["view_and_pose_redraws"]["witness_ids"].append("W-2")
    assert dossier_state_problems(dossier, {"keeper#S0": "W-1", "keeper#S1": "W-2"}) == []
