"""R3-C02 — ONE shot coordinate space, shared by every producer and the renderer.

The directed shot plan is authored in plan units (`plan_width` × `plan_height`, origin top-left, actor anchor top-left of its box).
Everything the renderer receives is converted HERE to output pixels; the Remotion scene graph never rescales (it asserts
`units == "px"`). x/left/width/camera-x/world-x scale by sx; y/top/height/camera-y/world-y scale by sy. A plan whose aspect ratio
differs from the render must say so (`aspect_policy: "INDEPENDENT_AXES"`) or it is refused — never silently stretched or cropped.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from ..util import Blocked

X_PROPS = ("x",)
Y_PROPS = ("y",)
UNITLESS_PROPS = ("rotation", "scale", "opacity", "brightness")
ANCHOR = "top_left"


@dataclass(frozen=True)
class ShotCoordinateSpace:
    plan_width: float
    plan_height: float
    out_width: int
    out_height: int
    sx: float
    sy: float
    aspect_policy: str
    anchor: str = ANCHOR
    input_units: str = "plan_px"
    output_units: str = "px"

    @staticmethod
    def from_shot_plan(sp: dict, out_width: int, out_height: int) -> "ShotCoordinateSpace":
        pw, ph = sp.get("plan_width"), sp.get("plan_height")
        if not isinstance(pw, (int, float)) or not isinstance(ph, (int, float)) or pw <= 0 or ph <= 0:
            raise Blocked("COORDINATE_SPACE_UNDECLARED", "shot_plan needs numeric plan_width AND plan_height (no implied axis)")
        sx, sy = out_width / float(pw), out_height / float(ph)
        policy = sp.get("aspect_policy", "REJECT_MISMATCH")
        if policy not in ("REJECT_MISMATCH", "INDEPENDENT_AXES"):
            raise Blocked("COORDINATE_ASPECT_POLICY_UNKNOWN", str(policy))
        if abs(sx - sy) > 1e-3 * max(sx, sy) and policy == "REJECT_MISMATCH":
            raise Blocked("ASPECT_RATIO_MISMATCH", f"plan {pw}x{ph} vs render {out_width}x{out_height} (sx={sx:.4f}, sy={sy:.4f}); "
                                                  "declare aspect_policy INDEPENDENT_AXES to scale each axis independently")
        return ShotCoordinateSpace(float(pw), float(ph), int(out_width), int(out_height), sx, sy, policy)

    # ---- the single transform -----------------------------------------------------------------------------------
    def x(self, v: float) -> float:
        return round(float(v) * self.sx, 6)

    def y(self, v: float) -> float:
        return round(float(v) * self.sy, 6)

    def w(self, v: float) -> float:
        return round(float(v) * self.sx, 6)

    def h(self, v: float) -> float:
        return round(float(v) * self.sy, 6)

    def key(self, k: dict) -> dict:
        out = {}
        for p, v in k.items():
            if p in X_PROPS:
                out[p] = self.x(v)
            elif p in Y_PROPS:
                out[p] = self.y(v)
            elif p in ("frame", "easing") or p in UNITLESS_PROPS:
                out[p] = v
            else:
                raise Blocked("KEYFRAME_PROPERTY_UNKNOWN", f"{p} (no declared unit)")
        return out

    def box(self, a: dict) -> dict:
        return {"x": self.x(a["x"]), "y": self.y(a["y"]), "w": self.w(a["w"]), "h": self.h(a["h"])}

    def to_dict(self) -> dict:
        return asdict(self)


def complete_keys(keys: list[dict], base: dict, props: tuple) -> list[dict]:
    """Every keyframe carries every positional prop (a key without y keeps the PREVIOUS y explicitly) so the renderer never falls
    back to an unscaled layer value."""
    out, cur = [], {p: base[p] for p in props if p in base}
    for k in sorted(keys, key=lambda k: int(k["frame"])):
        cur = {**cur, **{p: k[p] for p in props if p in k}}
        out.append({"frame": int(k["frame"]), **cur, **{p: v for p, v in k.items() if p not in props and p != "frame"}})
    return out


def check_on_canvas(space: ShotCoordinateSpace, box: dict, keys: list[dict], who: str) -> None:
    """Every transformed key must leave the actor's box at least partly inside the canvas (physical bounds)."""
    for k in keys:
        x, y = k.get("x", box["x"]), k.get("y", box["y"])
        s = float(k.get("scale", 1.0))
        if x + box["w"] * s <= 0 or y + box["h"] * s <= 0 or x >= space.out_width or y >= space.out_height:
            raise Blocked("ACTOR_OUTSIDE_CANVAS", f"{who} at frame {k['frame']}: ({x:.1f},{y:.1f}) {box['w']:.1f}x{box['h']:.1f} "
                                                  f"outside {space.out_width}x{space.out_height}")
