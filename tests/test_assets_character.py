"""Character-first manufacture and raster/layer truth (A21, A38–A41, A45, A58–A60, B25–B29, C19–C24, spec 17 §7)."""
import copy
import io

import numpy as np
import pytest
from PIL import Image

from vme.util import Blocked, sha256_bytes
from vme.artwork.raster import decode_raster, require_transparency
from vme.artwork.assets import coordinate_map, verify_pack, recompose, recomposition_report
from vme.artwork.character import (derive_animation_demand, character_construction_plan, validate_construction_order,
                                   validate_character_answer, cross_actor_witness_group)
from vme.fixtures import loop_fixtures as fx
from vme.skills.operators import registered


def _png(mode="RGB", size=(32, 32), alpha=255):
    im = Image.new(mode, size, (10, 20, 30, alpha) if mode == "RGBA" else (10, 20, 30))
    b = io.BytesIO()
    im.save(b, format="PNG")
    return b.getvalue()


@pytest.mark.req("B25", "C23")
def test_opaque_png_never_transparent():
    for data in (_png("RGB"), _png("RGBA", alpha=255)):
        ra = decode_raster(data, asset_id="a", owner="o", skill_version="s")
        assert not ra.has_nonopaque_alpha
        with pytest.raises(Blocked) as e:
            require_transparency(ra)
        assert e.value.code == "OPAQUE_ASSET_NOT_TRANSPARENT"
    ra = decode_raster(_png("RGBA", alpha=0), asset_id="b", owner="o", skill_version="s")
    assert ra.has_nonopaque_alpha and ra.transparent_fraction == 1.0


@pytest.mark.req("C18")
def test_invalid_bytes_rejected():
    with pytest.raises(Blocked) as e:
        decode_raster(b"\x89PNG\r\n\x1a\nnope", asset_id="x", owner="o", skill_version="s")
    assert e.value.code == "INVALID_IMAGE_BYTES"


@pytest.mark.req("C24", "B26")
def test_coordinate_mapping_uniform_never_stretch():
    m = coordinate_map(1536, 864)
    assert m["scale"] == 1.25 and not m["stretch"] and m["crop"] is None
    m2 = coordinate_map(1920, 1088)
    assert m2["crop"]["h"] == 1080 and m2["scale"] == 1.0 and abs(m2["offset"][1] + 4) < 1e-9
    with pytest.raises(Blocked):
        coordinate_map(1000, 1000, policy="stretch")


@pytest.mark.req("A60", "B27", "A58", "A59", "C20", "C21", "C22", "A45")
def test_animation_demand_and_construction_order_before_generation():
    d = derive_animation_demand("explorer", fx.synthetic_shot_actions())
    assert d.contacts[0]["hand_side"] == "right" and d.occluded_surfaces_to_create and "front" in d.views
    plan = character_construction_plan("explorer", "B", "h", d)
    seq = plan["generation_sequence"]
    assert seq[0]["operator"] == "op.canonical_character"
    grip = next(s for s in seq if s["step"].startswith("grip"))
    assert grip["hand_and_prop_in_one_drawing"] and grip["identity_reference"] == "explorer:canonical"
    first_layer = next(i for i, s in enumerate(seq) if s["kind"] == "LAYER")
    assert all(s["kind"] != "CHARACTER_STATE" for s in seq[first_layer:])
    assert plan["svg_or_tube_actor_allowed"] is False
    bad = copy.deepcopy(plan)
    bad["generation_sequence"] = [seq[0], next(s for s in seq if s["kind"] == "LAYER"), grip]
    with pytest.raises(Blocked) as e:
        validate_construction_order(bad)
    assert e.value.code == "LAYERS_BEFORE_WHOLE_POSE"
    bad2 = copy.deepcopy(plan)
    for s in bad2["generation_sequence"]:
        if s["step"].startswith("grip"):
            s["hand_and_prop_in_one_drawing"] = False
    with pytest.raises(Blocked) as e2:
        validate_construction_order(bad2)
    assert e2.value.code == "HAND_AND_PROP_GENERATED_SEPARATELY"
    with pytest.raises(Blocked):
        derive_animation_demand("x", [{"actor": "x", "event_id": "e", "contact_prop": "p"}])  # hand side unspecified


