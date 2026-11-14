"""Raster asset family: masks, alpha, layers, anchors, coordinate mapping, recomposition (spec 17, A40/A41, B25/B26, C23/C24).

All checks operate on actual decoded pixels. Fixture rasters prove wiring only.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, asdict, field
from pathlib import Path

import numpy as np
from PIL import Image

from ..util import Blocked, sha256_bytes
from .raster import decode_raster, load_rgba


def coordinate_map(gen_w: int, gen_h: int, scene_w: int = 1920, scene_h: int = 1080, *, policy: str = "uniform") -> dict:
    """Uniform scale (never stretch). 1536x864→1920x1080 = 1.25; 1920x1088 → explicit crop of 8 rows."""
    sx, sy = scene_w / gen_w, scene_h / gen_h
    if abs(sx - sy) < 1e-9:
        return {"scale": sx, "crop": None, "offset": [0, 0], "stretch": False}
    if policy == "uniform":
        s = max(sx, sy)  # cover, then crop explicitly
        cw, ch = gen_w * s, gen_h * s
        return {"scale": s, "crop": {"x": (cw - scene_w) / 2, "y": (ch - scene_h) / 2, "w": scene_w, "h": scene_h},
                "offset": [-(cw - scene_w) / 2, -(ch - scene_h) / 2], "stretch": False}
    raise Blocked("NON_UNIFORM_STRETCH_FORBIDDEN", f"{gen_w}x{gen_h}→{scene_w}x{scene_h}")


@dataclass
class ArtLayer:
    layer_id: str
    owner: str                    # character/prop id
    body_part: str
    side: str                     # left | right | center | n/a  (character's own side)
    image_path: str
    image_sha256: str
    mode: str                     # RGBA | OPAQUE
    mask_path: str | None
    mask_sha256: str | None
    local_origin: list            # [x, y] in owner-local pixels
    pivot: list                   # [x, y] in layer pixels
    natural_size: list            # [w, h]
    z: int
    parent: str | None
    parent_scale_applied: bool
    occluded_fill: str | None     # clean plate / hidden surface asset path when the part moves
    moves: bool = False
    motion_range_px: list = field(default_factory=lambda: [0, 0])
    source_composite_sha256: str | None = None
    state_applicability: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def verify_mask(mask_bytes: bytes, parent_w: int, parent_h: int) -> dict:
    im = Image.open(io.BytesIO(mask_bytes))
    if (im.width, im.height) != (parent_w, parent_h):
        raise Blocked("MASK_WRONG_SIZE", f"{im.width}x{im.height} != parent {parent_w}x{parent_h}")
    m = np.asarray(im.convert("L"))
    return {"coverage": float((m > 127).mean()), "binary_fraction": float(((m < 8) | (m > 247)).mean())}


def recompose(layers: list[dict], canvas: tuple[int, int], background: np.ndarray | None = None) -> np.ndarray:
    W, H = canvas
    out = np.zeros((H, W, 4), np.float32) if background is None else background.copy()
    for L in sorted(layers, key=lambda l: l["z"]):
        img = load_rgba(Path(L["image_path"]).read_bytes())
        if L["mode"] != "RGBA":
            img[:, :, 3] = 1.0
        h, w = img.shape[:2]
        x0, y0 = int(round(L["local_origin"][0])), int(round(L["local_origin"][1]))
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
        if xa >= xb or ya >= yb:
            continue
        src = img[ya - y0:yb - y0, xa - x0:xb - x0]
        a = src[:, :, 3:4]
        dst = out[ya:yb, xa:xb]
        out[ya:yb, xa:xb, :3] = src[:, :, :3] * a + dst[:, :, :3] * (1 - a)
        out[ya:yb, xa:xb, 3:4] = a + dst[:, :, 3:4] * (1 - a)
    return out


def recomposition_report(recomposed: np.ndarray, canonical: np.ndarray, *, tol: float = 0.04) -> dict:
    if recomposed.shape != canonical.shape:
        raise Blocked("RECOMPOSE_CANVAS_MISMATCH", f"{recomposed.shape} vs {canonical.shape}")
    diff = np.abs(recomposed[:, :, :3] - canonical[:, :, :3]).mean(axis=2)
    canon_opaque = canonical[:, :, 3] > 0.5
    holes = canon_opaque & (recomposed[:, :, 3] < 0.5)
    halo = (~canon_opaque) & (recomposed[:, :, 3] > 0.5)
    return {"mean_abs_diff": float(diff.mean()), "max_abs_diff": float(diff.max()), "pct_pixels_over_tol": float((diff > tol).mean()),
            "hole_pixels": int(holes.sum()), "halo_pixels": int(halo.sum()),
            "ok": float((diff > tol).mean()) < 0.002 and int(holes.sum()) == 0 and int(halo.sum()) == 0}


def verify_pack(pack: dict) -> dict:
    """Engineering checks on a CharacterPack/asset family (spec 17 §7 injected failures)."""
    problems = []
    layers = pack["layers"]
    ids = [l["layer_id"] for l in layers]
    if len(set(ids)) != len(ids):
        problems.append("DUPLICATE_LAYER_ID")
    canon = pack["canonical"]
    cw, ch = canon["width"], canon["height"]
    for L in layers:
        p = Path(L["image_path"])
        if not p.exists():
            problems.append(f"LAYER_FILE_MISSING:{L['layer_id']}")
            continue
        data = p.read_bytes()
        if sha256_bytes(data) != L["image_sha256"]:
            problems.append(f"LAYER_BYTES_CHANGED:{L['layer_id']}")
        ra = decode_raster(data, asset_id=L["layer_id"], owner=L["owner"], skill_version=pack.get("skill_hash", "?"))
        if L["mode"] == "RGBA" and not ra.has_nonopaque_alpha:
            problems.append(f"OPAQUE_PNG_CLAIMED_TRANSPARENT:{L['layer_id']}")
        if [ra.width, ra.height] != list(L["natural_size"]):
            problems.append(f"LAYER_SIZE_MISMATCH:{L['layer_id']}")
        if L.get("mask_path"):
            try:
                verify_mask(Path(L["mask_path"]).read_bytes(), ra.width, ra.height)
            except Blocked as b:
                problems.append(f"{b.code}:{L['layer_id']}")
        if L.get("parent") and L.get("parent_scale_applied") and pack.get("parent_scales", {}).get(L["parent"], 1.0) != 1.0 \
                and L.get("declared_world_scale") == pack.get("parent_scales", {}).get(L["parent"], 1.0) ** 2:
            problems.append(f"PARENT_SCALE_APPLIED_TWICE:{L['layer_id']}")
        if L.get("moves") and not L.get("occluded_fill"):
            problems.append(f"MOVING_PART_WITHOUT_CLEAN_PLATE:{L['layer_id']}")
        x, y = L["local_origin"]
        if x < 0 or y < 0 or x + L["natural_size"][0] > cw or y + L["natural_size"][1] > ch:
            problems.append(f"LAYER_OUTSIDE_CANONICAL_CANVAS:{L['layer_id']}")
    # left/right swap: in a front view the character's RIGHT arm appears on the viewer's LEFT half.
    cx = cw / 2
    for L in layers:
        if L.get("side") in ("left", "right") and pack.get("view") == "front":
            mid = L["local_origin"][0] + L["natural_size"][0] / 2
            on_viewer_left = mid < cx
            if (L["side"] == "right") != on_viewer_left:
                problems.append(f"LEFT_RIGHT_SWAPPED:{L['layer_id']}")
    # z order rules for contacts: near hand above prop above torso above far arm
    zs = {l["body_part"]: l["z"] for l in layers}
    for c in pack.get("contacts", []):
        order = c.get("required_order", [])
        vals = [zs[o] for o in order if o in zs]
        if vals != sorted(vals):
            problems.append(f"Z_ORDER_VIOLATES_CONTACT:{c['contact_id']}")
        ha, pa = c.get("hand_anchor_world"), c.get("prop_anchor_world")
        if ha and pa and (abs(ha[0] - pa[0]) > c.get("tolerance_px", 4) or abs(ha[1] - pa[1]) > c.get("tolerance_px", 4)):
            problems.append(f"CONTACT_ANCHOR_INCONSISTENT:{c['contact_id']}")
        if not c.get("approved_hand_prop_state"):
            problems.append(f"CONTACT_WITHOUT_WHOLE_HAND_PROP_DRAWING:{c['contact_id']}")
    for st in pack.get("states", []):
        if [st["width"], st["height"]] != [cw, ch] and not st.get("registration"):
            problems.append(f"STATE_CANVAS_MISMATCH:{st['state_id']}")
        if not st.get("identity_reference_sha256") == canon["sha256"]:
            problems.append(f"STATE_NOT_CONDITIONED_ON_CANONICAL:{st['state_id']}")
    # moving parts must not expose holes: shift each moving layer and check background coverage
    if pack.get("check_motion_holes"):
        for L in [l for l in layers if l.get("moves")]:
            if L.get("occluded_fill"):
                fill = load_rgba(Path(L["occluded_fill"]).read_bytes())
                if fill.shape[:2] != (ch, cw) or float((fill[:, :, 3] < 0.5).mean()) > 0.0:
                    problems.append(f"CLEAN_PLATE_HAS_HOLES:{L['layer_id']}")
    return {"ok": not problems, "problems": problems}
