"""SIMULATED Claude client for offline REAL-path drills. FIXTURE — never real vision, never learning evidence.

Implements the subset of the official SDK surface the production adapter calls:
  client.messages.batches.create(requests=[{custom_id, params}]) / .retrieve(id) / .results(id)
  client.models.retrieve(model_id)
State is durable on disk (a killed process can reconcile). Outputs are deterministic functions of the ACTUAL
image bytes it receives plus the request JSON; every text field starts with "SIMULATED:".
"""
from __future__ import annotations

import base64
import io
import json
import re
from pathlib import Path
from types import SimpleNamespace as NS

from PIL import Image, ImageStat

from ..util import atomic_write_json, read_json, sha256_bytes, digest

DIMS = ["WHOLE_FRAME_LANGUAGE", "ORIGINAL_SUBJECT_DESIGN", "CHARACTER_WHOLE_DESIGN", "CHARACTER_FACE_ACTING", "CHARACTER_BODY_HAND_CONTACT",
        "SHAPE_SURFACE_DETAIL", "COLOUR_RELATIONS", "MATERIAL_LIGHT_FINISH", "WORLD_ASSEMBLY", "SUBJECT_WORLD_INTEGRATION", "DEPTH_VIEWPOINT",
        "ART_STATE_TRANSFORMATION", "MOTION_ACTING", "SIMULTANEOUS_CHOREOGRAPHY", "TRANSITIONS_VISUAL_GRAMMAR", "FINISH_AND_READABILITY"]
JOINTS = [["CHARACTER_FACE_ACTING", "DEPTH_VIEWPOINT", "MATERIAL_LIGHT_FINISH"], ["CHARACTER_BODY_HAND_CONTACT", "MATERIAL_LIGHT_FINISH"],
          ["CHARACTER_WHOLE_DESIGN", "SUBJECT_WORLD_INTEGRATION"], ["WORLD_ASSEMBLY", "DEPTH_VIEWPOINT"],
          ["CHARACTER_FACE_ACTING", "DEPTH_VIEWPOINT"], ["DEPTH_VIEWPOINT", "ART_STATE_TRANSFORMATION"]]
CLASSES = ["biped", "creature", "machine", "landscape"]


