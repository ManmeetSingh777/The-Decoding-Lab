"""R3-C08 — the inspection gate separates FORMAT / IDENTITY / ARTISTIC ADEQUACY and an INDEPENDENT auditor names every unexplained
phenomenon at its exact interval."""
from __future__ import annotations

import copy

import pytest

FA = "a" * 64
REL = "the near contour of the keeper's coat overlaps the lantern handle while the far sleeve stays behind the torso edge"


def _man(n=1, start=10, audio=None):
    return [{"frame_id": f"{FA[:16]}:{start + i}", "source_sha": FA[:16], "pts_time": round((start + i) / 30, 6), "image_sha": f"i{i}",
             **({"audio_events": audio} if audio and i == 0 else {})} for i in range(n)]


def _resp(obs, edges=None, boundary=None):
    return {"frame_observations": obs, "packet_transition_graph": {"edges": edges if edges is not None else []},
            "boundary_state": boundary if boundary is not None else {"active_objects": [{"id": "keeper"}]}}


def _good(m, **over):
    o = {"frame_id": m["frame_id"], "source_sha": m["source_sha"], "pts_time": m["pts_time"], "request_id": "r", "submitted_image_sha": m["image_sha"],
         "active_question_ids": [], "scene_and_world_state": "storm-lit gallery with the keeper on the left and the sea behind the rail",
         "actually_visible_actor_and_object_ids": ["keeper"], "entity_kinds": {"keeper": "character"},
         "focal_whole_artwork_state": "the keeper's dark coat mass reads against the pale storm sky behind the gallery rail",
         "visible_design_relations": [{"relation": REL, "dimensions": ["CHARACTER_BODY_HAND_CONTACT", "MATERIAL_LIGHT_FINISH"], "entity_ids": ["keeper"]}],
         "character_face_limb_contact_state": "the right hand wraps the lantern handle with the thumb in front and fingers behind it",
         "visible_layer_depth_attention_state": "keeper in the near layer, rail mid layer, sea and sky far layer; attention on the lantern",
         "changed_since_prior_frame": [], "no_significant_change_reason": "every contour and fill matches the previous frame exactly at native resolution",
         "simultaneous_event_links": {"not_applicable": "only the keeper is visible so no second action can overlap here"},
         "camera_vs_actor_vs_drawing_state": {"not_applicable": "nothing moves between this frame and the previous one"},
         "material_finish_or_colour_change": "warm lantern light rims the hand while the coat keeps one flat cool fill",
         "native_detail_followups": [], "source_fact_statements": [], "hypothesis_or_uncertainty": [], "confidence_limitations": [],
         "persistent_state_ids": ["keeper"], "unexplained_phenomena": []}
    o.update(over)
    return o


def _v(obs, man, **kw):
    from vme.vision.contracts import validate_packet_response
    return validate_packet_response(_resp(obs, **kw), man, None, images_actually_sent=len(man))


def _minimal(m):
    return {"frame_id": m["frame_id"], "source_sha": m["source_sha"], "pts_time": m["pts_time"], "request_id": "r", "submitted_image_sha": m["image_sha"],
            "active_question_ids": [], "scene_and_world_state": "", "actually_visible_actor_and_object_ids": [],
            "focal_whole_artwork_state": "The red focal circle overlaps a blue circle behind it",
            "visible_design_relations": [{"relation": "The red focal circle overlaps a blue circle behind it"}],
            "character_face_limb_contact_state": None, "visible_layer_depth_attention_state": None, "changed_since_prior_frame": [],
            "no_significant_change_reason": "first frame", "simultaneous_event_links": [], "camera_vs_actor_vs_drawing_state": None,
            "material_finish_or_colour_change": None, "native_detail_followups": [], "source_fact_statements": [],
            "hypothesis_or_uncertainty": None, "confidence_limitations": None, "persistent_state_ids": [], "unexplained_phenomena": []}


@pytest.mark.req("R3-C08")
def test_the_audited_minimal_record_is_inspection_insufficient_not_validated():
    man = _man()
    v = _v([_minimal(man[0])], man, boundary={})
    assert v["status"] == "INSPECTION_INSUFFICIENT" and v["identity_valid"] and v["format_valid"]
    gaps = {g["gap"] for g in v["inspection"]["per_frame"][man[0]["frame_id"]]["gaps"]}
    assert {"ENTITIES_NOT_ENUMERATED", "DIMENSION_NOT_ADDRESSED", "PERSISTENCE_UNJUSTIFIED", "DESIGN_RELATIONS_TOO_FEW"} <= gaps
    assert all(g["pts_time"] == man[0]["pts_time"] for g in v["inspection"]["per_frame"][man[0]["frame_id"]]["gaps"])


