"""Every-presented-frame decode index with true PTS (A26, A29, B02, C02, ADD25 1.1).

Index = actual decode via ffmpeg `framehash` (sha256 of each decoded frame in its
native pixel format), passthrough timing (no duplication/dropping) and -copyts
(original PTS preserved). Frame counts are never derived from fps x duration.
"""
from __future__ import annotations

import gzip
import json
import subprocess
from dataclasses import dataclass, asdict, field
from fractions import Fraction
from pathlib import Path
from typing import Iterator

from ..util import Blocked, atomic_write_json, sha256_file, now_iso
from .probe import require_tool


@dataclass
class FrameRecord:
    film_sha256: str
    video_stream_id: int
    presentation_index: int
    pts: int
    pts_time: float
    duration: int
    frame_width: int
    frame_height: int
    pix_fmt: str
    frame_content_sha256: str
    decode_status: str = "DECODED"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class IndexSummary:
    film_sha256: str
    video_path: str
    frame_count_decoded: int
    first_pts: int | None
    last_pts: int | None
    time_base: str
    pts_monotonic: bool
    duplicate_pts: list
    pts_discontinuities: list
    distinct_durations: list
    vfr_observed: bool
    metadata_nb_frames: int | None
    metadata_count_mismatch: bool
    last_frame_end_s: float | None
    stream_duration_s: float | None
    end_gap_s: float | None
    index_path: str
    index_sha256: str
    complete_frame_index: bool
    problems: list = field(default_factory=list)
    indexed_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _framehash_lines(path: str | Path) -> Iterator[str]:
    exe = require_tool("ffmpeg")
    cmd = [exe, "-v", "error", "-nostdin", "-copyts", "-i", str(path), "-map", "0:v:0",
           "-fps_mode", "passthrough", "-enc_time_base:v", "demux",  # keep stream timebase: no VFR collapse
           "-f", "framehash", "-hash", "sha256", "-"]
    import tempfile
    with tempfile.TemporaryFile() as errf:  # stderr to file: avoids pipe deadlock on long decodes
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=errf, text=True, encoding="utf-8",
                                errors="replace", bufsize=1 << 16)
        assert proc.stdout is not None
        for line in proc.stdout:
            yield line.rstrip("\n")
        rc = proc.wait()
        errf.seek(0)
        err = errf.read().decode("utf-8", errors="replace")
    if rc != 0:
        raise Blocked("DECODE_FAILED", err.strip()[:400], path=str(path))
    if err.strip():
        # Decoder warnings are preserved, not hidden.
        yield f"#decoder_stderr {err.strip()[:2000]}"


def parse_framehash(lines: Iterator[str], film_sha: str, width: int, height: int) -> tuple[list[FrameRecord], dict]:
    header: dict = {"decoder_warnings": []}
    frames: list[FrameRecord] = []
    tb = Fraction(1, 1)
    pix = "?"
    for line in lines:
        if line.startswith("#"):
            if line.startswith("#tb 0:"):
                tb = Fraction(line.split(":", 1)[1].strip())
                header["time_base"] = str(tb)
            elif line.startswith("#dimensions 0:"):
                d = line.split(":", 1)[1].strip()
                w, h = d.split("x")
                width, height = int(w), int(h)
            elif line.startswith("#pix_fmt 0:") or line.startswith("#format 0:"):
                pix = line.split(":", 1)[1].strip()
            elif line.startswith("#decoder_stderr"):
                header["decoder_warnings"].append(line[len("#decoder_stderr "):])
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6:
            continue
        stream, _dts, pts, dur, _size, h = parts[:6]
        if int(stream) != 0:
            continue
        p = int(pts)
        frames.append(FrameRecord(film_sha, 0, len(frames), p, float(p * tb), int(dur), width, height, pix, h.lower()))
    header.setdefault("time_base", str(tb))
    header["pix_fmt"] = pix
    return frames, header


