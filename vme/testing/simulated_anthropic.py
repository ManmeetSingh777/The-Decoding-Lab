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


class _Batches:
    def __init__(self, root: Path, mode: str):
        self.root, self.mode = root, mode

    def create(self, *, requests):
        reqs = list(requests)
        bid = "msgbatch_sim_" + digest([r["custom_id"] for r in reqs])[:16]
        p = self.root / f"{bid}.json"
        if p.exists():   # the provider would create a new batch; the adapter must never call twice for one task
            rec = read_json(p)
            rec["duplicate_creates"] = rec.get("duplicate_creates", 0) + 1
            atomic_write_json(p, rec)
            return NS(id=bid, processing_status="in_progress")
        results = [{"custom_id": r["custom_id"], "text": json.dumps(_respond(r["params"])), "in": _in_tokens(r["params"])} for r in reqs]
        atomic_write_json(p, {"id": bid, "results": results, "retrieves": 0, "billed_requests": len(reqs), "mode": self.mode})
        return NS(id=bid, processing_status="in_progress")

    def retrieve(self, bid):
        p = self.root / f"{bid}.json"
        rec = read_json(p)
        rec["retrieves"] += 1
        atomic_write_json(p, rec)
        ended = self.mode != "slow" or rec["retrieves"] > 1
        return NS(id=bid, processing_status="ended" if ended else "in_progress")

    def results(self, bid):
        rec = read_json(self.root / f"{bid}.json")
        for r in rec["results"]:
            msg = NS(content=[NS(type="text", text=r["text"])], stop_reason="end_turn", usage=NS(input_tokens=r["in"], output_tokens=900))
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
    if kind == "native_detail":
        return {"relations": [{"relation": "SIMULATED: in the native crop the focal edge separates from the surrounding region by value contrast "
                                           f"(crop mean {_stats(imgs[1][1])} vs frame {_stats(imgs[0][1])})", "dimensions": ["SHAPE_SURFACE_DETAIL"]}],
                "changes_vs_neighbours": "SIMULATED: compared with neighbours the crop region shifts slightly", "uncertainty": ["SIMULATED"]}
    if kind == "question_answer":
        return _answer(user, imgs)
    return {}


def _frame_packet(user, imgs) -> dict:
    tg = user["target_frames"]
    by_label = {l.split()[1]: b for l, b in imgs}
    obs, prev = [], None
    for t in tg:
        png = by_label[t["frame_id"]]
        k = int(t["frame_id"].split(":")[1])
        m = _stats(png)
        delta: float | None = None if prev is None else round(sum(abs(a - b) for a, b in zip(m, prev)), 1)
        dims = [DIMS[k % len(DIMS)], DIMS[(k + 5) % len(DIMS)]]
        rels = [{"relation": f"SIMULATED: region with mean colour {m} separates from the surrounding area through value contrast relative to the background",
                 "dimensions": dims, "region": {"x": 8, "y": 8, "w": 32, "h": 24}},
                {"relation": "SIMULATED: near and far parts of the focal form change together while the background structure stays constant",
                 "dimensions": JOINTS[k % len(JOINTS)]}]
        changed = [] if (delta is not None and delta < 0.3) else [{"kind": "OBSERVED_DIFF", "what": f"SIMULATED: mean shift {delta} relative to prior frame"}]
        obs.append({"frame_id": t["frame_id"], "source_sha": t["frame_id"].split(":")[0], "pts_time": t["pts_time"], "request_id": user["packet_id"],
                    "submitted_image_sha": sha256_bytes(png), "active_question_ids": [q.get("question_id") for q in user["active_questions"]],
                    "scene_and_world_state": f"SIMULATED: frame statistics {m}", "actually_visible_actor_and_object_ids": ["sim_focal"],
                    "focal_whole_artwork_state": f"SIMULATED: focal region at frame {k} keeps its outline while the setting stays behind it",
                    "visible_design_relations": rels, "character_face_limb_contact_state": [], "visible_layer_depth_attention_state": "UNKNOWN",
                    "changed_since_prior_frame": changed, "no_significant_change_reason": None if changed else f"SIMULATED: unchanged vs prior (delta {delta})",
                    "simultaneous_event_links": [], "camera_vs_actor_vs_drawing_state": "UNKNOWN", "material_finish_or_colour_change": [],
                    "native_detail_followups": [{"region": {"x": 8, "y": 8, "w": 32, "h": 24}, "reason": "SIMULATED: verify edge treatment"}] if k % 7 == 0 else [],
                    "source_fact_statements": [f"fixture tint reading at index {k}: {m}"], "subject_class": CLASSES[k % len(CLASSES)],
                    "hypothesis_or_uncertainty": ["SIMULATED"], "confidence_limitations": ["SIMULATED transport — not perception"]})
        prev = m
    return {"frame_observations": obs,
            "packet_transition_graph": {"edges": [[a["frame_id"], b["frame_id"]] for a, b in zip(obs, obs[1:])]},
            "boundary_state": {"scene_world": "SIMULATED", "active_objects": [], "open_events": [], "attention": "UNKNOWN", "hypotheses": [],
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
    base["BRANCHES"] = [{"when": rb["conditions"], "operation_id": rb["operation_ids"][0],
                         "construction_action": (f"SIMULATED: draw the {{subject}} with {' and '.join(d.lower().replace('_', ' ') for d in dims)} decided together, "
                                                 f"keeping its connected parts separated from the {{setting}} by value grouping ({', '.join(f'{k}={v}' for k, v in sorted(rb['conditions'].items()))})")}
                        for rb in user["required_branches"]]
    return base
