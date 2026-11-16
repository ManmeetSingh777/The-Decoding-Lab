"""First-15 selection and the sixth volcano→logo locator (ADD25-S01..S05, ADD26-D01..D05, ADD24-E1)."""
import json

import pytest

from conftest import ROOT
from vme.util import Blocked, digest
from vme.fixtures import loop_fixtures as fx
from vme.selection.first15 import propose_selection
from vme.selection.sixth import locate_sixth_intro, lock_sixth_interval


@pytest.mark.req("ADD25-S01")
def test_four_films_blocks_selection():
    m = propose_selection(fx.synthetic_candidates(), fx.SYNTHETIC_BASE_FILMS[:4])
    assert m["status"] == "BLOCKED" and m["reason"] == "BASE_FILM_COUNT_NOT_FIVE"


@pytest.mark.req("ADD25-S02", "ADD25-S03", "ADD25-S04", "ADD25-S05", "ADD24-E1")
def test_three_per_film_dedupe_substitution_expansion_and_evidence():
    m = propose_selection(fx.synthetic_candidates(), fx.SYNTHETIC_BASE_FILMS)
    assert m["selected_count"] == 15 and m["status"] == "PROPOSED_AWAITING_USER_REVIEW"
    per = {}
    for s in m["selected"]:
        per.setdefault(s["film_sha"], []).append(s["selection_role"])
    assert all(sorted(v) == ["C", "T", "W"] for v in per.values())
    rej = {r["candidate_id"]: r["reasons"] for r in m["rejected"]}
    assert any("DUPLICATE_OF" in x for x in rej["F1-C1-dup"])                       # S02
    assert any(s["film_sha"] == fx.SYNTHETIC_BASE_FILMS[2] for s in m["substitutions"])   # S03: no fabricated character
    f2t = next(s for s in m["selected"] if s["candidate_id"] == "F2-T1")
    assert f2t["start_frame_index"] == 2380 and f2t["boundary_expansions"]              # S04
    assert "NO_WHOLE_ARTWORK_EVIDENCE" in rej["F2-vague"]                               # S05
    assert "SPONSOR_OUTRO_EXCLUDED" in rej["F4-sponsor"]
    assert m["coverage_ledger"]["largest_unknowns"] == [] or isinstance(m["coverage_ledger"]["largest_unknowns"], list)


@pytest.mark.req("ADD25-S05")
def test_real_survey_navigation_windows_cannot_be_selected_without_rationale():
    from vme.selection.first15 import navigation_candidates_from_survey
    sv = {"shots": [{"shot_id": "s", "start_frame_index": 0, "end_frame_index_inclusive": 299, "start_pts_time": 0, "end_pts_time": 5,
                     "frame_count": 300}]}
    nav = navigation_candidates_from_survey("a" * 64, sv)
    m = propose_selection(nav * 5, ["a" * 64, "b" * 64, "c" * 64, "d" * 64, "e" * 64])
    assert m["selected_count"] == 0 and m["status"] == "NEEDS_SELECTION_REVIEW"


@pytest.mark.req("ADD26-D02")
def test_sixth_absent():
    r = locate_sixth_intro(None, None, None)
    assert r.status == "SIXTH_SOURCE_NOT_AVAILABLE" and r.proposed_interval is None and r.clip_file is None


@pytest.mark.req("ADD26-D03")
def test_sixth_located_from_actual_frames_nonround_pts(tmp_path):
    clip = fx.make_sixth_clip(tmp_path / "six.mp4", segments=[("gray", 13), ("red", 37), ("blue", 19)])
    idx, loader = fx.index_and_loader(clip, tmp_path / "i")
    r = locate_sixth_intro(clip, idx[0]["film_sha256"], idx, classifier=fx.colour_classifier_factory(loader),
                           classifier_kind="SYNTHETIC_COLOUR_FIXTURE", search_window_s=(0, 5))
    assert r.status == "PROPOSED_AWAITING_HUMAN_CONFIRMATION"
    assert r.proposed_interval["start_frame_index"] == 13 and r.proposed_interval["end_frame_index_inclusive"] == 50
    assert abs(r.proposed_interval["start_pts_time"] - 13 / 60) < 1e-6
    with pytest.raises(Blocked):
        lock_sixth_interval(r.to_dict(), start_frame_index=13, end_frame_index_inclusive=50, confirmed_by="agent", index=idx,
                            witness_packet_sha=digest(r.witness_packet))
    with pytest.raises(Blocked):
        lock_sixth_interval(r.to_dict(), start_frame_index=13, end_frame_index_inclusive=50, confirmed_by="user", index=idx,
                            witness_packet_sha="wrong")
    lk = lock_sixth_interval(r.to_dict(), start_frame_index=13, end_frame_index_inclusive=50, confirmed_by="user", index=idx,
                             witness_packet_sha=digest(r.witness_packet))
    assert lk["status"] == "LOCKED" and lk["frame_count"] == 38 and lk["separate_from_first15"]
    assert "brand earth logo" in lk["forbidden_source_specific_copies"]


@pytest.mark.req("ADD26-D04")
def test_multiple_volcano_or_logo_events_not_auto_locked(tmp_path):
    clip = fx.make_sixth_clip(tmp_path / "six2.mp4", segments=[("red", 12), ("blue", 10), ("red", 12), ("blue", 10)])
    idx, loader = fx.index_and_loader(clip, tmp_path / "i")
    r = locate_sixth_intro(clip, idx[0]["film_sha256"], idx, classifier=fx.colour_classifier_factory(loader), search_window_s=(0, 5))
    assert r.status == "AMBIGUOUS_REQUIRES_REVIEW" and r.proposed_interval is None
    assert len(r.candidate_starts) == 2 and len(r.candidate_logo_entrances) == 2


@pytest.mark.req("ADD26-D03", "ADD26-D04")
def test_real_sixth_locator_local_candidates_awaiting_human():
    p = ROOT / "workspace" / "state" / "SIXTH_LOCATOR_STATUS.json"
    if not p.exists():
        pytest.skip("real sixth locator not run")
    r = json.loads(p.read_text(encoding="utf-8"))
    assert r["status"] == "CANDIDATE_BOUNDARIES_AWAITING_HUMAN_REVIEW" and r["proposed_interval"] is None
    assert r["viewed_by_agent_or_uploaded"] is False and r["witness_packet_files"]


@pytest.mark.req("ADD26-D01")
def test_only_authoritative_spec_set_used():
    from vme.spec_registry import authority_report
    rep = authority_report(ROOT.parent / "Visual_Mastery_Engine_Build_Spec_v1_3")
    assert rep["missing_authoritative"] == []
    assert "00_PREVIOUS_V12_LAUNCH_REFERENCE_DO_NOT_PASTE.md" in rep["superseded_present"]
    assert rep["authoritative_launch"].endswith("ADDENDA_24_25_26_27_PASTE_THIS.txt")