class SimulatedAPIStatusError(Exception):
    """Mirrors the SDK's APIStatusError surface (`status_code`) for strict rejection paths."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


class SimulatedConnectionError(Exception):
    """Transport failure AFTER the simulated server accepted and billed the batch (accept_then_raise mode)."""


_CID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_PARAM_KEYS = {"model", "max_tokens", "messages", "system", "output_config", "temperature", "thinking", "metadata", "stop_sequences"}


class _Batches:
    """STRICT Message Batches fake: rejects invalid custom_id (1-64 [A-Za-z0-9_-]), duplicate ids within a batch, unknown
    params, missing model/max_tokens/messages; every successful create() is a NEW billable batch (no cross-batch dedup)."""

    def __init__(self, root: Path, mode: str):
        self.root, self.mode = root, mode

    def _validate(self, reqs) -> None:
        ids = [r.get("custom_id") for r in reqs]
        for cid in ids:
            if not isinstance(cid, str) or not _CID.fullmatch(cid):
                raise SimulatedAPIStatusError(400, f"invalid_request_error: custom_id {cid!r} must match ^[a-zA-Z0-9_-]{{1,64}}$")
        if len(set(ids)) != len(ids):
            raise SimulatedAPIStatusError(400, "invalid_request_error: duplicate custom_id within batch")
        for r in reqs:
            pr = r.get("params") or {}
            if set(pr) - _PARAM_KEYS or not isinstance(pr.get("model"), str) or not isinstance(pr.get("max_tokens"), int)                     or not isinstance(pr.get("messages"), list):
                raise SimulatedAPIStatusError(400, f"invalid_request_error: params {sorted(pr)}")

    def create(self, *, requests):
        reqs = list(requests)
        self._validate(reqs)
        n = len(list(self.root.glob("msgbatch_*.json")))
        bid = f"msgbatch_sim_{n:04d}_" + digest([r["custom_id"] for r in reqs])[:12]
        seen = {c for p in self.root.glob("msgbatch_*.json") for c in read_json(p)["custom_ids"]}
        dup = sum(1 for r in reqs if r["custom_id"] in seen)
        results = [{"custom_id": r["custom_id"], "text": json.dumps(_respond(r["params"])), "in": _in_tokens(r["params"])} for r in reqs]
        atomic_write_json(self.root / f"{bid}.json", {"id": bid, "custom_ids": [r["custom_id"] for r in reqs], "results": results,
                                                     "retrieves": 0, "billed_requests": len(reqs), "mode": self.mode,
                                                     "duplicate_creates": dup})
        if self.mode == "accept_then_raise":
            raise SimulatedConnectionError("connection reset after the batch was accepted")
        return NS(id=bid, processing_status="in_progress")

    def retrieve(self, bid):
        p = self.root / f"{bid}.json"
        if not p.exists():
            raise SimulatedAPIStatusError(404, f"not_found_error: {bid}")
        rec = read_json(p)
        rec["retrieves"] += 1
        atomic_write_json(p, rec)
        ended = self.mode != "slow" or rec["retrieves"] > 1
        return NS(id=bid, processing_status="ended" if ended else "in_progress")

    def results(self, bid):
        rec = read_json(self.root / f"{bid}.json")
        for r in rec["results"]:
            if self.mode in ("errored", "expired", "canceled"):
                yield NS(custom_id=r["custom_id"], result=NS(type=self.mode, error={"type": "simulated"}))
                continue
            text, stop = r["text"], "end_turn"
            if self.mode == "truncated" or (self.mode == "truncate_over_4" and len(json.loads(text).get("frame_observations") or []) > 4):
                text, stop = text[: len(text) // 2], "max_tokens"
            elif self.mode == "non_json":
                text = "SIMULATED: I looked at the frames and they are nice."
            msg = NS(content=[NS(type="text", text=text)], stop_reason=stop, model="SIMULATED",
                     usage=NS(input_tokens=r["in"], output_tokens=900))
            yield NS(custom_id=r["custom_id"], result=NS(type="succeeded", message=msg))


class SimulatedAnthropicClient:
    label = "SIMULATED_FIXTURE_CLIENT"

    def __init__(self, state_dir: str | Path, *, mode: str = "ok"):
        root = Path(state_dir)
        root.mkdir(parents=True, exist_ok=True)
        self.root = root
        self.messages = NS(batches=_Batches(root, mode))
        self.models = NS(retrieve=lambda mid: NS(id=mid, max_input_tokens=1_000_000, max_tokens=128_000, capabilities={"vision": True}))

    def billed_requests(self) -> int:
        return sum(read_json(p)["billed_requests"] for p in self.root.glob("msgbatch_*.json"))

    def duplicate_creates(self) -> int:
        return sum(read_json(p).get("duplicate_creates", 0) for p in self.root.glob("msgbatch_*.json"))


def _in_tokens(params) -> int:
    return 1500 * sum(1 for b in params["messages"][0]["content"] if b["type"] == "image")


def _images(params) -> list:
    out, label = [], None
    for b in params["messages"][0]["content"][1:]:
        if b["type"] == "text":
            label = b["text"]
        else:
            out.append((label, base64.b64decode(b["source"]["data"])))
    return out


def _stats(png: bytes) -> list[float]:
    return [round(x, 1) for x in ImageStat.Stat(Image.open(io.BytesIO(png)).convert("RGB")).mean]


def _respond(params) -> dict:
    mk = re.search(r"VME_REQUEST_KIND: (\w+)", params["system"])
    kind = mk.group(1) if mk else "unknown"
    user = json.loads(params["messages"][0]["content"][0]["text"])
    imgs = _images(params)
    if kind == "frame_packet":
        return _frame_packet(user, imgs)
    if kind == "window_rationale":
        return _rationale(user, imgs)
    if kind == "adversarial_sweep":
        return _adversarial(user, imgs)
    if kind == "native_detail":
        dims = [d for d in user.get("dimensions") or [] if isinstance(d, str)] or ["SHAPE_SURFACE_DETAIL"]
        if "gap" in user and user["gap"].get("phenomenon_id"):
            from ..investigation.auditor import KIND_DIMS
            dims = sorted(set(dims) | {"DEPTH_VIEWPOINT"} | set(sorted(KIND_DIMS.get(user["gap"].get("kind"), set()))[:1]))
        rel = {"relation": "SIMULATED: in the native crop the focal edge separates from the surrounding region by value contrast "
                           f"(crop mean {_stats(imgs[1][1])} vs frame {_stats(imgs[0][1])}) while the neighbours keep the same overlap order",
               "dimensions": dims}
        if user.get("dimensions") is not None and not user.get("dimensions") and not user.get("gap", {}).get("phenomenon_id"):
            return {"relations": [], "changes_vs_neighbours": "SIMULATED: UNKNOWN", "uncertainty": ["SIMULATED: pixels do not show it"]}
        return {"relations": [rel], "changes_vs_neighbours": "SIMULATED: compared with neighbours the crop region shifts slightly",
                "uncertainty": ["SIMULATED: material cause not determinable from 720p pixels"], "phenomenon_dimensions": dims}
    if kind == "question_answer":
        return _answer(user, imgs)
    if kind == "character_dossier":
        return _dossier(user, imgs)
    return {}


MOTION_OPS = {"op.motion_actor_track": "ACTOR_ACTING", "op.camera_attention": "CAMERA", "op.attention_focus": "ATTENTION",
              "op.world_motion": "WORLD", "op.audio_cue": "AUDIO"}


def _dossier(user, imgs) -> dict:
    """SIMULATED Addendum-29 study: deterministic per real image statistics; every field cites a SUBMITTED witness id."""
    ti = (user.get("binding") or {}).get("target_images") or []
    states = [t["witness_id"] for t in ti if t["role"] == "TARGET"]
    crop = [t["witness_id"] for t in ti if t["role"] == "NATIVE_CROP"]
    con = [t["witness_id"] for t in ti if t["role"] == "CONTRAST"]
    m = [_stats(b) for _, b in imgs]
    f = lambda rel, imp, w: {"state": "OBSERVED", "visible_relation": f"SIMULATED: {rel}", "reconstruction_impact": f"SIMULATED: {imp}",
                             "witness_ids": w, "precise_next_witness": ""}
    fields = {"whole_design": f(f"the drawn entity reads as one dominant mass against the setting (mean {m[0]})", "draw one connected mass first", states[:2]),
              "outer_contour_and_taper": f("the outer contour widens at the upper mass and narrows toward the lower edge while staying continuous",
                                           "contour width changes along the segment, never a constant-width extrusion", states[:1] + crop[:1]),
              "negative_spaces": f("a pocket of setting colour stays open between the mass and its extension", "keep the open pocket", states[:1]),
              "visual_piece_junctions": f("pieces merge into the parent mass with no separate outline at the junction", "merge junctions", crop[:1] or states[:1]),
              "fills_edges_materials": f("adjacent fill regions meet at a value step with no drawn outline between them, so the edge stays soft against the setting", "edge by value step", crop[:1] or states[:1]),
              "lighting_and_shadows": f("one darker region follows the lower contour on the side away from the brighter setting area",
                                        "shadow region follows the contour", states[:2]),
              "view_and_pose_redraws": f("between the two states the contour is redrawn, not rotated", "needs a redrawn state asset", states[:2]),
              "contact_and_occlusion": f("the near part overlaps the setting edge while the far part stays behind", "near/far layer order", states[:1]),
              "world_integration": f("the entity's value range sits inside the setting's range with higher local contrast", "value-relative integration",
                                     states[:1] + con[:1])}
    if user.get("entity_id") == "sim_unknown_pose":
        fields["view_and_pose_redraws"] = {"state": "UNKNOWN", "witness_ids": states[:1], "precise_next_witness": "a profile state of this entity"}
    return {"study_basis": "SOURCE_FIRST_DRAWN_ENTITY", "entity_id": user.get("entity_id"), "fields": fields,
            "identity_across_drawings": [{"witness_ids": states[:2], "what_persists": "SIMULATED: mass grouping and value roles",
                                          "what_is_redrawn": "SIMULATED: outer contour"}],
            "contrasting_examples": [{"witness_ids": con[:1], "difference": "SIMULATED: the contrast entity uses a different mass grouping"}],
            "scope_class": "CONDITIONAL_STYLE_RULE"}


def _adversarial(user, imgs) -> dict:
    """SIMULATED P5 adversarial sweep: sees the sampled native frames only (no P1 text) and names every sampled pair whose pixels
    differ as a VISUAL_CHANGE phenomenon an observer must explain."""
    ks = [int(l.split()[1].split(":")[1]) for l, _ in imgs]
    st = [_stats(b) for _, b in imgs]
    out = []
    for (k0, s0), (k1, s1) in zip(zip(ks, st), list(zip(ks, st))[1:]):
        d = round(sum(abs(x - y) for x, y in zip(s0, s1)), 1)
        if d >= 1.0:
            out.append({"kind": "VISUAL_CHANGE", "frames": [k0, k1], "entity_ids": ["sim_focal"],
                        "why_salient": f"SIMULATED: the sampled frames {k0} and {k1} differ by mean colour {d}, so the focal form changes in between"})
    return {"phenomena": out}


def _frame_packet(user, imgs) -> dict:
    """SIMULATED P1 records that ADDRESS every artistic dimension for their (synthetic) content: entity enumerated and typed, a
    relation per entity, contact/lighting/depth/camera stated or N/A with a reason, every change described for its entity and
    attributed, persistence justified, local audio events linked. Still SIMULATED text — wiring, not perception."""
    tg = user["target_frames"]
    by_label = {l.split()[1]: b for l, b in imgs}
    obs, prev = [], None
    for t in tg:
        png = by_label[t["frame_id"]]
        k = int(t["frame_id"].split(":")[1])
        m = _stats(png)
        delta: float | None = None if prev is None else round(sum(abs(a - b) for a, b in zip(m, prev)), 1)
        dims = [DIMS[k % len(DIMS)], DIMS[(k + 5) % len(DIMS)]]
        changed = [] if (delta is not None and delta < 0.3) else [{"kind": "OBSERVED_DIFF", "entity_ids": ["sim_focal"],
                                                                    "what": f"SIMULATED: the focal form's mean colour shifts by {delta} relative to the prior frame"}]
        rels = [{"relation": f"SIMULATED: region with mean colour {m} separates from the surrounding area through value contrast relative to the background",
                 "dimensions": dims + (["ART_STATE_TRANSFORMATION"] if changed else []), "region": {"x": 8, "y": 8, "w": 32, "h": 24},
                 "entity_ids": ["sim_focal"]},
                {"relation": "SIMULATED: near and far parts of the focal form change together while the background structure stays constant",
                 "dimensions": JOINTS[k % len(JOINTS)], "entity_ids": ["sim_focal"]}]
        ae = t.get("audio_events") or []
        obs.append({"frame_id": t["frame_id"], "source_sha": t["frame_id"].split(":")[0], "pts_time": t["pts_time"], "request_id": user["packet_id"],
                    "submitted_image_sha": sha256_bytes(png), "active_question_ids": [q.get("question_id") for q in user["active_questions"]],
                    "scene_and_world_state": f"SIMULATED: frame statistics {m}", "actually_visible_actor_and_object_ids": ["sim_focal"],
                    "entity_kinds": {"sim_focal": "character"},
                    "focal_whole_artwork_state": f"SIMULATED: focal region at frame {k} keeps its outline while the setting stays behind it",
                    "visible_design_relations": rels,
                    "character_face_limb_contact_state": {"not_applicable": "SIMULATED: the focal form shows no face, limb or contact region at this frame"},
                    "visible_layer_depth_attention_state": "SIMULATED: the focal form sits in front of the setting layer and holds the attention region",
                    "changed_since_prior_frame": changed,
                    "no_significant_change_reason": None if changed else f"SIMULATED: every region keeps its colour and position relative to the prior frame (delta {delta})",
                    "simultaneous_event_links": {"not_applicable": "SIMULATED: only one entity is visible so no simultaneous events exist here"},
                    "camera_vs_actor_vs_drawing_state": ("SIMULATED: the focal form changes while the setting stays fixed, so the change is the drawing not the camera"
                                                         if changed else {"not_applicable": "SIMULATED: nothing moves between this frame and the prior one"}),
                    "material_finish_or_colour_change": {"not_applicable": "SIMULATED: flat synthetic fills carry no material or lighting change"},
                    "audiovisual_links": [{"audio_event": e.get("kind"), "frame": e.get("frame"),
                                           "visual_relation": "SIMULATED: the onset coincides with the frame where the focal form shifts colour"} for e in ae],
                    "native_detail_followups": [{"region": {"x": 8, "y": 8, "w": 32, "h": 24}, "reason": "SIMULATED: verify edge treatment"}] if k % 7 == 0 else [],
                    "source_fact_statements": [f"fixture tint reading at index {k}: {m}"], "subject_class": CLASSES[k % len(CLASSES)],
                    "hypothesis_or_uncertainty": ["SIMULATED"], "confidence_limitations": ["SIMULATED transport — not perception"],
                    "persistent_state_ids": ["sim_focal"],
                    "unexplained_phenomena": ([{"phenomenon": "SIMULATED: a foreground element passes in front of the focal form while the focal "
                                                              "form keeps its silhouette and the setting holds still",
                                                "why": "SIMULATED: no current decision says which layer may occlude the focal actor",
                                                "connected_dimensions": ["DEPTH_VIEWPOINT", "SUBJECT_WORLD_INTEGRATION"],
                                                "region": {"x": 4, "y": 4, "w": 24, "h": 16}}] if k == 11 else [])})
        prev = m
    return {"frame_observations": obs,
            "packet_transition_graph": {"edges": [[a["frame_id"], b["frame_id"]] for a, b in zip(obs, obs[1:])]},
            "boundary_state": {"scene_world": "SIMULATED", "active_objects": [{"id": "sim_focal", "identity": "SIMULATED focal entity",
                                                                               "drawing_state": "current"}], "open_events": [], "attention": "UNKNOWN", "hypotheses": [],
                               "open_questions": [q.get("question_id") for q in user["active_questions"]]},
            "reconciled_events": [{"event_id": e.get("event_id"), "resolution": "CONTINUES"} for e in (user.get("prior_boundary_state") or {}).get("open_events", [])],
            "question_update": None}


def _rationale(user, imgs) -> dict:
    i = user["window_index"]
    role = ["C", "W", "T"][i % 3]
    opps = {"C": ["character_shape", "body_face_relation", "hand_prop"], "W": ["complete_world", "integrated_object_artwork", "colour_material_finish"],
            "T": ["viewpoint", "state_substitution", "spatial_transformation"]}[role]
    return {"whole_visual_quality_statement": f"SIMULATED: across frames {user['frames']} the focal form stays separate from the setting while its parts change together",
            "selection_role_candidates": [role], "opportunities": opps,
            "visible_proof_for_each_opportunity": {o: f"SIMULATED: frames {user['frames']} show {o.replace('_', ' ')} relative to the world" for o in opps},
            "actor_class": CLASSES[i % len(CLASSES)], "content_label": "MAIN_FILM", "new_question_contributed": f"SIMULATED question {role}{i}",
            "known_limitations": ["SIMULATED transport"]}


def _answer(user, imgs) -> dict:
    q = user["question"]
    wids = [l.split()[1] for l, _ in imgs]
    dims = user["dimensions"]
    ops = user["allowed_operations"]
    base = {"answer_status": "INFERRED" if q["owner_stage"] != "SOURCE_OBSERVATION" else "OBSERVED",
            "REFERENCE_REQUIRED": dims == ["CHARACTER_WHOLE_DESIGN"] or (dims == ["CHARACTER_BODY_HAND_CONTACT"]),
            "SOURCE_VISIBLE_FACTS": [{"relation": f"SIMULATED: in {w} the {' and '.join(d.lower() for d in dims)} relation holds as parts change together relative to the setting",
                                      "witness_ids": [w]} for w in wids[:3]],
            "IMPORTANT_LINKED_CHANGES": [d.lower() for d in dims],
            "CONSTRUCTION_EXPLANATION": f"SIMULATED: the {' + '.join(dims)} qualities are produced together: major parts are drawn as one connected form whose "
                                        "value grouping separates it from the setting while views change",
            "WHY_THE_DECISION_MATTERS": "SIMULATED: keeps the focal form coherent with its world",
            "WHEN_APPLICABLE": {}, "WHEN_NOT_APPLICABLE": ["SIMULATED exception: explanatory diagram frames"],
            "ACTUAL_PRODUCING_OPERATION": {"operation_id": ops[0]}, "WHERE_IT_ENTERS_COMPILED_REQUEST": {"decision": q["missing_decision_id"], "operator": ops[0]},
            "REMAINING_UNKNOWN": ["SIMULATED: profile views"], "answer_evidence_ids": wids,
            "INVARIANT": "SIMULATED: connected major parts with value separation from the setting",
            "ADAPTS_WITH": ["subject anatomy", "material"], "CREATIVE_FREEDOM": ["original identity", "palette choice within the brief"],
            "FORBIDDEN_SOURCE_SPECIFIC": ["source character identity", "source logos"]}
    def action(rb):
        cond = ', '.join(f'{k}={v}' for k, v in sorted(rb['conditions'].items()))
        if rb["operation_ids"][0] == "op.world_plate":
            return (f"SIMULATED: paint the {{setting}} as an empty plate whose depth layers keep a clear value step between near and far "
                    f"planes, leaving the focal area open for a separately drawn actor ({cond})")
        rev = ""
        if user.get("human_art_defects"):
            rev = f"; revised after {len(user['human_art_defects'])} rejected-art defect(s): the near contour is redrawn over the adjacent part"
        return (f"SIMULATED: draw the {{subject}} with {' and '.join(d.lower().replace('_', ' ') for d in dims)} decided together, "
                f"keeping its connected parts separated from the {{setting}} by value grouping ({cond}){rev}")
    def policy(rb):
        if dims in (["CHARACTER_WHOLE_DESIGN"], ["CHARACTER_BODY_HAND_CONTACT"]) and rb["operation_ids"][0] not in MOTION_OPS:
            roles = [{"role": "positive_view", "witness_id": wids[0]}] + ([{"role": "contrast", "witness_id": wids[1]}] if len(wids) > 1 else [])
            return {"mode": "REQUIRED", "roles": roles, "reason": "SIMULATED: character construction needs visual exemplars"}
        return {"mode": "NOT_APPLICABLE", "reason": "SIMULATED: decision carried by the relation clause; no exemplar conditioning claimed"}

    def program(rb):
        op = rb["operation_ids"][0]
        if op not in MOTION_OPS:
            return None
        # SIMULATED values: each method states EVERY parameter of its contract (vme.render.motion_program.TRACK_METHOD_PARAMS)
        tk = MOTION_OPS[op]
        params = {"ACTOR_ACTING": {"method": "ANTICIPATE_OVERSHOOT", "hold_ratio": 0.25, "anticipation_ratio": 0.12, "anticipation_span": 0.2,
                                   "overshoot_ratio": 0.08, "overshoot_span": 0.15},
                  "CAMERA": {"method": "EASE_IN_OUT"},
                  "ATTENTION": {"method": "DIM_OTHERS", "transition_frames": 4, "hold_frames": 6, "release_frames": 4, "magnitude": 0.35},
                  "WORLD": {"method": "PARALLAX_LAYERS", "layer_coefficients": {"far": 0.3, "mid": 0.6, "near": 0.9}},
                  "AUDIO": {"method": "CUE_ON_EVENT", "cue_offset_frames": 0}}[tk]
        return {"track_kind": tk, **params, "witness_ids": wids[:2]}
    base["BRANCHES"] = [{"when": rb["conditions"], "operation_id": rb["operation_ids"][0], "construction_action": action(rb),
                         "reference_policy": policy(rb), **({"MOTION_PROGRAM": program(rb)} if program(rb) else {})}
                        for rb in user["required_branches"]]
    return base
