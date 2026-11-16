"""R3-C07 — targeted visual navigation over the immutable per-frame index (no mass re-decoding).

`inspect_range(...)` resolves a native-PTS interval to exact presentation indices (VFR-safe, from the index, never an assumed fps),
returns NATIVE frames (no resampling) with a receipt per frame — film SHA, index, pts, raw-frame SHA (the index identity) and PNG SHA —
and optionally a CONTACT SHEET that is labelled navigation-only (a downscaled mosaic is never evidence). Every returned frame is
re-checked against the index identity; a mismatch is SOURCE_IDENTITY_CHANGED, so a witness built on it can be invalidated.

`search_events(...)` queries what the investigation already recorded — witnesses, per-frame inspections, the audiovisual event index
(transcript words / cues), phenomena and audits — by text, actor, art state, event kind, time and scene, returning PTS-anchored hits that
point back to exact frames for native retrieval.
"""
from __future__ import annotations

import io
from pathlib import Path

from ..util import Blocked, sha256_bytes

GRANULARITIES = ("every_frame", "every_nth", "scene_boundaries")


def frames_in_pts_range(index: list[dict], start_pts: float, end_pts: float) -> list[int]:
    if end_pts < start_pts:
        raise Blocked("BAD_PTS_RANGE", f"{start_pts} > {end_pts}")
    return [r["presentation_index"] if "presentation_index" in r else i for i, r in enumerate(index)
            if start_pts - 1e-9 <= float(r["pts_time"]) <= end_pts + 1e-9]


def _frame(cache, index: list[dict], k: int):
    """A FrameCache (.frame) or a PacketRunner-style loader callable(rec) -> {png, png_sha, raw_sha, w, h}."""
    if hasattr(cache, "frame"):
        return cache.frame(k)
    from .frames import RetrievedFrame
    d, r = cache(index[k]), index[k]
    return RetrievedFrame(r["film_sha256"], k, r["pts"], r["pts_time"], d["w"], d["h"], d["raw_sha"], True, d["png"], d["png_sha"],
                          float(d.get("scale", 1.0)), float(d.get("scale", 1.0)) == 1.0)


def inspect_range(*, film_sha: str, index: list[dict], cache, start_pts: float, end_pts: float, purpose: str,
                  granularity: str = "every_frame", nth: int = 1, survey: dict | None = None, contact_sheet_to: str | Path | None = None,
                  write_frames_to: str | Path | None = None) -> dict:
    if granularity not in GRANULARITIES:
        raise Blocked("UNKNOWN_GRANULARITY", granularity)
    if not purpose or len(purpose.split()) < 3:
        raise Blocked("INSPECTION_PURPOSE_REQUIRED", "say what this range is inspected for (it is recorded with the receipts)")
    ks = frames_in_pts_range(index, start_pts, end_pts)
    if not ks:
        raise Blocked("NO_FRAMES_IN_RANGE", f"{start_pts}..{end_pts}")
    if granularity == "every_nth":
        ks = ks[:: max(1, int(nth))] + ([ks[-1]] if (len(ks) - 1) % max(1, int(nth)) else [])
    elif granularity == "scene_boundaries":
        cuts = {int(s["start_frame_index"]) for s in (survey or {}).get("shots", [])}
        ks = sorted({ks[0], ks[-1]} | {k for k in ks if k in cuts or k - 1 in cuts})
    receipts, pngs = [], []
    out_dir = Path(write_frames_to) if write_frames_to else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
    for k in ks:
        fr = _frame(cache, index, k)
        rec = index[k]
        if fr.raw_sha256 != rec["frame_content_sha256"]:
            raise Blocked("SOURCE_IDENTITY_CHANGED", f"frame {k}: decoded raw sha differs from the index identity")
        if not fr.native or fr.scale_factor != 1.0:
            raise Blocked("NOT_NATIVE_FRAME", str(k))
        r = {"film_sha256": film_sha, "frame_index": k, "frame_id": f"{film_sha[:16]}:{k}", "pts": rec["pts"], "pts_time": rec["pts_time"],
             "raw_frame_sha256": fr.raw_sha256, "png_sha256": fr.png_sha256, "width": fr.width, "height": fr.height, "native": True}
        if out_dir:
            p = out_dir / f"{film_sha[:12]}_{k:06d}_{rec['pts_time']:.6f}.png"
            p.write_bytes(fr.png_bytes)
            if sha256_bytes(p.read_bytes()) != fr.png_sha256:
                raise Blocked("FRAME_WRITE_MISMATCH", str(p))
            r["path"] = str(p)
        receipts.append(r)
        pngs.append(fr.png_bytes)
    sheet = None
    if contact_sheet_to:
        sheet = _contact_sheet(pngs, [r["frame_id"] for r in receipts], Path(contact_sheet_to))
    return {"film_sha256": film_sha, "purpose": purpose, "granularity": granularity, "start_pts": start_pts, "end_pts": end_pts,
            "frames": receipts, "contact_sheet": sheet}