def analyse_index(frames: list[FrameRecord], time_base: str, stream_duration_s: float | None,
                  metadata_nb_frames: int | None) -> dict:
    tb = Fraction(time_base)
    problems: list[str] = []
    dup: list = []
    disc: list = []
    monotonic = True
    seen_pts: dict[int, int] = {}
    durations = sorted({f.duration for f in frames})
    for i, f in enumerate(frames):
        if f.presentation_index != i:
            problems.append(f"INDEX_NOT_CONTIGUOUS at {i}")
        if f.pts in seen_pts:
            dup.append([seen_pts[f.pts], i, f.pts])
        seen_pts[f.pts] = i
        if i:
            prev = frames[i - 1]
            if f.pts <= prev.pts:
                monotonic = False
                problems.append(f"PTS_NOT_MONOTONIC at {i}")
            elif prev.duration and f.pts - prev.pts != prev.duration:
                disc.append([i, prev.pts, f.pts, f.pts - prev.pts, prev.duration])
    if dup:
        problems.append(f"DUPLICATE_PTS x{len(dup)}")
    last_end = float((frames[-1].pts + frames[-1].duration) * tb) if frames else None
    first_t = frames[0].pts_time if frames else None
    end_gap = None
    if stream_duration_s is not None and last_end is not None and first_t is not None:
        # stream duration is measured from first pts
        end_gap = round(stream_duration_s - (last_end - first_t), 6)
        if end_gap > 2 * float(Fraction(max(durations or [1])) * tb):
            problems.append(f"POSSIBLE_MISSING_TAIL gap={end_gap}s")
    mismatch = metadata_nb_frames is not None and metadata_nb_frames != len(frames)
    if not frames:
        problems.append("NO_FRAMES_DECODED")
    return {
        "pts_monotonic": monotonic, "duplicate_pts": dup[:50], "pts_discontinuities": disc[:200],
        "distinct_durations": durations, "vfr_observed": len(durations) > 1 or bool(disc),
        "metadata_count_mismatch": bool(mismatch), "last_frame_end_s": last_end, "end_gap_s": end_gap,
        "problems": problems,
    }


def write_index(frames: list[FrameRecord], out_path: Path) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as f:
        for fr in frames:
            f.write(json.dumps(fr.to_dict(), sort_keys=True, separators=(",", ":")) + "\n")
    tmp.replace(out_path)
    return sha256_file(out_path)


def read_index(path: str | Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def index_every_frame(video_path: str | Path, film_sha: str, out_dir: str | Path, *,
                      width: int, height: int, stream_duration_s: float | None,
                      metadata_nb_frames: int | None) -> IndexSummary:
    """Decode all presented frames and persist the per-frame index + summary."""
    out_dir = Path(out_dir)
    frames, header = parse_framehash(_framehash_lines(video_path), film_sha, width, height)
    an = analyse_index(frames, header["time_base"], stream_duration_s, metadata_nb_frames)
    idx_path = out_dir / "index.jsonl.gz"
    idx_sha = write_index(frames, idx_path)
    complete = bool(frames) and an["pts_monotonic"] and not an["duplicate_pts"] and \
        not any(p.startswith(("INDEX_NOT_CONTIGUOUS", "POSSIBLE_MISSING_TAIL", "NO_FRAMES")) for p in an["problems"])
    summary = IndexSummary(
        film_sha256=film_sha, video_path=str(video_path), frame_count_decoded=len(frames),
        first_pts=frames[0].pts if frames else None, last_pts=frames[-1].pts if frames else None,
        time_base=header["time_base"], pts_monotonic=an["pts_monotonic"], duplicate_pts=an["duplicate_pts"],
        pts_discontinuities=an["pts_discontinuities"], distinct_durations=an["distinct_durations"],
        vfr_observed=an["vfr_observed"], metadata_nb_frames=metadata_nb_frames,
        metadata_count_mismatch=an["metadata_count_mismatch"], last_frame_end_s=an["last_frame_end_s"],
        stream_duration_s=stream_duration_s, end_gap_s=an["end_gap_s"], index_path=str(idx_path),
        index_sha256=idx_sha, complete_frame_index=complete,
        problems=an["problems"] + [f"DECODER_WARNING {w[:200]}" for w in header["decoder_warnings"]],
        indexed_at=now_iso(),
    )
    atomic_write_json(out_dir / "index_summary.json", summary.to_dict())
    return summary


def validate_claimed_coverage(index: list[dict], claimed_indices: list[int]) -> dict:
    """Refuse a false 100% claim: compares a claimed processed set against the true index (A29)."""
    n = len(index)
    want = set(range(n))
    got = set(claimed_indices)
    missing = sorted(want - got)
    extra = sorted(got - want)
    dups = len(claimed_indices) - len(got)
    return {"expected": n, "claimed": len(claimed_indices), "missing_count": len(missing),
            "missing_ranges": _ranges(missing), "out_of_range": extra[:20], "duplicate_claims": dups,
            "complete": not missing and not extra and dups == 0}


def _ranges(xs: list[int]) -> list[list[int]]:
    out: list[list[int]] = []
    for x in xs:
        if out and x == out[-1][1] + 1:
            out[-1][1] = x
        else:
            out.append([x, x])
    return out


ranges = _ranges