@pytest.mark.req("C19", "C20")
def test_svg_tube_actor_refused():
    with pytest.raises(Blocked) as e:
        validate_construction_order({"generation_sequence": [{"step": "rig", "operator": "svg.tube_rig", "kind": "SVG_ACTOR"}]})
    assert e.value.code in ("CANONICAL_NOT_FIRST", "SVG_TUBE_ACTOR_FORBIDDEN")


def _pack(tmp_path):
    canon = tmp_path / "canon.png"
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 255))
    from PIL import ImageDraw
    ImageDraw.Draw(im).rectangle([60, 60, 200, 200], fill=(200, 120, 40, 255))
    im.save(canon)
    sha = sha256_bytes(canon.read_bytes())
    st = {"n3_view": {"image": str(canon), "identity_ref": sha}, "n4_grip": {"image": str(canon), "identity_ref": sha}}
    return fx.fixture_layer_pack(tmp_path / "pack", canonical_path=str(canon), canonical_sha=sha, states=st), canon


@pytest.mark.req("A41", "C23", "C24")
def test_valid_pack_and_recomposition_matches_canonical(tmp_path):
    pack, canon = _pack(tmp_path)
    assert verify_pack(pack)["ok"], verify_pack(pack)
    from vme.artwork.raster import load_rgba
    rec = recompose([{**l} for l in pack["layers"]], (256, 256))
    rep = recomposition_report(rec, load_rgba(canon.read_bytes()))
    assert rep["ok"], rep


@pytest.mark.parametrize("inject,code", [
    ("opaque_claimed", "OPAQUE_PNG_CLAIMED_TRANSPARENT"), ("mask_size", "MASK_WRONG_SIZE"), ("bytes_changed", "LAYER_BYTES_CHANGED"),
    ("no_clean_plate", "MOVING_PART_WITHOUT_CLEAN_PLATE"), ("lr_swap", "LEFT_RIGHT_SWAPPED"), ("z_order", "Z_ORDER_VIOLATES_CONTACT"),
    ("anchor", "CONTACT_ANCHOR_INCONSISTENT"), ("state_canvas", "STATE_CANVAS_MISMATCH"), ("not_canonical", "STATE_NOT_CONDITIONED_ON_CANONICAL"),
    ("outside", "LAYER_OUTSIDE_CANONICAL_CANVAS"), ("double_scale", "PARENT_SCALE_APPLIED_TWICE"), ("plate_hole", "CLEAN_PLATE_HAS_HOLES"),
    ("no_hand_prop_state", "CONTACT_WITHOUT_WHOLE_HAND_PROP_DRAWING")])
def test_injected_asset_failures_detected(tmp_path, inject, code):
    pack, canon = _pack(tmp_path)
    arm = pack["layers"][1]
    if inject == "opaque_claimed":
        p = tmp_path / "opaque.png"
        Image.new("RGBA", tuple(arm["natural_size"]), (1, 2, 3, 255)).save(p)
        arm.update(image_path=str(p), image_sha256=sha256_bytes(p.read_bytes()))
    elif inject == "mask_size":
        p = tmp_path / "m.png"
        Image.new("L", (5, 5), 255).save(p)
        arm["mask_path"] = str(p)
    elif inject == "bytes_changed":
        arm["image_sha256"] = "0" * 64
    elif inject == "no_clean_plate":
        arm["occluded_fill"] = None
    elif inject == "lr_swap":
        pack["view"] = "front"
        arm["side"] = "left" if arm["local_origin"][0] + arm["natural_size"][0] / 2 < 128 else "right"
        arm["side"] = "right" if arm["side"] == "left" else "left"
        arm["side"] = "left" if (arm["local_origin"][0] + arm["natural_size"][0] / 2) < 128 else "right"
    elif inject == "z_order":
        arm["z"] = -1
    elif inject == "anchor":
        pack["contacts"][0]["prop_anchor_world"] = [140, 100]
    elif inject == "state_canvas":
        pack["states"][0]["width"] = 300
    elif inject == "not_canonical":
        pack["states"][0]["identity_reference_sha256"] = "f" * 64
    elif inject == "outside":
        arm["local_origin"] = [240, 240]
    elif inject == "double_scale":
        arm.update(parent="L-bg", parent_scale_applied=True, declared_world_scale=4.0)
        pack["parent_scales"] = {"L-bg": 2.0}
    elif inject == "plate_hole":
        p = tmp_path / "holey.png"
        a = np.zeros((256, 256, 4), np.uint8)
        a[..., 3] = 255
        a[0:10, 0:10, 3] = 0
        Image.fromarray(a, "RGBA").save(p)
        arm["occluded_fill"] = str(p)
    elif inject == "no_hand_prop_state":
        pack["contacts"][0]["approved_hand_prop_state"] = None
    rep = verify_pack(pack)
    assert not rep["ok"] and any(code in p for p in rep["problems"]), rep


