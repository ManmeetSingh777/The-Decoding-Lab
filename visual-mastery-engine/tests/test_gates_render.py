"""Art → asset → video gates, approvals bound to bytes, renderer refusal and real Remotion render
(A06, A07, A18, A23, A24, A25, A42–A44, A47, A48, A67, B30, B34, C25–C28, C33, C37)."""
import json
from pathlib import Path

import pytest
from PIL import Image

from vme.util import Blocked, sha256_file
from vme.review.approvals import GateKeeper, FIXTURE_SIGNER, save_user_review
from vme.render.renderer import render_video, validate_scene_graph


def _img(p, col):
    Image.new("RGB", (64, 64), col).save(p)
    return str(p)


def _texture(p, w, h):
    """Smooth (codec-friendly) textured fixture so motion is visually defined."""
    import numpy as np
    y, x = np.mgrid[0:h, 0:w]
    arr = np.stack([127 + 100 * np.sin(x / 9.0) * np.cos(y / 13.0), 127 + 90 * np.sin((x + y) / 17.0),
                    127 + 80 * np.cos(x / 23.0 - y / 7.0)], axis=2).clip(0, 255).astype("uint8")
    Image.fromarray(arr).save(p)
    return p


def _to_review(gk, run, synthetic=True):
    gk.transition(run, "ART_GENERATING", synthetic=synthetic)
    gk.transition(run, "AWAITING_ARTWORK_REVIEW")


@pytest.mark.req("A42", "A67", "C33", "ADD26-I02")
def test_rejected_art_blocks_everything_downstream(store, tmp_path):
    gk = GateKeeper(store)
    _to_review(gk, "r1")
    a = _img(tmp_path / "a.png", (1, 2, 3))
    gk.submit_art_verdict("r1", image_paths=[a], brief_id="b", skill_versions=["s"], verdict="REJECTED",
                          defects=["face reads as pasted sticker"], signed_by=FIXTURE_SIGNER)
    assert gk.state("r1")["state"] == "ARTWORK_REJECTED"
    with pytest.raises(Blocked):
        gk.transition("r1", "ASSET_PREPARING")
    with pytest.raises(Blocked) as e:
        gk.authorize_render("r1", scene_asset_paths=[a])
    assert e.value.code == "RENDER_REFUSED_GATE"


@pytest.mark.req("A42", "C33")
def test_agent_cannot_sign_and_fixture_signer_cannot_approve_real_run(store, tmp_path):
    gk = GateKeeper(store)
    _to_review(gk, "r2", synthetic=False)
    a = _img(tmp_path / "a.png", (1, 2, 3))
    for who in ("claude", "agent", ""):
        with pytest.raises(Blocked):
            gk.submit_art_verdict("r2", image_paths=[a], brief_id="b", skill_versions=[], verdict="APPROVED", defects=[], signed_by=who)
    with pytest.raises(Blocked) as e:
        gk.submit_art_verdict("r2", image_paths=[a], brief_id="b", skill_versions=[], verdict="APPROVED", defects=[], signed_by=FIXTURE_SIGNER)
    assert e.value.code == "FIXTURE_SIGNATURE_ON_REAL_RUN"


def _approved_run(store, tmp_path, run="r3"):
    gk = GateKeeper(store)
    _to_review(gk, run)
    art = _img(tmp_path / f"{run}_art.png", (200, 10, 10))
    gk.submit_art_verdict(run, image_paths=[art], brief_id="b", skill_versions=["s"], verdict="APPROVED", defects=[], signed_by=FIXTURE_SIGNER)
    gk.transition(run, "ASSET_PREPARING")
    gk.transition(run, "AWAITING_ASSET_REVIEW")
    asset = _img(tmp_path / f"{run}_asset.png", (10, 200, 10))
    gk.submit_asset_verdict(run, pack_manifest={"files": [asset]}, verdict="APPROVED", signed_by=FIXTURE_SIGNER, character_family_ids=["c"])
    return gk, art, asset


@pytest.mark.req("A43", "A44", "B30", "C33")
def test_asset_approval_then_byte_change_invalidates(store, tmp_path):
    gk, art, asset = _approved_run(store, tmp_path)
    _img(Path(asset), (11, 200, 10))  # swap bytes after sign-off
    with pytest.raises(Blocked) as e:
        gk.authorize_render("r3", scene_asset_paths=[art, asset])
    assert e.value.code == "APPROVED_ASSET_BYTES_CHANGED"
    assert gk.state("r3")["authorized_render_asset_hashes"] == []


@pytest.mark.req("A44", "B30")
def test_art_replacement_after_approval_invalidates(store, tmp_path):
    gk, art, asset = _approved_run(store, tmp_path, run="r4")
    _img(Path(art), (201, 10, 10))
    with pytest.raises(Blocked) as e:
        gk.authorize_render("r4", scene_asset_paths=[art, asset])
    assert e.value.code == "APPROVED_ART_BYTES_CHANGED"


