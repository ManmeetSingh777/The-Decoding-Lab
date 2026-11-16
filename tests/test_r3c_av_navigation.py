"""R3-C06 transcript/AV index + layered original audio, R3-C07 targeted navigation."""
from __future__ import annotations

import wave

import numpy as np
import pytest

from vme.util import Blocked


# ------------------------------------------------------------------------------------------------ C06 transcript alignment
FP = [(k, round(k / 30, 6)) for k in range(0, 300)]


@pytest.mark.req("R3-C06")
def test_human_words_align_to_waveform_onsets_and_native_pts():
    from vme.reference.transcript import align_words
    words = [{"text": "volcanoes", "start": 1.02, "end": 1.5}, {"text": "erupt", "start": 2.51, "end": 2.9}]
    a = align_words(words, onset_times_abs=[1.0, 2.5], frame_pts=FP, origin="HUMAN")
    assert [(w["status"], w["frame_index"], w["correction_s"]) for w in a] == [("TRANSCRIPT_OBSERVED", 30, -0.02), ("TRANSCRIPT_OBSERVED", 75, -0.01)]


@pytest.mark.req("R3-C06")
def test_a_misaligned_transcript_time_is_rejected_not_trusted():
    from vme.reference.transcript import align_words
    a = align_words([{"text": "erupt", "start": 4.0, "end": 4.3}], onset_times_abs=[2.5], frame_pts=FP, origin="HUMAN")
    assert a[0]["status"] == "MISALIGNED_REJECTED"


@pytest.mark.req("R3-C06")
def test_machine_words_are_never_observed_and_energy_never_implies_meaning(store):
    from vme.reference.transcript import align_words, build_audiovisual_event_index
    a = align_words([{"text": "lava", "start": 1.0, "end": 1.2, "confidence": 0.99}], onset_times_abs=[1.0], frame_pts=FP, origin="LOCAL_ASR")
    assert a[0]["status"] == "ASR_UNCERTAIN"
    rec = build_audiovisual_event_index(store, film_sha="f" * 64, seq="S1", aligned_words=a, onsets=[(30, 1.0), (90, 3.0)],
                                        cuts=[(60, 2.0)], visual_events=[{"frame_index": 31, "pts_time": 31 / 30, "text": "crater glows", "witness_id": "W-9"}])
    evs = {e["kind"]: e for e in store.list("AudioVisualEvent")}
    assert evs["NON_SPEECH_ONSET"]["status"] == "NON_SPEECH_UNCLASSIFIED" and evs["NON_SPEECH_ONSET"]["frame_index"] == 90
    assert evs["WORD"]["linked_visual"] == ["W-9"] and rec["meaning_status"] == "ASR_UNCERTAIN"


@pytest.mark.req("R3-C06")
def test_no_backend_is_an_explicit_block():
    from vme.reference.transcript import transcribe_local, available_backends
    with pytest.raises(Blocked) as e:
        transcribe_local("x.mp4", start_pts=0, end_pts=1, backend="human_transcript")
    assert e.value.code == "ASR_BACKEND_UNAVAILABLE"
    if "faster_whisper" not in available_backends():
        with pytest.raises(Blocked) as e:
            transcribe_local("x.mp4", start_pts=0, end_pts=1, backend="faster_whisper")
        assert e.value.code == "ASR_BACKEND_UNAVAILABLE"


# ------------------------------------------------------------------------------------------------ C06 layered original audio
def _tone(path, hz, secs=0.15):
    t = np.arange(int(16000 * secs)) / 16000
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes((0.5 * np.sin(2 * np.pi * hz * t) * 32767).astype(np.int16).tobytes())
    from vme.util import sha256_file
    return {"path": str(path), "sha256": sha256_file(path)}


