"""R3-C05 — the PART-LEVEL character route (components, pivots, limits, contacts) next to whole-state redraws.

Whole-image state substitution stays the route for motion that the source achieves with REDRAWN drawings. Where an actor's motion needs
independent parts (hand gripping a moving prop, head turn over a fixed torso, planted foot during a weight shift, arm overlapping torso),
the route is a registered RIG:
  * topology: parts with parent, pivot (in the parent's frame), front/back order, rotation limits, allowed state transitions;
  * contacts: an anchor on a part that must coincide with a world/prop anchor for an interval; planted feet that must not slide;
  * assets: every part needs an APPROVED, SOURCE-DERIVED component image (and clean plate / mask where the parts overlap). Without them
    the route is BLOCKED:PART_RIG_ASSETS_UNAVAILABLE — generic tube limbs or auto-generated parts are never substituted.
`compile_rig_program` verifies a pose program with forward kinematics BEFORE anything is rendered and returns the per-part render layers.
Status of this route in the current build: CONTRACT + KINEMATIC VERIFIER; no segmentation/inpainting capability exists to produce parts.
"""
from __future__ import annotations

import math

from ..util import Blocked, digest

PART_FIELDS = ("id", "parent", "pivot", "rest_angle", "min_angle", "max_angle", "z")


def _fk(parts: dict, angles: dict, root_xy: tuple[float, float]) -> dict:
    """World transform (x, y, angle) of every part's pivot; parent-first."""
    out: dict = {}

    def go(pid):
        if pid in out:
            return out[pid]
        p = parts[pid]
        a = float(angles.get(pid, p["rest_angle"]))
        if p["parent"] is None:
            out[pid] = (root_xy[0] + p["pivot"][0], root_xy[1] + p["pivot"][1], a)
        else:
            px, py, pa = go(p["parent"])
            r = math.radians(pa)
            ox, oy = p["pivot"]
            out[pid] = (px + ox * math.cos(r) - oy * math.sin(r), py + ox * math.sin(r) + oy * math.cos(r), pa + a)
        return out[pid]
    for pid in parts:
        go(pid)
    return out


def anchor_world(parts: dict, angles: dict, root_xy, part: str, local: tuple[float, float]) -> tuple[float, float]:
    x, y, a = _fk(parts, angles, root_xy)[part]
    r = math.radians(a)
    return (x + local[0] * math.cos(r) - local[1] * math.sin(r), y + local[0] * math.sin(r) + local[1] * math.cos(r))


def validate_rig(rig: dict) -> dict:
    parts = {p["id"]: p for p in rig.get("parts", [])}
    if not parts:
        raise Blocked("RIG_HAS_NO_PARTS", rig.get("actor_id", "?"))
    for p in parts.values():
        miss = [f for f in PART_FIELDS if f not in p]
        if miss:
            raise Blocked("RIG_PART_INCOMPLETE", f"{p.get('id')}: {miss}")
        if p["parent"] is not None and p["parent"] not in parts:
            raise Blocked("RIG_PARENT_UNKNOWN", p["id"])
        if not p["min_angle"] <= p["rest_angle"] <= p["max_angle"]:
            raise Blocked("RIG_REST_OUTSIDE_LIMITS", p["id"])
    roots = [p for p in parts.values() if p["parent"] is None]
    if len(roots) != 1:
        raise Blocked("RIG_NEEDS_ONE_ROOT", str([p["id"] for p in roots]))
    if not rig.get("source_derivation") or not rig["source_derivation"].get("dossier_id"):
        raise Blocked("RIG_NOT_SOURCE_DERIVED", "topology/limits must come from a validated character dossier, not a generic skeleton")
    return parts


def compile_rig_program(rig: dict, poses: list[dict], *, contacts: list[dict] | None = None, planted: list[dict] | None = None,
                        assets: dict | None = None, tol_px: float = 0.75) -> dict:
    """poses = [{"frame", "root": [x, y], "angles": {part: deg}}]; contacts = [{"part", "local": [x, y], "prop_anchor": {frame: [x, y]},
    "frames": [a, b]}]; planted = [{"part", "local", "frames": [a, b]}]. Verifies limits, contacts and planted feet on EVERY pose,
    then requires approved source-derived part assets before returning render layers."""
    parts = validate_rig(rig)
    poses = sorted(poses, key=lambda p: int(p["frame"]))
    for p in poses:
        for pid, a in p["angles"].items():
            if pid not in parts:
                raise Blocked("POSE_PART_UNKNOWN", pid)
            if not parts[pid]["min_angle"] <= a <= parts[pid]["max_angle"]:
                raise Blocked("POSE_EXCEEDS_SOURCE_LIMIT", f"{pid}={a} outside [{parts[pid]['min_angle']},{parts[pid]['max_angle']}] at {p['frame']}")
    for prev, cur in zip(poses, poses[1:]):
        t = (prev.get("state"), cur.get("state"))
        if t[0] != t[1] and t not in {tuple(x) for x in rig.get("allowed_transitions", [])}:
            raise Blocked("STATE_TRANSITION_NOT_ALLOWED", f"{t} at frame {cur['frame']}")
    checks = []
    for c in contacts or []:
        for p in poses:
            if c["frames"][0] <= p["frame"] <= c["frames"][1]:
                hx, hy = anchor_world(parts, p["angles"], tuple(p["root"]), c["part"], tuple(c["local"]))
                px, py = c["prop_anchor"][str(p["frame"])] if str(p["frame"]) in c["prop_anchor"] else c["prop_anchor"][p["frame"]]
                err = math.hypot(hx - px, hy - py)
                checks.append({"kind": "CONTACT", "part": c["part"], "frame": p["frame"], "error_px": round(err, 3)})
                if err > tol_px:
                    raise Blocked("CONTACT_BROKEN", f"{c['part']} is {err:.2f}px from its prop anchor at frame {p['frame']}")
    for f in planted or []:
        ref = None
        for p in poses:
            if f["frames"][0] <= p["frame"] <= f["frames"][1]:
                w = anchor_world(parts, p["angles"], tuple(p["root"]), f["part"], tuple(f["local"]))
                ref = ref or w
                err = math.hypot(w[0] - ref[0], w[1] - ref[1])
                checks.append({"kind": "PLANTED", "part": f["part"], "frame": p["frame"], "slide_px": round(err, 3)})
                if err > tol_px:
                    raise Blocked("PLANTED_FOOT_SLIDES", f"{f['part']} slides {err:.2f}px at frame {p['frame']}")
    missing = [pid for pid in parts if not (assets or {}).get(pid, {}).get("approved") or
               (assets or {}).get(pid, {}).get("origin") != "SOURCE_DERIVED_COMPONENT"]
    if missing:
        raise Blocked("PART_RIG_ASSETS_UNAVAILABLE", f"no approved source-derived component image for {missing} (no generic/auto parts)")
    layers = []
    for p in poses:
        fk = _fk(parts, p["angles"], tuple(p["root"]))
        layers.append({"frame": p["frame"], "parts": [{"id": pid, "x": round(fk[pid][0], 3), "y": round(fk[pid][1], 3), "rotation": round(fk[pid][2], 3),
                                                        "z": parts[pid]["z"], "src_sha": assets[pid]["sha256"]}
                                                       for pid in sorted(parts, key=lambda q: parts[q]["z"])]})
    prog = {"actor_id": rig.get("actor_id"), "route": "PART_LEVEL_RIG", "checks": checks, "frames": layers, "front_back_order":
            [pid for pid in sorted(parts, key=lambda q: parts[q]["z"])]}
    prog["program_sha"] = digest(prog)
    return prog