@pytest.mark.req("R3-C08")
@pytest.mark.parametrize("pts,code", [(None, "PTS_MISSING_OR_NON_NUMERIC"), ("0.333", "PTS_MISSING_OR_NON_NUMERIC"), (True, "PTS_MISSING_OR_NON_NUMERIC"),
                                      (0.5, "PTS_MISMATCH")])
def test_pts_is_a_required_exact_identity_field(pts, code):
    man = _man()
    o = _good(man[0], pts_time=pts)
    v = _v([o], man)
    assert not v["ok"] and not v["identity_valid"] and any(p.startswith(code) for p in v["problems"])


@pytest.mark.req("R3-C08")
def test_a_well_evidenced_static_frame_passes():
    man = _man()
    v = _v([_good(man[0])], man)
    assert v["status"] == "VALIDATED" and v["inspection"]["per_frame"][man[0]["frame_id"]]["status"] == "ARTISTIC_INSPECTION_ADEQUATE"


@pytest.mark.req("R3-C08")
def test_a_character_turn_and_sound_transition_with_one_generic_relation_fail():
    man = _man(audio=[{"kind": "AUDIO_ONSET", "frame": 10}])
    o = _good(man[0], changed_since_prior_frame=[{"kind": "INFERRED_NEW_DRAWING", "entity_ids": ["keeper"],
                                                  "what": "the keeper's head is redrawn from three-quarter to front view"}],
              no_significant_change_reason=None,
              camera_vs_actor_vs_drawing_state="the setting is fixed while the head contour is redrawn, so this is a drawing change",
              visible_design_relations=[{"relation": REL, "dimensions": ["MATERIAL_LIGHT_FINISH"], "entity_ids": ["keeper"]}])
    v = _v([o], man, edges=[["x", "y"]])
    gaps = {g["gap"] for g in v["inspection"]["per_frame"][man[0]["frame_id"]]["gaps"]}
    assert v["status"] == "INSPECTION_INSUFFICIENT" and {"STATE_CHANGE_WITHOUT_RELATION", "AV_LINK_MISSING"} <= gaps
    o2 = copy.deepcopy(o)
    o2["visible_design_relations"].append({"relation": "the far eye is hidden behind the redrawn nose line while the skull contour narrows",
                                           "dimensions": ["CHARACTER_FACE_ACTING", "ART_STATE_TRANSFORMATION"], "entity_ids": ["keeper"]})
    o2["audiovisual_links"] = [{"audio_event": "AUDIO_ONSET", "visual_relation": "the onset lands on the first frame of the front-view drawing"}]
    assert _v([o2], man, edges=[["x", "y"]])["status"] == "VALIDATED"


@pytest.mark.req("R3-C08")
def test_bare_unknown_does_not_address_a_dimension_but_a_targeted_unknown_stays_open():
    man = _man()
    v = _v([_good(man[0], visible_layer_depth_attention_state="UNKNOWN")], man)
    assert v["status"] == "INSPECTION_INSUFFICIENT"
    u = {"unknown": "cannot tell whether the rail is in front of the coat", "next_witness": "native crop of frame 10 around the rail"}
    v = _v([_good(man[0], visible_layer_depth_attention_state=u)], man)
    assert v["status"] == "VALIDATED" and v["inspection"]["open_unknowns"][0]["next_witness"].startswith("native crop")


# ----------------------------------------------------------------------- independent auditor: each removed phenomenon = named gap
def _scene():
    man = _man(n=11, start=10)
    obs = [_good(m) for m in man]
    obs[2]["actually_visible_actor_and_object_ids"] = ["keeper", "moth"]
    obs[2]["simultaneous_event_links"] = [{"entity_ids": ["keeper", "moth"], "link": "the moth turns while the keeper is still lifting the lantern"}]
    obs[4]["changed_since_prior_frame"] = [{"kind": "INFERRED_NEW_DRAWING", "entity_ids": ["keeper"], "what": "head redrawn to a front view"}]
    obs[6]["camera_vs_actor_vs_drawing_state"] = "the rail slides left at constant speed so the camera pans while the keeper holds"
    obs[8]["changed_since_prior_frame"] = [{"kind": "OBSERVED_DIFF", "entity_ids": [], "what": "hard cut transition to the lamp room interior"}]
    expected = [{"phenomenon_id": "P-overlap", "kind": "TEMPORAL_OVERLAP", "frames": [11, 13], "entity_ids": ["keeper", "moth"]},
                {"phenomenon_id": "P-grip", "kind": "HAND_CONTACT", "frames": [10, 11], "entity_ids": ["keeper"]},
                {"phenomenon_id": "P-turn", "kind": "ALTERNATE_STATE", "frames": [14, 14], "entity_ids": ["keeper"]},
                {"phenomenon_id": "P-pan", "kind": "CAMERA_ATTRIBUTION", "frames": [16, 16], "entity_ids": []},
                {"phenomenon_id": "P-light", "kind": "LIGHTING_RELATION", "frames": [19, 20], "entity_ids": ["keeper"]},
                {"phenomenon_id": "P-cut", "kind": "SCENE_TRANSITION", "frames": [18, 18], "entity_ids": []}]
    return obs, expected


