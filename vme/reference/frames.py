"""Exact frame retrieval by presentation index with byte-identity verification (A03, C04).

A retrieved frame is decoded at its true PTS and its raw decoded bytes are hashed and
compared to the index hash. Native crops use real pixel coordinates; resized images are
never labelled native (ADD25-F06).
"""
from __future__ import annotations

import io
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

from PIL import Image

from ..util import Blocked, sha256_bytes
from .probe import require_tool

_PIXBYTES = {"yuv420p": 1.5, "yuvj420p": 1.5, "yuv444p": 3, "rgb24": 3, "nv12": 1.5}


@dataclass
class RetrievedFrame:
    film_sha256: str
    presentation_index: int
    pts: int
    pts_time: float
    width: int
    height: int
    raw_sha256: str
    identity_verified: bool
    png_bytes: bytes
    png_sha256: str
    scale_factor: float = 1.0
    native: bool = True

    def manifest(self) -> dict:
        d = asdict(self)
        d.pop("png_bytes")
        return d


def _decode_raw_at(video: str | Path, pts_time: float, pts: int, pix_fmt: str, w: int, h: int) -> bytes:
    exe = require_tool("ffmpeg")
    seek = max(0.0, pts_time - 2.0)
    cmd = [exe, "-v", "error", "-nostdin", "-copyts", "-ss", f"{seek:.6f}", "-i", str(video), "-map", "0:v:0",
           "-vf", f"select='eq(pts\\,{pts})'", "-fps_mode", "passthrough", "-frames:v", "1",
           "-f", "rawvideo", "-pix_fmt", pix_fmt, "-"]
    out = subprocess.run(cmd, capture_output=True)
    if out.returncode != 0:
        raise Blocked("FRAME_DECODE_FAILED", out.stderr.decode(errors="replace")[:300])
    expected = int(w * h * _PIXBYTES.get(pix_fmt, 1.5))
    if len(out.stdout) != expected:
        raise Blocked("FRAME_NOT_FOUND_AT_PTS", f"got {len(out.stdout)} bytes, expected {expected}", pts=pts)
    return out.stdout


def raw_to_png(raw: bytes, pix_fmt: str, w: int, h: int) -> bytes:
    exe = require_tool("ffmpeg")
    cmd = [exe, "-v", "error", "-nostdin", "-f", "rawvideo", "-pix_fmt", pix_fmt, "-s", f"{w}x{h}", "-i", "-",
           "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"]
    out = subprocess.run(cmd, input=raw, capture_output=True)
    if out.returncode != 0:
        raise Blocked("PNG_CONVERT_FAILED", out.stderr.decode(errors="replace")[:300])
    return out.stdout


def retrieve_frame(video: str | Path, rec: dict, *, pix_fmt: str = "yuv420p") -> RetrievedFrame:
    raw = _decode_raw_at(video, rec["pts_time"], rec["pts"], pix_fmt, rec["frame_width"], rec["frame_height"])
    rsha = sha256_bytes(raw)
    ok = rsha == rec["frame_content_sha256"]
    if not ok:
        raise Blocked("FRAME_IDENTITY_MISMATCH", f"index {rec['presentation_index']} raw sha differs",
                      expected=rec["frame_content_sha256"], actual=rsha)
    png = raw_to_png(raw, pix_fmt, rec["frame_width"], rec["frame_height"])
    return RetrievedFrame(rec["film_sha256"], rec["presentation_index"], rec["pts"], rec["pts_time"],
                          rec["frame_width"], rec["frame_height"], rsha, ok, png, sha256_bytes(png))


@dataclass
class NativeCrop:
    film_sha256: str
    presentation_index: int
    parent_png_sha256: str
    x: int
    y: int
    w: int
    h: int
    crop_png_sha256: str
    native_resolution: bool
    output_width: int
    output_height: int
    png_bytes: bytes

    def manifest(self) -> dict:
        d = asdict(self)
        d.pop("png_bytes")
        return d


def native_crop(frame: RetrievedFrame, x: int, y: int, w: int, h: int) -> NativeCrop:
    if not frame.native or frame.scale_factor != 1.0:
        raise Blocked("NOT_NATIVE_PARENT", "crop parent is a resized image")
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > frame.width or y + h > frame.height:
        raise Blocked("CROP_OUT_OF_BOUNDS", f"{x},{y},{w},{h} on {frame.width}x{frame.height}")
    im = Image.open(io.BytesIO(frame.png_bytes))
    c = im.crop((x, y, x + w, y + h))
    buf = io.BytesIO()
    c.save(buf, format="PNG")
    b = buf.getvalue()
    return NativeCrop(frame.film_sha256, frame.presentation_index, frame.png_sha256, x, y, w, h, sha256_bytes(b),
                      True, c.width, c.height, b)