test_injected_asset_failures_detected = pytest.mark.req("A40", "A41", "B26", "C22", "C23", "C24")(test_injected_asset_failures_detected)


@pytest.mark.req("A41")
def test_recomposition_detects_holes_and_halo(tmp_path):
    canon = np.zeros((20, 20, 4), np.float32)
    canon[5:15, 5:15] = [1, 0, 0, 1]
    rec = canon.copy()
    rec[8:10, 8:10, 3] = 0       # hole
    rec[0:2, 0:2] = [0, 1, 0, 1]  # halo
    r = recomposition_report(rec, canon)
    assert r["hole_pixels"] == 4 and r["halo_pixels"] == 4 and not r["ok"]


@pytest.mark.req("ADD24-B2", "A38")
def test_character_answer_rejects_shallow_part_labels():
    good = {"observed_whole_visual_effect": "whole actor silhouette reads before face detail while turning toward the prop",
            "source_witnesses": ["W-SYN-A01"], "contrasting_witnesses": ["W-SYN-B01"],
            "artistic_relationships": "head contour, gaze and shoulder silhouette change together relative to the prop",
            "candidate_cause": "coordinated redraw", "what_is_actor_specific": ["orange jacket"], "what_transfers": "joint redraw of gaze+shoulder",
            "condition_of_use": "focal actor, three quarter", "expected_new_art_change": "new actor turn keeps identity",
            "actual_art_operation": {"operation_id": "op.face_view_state"}, "unresolved_production_ambiguity": ["profile"]}
    assert validate_character_answer("expression_as_whole_actor", good, registered())["ok"]
    bad = dict(good, observed_whole_visual_effect="bold eyes and a rounded body", artistic_relationships="", contrasting_witnesses=[],
               actual_art_operation={"operation_id": "op.nope"})
    r = validate_character_answer("whole_design_identity", bad, registered())
    assert {"SHALLOW_PART_LABEL", "NO_UNLIKE_ACTOR_CONTRAST", "NO_ART_OPERATION"} <= set(r["problems"])


@pytest.mark.req("ADD24-B1")
def test_cross_actor_witness_group_scope():
    w = list(fx.synthetic_witnesses().values())
    g = cross_actor_witness_group(w, "new actor three-quarter reach")
    assert g["scope"] == "SUPPORTED_FOR_CONDITIONAL_DECISION" and g["status"]["d_different_actor_other_film"]
    one = cross_actor_witness_group([w[0]], "x")
    assert one["scope"] == "INVESTIGATION_START_ONLY"


@pytest.mark.req("A21", "A39", "B28", "B29", phase="ART")
def test_identity_consistency_requires_real_outputs():
    """Identity preservation across views/expressions can only be judged on real provider art + human review.
    Offline proof: every derived state is compiled with the canonical bytes as conditioning (see compiler tests)."""
    d = derive_animation_demand("explorer", fx.synthetic_shot_actions())
    plan = character_construction_plan("explorer", "B", "h", d)
    assert all(s.get("identity_reference") for s in plan["generation_sequence"] if s["kind"] == "CHARACTER_STATE")