def _contact_sheet(pngs: list[bytes], labels: list[str], out: Path, cols: int = 6, thumb_w: int = 256) -> dict:
    from PIL import Image, ImageDraw
    ims = [Image.open(io.BytesIO(b)).convert("RGB") for b in pngs]
    th = int(ims[0].height * thumb_w / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows * (th + 14)), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    for i, (im, lab) in enumerate(zip(ims, labels)):
        x, y = (i % cols) * thumb_w, (i // cols) * (th + 14)
        sheet.paste(im.resize((thumb_w, th)), (x, y + 14))
        d.text((x + 2, y + 1), lab, fill=(255, 255, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return {"path": str(out), "sha256": sha256_bytes(out.read_bytes()), "use": "NAVIGATION_ONLY — downscaled mosaic, never evidence"}


def search_events(st, *, text: str | None = None, actor: str | None = None, art_state: str | None = None, event_kind: str | None = None,
                  time: tuple[float, float] | None = None, scene: str | None = None, film_sha: str | None = None) -> list[dict]:
    """PTS-anchored hits across the recorded evidence. Each hit names its exact frame(s) so the caller can inspect_range it natively."""
    t = (text or "").lower()
    hits: list[dict] = []

    def keep(h):
        if film_sha and h.get("film_sha256") and h["film_sha256"] != film_sha:
            return False
        if scene and h.get("sequence_id") and h["sequence_id"] != scene:
            return False
        if time and h.get("pts_time") is not None and not (time[0] - 1e-6 <= float(h["pts_time"]) <= time[1] + 1e-6):
            return False
        if time and h.get("pts_time") is None:
            return False
        blob = " ".join(str(v) for v in h.values()).lower()
        if t and t not in blob:
            return False
        if actor and actor.lower() not in blob:
            return False
        if art_state and art_state.lower() not in blob:
            return False
        if event_kind and event_kind.lower() not in blob:
            return False
        return True
    for w in st.list("Witness"):
        hits.append({"source": "Witness", "id": w["witness_id"], "film_sha256": w.get("film_sha256"), "sequence_id": w.get("sequence_id"),
                     "frame_index": w.get("frame_start"), "pts_time": w.get("pts_time"), "kind": w.get("evidence_kind"),
                     "text": w.get("visible_relation"), "dimensions": w.get("dimensions")})
    for e in st.list("AudioVisualEvent"):
        hits.append({"source": "AudioVisualEventIndex", "id": e["event_id"], "film_sha256": e.get("film_sha256"), "sequence_id": e.get("sequence_id"),
                     "frame_index": e.get("frame_index"), "pts_time": e.get("pts_time"), "kind": e.get("kind"), "text": e.get("text"),
                     "status": e.get("status")})
    for p in st.list("VisualPhenomenon"):
        hits.append({"source": "VisualPhenomenon", "id": p["phenomenon_id"], "film_sha256": p.get("film_sha256"), "sequence_id": p.get("sequence_id"),
                     "frame_index": p.get("frame_index"), "pts_time": None, "kind": "PHENOMENON", "text": p.get("phenomenon")})
    for f in st.list("FrameInspection"):
        hits.append({"source": "FrameInspection", "id": f"{f['pass_id']}:{f['frame_id']}", "film_sha256": f.get("film_sha256"),
                     "sequence_id": None, "frame_index": f.get("frame_index"), "pts_time": f.get("pts_time"), "kind": f.get("status"),
                     "text": " ".join(g["gap"] for g in f.get("gaps") or [])})
    return sorted((h for h in hits if keep(h)), key=lambda h: (h.get("pts_time") is None, h.get("pts_time") or 0, str(h["id"])))
