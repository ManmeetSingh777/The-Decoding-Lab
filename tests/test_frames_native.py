"""Native-resolution crops and truthful scale labels (A03, C04, ADD25-F06, B03 real)."""
import json
import sqlite3

import pytest

from conftest import ROOT
from vme.util import Blocked
from vme.reference.frames import native_crop, verify_native_claim, resized_for_provider, retrieve_frame


@pytest.mark.req("A03", "C04")
def test_native_crop_real_pixel_coordinates(indexed24):
    clip, idx, _ = indexed24
    fr = retrieve_frame(clip, idx[5])
    c = native_crop(fr, 10, 20, 40, 30)
    assert (c.output_width, c.output_height) == (40, 30) and c.native_resolution and c.parent_png_sha256 == fr.png_sha256
    with pytest.raises(Blocked):
        native_crop(fr, 150, 80, 40, 30)


@pytest.mark.req("ADD25-F06", "C04")
def test_resized_crop_labelled_native_rejected(indexed24):
    clip, idx, _ = indexed24
    fr = retrieve_frame(clip, idx[3])
    small = resized_for_provider(fr, 80)
    assert not small.native and small.scale_factor < 1 and small.raw_sha256 == fr.raw_sha256
    with pytest.raises(Blocked) as e:
        native_crop(small, 0, 0, 10, 10)
    assert e.value.code == "NOT_NATIVE_PARENT"
    m = native_crop(fr, 0, 0, 40, 40).manifest()
    m["output_width"] = 20
    with pytest.raises(Blocked) as e2:
        verify_native_claim(m)
    assert e2.value.code == "FALSE_NATIVE_DETAIL_CLAIM"


@pytest.mark.req("B03", "C03", "A27")
def test_real_films_indexed_but_zero_vlm_seen():
    db = ROOT / "workspace" / "store" / "vme.sqlite"
    summ = ROOT / "workspace" / "state" / "FRAME_INDEX_SUMMARY.json"
    if not db.exists() or not summ.exists():
        pytest.skip("real workspace absent")
    con = sqlite3.connect(str(db))
    n = con.execute("SELECT COUNT(*) FROM frame_vision WHERE status IN ('VISION_OUTPUT_VERIFIED','RESPONSE_IDENTITY_BOUND')").fetchone()[0]
    con.close()
    assert n == 0 and json.loads(summ.read_text(encoding="utf-8"))["total_frames_decoded"] > 0
