"""R3-C06 — timestamped transcript / sound understanding, aligned to NATIVE PTS, and the searchable AudioVisualEventIndex.

ASR runs LOCALLY only (no film or audio leaves the machine). Backends are pluggable:
  * `faster_whisper` — used only if that package and a local model are installed (not bundled; installing it is a user decision);
  * `human_transcript` — a human-supplied JSON of {words:[{text,start,end,speaker?}]} (TRANSCRIPT_OBSERVED after alignment check).
With no backend the state is BLOCKED:ASR_BACKEND_UNAVAILABLE — never a silent pass and never energy-implied meaning.

Status separation: TRANSCRIPT_OBSERVED (human transcript passing alignment) vs ASR_UNCERTAIN (machine words, any confidence) vs
MISALIGNED_REJECTED (word time contradicts the waveform beyond the correction window). Onset energy NEVER implies meaning; a sound cue
without words is NON_SPEECH_UNCLASSIFIED until a classifier/human labels it.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..util import Blocked, digest

ASR_BACKENDS = ("faster_whisper", "human_transcript")
EVENT_STATUSES = ("TRANSCRIPT_OBSERVED", "ASR_UNCERTAIN", "MISALIGNED_REJECTED", "NON_SPEECH_UNCLASSIFIED", "NON_SPEECH_LABELLED",
                  "VISUAL_EVENT", "SHOT_CUT", "DELIBERATE_SILENCE")


def available_backends() -> list[str]:
    import importlib.util as u
    out = ["human_transcript"]
    if u.find_spec("faster_whisper"):
        out.insert(0, "faster_whisper")
    return out


def transcribe_local(video: str | Path, *, start_pts: float, end_pts: float, backend: str, human_file: str | Path | None = None,
                     model_dir: str | Path | None = None) -> dict:
    """Return {"backend", "words": [{text, start, end, confidence?, speaker?}], "status"} with times ABSOLUTE (film PTS seconds)."""
    if backend not in ASR_BACKENDS:
        raise Blocked("ASR_BACKEND_UNKNOWN", backend)
    if backend == "human_transcript":
        if not human_file or not Path(human_file).exists():
            raise Blocked("ASR_BACKEND_UNAVAILABLE", "no human transcript file supplied for this interval")
        d = json.loads(Path(human_file).read_text(encoding="utf-8"))
        words = [w for w in d.get("words", []) if start_pts - 1e-6 <= float(w["start"]) <= end_pts + 1e-6]
        return {"backend": backend, "words": words, "origin": "HUMAN", "source_file_sha": digest(d)}
    if backend not in available_backends():
        raise Blocked("ASR_BACKEND_UNAVAILABLE", "faster_whisper is not installed locally (install is a user decision; nothing is uploaded)")
    from faster_whisper import WhisperModel  # type: ignore[import-not-found]   # pragma: no cover - optional local backend
    if not model_dir:
        raise Blocked("ASR_MODEL_NOT_CONFIGURED", "set a local model directory; models are never downloaded implicitly")
    m = WhisperModel(str(model_dir), device="cpu", local_files_only=True)  # pragma: no cover
    segs, _info = m.transcribe(str(video), word_timestamps=True, clip_timestamps=[start_pts, end_pts])  # pragma: no cover
    words = [{"text": w.word.strip(), "start": float(w.start), "end": float(w.end), "confidence": float(w.probability)}
             for s in segs for w in (s.words or [])]  # pragma: no cover
    return {"backend": backend, "words": words, "origin": "LOCAL_ASR"}  # pragma: no cover


def align_words(words: list[dict], *, onset_times_abs: list[float], frame_pts: list[tuple[int, float]], origin: str,
                window_s: float = 0.12) -> list[dict]:
    """Bind each word to the frame whose native PTS is nearest its (verified) start. A word whose start has no waveform onset within
    `window_s` is MISALIGNED_REJECTED; one within the window is snapped to the measured onset (correction recorded)."""
    if not frame_pts:
        raise Blocked("NO_FRAME_TIMEBASE", "align against the native frame index")
    out = []
    for i, w in enumerate(words):
        s = float(w["start"])
        near = min(onset_times_abs, key=lambda t: abs(t - s)) if onset_times_abs else None
        if near is None or abs(near - s) > window_s:
            status, t = "MISALIGNED_REJECTED", s
        else:
            status = "TRANSCRIPT_OBSERVED" if origin == "HUMAN" else "ASR_UNCERTAIN"
            t = near
        k, pts = min(frame_pts, key=lambda kp: (abs(kp[1] - t), kp[0]))
        out.append({"word_index": i, "text": w["text"], "claimed_start": s, "aligned_start": t, "correction_s": round(t - s, 6),
                    "frame_index": k, "pts_time": pts, "status": status, "speaker": w.get("speaker"), "confidence": w.get("confidence")})
    return out


def build_audiovisual_event_index(st, *, film_sha: str, seq: str, aligned_words: list[dict], onsets: list[tuple[int, float]],
                                  cuts: list[tuple[int, float]], visual_events: list[dict], silence_spans: list[tuple[int, int]] | None = None) -> dict:
    """Store one AudioVisualEvent per word / non-speech onset / shot cut / visual event / deliberate silence, all on native PTS, and
    LINK words to coinciding visual events (same frame ±1). Never upgrades meaning: a non-speech onset stays NON_SPEECH_UNCLASSIFIED."""
    rows: list[dict] = []
    word_frames = {w["frame_index"] for w in aligned_words if w["status"] != "MISALIGNED_REJECTED"}
    for w in aligned_words:
        rows.append({"kind": "WORD", "frame_index": w["frame_index"], "pts_time": w["pts_time"], "text": w["text"], "status": w["status"],
                     "speaker": w.get("speaker"), "correction_s": w["correction_s"]})
    for k, pts in onsets:
        if not any(abs(k - f) <= 1 for f in word_frames):
            rows.append({"kind": "NON_SPEECH_ONSET", "frame_index": k, "pts_time": pts, "text": "", "status": "NON_SPEECH_UNCLASSIFIED"})
    for k, pts in cuts:
        rows.append({"kind": "SHOT_CUT", "frame_index": k, "pts_time": pts, "text": "", "status": "SHOT_CUT"})
    for e in visual_events:
        rows.append({"kind": "VISUAL_EVENT", "frame_index": e["frame_index"], "pts_time": e["pts_time"], "text": e.get("text", ""),
                     "status": "VISUAL_EVENT", "witness_id": e.get("witness_id")})
    for a, b in silence_spans or []:
        rows.append({"kind": "DELIBERATE_SILENCE", "frame_index": a, "pts_time": None, "text": f"silence frames {a}..{b}", "status": "DELIBERATE_SILENCE"})
    vis = [r for r in rows if r["kind"] in ("VISUAL_EVENT", "SHOT_CUT")]
    for r in rows:
        if r["kind"] == "WORD" and r["status"] != "MISALIGNED_REJECTED":
            r["linked_visual"] = [v.get("witness_id") or f"{v['kind']}@{v['frame_index']}" for v in vis if abs(v["frame_index"] - r["frame_index"]) <= 1]
    for i, r in enumerate(sorted(rows, key=lambda r: (r["frame_index"], r["kind"], r["text"]))):
        r.update(event_id=f"AV-{film_sha[:10]}-{seq}-{i:04d}", film_sha256=film_sha, sequence_id=seq)
        st.put("AudioVisualEvent", r["event_id"], r)
    summary = {k: sum(1 for r in rows if r["status"] == k) for k in EVENT_STATUSES}
    rec = {"film_sha256": film_sha, "sequence_id": seq, "events": len(rows), "by_status": summary,
           "meaning_status": "TRANSCRIPT_OBSERVED" if summary["TRANSCRIPT_OBSERVED"] else
                             "ASR_UNCERTAIN" if summary["ASR_UNCERTAIN"] else "AUDIO_MEANING_UNSTUDIED"}
    st.put("AudioVisualEventIndex", f"{film_sha[:16]}:{seq}", rec)
    return rec
