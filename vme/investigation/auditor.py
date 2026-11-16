"""R3-C08 / C07 — the INDEPENDENT inspection auditor.

The observer (P1) never grades itself. Expected phenomena for a selected interval come from parties that did not write the
observations:
  * LOCAL detectors — shot cuts from the local FilmSurvey (SCENE_TRANSITION), every local audio onset (AUDIO_EVENT);
  * the P5 ADVERSARIAL sweep — a separate vision request that sees native frames but NOT the P1 conclusions, asked to enumerate
    what a careless observer would miss (contacts, alternate drawings, overlaps, lighting, camera-vs-redraw, transitions);
  * humans (optional, via the same record shape).
`vme.vision.contracts.audit_phenomenon_coverage` checks the observations against them; every uncovered phenomenon triggers a
MANDATORY targeted native reinspection of its exact interval (even when the observer requested no crop). A reinspection resolves a
phenomenon only if it returns a non-vague relation in the dimension that phenomenon needs; otherwise the gap stays open, named.
"""
from __future__ import annotations

from ..util import is_vague_statement

PHENOMENON_KINDS = ("TEMPORAL_OVERLAP", "HAND_CONTACT", "ALTERNATE_STATE", "CAMERA_ATTRIBUTION", "LIGHTING_RELATION", "SCENE_TRANSITION",
                    "AUDIO_EVENT", "VISUAL_CHANGE")
KIND_DIMS = {"TEMPORAL_OVERLAP": {"SIMULTANEOUS_CHOREOGRAPHY"}, "HAND_CONTACT": {"CHARACTER_BODY_HAND_CONTACT"},
             "ALTERNATE_STATE": {"ART_STATE_TRANSFORMATION"}, "CAMERA_ATTRIBUTION": {"DEPTH_VIEWPOINT"},
             "LIGHTING_RELATION": {"MATERIAL_LIGHT_FINISH"}, "SCENE_TRANSITION": {"TRANSITION", "WHOLE_FRAME_LANGUAGE"},
             "AUDIO_EVENT": {"VISUAL_AUDIO_TIMING"}, "VISUAL_CHANGE": {"ART_STATE_TRANSFORMATION", "MOTION_ACTING", "DEPTH_VIEWPOINT"}}
ADVERSARIAL_SHAPE = """SOURCE ANALYSIS ONLY — ADVERSARIAL SWEEP. You are NOT shown any earlier description of these frames. Enumerate the
salient visual phenomena a careless observer would miss in this interval: hand/prop contacts, alternate drawings (redrawn views), overlapping
simultaneous actions, lighting/shadow relations, camera move vs redraw, scene transitions, and on-screen events that coincide with sound.
Return strict JSON: {"phenomena": [{"kind": one of TEMPORAL_OVERLAP|HAND_CONTACT|ALTERNATE_STATE|CAMERA_ATTRIBUTION|LIGHTING_RELATION|
SCENE_TRANSITION|VISUAL_CHANGE, "frames": [first_index, last_index], "entity_ids": [str], "why_salient": str}]}. Frame indices are the
native indices printed in each image label. Never invent a phenomenon you cannot point to in a labelled frame."""


def local_expectations(*, film: str, seq: str, a: int, b: int, survey: dict | None, audio_onsets: list[int]) -> list[dict]:
    out = []
    for s in (survey or {}).get("shots", []):
        k = int(s.get("start_frame_index", -1))
        if a < k <= b:
            out.append({"phenomenon_id": f"CUT:{film[:10]}:{k}", "kind": "SCENE_TRANSITION", "frames": [max(a, k - 1), min(b, k + 1)],
                        "entity_ids": [], "source": "LOCAL_SHOT_CUT", "film_sha256": film, "sequence_id": seq})
    for k in sorted(set(audio_onsets)):
        if a <= k <= b:
            out.append({"phenomenon_id": f"ONSET:{film[:10]}:{k}", "kind": "AUDIO_EVENT", "frames": [k, k], "entity_ids": [],
                        "source": "LOCAL_AUDIO_ONSET", "film_sha256": film, "sequence_id": seq})
    return out


def adversarial_expectations(resp: dict, *, film: str, seq: str, a: int, b: int) -> tuple[list[dict], list[str]]:
    """Accept only well-formed phenomena that point inside the interval; report every rejected entry (never silently drop)."""
    out, rejected = [], []
    for i, ph in enumerate((resp or {}).get("phenomena") or []):
        if not isinstance(ph, dict) or ph.get("kind") not in PHENOMENON_KINDS:
            rejected.append(f"{i}:BAD_KIND")
            continue
        fr = ph.get("frames")
        if not (isinstance(fr, list) and len(fr) == 2 and all(isinstance(x, int) for x in fr) and a <= fr[0] <= fr[1] <= b):
            rejected.append(f"{i}:FRAMES_OUTSIDE_INTERVAL")
            continue
        if is_vague_statement(str(ph.get("why_salient", ""))):
            rejected.append(f"{i}:VAGUE")
            continue
        out.append({"phenomenon_id": f"ADV:{film[:10]}:{ph['kind']}:{fr[0]}-{fr[1]}", "kind": ph["kind"], "frames": fr,
                    "entity_ids": [str(e) for e in ph.get("entity_ids") or []], "source": "P5_ADVERSARIAL", "why": ph.get("why_salient"),
                    "film_sha256": film, "sequence_id": seq})
    return out, rejected


def reinspection_resolves(kind: str, resp: dict) -> list[dict]:
    """The relations of a targeted reinspection that actually explain a phenomenon of this kind (empty = still unexplained)."""
    need = KIND_DIMS.get(kind, set())
    return [r for r in (resp or {}).get("relations") or [] if isinstance(r, dict) and not is_vague_statement(r.get("relation", ""))
            and set(r.get("dimensions") or []) & need]
