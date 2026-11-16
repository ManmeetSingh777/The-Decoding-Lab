"""Primary renderer: Remotion + FFmpeg (01 §8/§14, 17 §4–§6, A07, B34, C25/C26).

`render_video` refuses unless GateKeeper.authorize_render passes. A diagnostic render is
allowed only under the explicit label DIAGNOSTIC_NOT_APPROVED and is never a milestone.
Motion evidence checks that something moves independently of the camera (no pan-only proof).
"""
from __future__ import annotations

import io
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from ..util import Blocked, atomic_write_json, digest, now_iso, sha256_file
from ..reference.probe import require_tool, ffprobe_json

REMOTION_DIR = Path(__file__).resolve().parents[2] / "render" / "remotion"


def validate_scene_graph(scene: dict) -> list[str]:
    p = []
    ids = []

    def walk(ls):
        for l in ls:
            ids.append(l["id"])
            walk(l.get("children", []))
    walk(scene.get("layers", []))
    if len(ids) != len(set(ids)):
        p.append("DUPLICATE_LAYER_ID")
    for k in ("width", "height", "fps", "durationInFrames", "camera", "layers"):
        if k not in scene:
            p.append(f"MISSING:{k}")
    for ev in scene.get("events", []):
        if ev.get("kind") == "contact":
            hand, prop = ev.get("hand_layer"), ev.get("prop_layer")
            if hand not in ids or prop not in ids:
                p.append(f"CONTACT_LAYER_MISSING:{ev.get('id')}")
            if ev.get("hand_interval") != ev.get("prop_interval"):
                p.append(f"HAND_MOVES_WITHOUT_PROP:{ev.get('id')}")
    movers = [l for l in scene.get("layers", []) if l.get("keyframes") and len(l["keyframes"]) > 1 or l.get("states")]
    cam_moves = len(scene.get("camera", {}).get("keyframes", [])) > 1
    if not movers and cam_moves:
        p.append("CAMERA_ONLY_MOTION")
    return p