@pytest.mark.req("A42", "C33")
def test_forged_or_tampered_approval_rejected(store, tmp_path):
    gk, art, asset = _approved_run(store, tmp_path, run="r5")
    st = gk.state("r5")
    aid = st["required_asset_approval_ids"][0]
    a = store.get("AssetApproval", aid)
    a["verdict"] = "APPROVED"
    a["signed_by"] = "someone-else"
    store.put("AssetApproval", aid, a)  # tamper: body no longer matches signed sha in the event log
    with pytest.raises(Blocked) as e:
        gk.authorize_render("r5", scene_asset_paths=[art, asset])
    assert e.value.code == "APPROVAL_TAMPERED_OR_FORGED"
    st["required_asset_approval_ids"] = ["assetapp_forged"]
    store.put("VisualGateState", "r5", st)
    with pytest.raises(Blocked) as e2:
        gk.authorize_render("r5", scene_asset_paths=[art, asset])
    assert e2.value.code == "APPROVAL_NOT_FOUND_OR_FORGED"


@pytest.mark.req("A47")
def test_gate_and_approvals_survive_restart(ws, tmp_path):
    s1 = ws.store()
    gk, art, asset = _approved_run(s1, tmp_path, run="r6")
    s1.close()
    s2 = ws.store()
    assert GateKeeper(s2).state("r6")["state"] == "ASSETS_APPROVED"
    assert GateKeeper(s2).authorize_render("r6", scene_asset_paths=[art, asset])["authorized"]
    s2.close()


@pytest.mark.req("A06")
def test_scene_graph_validation():
    bad = {"width": 10, "height": 10, "fps": 30, "durationInFrames": 2, "camera": {"keyframes": [{"frame": 0}, {"frame": 1, "x": 5}]},
           "layers": [{"id": "a", "src": "x"}, {"id": "a", "src": "y"}],
           "events": [{"id": "c", "kind": "contact", "hand_layer": "a", "prop_layer": "zz", "hand_interval": [0, 1], "prop_interval": [0, 2]}]}
    p = validate_scene_graph(bad)
    assert "DUPLICATE_LAYER_ID" in p and any("CONTACT_LAYER_MISSING" in x for x in p) and "CAMERA_ONLY_MOTION" in p


@pytest.mark.req("A07", "C25", "C26", "B34", "A24")
def test_render_refused_before_approval_then_real_remotion_after(store, tmp_path):
    from vme.render.renderer import REMOTION_DIR
    if not (REMOTION_DIR / "node_modules" / "remotion").exists():
        pytest.skip("remotion not installed")
    bg = str(_texture(tmp_path / "bg.png", 320, 180))
    disc = tmp_path / "disc.png"
    Image.new("RGBA", (40, 40), (240, 180, 40, 255)).save(disc)
    scene = {"width": 320, "height": 180, "fps": 30, "durationInFrames": 30, "camera": {"keyframes": [{"frame": 0, "x": 0, "y": 0, "scale": 1}]},
             "layers": [{"id": "bg", "src": "bg.png", "x": 0, "y": 0, "w": 320, "h": 180, "z": 0},
                        {"id": "d", "src": "disc.png", "x": 10, "y": 70, "w": 40, "h": 40, "z": 1,
                         "keyframes": [{"frame": 0, "x": 10}, {"frame": 29, "x": 260}]}]}
    assets = {"bg.png": bg, "disc.png": str(disc)}
    gk = GateKeeper(store)
    _to_review(gk, "rv")
    with pytest.raises(Blocked) as e:
        render_video(scene, assets, tmp_path / "x.mp4", gate=gk, run_id="rv")
    assert e.value.code == "RENDER_REFUSED_GATE"
    gk.submit_art_verdict("rv", image_paths=[bg], brief_id="b", skill_versions=[], verdict="APPROVED", defects=[], signed_by=FIXTURE_SIGNER)
    gk.transition("rv", "ASSET_PREPARING")
    gk.transition("rv", "AWAITING_ASSET_REVIEW")
    gk.submit_asset_verdict("rv", pack_manifest={"files": [str(disc)]}, verdict="APPROVED", signed_by=FIXTURE_SIGNER, character_family_ids=[])
    rep = render_video(scene, assets, tmp_path / "ok.mp4", gate=gk, run_id="rv")
    assert rep["ffprobe"]["ok"] and rep["motion"]["verdict"] == "INDEPENDENT_MOTION_PRESENT"
    assert gk.state("rv")["state"] == "AWAITING_VIDEO_REVIEW"


