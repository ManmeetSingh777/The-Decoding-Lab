"""Source identity: SHA256, ffprobe facts, read-only allowlist and source lock (A02, C01, C02)."""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from dataclasses import dataclass, asdict
from fractions import Fraction
from pathlib import Path

from ..util import Blocked, sha256_file, now_iso

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".m4v"}

# Directory/file names that must never be ingested as film evidence (A01/C01).
FORBIDDEN_SOURCE_MARKERS = ("animationlab", "cmr", "old_research", "prior_findings", "style_hypotheses")


def which(tool: str) -> str | None:
    return shutil.which(tool)


def require_tool(tool: str) -> str:
    p = which(tool)
    if not p:
        raise Blocked("TOOL_MISSING", f"{tool} not on PATH")
    return p


@dataclass
class SourceProbe:
    path: str
    file_name: str
    sha256: str
    size_bytes: int
    codec: str
    width: int
    height: int
    r_frame_rate: str
    avg_frame_rate: str
    time_base: str
    start_pts: int
    rotation: int
    stream_duration_s: float | None
    format_duration_s: float | None
    metadata_nb_frames: int | None
    audio_streams: int
    vfr_suspected: bool
    probed_at: str

    def to_dict(self) -> dict:
        return asdict(self)


def ffprobe_json(path: str | Path) -> dict:
    exe = require_tool("ffprobe")
    out = subprocess.run([exe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise Blocked("SOURCE_ACCESS", f"ffprobe failed: {out.stderr.strip()[:300]}", path=str(path))
    return json.loads(out.stdout)


def probe_source(path: str | Path, *, sha: str | None = None) -> SourceProbe:
    path = Path(path)
    if not path.exists():
        raise Blocked("SOURCE_ACCESS", f"missing {path}")
    info = ffprobe_json(path)
    vids = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    if not vids:
        raise Blocked("SOURCE_ACCESS", "no video stream", path=str(path))
    v = vids[0]
    auds = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    if "rotate" in (v.get("tags") or {}):
        rot = int(v["tags"]["rotate"])
    r = v.get("r_frame_rate", "0/1")
    a = v.get("avg_frame_rate", "0/1")
    try:
        vfr = Fraction(r) != Fraction(a) if Fraction(a) != 0 else True
    except (ZeroDivisionError, ValueError):
        vfr = True
    nb = v.get("nb_frames")
    return SourceProbe(
        path=str(path), file_name=path.name,
        sha256=sha or sha256_file(path), size_bytes=path.stat().st_size,
        codec=v.get("codec_name", "?"), width=int(v.get("width", 0)), height=int(v.get("height", 0)),
        r_frame_rate=r, avg_frame_rate=a, time_base=v.get("time_base", "?"),
        start_pts=int(v.get("start_pts", 0) or 0), rotation=rot,
        stream_duration_s=float(v["duration"]) if v.get("duration") else None,
        format_duration_s=float(info["format"]["duration"]) if info.get("format", {}).get("duration") else None,
        metadata_nb_frames=int(nb) if nb not in (None, "N/A") else None,
        audio_streams=len(auds), vfr_suspected=bool(vfr), probed_at=now_iso(),
    )


def discover_sources(folder: str | Path) -> list[Path]:
    folder = Path(folder)
    if not folder.is_dir():
        raise Blocked("SOURCE_ACCESS", f"source folder missing: {folder}")
    lower = str(folder).lower()
    if any(m in lower for m in FORBIDDEN_SOURCE_MARKERS):
        raise Blocked("FORBIDDEN_SOURCE_ROOT", f"{folder} looks like prior research material")
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in VIDEO_EXTS and p.is_file())
    for p in files:
        if any(m in p.name.lower() for m in FORBIDDEN_SOURCE_MARKERS):
            raise Blocked("FORBIDDEN_SOURCE_FILE", p.name)
    return files


def make_read_only(path: str | Path) -> bool:
    """Mark the original read-only (best effort on Windows). Returns True if read-only now."""
    p = Path(path)
    try:
        mode = p.stat().st_mode
        os.chmod(p, mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
    except OSError:
        pass
    return not os.access(p, os.W_OK)


def verify_source_lock(lock: dict, path: str | Path) -> None:
    """Rebind by bytes, not names (Addendum 24 D1): STOP if bytes differ."""
    actual = sha256_file(path)
    if actual != lock["sha256"]:
        raise Blocked("SOURCE_HASH_MISMATCH", f"{path} sha {actual[:12]} != locked {lock['sha256'][:12]}",
                      expected=lock["sha256"], actual=actual)