def _decode_frames(mp4: Path, every: int = 1, w: int = 160) -> list[np.ndarray]:
    ff = require_tool("ffmpeg")
    out = subprocess.run([ff, "-v", "error", "-i", str(mp4), "-vf", f"select='not(mod(n\\,{every}))',scale={w}:-2",
                          "-fps_mode", "passthrough", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    data, frames = out.stdout, []
    sig = b"\x89PNG\r\n\x1a\n"
    parts = data.split(sig)
    for part in parts[1:]:
        frames.append(np.asarray(Image.open(io.BytesIO(sig + part)).convert("L")).astype(np.float32))
    return frames


def _block_motion(a: np.ndarray, b: np.ndarray, *, grid=(4, 6), m: int = 4, tex_min: float = 4.0, noise: float = 2.5) -> dict:
    """Per-block best translation between two frames. Textureless blocks are ignored (motion there is
    visually undefined). Returns whether the pair is explained by ONE common translation."""
    H, W = a.shape
    gy, gx = grid
    bh, bw = (H - 2 * m) // gy, (W - 2 * m) // gx
    shifts, unexplained, changed = [], 0, 0
    for i in range(gy):
        for j in range(gx):
            y0, x0 = m + i * bh, m + j * bw
            A = a[y0:y0 + bh, x0:x0 + bw]
            zero = float(np.abs(A - b[y0:y0 + bh, x0:x0 + bw]).mean())
            if zero > noise:
                changed += 1
            if A.std() < tex_min:
                continue
            best = (zero, (0, 0))
            for dy in range(-m, m + 1):
                for dx in range(-m, m + 1):
                    e = float(np.abs(A - b[y0 + dy:y0 + dy + bh, x0 + dx:x0 + dx + bw]).mean())
                    if e < best[0] - 1e-6:
                        best = (e, (dx, dy))
            if zero > noise and best[0] > max(noise, 0.5 * zero):
                unexplained += 1           # content changed in a way no translation explains (redraw/rotation/swap)
            shifts.append(best[1])
    distinct = {s for s in shifts}
    spread = max((abs(p[0] - q[0]) + abs(p[1] - q[1]) for p in distinct for q in distinct), default=0)
    return {"changed_blocks": changed, "informative_blocks": len(shifts), "unexplained_blocks": unexplained,
            "shift_spread": spread, "common_shift": next(iter(distinct)) if len(distinct) == 1 else None}


def motion_evidence(mp4: str | Path) -> dict:
    """Block-wise motion analysis over consecutive decoded frames.

    INDEPENDENT_MOTION_PRESENT: some blocks move differently from others, or change in a way no
    translation explains (drawing-state swap, rotation). CAMERA_PAN_ONLY: every textured block shares
    one translation. STATIC: nothing changes. Limitation (recorded): motion over textureless regions
    is visually indistinguishable from a pan and is not counted either way.
    """
    fr = _decode_frames(Path(mp4))
    if len(fr) < 2:
        return {"ok": False, "verdict": "TOO_FEW_FRAMES"}
    pairs = [_block_motion(a, b) for a, b in zip(fr, fr[1:])]
    indep = [k for k, p in enumerate(pairs) if p["changed_blocks"] and (p["unexplained_blocks"] or p["shift_spread"] > 1)]
    changed = [k for k, p in enumerate(pairs) if p["changed_blocks"]]
    verdict = "INDEPENDENT_MOTION_PRESENT" if indep else ("CAMERA_PAN_ONLY" if changed else "STATIC")
    return {"ok": verdict == "INDEPENDENT_MOTION_PRESENT", "verdict": verdict, "frames_checked": len(fr),
            "independent_pairs": len(indep), "changed_pairs": len(changed), "sample": pairs[:3],
            "limitation": "textureless regions carry no motion evidence"}


def ffprobe_verify(mp4: str | Path, expect: dict) -> dict:
    info = ffprobe_json(mp4)
    v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    got = {"width": int(v["width"]), "height": int(v["height"]), "fps": v["r_frame_rate"], "nb_frames": int(v.get("nb_frames", 0)),
           "codec": v["codec_name"]}
    probs = []
    if got["width"] != expect["width"] or got["height"] != expect["height"]:
        probs.append("DIMENSION_MISMATCH")
    if got["nb_frames"] != expect["durationInFrames"]:
        probs.append("FRAME_COUNT_MISMATCH")
    if got["fps"] not in (f"{expect['fps']}/1", str(expect["fps"])):
        probs.append("FPS_MISMATCH")
    return {"ok": not probs, "problems": probs, **got}


def render_video(scene: dict, assets: dict, out_mp4: str | Path, *, gate=None, run_id: str | None = None,
                 diagnostic_label: str | None = None, transition_on_success: bool = True) -> dict:
    """assets: {public_relative_src: local_path}. Integrated renders need gate.authorize_render."""
    probs = validate_scene_graph(scene)
    if probs:
        raise Blocked("SCENE_GRAPH_INVALID", ";".join(probs))
    if diagnostic_label is None:
        if gate is None or run_id is None:
            raise Blocked("RENDER_REFUSED_NO_GATE")
        gate.authorize_render(run_id, scene_asset_paths=sorted(assets.values()))
        label = "INTEGRATED_RENDER_AFTER_APPROVALS"
    else:
        if diagnostic_label != "DIAGNOSTIC_NOT_APPROVED":
            raise Blocked("BAD_DIAGNOSTIC_LABEL")
        label = diagnostic_label
    if not (REMOTION_DIR / "node_modules" / "remotion").exists():
        raise Blocked("RENDER_ENGINE_NOT_INSTALLED", "run npm install in render/remotion")
    job = digest({"scene": scene, "assets": {k: sha256_file(v) for k, v in assets.items()}})[:16]
    pub = REMOTION_DIR / "public" / f"job_{job}"
    pub.mkdir(parents=True, exist_ok=True)
    remap = {}
    for src, local in assets.items():
        dst = pub / Path(src).name
        shutil.copyfile(local, dst)
        remap[src] = f"job_{job}/{Path(src).name}"

    def rw(ls):
        for l in ls:
            l["src"] = remap.get(l["src"], l["src"])
            for st in l.get("states", []):
                st["src"] = remap.get(st["src"], st["src"])
            rw(l.get("children", []))
    sc = json.loads(json.dumps(scene))
    rw(sc["layers"])
    scene_file = pub / "scene.json"
    atomic_write_json(scene_file, sc)
    node = require_tool("node")
    out_mp4 = Path(out_mp4)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([node, "render.mjs", str(scene_file), str(out_mp4.resolve())], cwd=str(REMOTION_DIR),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    if r.returncode != 0:
        raise Blocked("RENDER_ENGINE", r.stderr[-600:])
    verify = ffprobe_verify(out_mp4, scene)
    motion = motion_evidence(out_mp4)
    # An mp4 merely existing is not a successful render. Keep diagnostic
    # transport runs distinguishable from an approved integrated film.
    if not verify.get("ok"):
        if gate and run_id and diagnostic_label is None:
            gate.transition(run_id, "ASSETS_APPROVED", reason="technical render failed")
        raise Blocked("TECHNICAL_RENDER_FAILED", str(verify.get("problems", [])))
    if diagnostic_label is None:
        expectation = (scene.get("motion_contract") or {}).get("expected_independent_motion")
        if expectation is None:
            raise Blocked("MOTION_CONTRACT_MISSING", "Integrated scene needs an independently reviewed motion expectation")
        if expectation is True and not motion.get("ok"):
            if gate and run_id:
                gate.transition(run_id, "ASSETS_APPROVED", reason="technical motion failed")
            raise Blocked("TECHNICAL_MOTION_FAILED", str(motion.get("verdict")))
        if expectation is False and not (scene.get("motion_contract") or {}).get("reviewed_static_intent_id"):
            raise Blocked("UNAPPROVED_STATIC_FILM", "No source-grounded intentional stillness evidence")
    rep = {"label": label, "mp4": str(out_mp4), "mp4_sha256": sha256_file(out_mp4), "ffprobe": verify, "motion": motion,
           "scene_sha": digest(scene), "rendered_at": now_iso(),
           "quality_claim": "TECHNICAL_RENDER_ONLY — not artistic motion quality"}
    if gate and run_id and diagnostic_label is None and transition_on_success:
        gate.transition(run_id, "AWAITING_VIDEO_REVIEW", reason="render complete")
    return rep