@pytest.mark.req("R3-C08")
def test_every_independently_enumerated_phenomenon_is_covered():
    from vme.vision.contracts import audit_phenomenon_coverage
    obs, expected = _scene()
    assert audit_phenomenon_coverage(obs, expected) == []


@pytest.mark.req("R3-C08")
@pytest.mark.parametrize("pid,frame,break_it", [
    ("P-overlap", 2, lambda o: o.update(simultaneous_event_links={"not_applicable": "x y z w only one"})),
    ("P-grip", 0, None),
    ("P-turn", 4, lambda o: o.update(changed_since_prior_frame=[])),
    ("P-pan", 6, lambda o: o.update(camera_vs_actor_vs_drawing_state={"not_applicable": "nothing moves here at all"})),
    ("P-light", 9, None),
    ("P-cut", 8, lambda o: o.update(changed_since_prior_frame=[{"kind": "OBSERVED_DIFF", "entity_ids": [], "what": "the colours change"}])),
])
def test_removing_one_phenomenon_names_a_gap_at_its_exact_interval(pid, frame, break_it):
    from vme.vision.contracts import audit_phenomenon_coverage
    obs, expected = _scene()
    if pid in ("P-grip", "P-light"):          # these are evidenced in every frame: remove the evidence across their whole interval
        ph = next(e for e in expected if e["phenomenon_id"] == pid)
        for o in obs:
            if ph["frames"][0] <= int(o["frame_id"].split(":")[1]) <= ph["frames"][1]:
                o["visible_design_relations"] = [{"relation": REL, "dimensions": ["DEPTH_VIEWPOINT"], "entity_ids": ["keeper"]}]
    else:
        break_it(obs[frame])
    gaps = audit_phenomenon_coverage(obs, expected)
    assert [g["phenomenon_id"] for g in gaps] == [pid]
    ph = next(e for e in expected if e["phenomenon_id"] == pid)
    assert gaps[0]["interval"] == ph["frames"] and gaps[0]["gap"].startswith("PHENOMENON_NOT_EXPLAINED")


@pytest.mark.req("R3-C08")
def test_mock_records_commit_as_identity_only_and_keep_the_scene_open(ws, indexed24):
    from vme.vision.runner import PacketRunner, plan_packets
    from vme.vision.providers import MockVisionProvider
    from vme.style.source_ledger import source_art_ledger
    clip, idx, loader = indexed24
    st = ws.store()
    plans = plan_packets(idx, 0, 3, film_sha=idx[0]["film_sha256"], pass_id="RUN-L0", cluster_id="seqA", model_version="m", max_images=12)
    pr = PacketRunner(st, ws.vision_dir, idx, loader, MockVisionProvider(ws.root / "rv"), source_is_synthetic=True,
                      active_questions=[{"question_id": "Q", "text": "t"}])
    assert pr.run(plans[0]) == "SEMANTIC_COMMITTED"
    fi = [r for r in st.list("FrameInspection") if r["packet_id"] == plans[0].packet_id]
    assert fi and all(r["status"] == "INSPECTION_INSUFFICIENT" and r["identity_status"] == "RESPONSE_IDENTITY_BOUND" for r in fi)
    led = source_art_ledger(st, ws, "RUN", [(idx[0]["film_sha256"], 0, 3, "seqA")], "RUN-L0")
    kinds = {g["kind"] for g in led["scenes"][0]["open_gaps"]}
    assert {"ARTISTIC_INSPECTION_INSUFFICIENT", "INDEPENDENT_AUDIT_NOT_RUN"} <= kinds
    assert led["scenes"][0]["status"] == "NEEDS_SOURCE_REINSPECTION" and not led["complete_for_promotion"]
    st.close()
