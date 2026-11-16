"""Real raster decoding: bytes → verified RasterAsset (spec 17 §3, A41, B25, C18, C23).

PNG/WEBP format never implies transparency: alpha is reported from actual pixels.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, asdict

import numpy as np
from PIL import Image, UnidentifiedImageError

from ..util import Blocked, sha256_bytes


@dataclass
class RasterAsset:
    id: str
    sha256: str
    width: int
    height: int
    pixel_mode: str               # RGB | RGBA | MASK_L | OTHER
    has_alpha_channel: bool
    has_nonopaque_alpha: bool
    transparent_fraction: float
    format: str
    coordinate_space: str
    origin_x: float
    origin_y: float
    owner: str
    skill_version: str
    alpha_convention: str = "straight"
    mask_asset: str | None = None
    source_composite_asset: str | None = None
    path: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def decode_raster(data: bytes, *, asset_id: str, owner: str, skill_version: str, coordinate_space: str = "scene",
                  origin=(0.0, 0.0), expected_size: tuple | None = None) -> RasterAsset:
    if not data:
        raise Blocked("EMPTY_IMAGE_BYTES")
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except (UnidentifiedImageError, OSError, ValueError) as e:
        raise Blocked("INVALID_IMAGE_BYTES", str(e)[:200])
    fmt = (im.format or "?").upper()
    mode = im.mode
    has_alpha = mode in ("RGBA", "LA", "PA") or (mode == "P" and "transparency" in im.info)
    frac = 0.0
    if has_alpha:
        a = np.asarray(im.convert("RGBA"))[:, :, 3]
        frac = float((a < 255).mean())
    pm = {"RGB": "RGB", "RGBA": "RGBA", "L": "MASK_L"}.get(mode, "OTHER")
    if expected_size and (im.width, im.height) != tuple(expected_size):
        raise Blocked("OUTPUT_DIMENSION_MISMATCH", f"{im.width}x{im.height} != {expected_size}")
    return RasterAsset(asset_id, sha256_bytes(data), im.width, im.height, pm, has_alpha, frac > 0.0, round(frac, 6), fmt,
                       coordinate_space, float(origin[0]), float(origin[1]), owner, skill_version)


def require_transparency(asset: RasterAsset | dict) -> None:
    a = asset.to_dict() if isinstance(asset, RasterAsset) else asset
    if not a["has_nonopaque_alpha"]:
        raise Blocked("OPAQUE_ASSET_NOT_TRANSPARENT", f"{a['id']}: {a['format']} {a['pixel_mode']} has no non-opaque alpha pixels")


def load_rgba(data: bytes) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(data)).convert("RGBA")).astype(np.float32) / 255.0


def to_png(arr: np.ndarray) -> bytes:
    a = np.clip(arr * 255.0 + 0.5, 0, 255).astype(np.uint8)
    im = Image.fromarray(a, "RGBA" if a.shape[2] == 4 else "RGB")
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()