@pytest.mark.req("C26", "B34", "A25", "C27", "C28")
def test_pan_only_video_not_counted_as_animation(tmp_path):
    from vme.render.renderer import REMOTION_DIR
    if not (REMOTION_DIR / "node_modules" / "remotion").exists():
        pytest.skip("remotion not installed")
    p = _texture(tmp_path / "tex.png", 640, 180)
    scene = {"width": 320, "height": 180, "fps": 30, "durationInFrames": 20,
             "camera": {"keyframes": [{"frame": 0, "x": 0, "y": 0, "scale": 1}, {"frame": 19, "x": 38, "y": 0, "scale": 1}]},
             "layers": [{"id": "tex", "src": "tex.png", "x": 0, "y": 0, "w": 640, "h": 180, "z": 0}]}
    assert "CAMERA_ONLY_MOTION" in validate_scene_graph(scene)
    rep = render_video(scene, {"tex.png": str(p)}, tmp_path / "pan.mp4", diagnostic_label="DIAGNOSTIC_NOT_APPROVED") \
        if False else None
    # validation refuses before rendering; render a diagnostic pan by bypassing the movers rule explicitly:
    scene["layers"][0]["keyframes"] = [{"frame": 0, "x": 0}, {"frame": 19, "x": 0}]  # static keyframes only
    rep = render_video(scene, {"tex.png": str(p)}, tmp_path / "pan.mp4", diagnostic_label="DIAGNOSTIC_NOT_APPROVED")
    assert rep["label"] == "DIAGNOSTIC_NOT_APPROVED" and rep["motion"]["verdict"] == "CAMERA_PAN_ONLY"


@pytest.mark.req("A18", "C36")
def test_review_page_and_feedback_persist(store, tmp_path):
    import urllib.request, urllib.parse
    from vme.review.server import serve
    img = _img(tmp_path / "i.png", (5, 5, 5))
    srv = serve(store, "rr", images=[{"path": img, "sha256": sha256_file(img), "label": "OFFLINE_FIXTURE_NOT_LEARNED_ART"}],
                packet={"gate": "x"}, port=8799, once=True)
    try:
        html = urllib.request.urlopen("http://127.0.0.1:8799/").read().decode()
        assert "SYNTHETIC / OFFLINE FIXTURE" in html and "Which important visual qualities" in html
        data = urllib.parse.urlencode({"run_id": "rr", "verdict": "PARTIAL", "gaps": "face\nhands", "focus": "hands", "by": "test-user"}).encode()
        r = json.loads(urllib.request.urlopen("http://127.0.0.1:8799/feedback", data=data).read())
        rec = store.get("VisualReview", r["saved"])
        assert rec["verdict"] == "PARTIAL" and rec["top_remaining_gaps"] == ["face", "hands"]
    finally:
        srv.shutdown()
    with pytest.raises(Blocked):
        save_user_review(store, run_id="rr", verdict="QUALIFIED", top_remaining_gaps=[], preferred_next_focus="", submitted_by="u",
                         linked_image_hashes=[])


@pytest.mark.req("A23", "A48", "C37", "ADD26-A02", "ADD25-A02")
def test_status_claims_separate_and_truthful(ws):
    st = ws.read_state()
    assert st["paid_vlm_frames_seen"] == 0 and st["runware_real_calls"] == 0
    import subprocess, sys
    from conftest import ROOT
    r = subprocess.run([sys.executable, "-m", "vme", "--workspace", str(ws.root), "status"], cwd=ROOT, capture_output=True, text=True)
    out = json.loads(r.stdout)
    c = out["claims"]
    assert c["ART_QUALITY_NOT_EVALUATED"] and c["ANIMATION_FIXTURE_ONLY"] and c["TRANSFER_NOT_EVALUATED"] and c["PAID_VLM_FRAMES_SEEN"] == 0


@pytest.mark.req("ADD26-I03", "A43")
def test_art_approved_but_asset_family_rejected_holds_before_video(store, tmp_path):
    gk = GateKeeper(store)
    _to_review(gk, "ri3")
    art = _img(tmp_path / "a.png", (9, 9, 9))
    gk.submit_art_verdict("ri3", image_paths=[art], brief_id="b", skill_versions=[], verdict="APPROVED", defects=[], signed_by=FIXTURE_SIGNER)
    gk.transition("ri3", "ASSET_PREPARING")
    gk.transition("ri3", "AWAITING_ASSET_REVIEW")
    with pytest.raises(Blocked):
        gk.authorize_render("ri3", scene_asset_paths=[art])
    asset = _img(tmp_path / "pose.png", (1, 1, 1))
    gk.submit_asset_verdict("ri3", pack_manifest={"files": [asset]}, verdict="REJECTED", signed_by=FIXTURE_SIGNER, character_family_ids=["c"])
    assert gk.state("ri3")["state"] == "ASSETS_REJECTED"
    with pytest.raises(Blocked) as e:
        gk.authorize_render("ri3", scene_asset_paths=[art])
    assert e.value.code == "RENDER_REFUSED_GATE"
    with pytest.raises(Blocked):
        gk.transition("ri3", "VIDEO_RENDERING")
