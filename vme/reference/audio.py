"""R3 F14 — LOCAL source-audio study and original audiovisual production checks (no upload, no source-audio copying).

Source study (`study_interval`): decode ONLY the selected interval's audio stream locally to mono PCM, measure an RMS envelope at the
video frame rate, detect onsets and silence spans, peak level and timebase. Narration words / music / SFX meaning are NOT inferred
from energy: they stay `AUDIO_MEANING_UNSTUDIED` until a consented transcript/review exists. A file without audio is
`AUDIO_STREAM_ABSENT` — an explicit state, never a silent pass.

Production (`build_cue_track`, `mux`, `verify_av`): an APPROVED original sound asset (authority SOUND_ASSET_APPROVAL) is placed at the
event program's cue frames, muxed into the rendered MP4, and the result is verified: audio stream present, duration matches the video,
measured onsets match scheduled cues within one frame. Any failure raises AUDIOVISUAL_SYNC_FAILED / AUDIO_STREAM_MISSING.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

from ..util import Blocked, sha256_file
from .probe import require_tool

SR = 16000


def _pcm(path: str | Path, start: float | None = None, dur: float | None = None) -> np.ndarray | None:
    ff = require_tool("ffmpeg")
    cmd = [ff, "-v", "error", "-nostdin"]
    if start is not None:
        cmd += ["-ss", f"{max(0.0, start):.6f}"]
    cmd += ["-i", str(path)]
    if dur is not None:
        cmd += ["-t", f"{dur:.6f}"]
    cmd += ["-map", "0:a:0?", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise Blocked("AUDIO_DECODE_FAILED", r.stderr.decode(errors="replace")[:300])
    if not r.stdout:
        return None
    return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def audio_stream_info(path: str | Path) -> dict | None:
    fp = require_tool("ffprobe")
    r = subprocess.run([fp, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name,sample_rate,channels,time_base,duration",
                        "-of", "json", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    s = (json.loads(r.stdout or "{}").get("streams") or [])
    return s[0] if s else None


def envelope(pcm: np.ndarray, fps: float) -> np.ndarray:
    hop = max(1, int(round(SR / fps)))
    n = len(pcm) // hop
    if n == 0:
        return np.zeros(0)
    return np.sqrt(np.mean(pcm[: n * hop].reshape(n, hop) ** 2, axis=1))


def onsets(env: np.ndarray, *, floor: float = 0.02) -> list[int]:
    if env.size == 0:
        return []
    thr = max(floor, 3.0 * float(np.median(env)))
    above = env > thr
    return [int(i) for i in range(len(env)) if above[i] and (i == 0 or not above[i - 1])]


def study_interval(video: str | Path, *, start_pts: float, end_pts: float, fps: float, film_sha256: str, sequence_id: str) -> dict:
    info = audio_stream_info(video)
    base = {"film_sha256": film_sha256, "sequence_id": sequence_id, "start_pts": start_pts, "end_pts": end_pts, "fps": fps,
            "meaning": "AUDIO_MEANING_UNSTUDIED (narration/music/SFX semantics need a consented transcript or human review)",
            "copied_audio": False}
    if not info:
        return {**base, "status": "AUDIO_STREAM_ABSENT", "onset_frames": [], "silence_spans": []}
    pcm = _pcm(video, start_pts, end_pts - start_pts + 1.0 / fps)
    if pcm is None or pcm.size == 0:
        return {**base, "status": "AUDIO_STREAM_EMPTY_IN_INTERVAL", "stream": info, "onset_frames": [], "silence_spans": []}
    env = envelope(pcm, fps)
    quiet = env < 0.005
    spans, s = [], None
    for i, q in enumerate(quiet):
        if q and s is None:
            s = i
        if not q and s is not None:
            if i - s >= 3:
                spans.append([s, i - 1])
            s = None
    if s is not None and len(quiet) - s >= 3:
        spans.append([s, len(quiet) - 1])
    hop = max(1, int(round(SR / fps)))
    ons = onsets(env)
    return {**base, "status": "AUDIO_SIGNAL_STUDIED_LOCALLY", "stream": info, "onset_frames": ons,
            # R3-C06: onset TIMES (seconds from start_pts, exact envelope-bin start) so callers map to frames by native PTS (VFR-safe)
            "onset_times_s": [round(i * hop / SR, 6) for i in ons], "silence_spans": spans,
            "peak_dbfs": float(20 * np.log10(max(1e-9, float(np.max(np.abs(pcm)))))), "envelope_frames": int(env.size)}


def build_cue_track(asset: str | Path, cue_frames: list[int], *, fps: float, frames: int, out_wav: str | Path) -> Path:
    """Place the approved asset at every cue frame on a silent bed exactly as long as the video."""
    ff = require_tool("ffmpeg")
    out_wav = Path(out_wav)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    dur = frames / fps
    if not cue_frames:
        raise Blocked("NO_AUDIO_CUES", "audio required but the event program scheduled no cue")
    inputs = ["-f", "lavfi", "-t", f"{dur:.6f}", "-i", f"anullsrc=r={SR}:cl=mono"]
    filt, labels = [], ["[0:a]"]
    for i, f in enumerate(cue_frames):
        inputs += ["-i", str(asset)]
        ms = int(round(f / fps * 1000))
        filt.append(f"[{i + 1}:a]aresample={SR},aformat=channel_layouts=mono,adelay={ms}[c{i}]")
        labels.append(f"[c{i}]")
    filt.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,atrim=0:{dur:.6f}[out]")
    r = subprocess.run([ff, "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt), "-map", "[out]", "-ar", str(SR), str(out_wav)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise Blocked("AUDIO_TRACK_BUILD_FAILED", r.stderr[-400:])
    return out_wav


def mux(video: str | Path, wav: str | Path, out_mp4: str | Path) -> Path:
    ff = require_tool("ffmpeg")
    r = subprocess.run([ff, "-v", "error", "-y", "-i", str(video), "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "128k", "-shortest", str(out_mp4)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise Blocked("AUDIO_MUX_FAILED", r.stderr[-400:])
    return Path(out_mp4)


def verify_av(mp4: str | Path, *, cue_frames: list[int], fps: float, frames: int, tolerance_frames: int = 1) -> dict:
    """Terminal AV gate: stream present, duration, and each scheduled cue is heard within tolerance (and nothing unscheduled)."""
    info = audio_stream_info(mp4)
    problems = []
    if not info:
        return {"ok": False, "problems": ["AUDIO_STREAM_MISSING"], "file_sha256": sha256_file(mp4)}
    pcm = _pcm(mp4)
    env = envelope(pcm if pcm is not None else np.zeros(0), fps)
    got = onsets(env)
    vdur = frames / fps
    adur = (pcm.size / SR) if pcm is not None else 0.0
    if abs(adur - vdur) > 2.0 / fps + 0.03:
        problems.append(f"AUDIO_DURATION_MISMATCH:{adur:.3f}s_vs_{vdur:.3f}s")
    for c in cue_frames:
        if not any(abs(g - c) <= tolerance_frames for g in got):
            problems.append(f"CUE_NOT_HEARD_AT_FRAME:{c}")
    for g in got:
        if not any(abs(g - c) <= tolerance_frames for c in cue_frames):
            problems.append(f"UNSCHEDULED_ONSET_AT_FRAME:{g}")
    peak = float(np.max(np.abs(pcm))) if pcm is not None and pcm.size else 0.0
    if peak >= 0.999:
        problems.append("AUDIO_CLIPPING")
    if peak < 0.01:
        problems.append("AUDIO_SILENT")
    return {"ok": not problems, "problems": problems, "measured_onsets": got, "scheduled_cues": cue_frames, "audio_duration_s": adur,
            "video_duration_s": vdur, "peak": peak, "stream": info, "file_sha256": sha256_file(mp4)}


def make_original_cue_asset(out_wav: str | Path, *, freq: float = 660.0, ms: int = 120) -> Path:
    """A locally SYNTHESIZED original tone (not source audio) for offline drills; must still be human-approved before use."""
    ff = require_tool("ffmpeg")
    out_wav = Path(out_wav)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([ff, "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency={freq}:sample_rate={SR}:duration={ms / 1000}",
                        "-af", "volume=0.5", str(out_wav)], capture_output=True, text=True)
    if r.returncode != 0:
        raise Blocked("AUDIO_ASSET_SYNTH_FAILED", r.stderr[-300:])
    return out_wav