@pytest.mark.req("R3-C06")
def test_each_layer_plays_its_own_approved_asset_and_fake_layering_is_refused(tmp_path):
    from vme.reference.audio import build_layered_audio
    layers = {"NARRATION": _tone(tmp_path / "n.wav", 220), "MUSIC": _tone(tmp_path / "m.wav", 440), "SFX": _tone(tmp_path / "s.wav", 880)}
    cues = [{"cue_id": "a", "frame": 10, "layer": "SFX"}, {"cue_id": "b", "frame": 10, "layer": "NARRATION"},
            {"cue_id": "c", "frame": 40, "layer": "MUSIC"}]
    mix = {"gain_db": {"NARRATION": 0, "MUSIC": -6, "SFX": -3}}
    r = build_layered_audio(layers, cues, mix_policy=mix, fps=30, frames=60, out_wav=tmp_path / "out.wav", approved=lambda s: True)
    assert r["per_layer_cue_frames"] == {"MUSIC": [40], "NARRATION": [10], "SFX": [10]}
    with pytest.raises(Blocked) as e:
        build_layered_audio({**layers, "MUSIC": layers["SFX"]}, cues, mix_policy=mix, fps=30, frames=60, out_wav=tmp_path / "o2.wav",
                            approved=lambda s: True)
    assert e.value.code == "ONE_ASSET_FAKING_SEVERAL_LAYERS"
    with pytest.raises(Blocked) as e:
        build_layered_audio(layers, cues, mix_policy={"gain_db": {"SFX": 0}}, fps=30, frames=60, out_wav=tmp_path / "o3.wav", approved=lambda s: True)
    assert e.value.code == "MIX_POLICY_UNDECLARED"
    with pytest.raises(Blocked) as e:
        build_layered_audio(layers, cues, mix_policy=mix, fps=30, frames=60, out_wav=tmp_path / "o4.wav", approved=lambda s: False)
    assert e.value.code == "NO_APPROVED_SOUND_ASSET"


# ------------------------------------------------------------------------------------------------ C07 navigation
@pytest.mark.req("R3-C07")
def test_inspect_range_returns_exact_native_frames_with_receipts(indexed24, tmp_path):
    from vme.reference.navigator import inspect_range
    clip, idx, loader = indexed24
    film = idx[0]["film_sha256"]
    t0, t1 = idx[5]["pts_time"], idx[9]["pts_time"]
    r = inspect_range(film_sha=film, index=idx, cache=loader, start_pts=t0, end_pts=t1, purpose="find the grip state in this range",
                      contact_sheet_to=tmp_path / "sheet.png", write_frames_to=tmp_path / "frames")
    assert [f["frame_index"] for f in r["frames"]] == [5, 6, 7, 8, 9]
    assert all(f["raw_frame_sha256"] == idx[f["frame_index"]]["frame_content_sha256"] and f["native"] for f in r["frames"])
    assert r["contact_sheet"]["use"].startswith("NAVIGATION_ONLY")
    with pytest.raises(Blocked) as e:
        inspect_range(film_sha=film, index=idx, cache=loader, start_pts=t0, end_pts=t1, purpose="x")
    assert e.value.code == "INSPECTION_PURPOSE_REQUIRED"


@pytest.mark.req("R3-C07")
def test_a_changed_source_identity_invalidates_the_retrieval(indexed24):
    from vme.reference.navigator import inspect_range
    clip, idx, loader = indexed24
    bad = [dict(r) for r in idx]
    bad[6]["frame_content_sha256"] = "0" * 64
    with pytest.raises(Blocked) as e:
        inspect_range(film_sha=idx[0]["film_sha256"], index=bad, cache=loader, start_pts=bad[5]["pts_time"], end_pts=bad[7]["pts_time"],
                      purpose="verify witness identity before reuse")
    assert e.value.code == "SOURCE_IDENTITY_CHANGED"


@pytest.mark.req("R3-C07", "R3-C06")
def test_search_finds_a_spoken_concept_and_its_scene_change_by_pts(store):
    from vme.reference.navigator import search_events
    from vme.reference.transcript import align_words, build_audiovisual_event_index
    a = align_words([{"text": "volcano", "start": 2.0, "end": 2.4}], onset_times_abs=[2.0], frame_pts=FP, origin="HUMAN")
    build_audiovisual_event_index(store, film_sha="f" * 64, seq="S1", aligned_words=a, onsets=[], cuts=[(61, 61 / 30)], visual_events=[])
    hits = search_events(store, text="volcano")
    assert hits and hits[0]["frame_index"] == 60 and hits[0]["pts_time"] == 2.0
    cut = search_events(store, event_kind="SHOT_CUT", time=(1.9, 2.1))
    assert [h["frame_index"] for h in cut] == [61]
