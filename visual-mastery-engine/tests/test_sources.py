"""Source identity, every-frame index and coverage-claim refusals (A01–A03, A26, A29, B01–B03, C01–C02, ADD25-R02)."""
import gzip
import json
from pathlib import Path

import pytest

from conftest import ROOT
from vme.util import Blocked, sha256_file

REAL_WS = ROOT / "workspace"


@pytest.mark.req("A01", "B01", "C01")
def test_fresh_repo_no_prior_animationlab_and_forbidden_roots(tmp_path):
    from vme.reference.probe import discover_sources
    hits = [p for p in ROOT.rglob("*") if ".venv" not in p.parts and "node_modules" not in p.parts
            and any(m in p.name.lower() for m in ("animationlab", "cmr_", "old_research"))]
    assert hits == []
    bad = tmp_path / "AnimationLab_old"
    bad.mkdir()
    with pytest.raises(Blocked) as e:
        discover_sources(bad)
    assert e.value.code == "FORBIDDEN_SOURCE_ROOT"


@pytest.mark.req("A02", "B02", "C02", "A26")
def test_synthetic_clip_decode_index_pts(indexed24):
    clip, idx, _ = indexed24
    assert len(idx) == 24
    assert [r["presentation_index"] for r in idx] == list(range(24))
    assert all(b["pts"] > a["pts"] for a, b in zip(idx, idx[1:]))
    assert len({r["frame_content_sha256"] for r in idx}) == 24  # testsrc2 frames differ


@pytest.mark.req("A26", "A29")
def test_vfr_timestamps_preserved_not_collapsed(tmp_path):
    from vme.fixtures.synthetic import make_clip
    from vme.reference.probe import probe_source
    from vme.reference.frame_index import index_every_frame, read_index
    c = make_clip(tmp_path / "vfr.mp4", frames=20, vfr=True)
    p = probe_source(c)
    s = index_every_frame(c, p.sha256, tmp_path / "i", width=p.width, height=p.height, stream_duration_s=p.stream_duration_s,
                          metadata_nb_frames=p.metadata_nb_frames)
    idx = read_index(s.index_path)
    d = [b["pts"] - a["pts"] for a, b in zip(idx, idx[1:])]
    assert len(idx) == 20 and len(set(d)) > 1, "VFR deltas must survive"
    assert s.vfr_observed


@pytest.mark.req("A29", "B03", "ADD25-F01")
def test_false_100pct_claim_rejected():
    from vme.reference.frame_index import validate_claimed_coverage
    idx = [{"presentation_index": i} for i in range(60)]
    sampled = list(range(0, 60, 6))  # 10fps of 60fps
    r = validate_claimed_coverage(idx, sampled)
    assert not r["complete"] and r["missing_count"] == 50
    r2 = validate_claimed_coverage(idx, list(range(59)))  # missing last frame
    assert not r2["complete"] and r2["missing_ranges"] == [[59, 59]]
    r3 = validate_claimed_coverage(idx, list(range(60)) + [5])
    assert not r3["complete"] and r3["duplicate_claims"] == 1


@pytest.mark.req("A29")
def test_index_analysis_flags_duplicate_pts_and_tail_gap():
    from vme.reference.frame_index import FrameRecord, analyse_index
    fr = [FrameRecord("x", 0, i, i, i / 60, 1, 4, 4, "yuv420p", "h") for i in range(10)]
    fr[5].pts = 4
    a = analyse_index(fr, "1/60", stream_duration_s=1.0, metadata_nb_frames=12)
    assert a["duplicate_pts"] and not a["pts_monotonic"]
    assert any("POSSIBLE_MISSING_TAIL" in p for p in a["problems"]) and a["metadata_count_mismatch"]


@pytest.mark.req("ADD25-R02", "C01")
def test_source_lock_rebind_refuses_changed_bytes(tmp_path, clip24):
    from vme.reference.probe import verify_source_lock
    f = tmp_path / "copy.mp4"
    f.write_bytes(Path(clip24).read_bytes() + b"\x00")
    with pytest.raises(Blocked) as e:
        verify_source_lock({"sha256": sha256_file(clip24)}, f)
    assert e.value.code == "SOURCE_HASH_MISMATCH"


@pytest.mark.req("A02", "A26", "A66", "C02")
def test_real_sources_indexed_every_frame_locally():
    """Reads the REAL local index produced by `vme sources ingest --index-every-frame` (no upload)."""
    summ_p = REAL_WS / "state" / "FRAME_INDEX_SUMMARY.json"
    if not summ_p.exists():
        pytest.skip("real workspace not indexed in this environment")
    summ = json.loads(summ_p.read_text(encoding="utf-8"))
    assert len(summ["films"]) == 6
    for f in summ["films"]:
        assert f["complete_frame_index"], f["file_name"]
        idx_p = Path(f["index_path"])
        n = 0
        last = -1
        with gzip.open(idx_p, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                assert r["presentation_index"] == n and r["pts"] > last
                last = r["pts"]
                n += 1
        assert n == f["frame_count_decoded"]
    assert summ["total_frames_decoded"] == sum(f["frame_count_decoded"] for f in summ["films"])


@pytest.mark.req("A03", "C04")
def test_real_frame_retrieval_identity_spot_check():
    """Exact real-frame retrieval by PTS with raw-byte identity verification (local only)."""
    from vme.reference.frame_index import read_index
    from vme.reference.frames import retrieve_frame
    lock_p = REAL_WS / "state" / "SOURCE_LOCK.json"
    if not lock_p.exists():
        pytest.skip("real workspace not ingested")
    lock = json.loads(lock_p.read_text(encoding="utf-8"))
    s = next(x for x in lock["sources"] if x["role"] == "SIXTH_SPECIAL")
    if not (Path(lock["folder"]) / s["relative_path"]).exists():
        pytest.skip("source MP4s are not distributed with the audit ZIP; place them to run this check")
    idx = read_index(REAL_WS / "frames" / s["sha256"] / "index.jsonl.gz")
    for k in (0, 1234, len(idx) - 1):
        fr = retrieve_frame(Path(lock["folder"]) / s["relative_path"], idx[k])
        assert fr.identity_verified and fr.presentation_index == k
