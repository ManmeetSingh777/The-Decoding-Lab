"""Navigation-only whole-film survey (ADD25 §1.1 step 3; ADD26-F01).

Local scene-change detection over the decoded stream. Output is `SURVEY_ONLY`: it
locates potentially important scenes; it is NOT vision, NOT per-frame artistic
inspection, and cannot advance any VLM coverage status.
"""
from __future__ import annotations

import bisect
import re
import subprocess
import tempfile
from dataclasses import dataclass, asdict, field
from pathlib import Path

from ..util import Blocked, atomic_write_json, digest, now_iso
from .probe import require_tool

SURVEY_STATUS = "SURVEY_ONLY_NOT_VISION"


@dataclass
class Shot:
    shot_id: str
    start_frame_index: int
    end_frame_index_inclusive: int
    start_pts_time: float
    end_pts_time: float
    frame_count: int
    entry_change_score: float
    boundary_confidence: str = "CANDIDATE_NOT_GROUND_TRUTH"
    content_label: str = "UNKNOWN_REQUIRES_VISUAL_REVIEW"  # credits/sponsor/main unknown without vision


@dataclass
class FilmSurvey:
    film_sha256: str
    method: str
    threshold: float
    shots: list
    status: str = SURVEY_STATUS
    navigation_thumbnails: list = field(default_factory=list)
    uncertainty: list = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def detect_scene_changes(video: str | Path, threshold: float = 0.30, scale_w: int = 320) -> list[tuple[float, float]]:
    """Return [(pts_time, score)] for frames whose scene score exceeds threshold."""
    exe = require_tool("ffmpeg")
    with tempfile.TemporaryDirectory() as td:
        meta = Path(td) / "scenes.txt"
        # Filter-graph path escaping for Windows drive letters.
        mpath = meta.as_posix().replace(":", "\\:")
        cmd = [exe, "-v", "error", "-nostdin", "-copyts", "-i", str(video), "-map", "0:v:0",
               "-vf", f"scale={scale_w}:-2,select='gt(scene\\,{threshold})',metadata=print:file='{mpath}'",
               "-fps_mode", "passthrough", "-f", "null", "-"]
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if out.returncode != 0:
            raise Blocked("SURVEY_FAILED", out.stderr[:300])
        text = meta.read_text(encoding="utf-8") if meta.exists() else ""
    res: list[tuple[float, float]] = []
    cur_t = None
    for line in text.splitlines():
        m = re.search(r"pts_time:([0-9.]+)", line)
        if m:
            cur_t = float(m.group(1))
        m2 = re.search(r"lavfi\.scene_score=([0-9.]+)", line)
        if m2 and cur_t is not None:
            res.append((cur_t, float(m2.group(1))))
            cur_t = None
    return res


def build_shots(index: list[dict], cuts: list[tuple[float, float]]) -> list[Shot]:
    times = [r["pts_time"] for r in index]
    starts = [(0, 1.0)]
    for t, score in cuts:
        i = bisect.bisect_left(times, t - 1e-6)
        if 0 < i < len(times) and i != starts[-1][0]:
            starts.append((i, score))
    shots = []
    for k, (s, score) in enumerate(starts):
        e = (starts[k + 1][0] - 1) if k + 1 < len(starts) else len(index) - 1
        shots.append(Shot(f"shot_{k:04d}", s, e, index[s]["pts_time"], index[e]["pts_time"], e - s + 1, round(score, 4)))
    return shots


def survey_film(video: str | Path, film_sha: str, index: list[dict], out_dir: str | Path, *,
                threshold: float = 0.30) -> FilmSurvey:
    cuts = detect_scene_changes(video, threshold)
    shots = build_shots(index, cuts)
    sv = FilmSurvey(film_sha, "ffmpeg_scene_score_navigation", threshold, [asdict(s) for s in shots],
                    uncertainty=["Shot boundaries are candidates; gradual dissolves/zooms may be missed or over-split.",
                                 "No content labels (main/credits/sponsor) without visual review.",
                                 "This survey never counts as VLM_SEEN or PER_FRAME_ART_OBSERVED."],
                    created_at=now_iso())
    atomic_write_json(Path(out_dir) / "film_survey.json", sv.to_dict())
    return sv


def survey_digest(sv: FilmSurvey | dict) -> str:
    return digest(sv.to_dict() if isinstance(sv, FilmSurvey) else sv)