def verify_native_claim(crop_manifest: dict) -> None:
    """ADD25-F06: a crop whose output size differs from its source region is NOT native."""
    if crop_manifest.get("native_resolution") and (
            crop_manifest["output_width"] != crop_manifest["w"] or crop_manifest["output_height"] != crop_manifest["h"]):
        raise Blocked("FALSE_NATIVE_DETAIL_CLAIM", "resized crop labelled native")


def resized_for_provider(frame: RetrievedFrame, max_side: int) -> RetrievedFrame:
    """Provider-size copy; identity kept, `native=False` and scale recorded (never called native)."""
    im = Image.open(io.BytesIO(frame.png_bytes))
    s = min(1.0, max_side / max(im.width, im.height))
    if s == 1.0:
        return frame
    im2 = im.resize((round(im.width * s), round(im.height * s)), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im2.save(buf, format="PNG")
    b = buf.getvalue()
    return RetrievedFrame(frame.film_sha256, frame.presentation_index, frame.pts, frame.pts_time, im2.width,
                          im2.height, frame.raw_sha256, frame.identity_verified, b, sha256_bytes(b), s, False)


def retrieve_range(video: str | Path, recs: list[dict], *, pix_fmt: str = "yuv420p") -> list[RetrievedFrame]:
    """Decode a contiguous run of presented frames in ONE ffmpeg pass; verify every frame's raw hash."""
    if not recs:
        return []
    exe = require_tool("ffmpeg")
    a, b = recs[0], recs[-1]
    w, h = a["frame_width"], a["frame_height"]
    size = int(w * h * _PIXBYTES.get(pix_fmt, 1.5))
    seek = max(0.0, a["pts_time"] - 2.0)
    cmd = [exe, "-v", "error", "-nostdin", "-copyts", "-ss", f"{seek:.6f}", "-i", str(video), "-map", "0:v:0",
           "-vf", "select='between(pts\\," + str(a["pts"]) + "\\," + str(b["pts"]) + ")'", "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", pix_fmt, "-"]
    out = subprocess.run(cmd, capture_output=True)
    if out.returncode != 0:
        raise Blocked("FRAME_DECODE_FAILED", out.stderr.decode(errors="replace")[:300])
    raws = [out.stdout[i:i + size] for i in range(0, len(out.stdout), size)]
    if len(raws) != len(recs):
        raise Blocked("RANGE_FRAME_COUNT_MISMATCH", f"decoded {len(raws)} expected {len(recs)}")
    res = []
    for rec, raw in zip(recs, raws):
        rsha = sha256_bytes(raw)
        if rsha != rec["frame_content_sha256"]:
            raise Blocked("FRAME_IDENTITY_MISMATCH", f"index {rec['presentation_index']}")
        png = raw_to_png(raw, pix_fmt, w, h)
        res.append(RetrievedFrame(rec["film_sha256"], rec["presentation_index"], rec["pts"], rec["pts_time"], w, h, rsha, True, png,
                                  sha256_bytes(png)))
    return res


class FrameCache:
    """Loader for PacketRunner: decodes whole contiguous chunks on a miss (real path; identity verified per frame)."""

    def __init__(self, video: str | Path, index: list[dict], chunk: int = 16):
        self.video, self.index, self.chunk = video, index, chunk
        self.cache: dict[int, dict] = {}

    def __call__(self, rec: dict) -> dict:
        k = rec["presentation_index"]
        if k not in self.cache:
            lo, hi = k, min(len(self.index) - 1, k + self.chunk - 1)
            for fr in retrieve_range(self.video, self.index[lo:hi + 1]):
                self.cache[fr.presentation_index] = {"png": fr.png_bytes, "png_sha": fr.png_sha256, "raw_sha": fr.raw_sha256,
                                                     "w": fr.width, "h": fr.height, "scale": 1.0}
        return self.cache[k]

    def frame(self, k: int) -> RetrievedFrame:
        d = self(self.index[k])
        r = self.index[k]
        return RetrievedFrame(r["film_sha256"], k, r["pts"], r["pts_time"], d["w"], d["h"], d["raw_sha"], True, d["png"], d["png_sha"])
