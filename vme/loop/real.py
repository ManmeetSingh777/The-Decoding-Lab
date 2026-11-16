"""REAL-path S0–S9 learning loop (audit P0-1/P0-4). Production code — MUST NOT import vme.fixtures or vme.testing.

Providers are injected through `RealProviders`. `RealProviders.production()` builds the Claude batch vision adapter
(official SDK) and the Runware HTTP transport; offline drills pass a simulated client/transport through the SAME
interfaces, and every artefact they produce carries evidence_origin=SIMULATED_VLM_TRANSPORT (never real learning).
Handlers stop only for: missing human decision, missing authorization/consent, provider pending, or a named
evidence blocker. Every transition is persisted as a `LoopTransition` (run_id prefix REAL).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..util import Blocked, digest, is_vague_statement, now_iso, read_json
from ..state.workspace import Workspace
from ..vision.runner import maybe_crash
from ..vision.protocol import PROTOCOL_SHA, pass_instructions
from ..providers.ids import custom_id_for

STAGES = ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9")
CONSUMERS = {
    "S0": "vme.loop.real:RealLoopRunner._s0 → ClaudeBatchVisionAdapter.request_json(window_rationale) → selection.first15:propose_selection",
    "S1": "RealLoopRunner._s1 → vision.runner:PacketRunner(ClaudeBatchVisionAdapter) → _extract_witnesses → _native_followups",
    "S2": "RealLoopRunner._s2 → style.coverage:review_visual_model_completeness → investigation.controller:LoopController → request_json(question_answer)",
    "S3": "RealLoopRunner._s3 → style.authoring:author_decision (called as S2 decision_writer) — verifies decisions",
    "S4": "RealLoopRunner._s4 → style.authoring:author_skill/verify_structural_derivation → review_visual_model_completeness",
    "S5": "RealLoopRunner._s5 → providers.gateway (probe) → skills.runtime:execute → compiler → gateway → RunwareAdapter",
    "S6": "RealLoopRunner._s6 → review.approvals:GateKeeper (human art verdict)",
    "S7": "RealLoopRunner._s7 → artwork.character + skills.runtime:execute(identity) → WHOLE_STATE_SWAP pack → human asset verdict",
    "S8": "RealLoopRunner._s8 → render.renderer:render_video (GateKeeper.authorize_render)",
    "S9": "RealLoopRunner._s9 → human video review → freeze check → HoldoutRegistry → runtime.execute → controller.observe_new_output",
}
OP_FOR_KIND = {"motion_actor_track": "op.motion_actor_track", "camera_attention": "op.camera_attention", "attention_focus": "op.attention_focus",
               "world_motion": "op.world_motion", "audio_cue": "op.audio_cue", "whole_scene": "op.whole_scene", "world_plate": "op.world_plate", "canonical_character": "op.canonical_character", "layer_extract": "op.layer_extract",
               "motion_render": "op.motion_render"}
RATIONALE_SHAPE = """SOURCE ANALYSIS ONLY. You see 3 actual frames (start, middle, end) of one contiguous window of a source film.
Return strict JSON: {"whole_visual_quality_statement": str (a specific visible relationship between designed forms, world, light or motion;
no standalone adjectives), "selection_role_candidates": subset of ["C","W","T"] (C=character identity/acting, W=complete illustrated world,
T=changing viewpoint/state/choreography), "opportunities": subset of [character_shape, body_face_relation, whole_body_acting, hand_prop,
complete_world, integrated_object_artwork, colour_material_finish, viewpoint, state_substitution, choreographed_coexistence,
spatial_transformation], "visible_proof_for_each_opportunity": {opportunity: frame-anchored description}, "actor_class": str|null,
"content_label": "MAIN_FILM"|"SPONSOR"|"OUTRO"|"CREDITS"|"INTRO_CARD", "new_question_contributed": str, "known_limitations": [str]}.
Say UNKNOWN when the frames do not show something. Never claim proprietary production methods."""
QA_SHAPE = """SOURCE ANALYSIS ONLY — answer ONE investigation question using ONLY the labelled source images provided
(each image is preceded by its witness id). Separate OBSERVED from INFERRED; if the images cannot settle it, answer_status=UNKNOWN.
Return strict JSON with keys: answer_status (OBSERVED|INFERRED|UNKNOWN|REFUTED), SOURCE_VISIBLE_FACTS [{relation, witness_ids}],
IMPORTANT_LINKED_CHANGES [str], CONSTRUCTION_EXPLANATION str, WHY_THE_DECISION_MATTERS str, WHEN_APPLICABLE {}, WHEN_NOT_APPLICABLE [str],
ACTUAL_PRODUCING_OPERATION {operation_id}, WHERE_IT_ENTERS_COMPILED_REQUEST {decision, operator}, REMAINING_UNKNOWN [str],
answer_evidence_ids [witness ids], and when the question asks for conditional production choices: BRANCHES
[{when:{condition:value}, construction_action: str written for a NEW subject using the placeholders {subject} and {setting}, never source
nouns, operation_id}], INVARIANT str, ADAPTS_WITH [str], CREATIVE_FREEDOM [str], FORBIDDEN_SOURCE_SPECIFIC [str].
One BRANCH is required for each entry of required_branches (same conditions, one of its operation_ids).
Every BRANCH also states reference_policy: {"mode": "REQUIRED"|"TEXT_ONLY_DEMONSTRATED"|"NOT_APPLICABLE", "roles": [{"role": "positive_view"|
"contrast"|..., "witness_id": <one of the labelled witnesses>}], "reason": str} — omitting it leaves requiredness UNKNOWN (blocks).
Motion/camera/attention/world/audio branches also give MOTION_PROGRAM {"track_kind", "method", <every parameter of that method>,
"witness_ids": [..]} derived from what the frames show, with these exact contracts (a missing parameter leaves the decision UNKNOWN):
ACTOR_ACTING: EASE_IN_OUT | HOLD_THEN_MOVE{hold_ratio} | ANTICIPATE_OVERSHOOT{hold_ratio, anticipation_ratio, anticipation_span,
overshoot_ratio, overshoot_span} (all 0..1); CAMERA: EASE_IN_OUT | HOLD_THEN_MOVE{hold_ratio}; ATTENTION: DIM_OTHERS | LOCAL_HIGHLIGHT |
LOCAL_SCALE {transition_frames, hold_frames, release_frames, magnitude}; WORLD: PARALLAX_LAYERS{layer_coefficients: {depth: camera
coefficient}}; AUDIO: CUE_ON_EVENT{cue_offset_frames}. UNKNOWN otherwise."""
NATIVE_SHAPE = """SOURCE ANALYSIS ONLY. Image 1 is a full frame, image 2 a NATIVE-resolution crop of it (no resampling), images 3-4
the neighbouring frames. Describe only what the crop shows in relation to the whole frame and the neighbours. Return strict JSON:
{"relations": [{"relation": str, "dimensions": [str]}], "changes_vs_neighbours": str, "uncertainty": [str]}."""
CHARACTER_DOSSIER_SHAPE = """SOURCE ANALYSIS ONLY — Addendum 29 character passes C0–C10 for ONE source-drawn entity, using only the labelled images
(whole frames, native crops, other states of the same entity and an unlike contrasting entity). Observe the DRAWN ENTITY first; anatomy
names are tags applied after observation, never geometry generators. Return strict JSON {"study_basis": "SOURCE_FIRST_DRAWN_ENTITY",
"entity_id": str, "fields": {"whole_design"|"outer_contour_and_taper"|"negative_spaces"|"visual_piece_junctions"|"fills_edges_materials"|
"lighting_and_shadows"|"view_and_pose_redraws"|"contact_and_occlusion"|"world_integration": {"state": "OBSERVED"|"UNKNOWN",
"visible_relation": str, "reconstruction_impact": str, "witness_ids": [str], "precise_next_witness": str}}, "identity_across_drawings":
[{"witness_ids": [str], "what_persists": str, "what_is_redrawn": str}], "contrasting_examples": [{"witness_ids": [str], "difference": str}],
"scope_class": "STYLE_INVARIANT_CANDIDATE"|"CONDITIONAL_STYLE_RULE"|"CHARACTER_IDENTITY_RULE"|"SHOT_OR_EVENT_RULE"|"UNKNOWN_OR_CONTRADICTED"}.
Mark UNKNOWN with the exact next witness whenever the pixels do not show it; never describe tubes, stock faces or default shading."""
RATIONALE_SYSTEM = pass_instructions("P2") + "\n\nPASS-SPECIFIC OUTPUT SHAPE:\n" + RATIONALE_SHAPE
QA_SYSTEM = pass_instructions("P4") + "\n\nPASS-SPECIFIC OUTPUT SHAPE:\n" + QA_SHAPE
NATIVE_SYSTEM = pass_instructions("P5") + "\n\nPASS-SPECIFIC OUTPUT SHAPE:\n" + NATIVE_SHAPE
from ..investigation.auditor import ADVERSARIAL_SHAPE as _ADV_SHAPE  # noqa: E402
ADVERSARIAL_SYSTEM = pass_instructions("P5") + "\n\nPASS-SPECIFIC OUTPUT SHAPE:\n" + _ADV_SHAPE
CHARACTER_DOSSIER_SYSTEM = pass_instructions("P2") + "\n\nPASS-SPECIFIC OUTPUT SHAPE:\n" + CHARACTER_DOSSIER_SHAPE


@dataclass
class RealLoopConfig:
    max_window_s: float = 12.0
    min_window_s: float = 2.0
    max_windows_per_film: int = 10          # INITIAL rationale batch per film; expanded when selection cannot be filled (R22)
    target_per_packet: int = 8
    per_target_output_tokens: int = 1400    # R3 F18: response budget reserved PER target frame (not one shared ceiling)
    packet_overhead_tokens: int = 2000
    max_split_rounds: int = 4
    native_followup_budget: int = 400       # total model-requested native crops per run (budget, not a per-sequence cap) (R11)
    reinspection_budget: int = 40           # gap-driven source reinspection requests per run (R11)
    max_questions: int = 60
    max_attempts_per_gap: int = 2
    render: dict = field(default_factory=lambda: {"width": 1280, "height": 720, "fps": 30})


class RealProviders:
    """Injected provider bundle. Same handler code for production and simulated drills."""

    def __init__(self, *, vision_client_factory, vision_transport_kind: str, image_transport, image_transport_kind: str):
        self.vision_client_factory = vision_client_factory
        self.vision_transport_kind = vision_transport_kind
        self.image_transport = image_transport
        self.image_transport_kind = image_transport_kind

    @classmethod
    def production(cls, ws: Workspace) -> "RealProviders":
        from ..vision.claude_adapter import production_client_factory
        from ..providers.runware import http_transport
        api = ((ws.state_dir / "PROVIDER_STATE.json").exists() and read_json(ws.state_dir / "PROVIDER_STATE.json").get("runware", {})
               .get("api_base")) or "https://api.runware.ai/v1"
        return cls(vision_client_factory=production_client_factory, vision_transport_kind="NETWORK",
                   image_transport=http_transport(api), image_transport_kind="NETWORK")

    @property
    def evidence_origin(self) -> str:
        return "REAL_VLM" if self.vision_transport_kind == "NETWORK" else "SIMULATED_VLM_TRANSPORT"


class RealLoopRunner:
    def __init__(self, ws: Workspace, *, run_id: str, providers: RealProviders, config: RealLoopConfig | None = None):
        if not run_id.startswith("REAL"):
            raise Blocked("REAL_RUN_ID_PREFIX", "REAL loop run ids start with 'REAL'")
        self.ws, self.run_id, self.p, self.cfg = ws, run_id, providers, config or RealLoopConfig()
        self.dir = ws.root / "runs" / run_id
        self.dir.mkdir(parents=True, exist_ok=True)

    # ---- orchestration (same persistence contract as the synthetic runner) ------------------------
    # ---- dependency-hash stage cache (R12) -----------------------------------------------------------------
    def _external_inputs(self, st, stage: str) -> dict:
        """Everything OUTSIDE the previous stage's output that a stage consumes. A change here (or upstream) invalidates
        exactly this stage and, through its new output hash, only the dependants whose inputs actually change."""
        def recs(t, pred=lambda r: True):
            return sorted(digest(r) for r in st.list(t) if pred(r))
        brief = None
        a = st.get("ActiveBrief", "anchor")
        if a:
            ob = st.get("OriginalBrief", a["brief_id"])
            brief = ob["brief"] if ob else None
        lockp = self.ws.state_dir / "SOURCE_LOCK.json"
        ps = (self.ws.state_dir / "PROVIDER_STATE.json")
        prov = read_json(ps) if ps.exists() else {}
        mine = lambda r: r.get("run_id") == self.run_id
        x: dict = {}
        if stage == "S0":
            x = {"lock": digest(read_json(lockp)) if lockp.exists() else None, "roles": recs("SourceLock"),
                 "vision": prov.get("vision", {}).get("model_id"), "approvals": recs("SelectionApproval"),
                 "sixth": digest(st.get("SpecialIntroSelection", "REAL")),
                 "source_protocol_sha": PROTOCOL_SHA, "rationale_system_sha": digest(RATIONALE_SYSTEM)}
        elif stage == "S1":
            from ..vision.prompt import VISION_PROMPT_SHA
            x = {"sixth": digest(st.get("SpecialIntroSelection", "REAL")), "vision": prov.get("vision", {}).get("model_id"),
                 "source_protocol_sha": PROTOCOL_SHA, "vision_prompt_content_sha": VISION_PROMPT_SHA}
        elif stage == "S2":
            x = {"scope": digest((brief or {}).get("scope")),     # revision IDS only: closing a revision must not re-invalidate S2
                 "revisions": sorted(r["revision_id"] for r in st.list("ArtRevision") if mine(r)),
                 "source_protocol_sha": PROTOCOL_SHA, "qa_system_sha": digest(QA_SYSTEM),
                 "native_system_sha": digest(NATIVE_SYSTEM)}
        elif stage in ("S3", "S4"):
            x = {"decisions": sorted(f"{d['decision_id']}@{d['version']}:{d['status']}" for d in st.list("ConditionalVisualDecision")
                                     if not d.get("synthetic")), "consent": recs("ReferenceExemplarConsent")}
        elif stage == "S5":
            x = {"brief": digest({k: (brief or {}).get(k) for k in ("slots", "subjects", "world")}),
                 "runware": digest({k: prov.get("runware", {}).get(k) for k in ("model_air_id", "user_confirmed_model")})}
        elif stage == "S6":
            x = {"art_verdicts": recs("ArtApproval", mine)}
        elif stage in ("S7", "S8"):
            x = {"shot_plan": digest((brief or {}).get("shot_plan")), "asset_verdicts": recs("AssetApproval", mine)}
        elif stage == "S9":
            x = {"video_reviews": recs("VisualReview", lambda r: mine(r) and r.get("stage") == "video"),
                 "holdouts": digest(read_json(self.ws.state_dir / "HOLDOUTS.json")) if (self.ws.state_dir / "HOLDOUTS.json").exists() else None}
        return x

    # the upstream fields a stage actually consumes (volatile counters/version labels in an upstream output never invalidate)
    UPSTREAM_FIELDS = {"S3": ("decisions",), "S4": ("decisions",), "S5": ("skill_hash",), "S6": None, "S7": ("art_approval_id",)}

    def _input_key(self, st, stage: str) -> dict:
        i = STAGES.index(stage)
        up = None
        if i:
            t = st.get("LoopTransition", f"{self.run_id}:{STAGES[i - 1]}")
            fields = self.UPSTREAM_FIELDS.get(stage)
            if t and fields and t.get("status") == "COMPLETED":
                up = digest({f: (t.get("outputs") or {}).get(f) for f in fields})
            else:
                up = t.get("output_sha") if t else None
        ext = self._external_inputs(st, stage)
        return {"upstream_output_sha": up, "external": ext, "key": digest({"up": up, "ext": ext})}

    def run(self, *, until: str = "S9") -> dict:
        st = self.ws.store()
        self._invalidated: set = set()
        try:
            done = {t["stage"]: t for t in st.list("LoopTransition") if t["run_id"] == self.run_id and t["status"] == "COMPLETED"}
            trace = []
            for s in STAGES:
                ik = self._input_key(st, s)
                if s in done and done[s].get("input_key") == ik["key"]:
                    trace.append({"stage": s, "status": "COMPLETED", "resumed_from_store": True, "input_key": ik["key"][:16]})
                    if s == until:
                        break
                    continue
                if s in done:
                    old = done[s].get("input_key_detail") or {}
                    changed = sorted(k for k in set(old.get("external", {})) | set(ik["external"])
                                     if old.get("external", {}).get(k) != ik["external"].get(k))
                    if old.get("upstream_output_sha") != ik["upstream_output_sha"]:
                        changed.append("upstream_output")
                    self._invalidated.add(s)
                    st.put("StageInvalidation", f"{self.run_id}:{s}:{ik['key'][:12]}", {"run_id": self.run_id, "stage": s,
                                                                                          "previous_key": done[s].get("input_key"),
                                                                                          "new_key": ik["key"], "changed_inputs": changed,
                                                                                          "at": now_iso()})
                try:
                    status, out = getattr(self, f"_{s.lower()}")(st)
                except Blocked as b:
                    status, out = "STOPPED", {"stop_reason": b.code, "blocked": b.to_dict()}
                self._commit(st, s, status, out, ik)
                trace.append({"stage": s, "status": status, "reason": out.get("stop_reason"), "rerun_due_to_invalidation": s in self._invalidated})
                if status != "COMPLETED":
                    return {"run_id": self.run_id, "stopped_at": s, "reason": out.get("stop_reason"), "trace": trace}
                if s == until:
                    break
            return {"run_id": self.run_id, "completed_through": trace[-1]["stage"] if trace else None, "trace": trace}
        finally:
            st.close()

    def _commit(self, st, stage, status, outputs, ik=None):
        st.put("LoopTransition", f"{self.run_id}:{stage}", {"run_id": self.run_id, "stage": stage, "status": status,
                                                              "consumer": CONSUMERS[stage], "outputs": outputs, "mode": "REAL",
                                                              "evidence_origin": self.p.evidence_origin,
                                                              "input_key": (ik or {}).get("key"), "input_key_detail": ik,
                                                              "output_sha": digest(outputs),
                                                              "stop_reason": outputs.get("stop_reason"), "at": now_iso()})
        self.ws.update_state(current_stage=stage, last_completed_unit=f"{self.run_id}:{stage}:{status}")
        maybe_crash(f"real_after_{stage}")

    def _out(self, st, stage):
        t = st.get("LoopTransition", f"{self.run_id}:{stage}")
        if not t or t["status"] != "COMPLETED":
            raise Blocked("MISSING_UPSTREAM_STAGE", stage)
        return t["outputs"]

    # ---- shared services --------------------------------------------------------------------------
    def _lock(self) -> dict:
        return read_json(self.ws.state_dir / "SOURCE_LOCK.json")

    def _film(self, sha: str):
        from ..reference.frame_index import read_index
        from ..reference.frames import FrameCache
        lock = self._lock()
        s = next(x for x in lock["sources"] if x["sha256"] == sha)
        idx = read_index(self.ws.frames_dir / sha / "index.jsonl.gz")
        return s, idx, FrameCache(Path(lock["folder"]) / s["relative_path"], idx)

    def _src_request(self, vis, task_id: str, kind: str, pass_id: str, shape: str, images: list[dict], payload: dict, *,
                     selection: dict, controlling_problem: dict | None = None, active_cluster: dict | None = None,
                     competing: list | None = None, required_response: dict | None = None):
        """Every source-analysis request goes through vision.dispatch (P0 + Pn, typed binding, verified byte manifest) (R3 F06)."""
        from ..vision.dispatch import prepare_verified_request, submit_source_request
        prep = prepare_verified_request(pass_id=pass_id, kind=kind, shape=shape, source_shas=sorted({i["source_sha256"] for i in images}),
                                        selection=selection, images=images[: vis.caps.max_images_per_request], prior_boundary=None,
                                        active_cluster=active_cluster, controlling_problem=controlling_problem, competing_explanations=competing,
                                        required_response=required_response or {"strict_json": True},
                                        provider_profile={"model": vis.caps.model_id, "max_images": vis.caps.max_images_per_request,
                                                          "max_output_tokens": vis.max_output_tokens}, payload=payload)
        return submit_source_request(vis, task_id, prep), prep

    @staticmethod
    def _img(role: str, film: str, fr, *, wid: str | None = None, label: str, png: bytes | None = None, region: dict | None = None,
             w: int | None = None, h: int | None = None) -> dict:
        from ..vision.dispatch import image_entry
        return image_entry(role=role, png=png if png is not None else fr.png_bytes, witness_id=wid or f"{film[:16]}:{fr.presentation_index}",
                           source_sha256=film, frame_index=fr.presentation_index, pts=fr.pts_time, width=w or fr.width, height=h or fr.height,
                           raw_frame_sha256=fr.raw_sha256, region=region, label=label)

    def _vision(self):
        from ..vision.claude_adapter import ClaudeBatchVisionAdapter, default_caps
        from ..providers.authorization import AuthorizationRegistry
        from .human import provider_state
        v = provider_state(self.ws).get("vision")
        if not v:
            raise Blocked("VISION_MODEL_NOT_CONFIRMED", "run `vme provider confirm-vision --model <id> --by <name>`")
        caps = default_caps(v["model_id"], max_images=v["max_images_per_request"], verified=bool(v.get("discovered")))
        return ClaudeBatchVisionAdapter(caps, AuthorizationRegistry(self.ws.state_dir), self.ws.root / "providers" / "anthropic",
                                        client_factory=self.p.vision_client_factory, transport_kind=self.p.vision_transport_kind)

    def _brief(self, st) -> dict:
        a = st.get("ActiveBrief", "anchor")
        if not a:
            raise Blocked("NO_ORIGINAL_BRIEF", "add one with `vme brief add --file <brief.json> --by <name>`")
        return st.get("OriginalBrief", a["brief_id"])["brief"]

    # ---- S0: source roles, windows, VLM rationales, selection, human approval ----------------------------
    def _windows(self, idx: list[dict], survey: dict) -> list[tuple[int, int]]:
        """ALL candidate windows of a film (no convenience cap); the review ORDER spreads the first batch evenly."""
        fps = 1.0 / max(1e-6, (idx[-1]["pts_time"] - idx[0]["pts_time"]) / max(1, len(idx) - 1))
        mx, mn = int(self.cfg.max_window_s * fps), int(self.cfg.min_window_s * fps)
        out = []
        for sh in survey["shots"]:
            a, b = sh["start_frame_index"], sh["end_frame_index_inclusive"]
            while a <= b:
                e = min(b, a + mx - 1)
                if e - a + 1 >= mn:
                    out.append((a, e))
                a = e + 1
        return out

    @staticmethod
    def _review_order(n: int, first: int) -> list[int]:
        """Evenly spread first batch, then the remaining windows in stride order (deterministic expansion)."""
        if n <= 0:
            return []
        step = max(1.0, n / max(1, first))
        head = sorted({int(i * step) for i in range(min(first, n))})
        return head + [i for i in range(n) if i not in set(head)]

    def _s0(self, st):
        from ..reference.roles import role_status
        from ..selection.first15 import propose_selection
        rs = role_status(self.ws)
        if not rs["base_five_confirmed"]:
            return "STOPPED", {"stop_reason": "SOURCE_ROLES_UNCONFIRMED", "unconfirmed": rs["unconfirmed"], "resolutions": rs["resolutions"]}
        lock = self._lock()
        base = [s["sha256"] for s in lock["sources"] if s["role"] == "BASE_FILM"]
        vis = self._vision()
        made, rejected = 0, []
        batches = 0
        cov_ledger: dict = {}
        while True:
            batches += 1
            new_this_batch = 0
            for sha in base:
                new_this_batch += self._rationale_batch(st, vis, sha, batches, cov_ledger, rejected)
            made += new_this_batch
            cands = [c for c in st.list("CandidateSequence") if c.get("observer") == "VLM" and c["film_sha"] in base]
            lens = {sha: len(self._film(sha)[1]) for sha in base}
            man = propose_selection(cands, base, index_lengths=lens)
            unreviewed = sum(v["unreviewed"] for v in cov_ledger.values())
            if man["status"] == "PROPOSED_AWAITING_USER_REVIEW" or not unreviewed or new_this_batch == 0:
                break
        st.put("CandidateCoverageLedger", self.run_id, {"films": cov_ledger, "expansion_batches": batches,
                                                        "note": "candidates expand batch by batch until the 3-per-film selection "
                                                                "can be filled or every window is reviewed (R22)"})
        st.put("SelectedSequenceManifest", "REAL:15", man)
        out = {"candidates": len(cands), "new_rationales": made, "selection_status": man["status"], "selected": man.get("selected_count"),
               "manifest_sha": man.get("manifest_sha"), "rejected": len(man.get("rejected", [])), "expansion_batches": batches,
               "unreviewed_windows": unreviewed}
        if man["status"] != "PROPOSED_AWAITING_USER_REVIEW":
            return "STOPPED", {**out, "stop_reason": "SELECTION_INCOMPLETE"}
        if not st.get("SelectionApproval", man["manifest_sha"]):
            return "STOPPED", {**out, "stop_reason": "AWAITING_SELECTION_APPROVAL",
                               "human_next_step": f"vme selection approve --manifest-sha {man['manifest_sha']} --by <name>"}
        six = st.get("SpecialIntroSelection", "REAL")
        if not six or six.get("status") != "LOCKED":     # R13: the 15+1 study cannot start without the sixteenth interval
            return "STOPPED", {**out, "sixth": "PENDING_HUMAN_BOUNDARY_LOCK", "stop_reason": "SIXTH_BOUNDARY_NOT_LOCKED",
                               "human_next_step": "view the sixth-clip witness frames, then `vme sixth lock --start <i> --end <j> --by <name>`"}
        out["sixth"] = "LOCKED"
        return "COMPLETED", out

    def _rationale_batch(self, st, vis, sha: str, batch: int, cov_ledger: dict, rejected: list) -> int:
        from ..selection.first15 import validate_candidate
        sv = st.get("FilmSurvey", sha)
        if not sv:
            raise Blocked("NO_SURVEY", sha[:12])
        src, idx, cache = self._film(sha)
        wins = self._windows(idx, sv)
        order = self._review_order(len(wins), self.cfg.max_windows_per_film)
        todo = [wins[i] for i in order if not st.get("CandidateSequence", f"win_{sha[:10]}_{wins[i][0]}_{wins[i][1]}")]
        made = 0
        for (a, b) in todo[: self.cfg.max_windows_per_film]:
            if True:
                cid = f"win_{sha[:10]}_{a}_{b}"
                keys = [a, (a + b) // 2, b]
                imgs = [self._img("TARGET", sha, cache.frame(k), label=f"FRAME {sha[:16]}:{k} pts_time={idx[k]['pts_time']:.6f}") for k in keys]
                tid = custom_id_for("window_rationale", {"source_sha": sha, "window": [a, b], "frames": [idx[k]["frame_content_sha256"] for k in keys],
                                                         "model": vis.caps.model_id, "system_sha": digest(RATIONALE_SYSTEM)})
                resp, _prep = self._src_request(vis, tid, "window_rationale", "P2", RATIONALE_SHAPE, imgs,
                                                {"window": {"start": a, "end": b}, "frames": keys, "window_index": made},
                                                selection={"film_sha256": sha, "candidate_window": [a, b]})
                cand = {"film_sha": sha, "candidate_id": cid, "start_frame_index": a, "end_frame_index_inclusive": b,
                        "start_pts": idx[a]["pts_time"], "end_pts": idx[b]["pts_time"], "actual_frame_count": b - a + 1,
                        "key_witness_frame_ids": keys, "observer": "VLM", "evidence_origin": self.p.evidence_origin,
                        **{k: resp.get(k) for k in ("whole_visual_quality_statement", "selection_role_candidates", "opportunities",
                                                    "visible_proof_for_each_opportunity", "actor_class", "new_question_contributed",
                                                    "known_limitations")},
                        "content_label": resp.get("content_label") or "MAIN_FILM", "observer_rank": 10, "raw_receipt": resp.get("receipt")}
                why = validate_candidate(cand, len(idx))
                if why:
                    rejected.append({"candidate_id": cid, "reasons": why})
                st.put("CandidateSequence", cid, cand)
                made += 1
        reviewed = sum(1 for (a, b) in wins if st.get("CandidateSequence", f"win_{sha[:10]}_{a}_{b}"))
        cov_ledger[sha] = {"windows_total": len(wins), "reviewed": reviewed, "unreviewed": len(wins) - reviewed,
                           "unreviewed_status": "UNREVIEWED_CANDIDATES_NOT_CLAIMED_ABSENT"}
        return made

    # ---- S1: every frame of the selected windows, witnesses, native-detail follow-ups ------------------
    def _s1(self, st):
        from ..vision.runner import PacketRunner, plan_packets, coverage_for_range
        from ..investigation.evidence import build_event_graph
        man = st.get("SelectedSequenceManifest", "REAL:15")
        intervals = [(s["film_sha"], s["start_frame_index"], s["end_frame_index_inclusive"], s["candidate_id"]) for s in man["selected"]]
        six = st.get("SpecialIntroSelection", "REAL")
        if not six or six.get("status") != "LOCKED":
            return "STOPPED", {"stop_reason": "SIXTH_BOUNDARY_NOT_LOCKED", "note": "the initial 15+1 study never runs as 15 (R13)"}
        intervals.append((six["clip_sha256"], six["start_frame_index"], six["end_frame_index_inclusive"], "SIXTH"))
        vis = self._vision()
        pass_id = f"{self.run_id}-L0"
        cov_all, pending, wit, native = {}, [], 0, 0
        audio_studies: list = []
        pending_native: list = []
        for film, a, b, seq in intervals:
            src, idx, cache = self._film(film)
            per = self._budgeted_targets(vis)
            plans = plan_packets(idx, a, b, film_sha=film, pass_id=pass_id, cluster_id=seq, model_version=vis.caps.model_id,
                                 max_images=vis.caps.max_images_per_request, target_per_packet=per)
            pr = PacketRunner(st, self.ws.vision_dir, idx, cache, vis, source_is_synthetic=False,
                              active_questions=[{"question_id": f"QC-{seq}", "text": "Which visible relations make this window's art and "
                                                 "motion work, and what must a producer decide for a NEW subject?"}])
            # R3-C06/C08: the LOCAL audio study runs first; EVERY onset (mapped to a frame by native PTS) is put in the packet manifest
            arec = self._audio_signal(st, film, seq, a, b, idx)
            for k in arec.get("onset_frame_indices", []):
                pr.audio_events[(film, k)] = [{"kind": "AUDIO_ONSET", "source": "LOCAL_SIGNAL_ANALYSIS", "frame": k,
                                               "pts_time": idx[k]["pts_time"]}]
            pr.register(plans)
            res = pr.resume(plans)
            res = self._split_truncated(st, pr, plans, res, idx, film, pass_id, seq, vis)
            not_done = {k: v for k, v in res["results"].items() if v != "SEMANTIC_COMMITTED"}
            if not_done:
                pending.append({"sequence": seq, "packets": not_done})
                continue
            cov = coverage_for_range(st, film, pass_id, a, b)
            cov_all[seq] = cov
            obs = []
            for p in plans:
                fp = self.ws.vision_dir / p.pass_id / p.packet_id / "frames.jsonl"
                obs += [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines() if l.strip()]
            st.put("CrossFrameEventGraph", f"{self.run_id}:{seq}", build_event_graph(obs))
            wit += self._extract_witnesses(st, film, seq, obs, idx)
            audio_studies.append(self._study_audio(st, film, seq, a, b, idx, obs, arec))
            self._register_phenomena(st, film, seq, obs)
            nf = self._native_followups(st, vis, film, seq, obs, idx, cache, src)
            native += nf["done"]
            if nf["pending"]:
                pending_native.extend(nf["pending"])
            au = self._audit_sequence(st, vis, film, seq, a, b, obs, idx, cache, arec)     # R3-C08 independent auditor + C07 reinspection
            native += au["reinspected"]
            if au["pending"]:
                pending_native.extend(au["pending"])
        if pending:
            codes = {s for p in pending for s in p["packets"].values()}
            reason = "BLOCKED_AUTHORIZATION" if "BLOCKED_CONSENT" in codes else "PROVIDER_PENDING_OR_REINSPECTION"
            return "STOPPED", {"stop_reason": reason, "pending": pending[:5], "states": sorted(codes)}
        incomplete = [k for k, v in cov_all.items() if not v["complete"]]
        if incomplete:
            return "STOPPED", {"stop_reason": "SELECTED_RANGE_NOT_FULLY_SEEN", "sequences": incomplete}
        if pending_native:
            st.put("PendingNativeFollowups", self.run_id, {"pending": pending_native, "budget": self.cfg.native_followup_budget})
            return "STOPPED", {"stop_reason": "NATIVE_FOLLOWUP_BUDGET_EXHAUSTED", "pending": len(pending_native),
                               "exact_next_input": pending_native[0], "human_next_step": "raise the authorized budget or accept the open list"}
        return "COMPLETED", {"sequences": len(intervals), "frames_verified": sum(v["verified"] for v in cov_all.values()),
                             "statuses": sorted({s for v in cov_all.values() for s in v["statuses"]}), "witnesses": wit,
                             "native_followups": native, "sixth_included": any(i[3] == "SIXTH" for i in intervals),
                             "audio_studies": {x["sequence_id"]: x["status"] for x in audio_studies},
                             "evidence_origin": self.p.evidence_origin}

    def _budgeted_targets(self, vis) -> int:
        """R3 F18: never pack more targets than the per-target response budget allows."""
        room = int(vis.max_output_tokens) - self.cfg.packet_overhead_tokens
        cap = max(1, room // max(1, self.cfg.per_target_output_tokens))
        return max(1, min(self.cfg.target_per_packet, cap))

    def _split_truncated(self, st, pr, plans, res, idx, film, pass_id, seq, vis) -> dict:
        """A truncated packet (max_tokens) is never accepted or silently dropped: it is SUPERSEDED by smaller contiguous packets covering
        exactly the same targets (new content-addressed ids), down to single frames; what still truncates stays NEEDS_REINSPECTION."""
        from ..vision.runner import plan_packets
        by_id = {p.packet_id: p for p in plans}
        results = dict(res["results"])
        for _round in range(self.cfg.max_split_rounds):
            trunc = [pid for pid, s_ in results.items() if s_ == "NEEDS_REINSPECTION" and pid in by_id
                     and (st.conn.execute("SELECT error FROM packets WHERE packet_id=?", (pid,)).fetchone() or [""])[0] == "PROVIDER_OUTPUT_TRUNCATED"
                     and len(by_id[pid].target_indices) > 1]
            if not trunc:
                break
            for pid in trunc:
                old = by_id[pid]
                size = max(1, len(old.target_indices) // 2)
                sub = plan_packets(idx, old.target_indices[0], old.target_indices[-1], film_sha=film, pass_id=pass_id, cluster_id=seq,
                                   model_version=vis.caps.model_id, max_images=vis.caps.max_images_per_request, target_per_packet=size)
                with st.tx() as c:
                    c.execute("UPDATE packets SET state='SUPERSEDED_BY_SPLIT', updated_at=? WHERE packet_id=?", (now_iso(), pid))
                    st.event("PACKET_SPLIT", pid, {"into": [x.packet_id for x in sub], "reason": "PROVIDER_OUTPUT_TRUNCATED"}, conn=c)
                results.pop(pid)
                pr.register(sub)
                for x in sub:
                    by_id[x.packet_id] = x
                    results[x.packet_id] = pr.run(x)
        return {**res, "results": results}

    def _audio_signal(self, st, film, seq, a, b, idx) -> dict:
        """R3 F14/C06: local decode of the selected interval's audio. The envelope uses the interval's OWN median frame duration, and
        every onset TIME is mapped to the frame whose native PTS is nearest (variable-frame-rate safe). Nothing is uploaded."""
        from ..reference.audio import study_interval
        lock = self._lock()
        s = next(x for x in lock["sources"] if x["sha256"] == film)
        d = sorted(idx[k + 1]["pts_time"] - idx[k]["pts_time"] for k in range(a, b) if k + 1 < len(idx)) or [1 / 30.0]
        fps = 1.0 / max(1e-6, d[len(d) // 2])
        t0 = idx[a]["pts_time"]
        rec = study_interval(Path(lock["folder"]) / s["relative_path"], start_pts=t0, end_pts=idx[b]["pts_time"], fps=fps,
                             film_sha256=film, sequence_id=seq)
        frames = []
        for t in rec.get("onset_times_s", []):
            k = min(range(a, b + 1), key=lambda i: (abs(idx[i]["pts_time"] - (t0 + t)), i))
            frames.append(k)
        rec["onset_frame_indices"] = sorted(set(frames))
        rec["frame_mapping"] = "NEAREST_NATIVE_PTS"
        st.put("SourceAudioStudy", f"{self.run_id}:{seq}", rec)
        return rec

    def _study_audio(self, st, film, seq, a, b, idx, obs, rec: dict | None = None) -> dict:
        """R3 F14: onsets that coincide with a committed full frame become AUDIO_SIGNAL witnesses — ALL of them (R3-C06), each bound
        to its aligned full-frame parent. No meaning is inferred from energy; nothing is uploaded or copied."""
        rec = rec if rec is not None else self._audio_signal(st, film, seq, a, b, idx)
        changed = {int(str(o["frame_id"]).split(":")[1]) for o in obs if o.get("changed_since_prior_frame")}
        full = {w["frame_start"]: w["witness_id"] for w in st.list("Witness")
                if w["film_sha256"] == film and w.get("sequence_id") == seq and w.get("evidence_kind") == "FULL_FRAME"}
        for j, k in enumerate(rec.get("onset_frame_indices", [])):
            if not a <= k <= b:
                continue
            near = sorted((x for x in full if abs(x - k) <= 1), key=lambda x: (abs(x - k), x))
            if not near:            # no committed full-frame witness at this time: the onset stays unlinked, never fabricated
                rec.setdefault("unlinked_onsets", []).append(k)
                continue
            parent = full[near[0]]
            wid = f"W-{film[:10]}-{k}-audio-{j}"
            vis_change = any(abs(k - c) <= 1 for c in changed)
            st.put("Witness", wid, {"witness_id": wid, "film_sha256": film, "sequence_id": seq, "frame_start": k, "frame_end": k,
                                    "evidence_kind": "AUDIO_SIGNAL", "observer": "LOCAL_SIGNAL_ANALYSIS", "parent_full_frame_witness": parent,
                                    "visible_relation": (f"an audio onset at frame {k} occurs together with a recorded visible change of the frame relative to the previous frame"
                                                         if vis_change else f"an audio onset at frame {k} occurs while the frame stays unchanged relative to the previous frame"),
                                    "image_sha256": idx[k]["frame_content_sha256"], "region": None, "subject_class": None,
                                    "scene_specific_facts": [], "observation_ids": [f"{film[:16]}:{k}"],
                                    "limits": "local RMS onset only; meaning unstudied", "dimensions": ["VISUAL_AUDIO_TIMING"],
                                    "pts_time": idx[k]["pts_time"], "evidence_origin": "LOCAL_SIGNAL_ANALYSIS", "audio_study": f"{self.run_id}:{seq}"})
        st.put("SourceAudioStudy", f"{self.run_id}:{seq}", rec)
        return rec

    def _extract_witnesses(self, st, film, seq, obs, idx) -> int:
        n = 0
        for o in obs:
            k = int(str(o["frame_id"]).split(":")[1])
            for i, r in enumerate(o.get("visible_design_relations") or []):
                if not isinstance(r, dict) or is_vague_statement(r.get("relation", "")):
                    continue
                wid = f"W-{film[:10]}-{k}-{i}"
                if st.get("Witness", wid):
                    continue
                st.put("Witness", wid, {"witness_id": wid, "film_sha256": film, "sequence_id": seq, "frame_start": k, "frame_end": k,
                                        "evidence_kind": "FULL_FRAME", "observer": "VLM", "visible_relation": r["relation"],
                                        "image_sha256": idx[k]["frame_content_sha256"], "region": r.get("region"),
                                        "subject_class": o.get("subject_class"), "scene_specific_facts": o.get("source_fact_statements") or [],
                                        "observation_ids": [o["frame_id"]], "limits": "; ".join(o.get("confidence_limitations") or []) or "VLM observation",
                                        "dimensions": [d for d in (r.get("dimensions") or []) if isinstance(d, str)],
                                        "pts_time": idx[k]["pts_time"], "evidence_origin": self.p.evidence_origin})
                n += 1
        return n

    def _native_budget_used(self, st) -> int:
        return int((st.get("NativeFollowupBudget", self.run_id) or {}).get("used", 0))

    def _native_followups(self, st, vis, film, seq, obs, idx, cache, src) -> dict:
        """EVERY model-requested native crop is performed until the authorized run budget is used; the rest are kept as an
        explicit pending list (exact next input), never silently dropped (R11; no per-sequence cap)."""
        from ..reference.frames import native_crop
        done, pending = 0, []
        for o in obs:
            for f in o.get("native_detail_followups") or []:
                if not isinstance(f, dict) or not f.get("region"):
                    continue
                k = int(str(o["frame_id"]).split(":")[1])
                r = f["region"]
                wid = f"W-{film[:10]}-{k}-native-{r['x']}-{r['y']}"
                if st.get("Witness", wid) or st.get("Witness", f"{wid}-0"):
                    done += 1
                    continue
                if self._native_budget_used(st) >= self.cfg.native_followup_budget:
                    pending.append({"film": film, "frame": k, "region": r, "reason": f.get("reason"), "sequence": seq})
                    continue
                full = cache.frame(k)
                crop = native_crop(full, int(r["x"]), int(r["y"]), int(r["w"]), int(r["h"]))
                nb = [cache.frame(j) for j in (max(0, k - 1), min(len(idx) - 1, k + 1))]
                imgs = [self._img("TARGET", film, full, label=f"FULL {film[:16]}:{k}"),
                        self._img("NATIVE_CROP", film, full, wid=f"{film[:16]}:{k}:crop:{r['x']},{r['y']},{r['w']},{r['h']}", png=crop.png_bytes,
                                  region=r, w=crop.output_width, h=crop.output_height,
                                  label=f"NATIVE_CROP {film[:16]}:{k} x={r['x']} y={r['y']} w={r['w']} h={r['h']}")]
                imgs += [self._img("NEIGHBOUR", film, x, label=f"NEIGHBOUR {film[:16]}:{x.presentation_index}") for x in nb if x.presentation_index != k]
                tid = custom_id_for("native_detail", {"source_sha": film, "frame": k, "region": r, "crop_sha": crop.crop_png_sha256,
                                                      "neighbours": [x.png_sha256 for x in nb], "model": vis.caps.model_id,
                                                      "system_sha": digest(NATIVE_SYSTEM)})
                resp, _prep = self._src_request(vis, tid, "native_detail", "P5", NATIVE_SHAPE, imgs, {"reason": f.get("reason"), "frame": k},
                                                selection={"film_sha256": film, "sequence_id": seq, "frame": k})
                for i, rel in enumerate(resp.get("relations") or []):
                    if is_vague_statement(rel.get("relation", "")):
                        continue
                    st.put("Witness", f"{wid}-{i}", {"witness_id": f"{wid}-{i}", "film_sha256": film, "sequence_id": seq, "frame_start": k,
                                                     "frame_end": k, "evidence_kind": "NATIVE_CROP", "observer": "VLM",
                                                     "visible_relation": rel["relation"], "image_sha256": crop.crop_png_sha256, "region": r,
                                                     "parent_full_frame_witness": f"W-{film[:10]}-{k}-0",
                                                     "temporal_neighbor_witnesses": [f"W-{film[:10]}-{x.presentation_index}-0" for x in nb],
                                                     "subject_class": o.get("subject_class"), "scene_specific_facts": [], "observation_ids": [o["frame_id"]],
                                                     "limits": "native 720p crop", "dimensions": rel.get("dimensions") or [],
                                                     "pts_time": idx[k]["pts_time"], "evidence_origin": self.p.evidence_origin})
                with st.tx() as c:
                    c.execute("INSERT OR REPLACE INTO frame_vision(film_sha256,frame_index,pass_id,status,packet_id,image_sha,observation_sha,updated_at) "
                              "VALUES(?,?,?,?,?,?,?,?)", (film, k, f"{self.run_id}-native", "NATIVE_DETAIL_REVIEWED" if self.p.evidence_origin == "REAL_VLM"
                                                          else "SIMULATED_NATIVE_DETAIL", wid, crop.crop_png_sha256, digest(resp), now_iso()))
                st.put("NativeFollowupBudget", self.run_id, {"used": self._native_budget_used(st) + 1, "budget": self.cfg.native_followup_budget})
                done += 1
        return {"done": done, "pending": pending}

    def _audit_sequence(self, st, vis, film, seq, a, b, obs, idx, cache, arec) -> dict:
        """R3-C08 independent auditor + R3-C07 mandatory targeted reinspection. Expected phenomena come from local detectors and a P5
        adversarial sweep that is NOT shown the P1 observations; each one the observations do not explain is reinspected natively
        (full native frame + neighbours) whether or not the observer asked; what reinspection cannot explain stays a NAMED gap."""
        from ..investigation.auditor import (ADVERSARIAL_SHAPE, adversarial_expectations, local_expectations, reinspection_resolves)
        from ..vision.contracts import audit_phenomenon_coverage
        from ..reference.frames import native_crop
        expected = local_expectations(film=film, seq=seq, a=a, b=b, survey=st.get("FilmSurvey", film),
                                      audio_onsets=arec.get("onset_frame_indices", []))
        step = max(1, (b - a) // max(1, vis.caps.max_images_per_request - 2))
        ks = sorted({a, b, *range(a, b + 1, step)})[: vis.caps.max_images_per_request]
        frs = [cache.frame(k) for k in ks]
        imgs = [self._img("TARGET", film, fr, label=f"FULL {film[:16]}:{fr.presentation_index}") for fr in frs]
        tid = custom_id_for("adversarial_sweep", {"source_sha": film, "interval": [a, b], "frames": [fr.png_sha256 for fr in frs],
                                                  "model": vis.caps.model_id, "system_sha": digest(ADVERSARIAL_SYSTEM)})
        resp, _p = self._src_request(vis, tid, "adversarial_sweep", "P5", ADVERSARIAL_SHAPE, imgs,
                                     {"interval": [a, b], "frames": ks, "prior_observations_withheld": True},
                                     selection={"film_sha256": film, "sequence_id": seq, "interval": [a, b]})
        adv, rejected = adversarial_expectations(resp, film=film, seq=seq, a=a, b=b)
        expected += adv
        gaps = audit_phenomenon_coverage(obs, expected)
        resolved, open_, pending, done = [], [], [], 0
        for g in gaps:
            k = (int(g["interval"][0]) + int(g["interval"][1])) // 2
            if self._native_budget_used(st) >= self.cfg.native_followup_budget:
                pending.append({"film": film, "frame": k, "region": None, "reason": g["gap"], "sequence": seq, "phenomenon_id": g["phenomenon_id"]})
                open_.append(g)
                continue
            full = cache.frame(k)
            r = {"x": 0, "y": 0, "w": full.width, "h": full.height}
            crop = native_crop(full, 0, 0, full.width, full.height)
            nb = [cache.frame(j) for j in (max(0, k - 1), min(len(idx) - 1, k + 1)) if j != k]
            wid = f"W-{film[:10]}-{k}-reinspect-{digest(g['phenomenon_id'])[:8]}"
            ims = [self._img("TARGET", film, full, label=f"FULL {film[:16]}:{k}"),
                   self._img("NATIVE_CROP", film, full, wid=f"{film[:16]}:{k}:crop:0,0,{full.width},{full.height}", png=crop.png_bytes, region=r,
                             w=crop.output_width, h=crop.output_height, label=f"NATIVE_CROP {film[:16]}:{k} x=0 y=0 w={full.width} h={full.height}")]
            ims += [self._img("NEIGHBOUR", film, x, label=f"NEIGHBOUR {film[:16]}:{x.presentation_index}") for x in nb]
            tid2 = custom_id_for("native_detail", {"source_sha": film, "frame": k, "gap": g["phenomenon_id"], "crop_sha": crop.crop_png_sha256,
                                                   "model": vis.caps.model_id, "system_sha": digest(NATIVE_SYSTEM)})
            resp2, _p2 = self._src_request(vis, tid2, "native_detail", "P5", NATIVE_SHAPE, ims,
                                           {"reason": f"MANDATORY reinspection: {g['gap']}", "frame": k,
                                            "gap": {"phenomenon_id": g["phenomenon_id"], "kind": g["kind"], "interval": g["interval"]}},
                                           selection={"film_sha256": film, "sequence_id": seq, "frame": k})
            st.put("NativeFollowupBudget", self.run_id, {"used": self._native_budget_used(st) + 1, "budget": self.cfg.native_followup_budget})
            done += 1
            ok = reinspection_resolves(g["kind"], resp2)
            for i, rel in enumerate(ok):
                st.put("Witness", f"{wid}-{i}", {"witness_id": f"{wid}-{i}", "film_sha256": film, "sequence_id": seq, "frame_start": k, "frame_end": k,
                                                 "evidence_kind": "NATIVE_CROP", "observer": "VLM", "visible_relation": rel["relation"],
                                                 "image_sha256": crop.crop_png_sha256, "region": r, "parent_full_frame_witness": f"W-{film[:10]}-{k}-0",
                                                 "temporal_neighbor_witnesses": [f"W-{film[:10]}-{x.presentation_index}-0" for x in nb],
                                                 "subject_class": None, "scene_specific_facts": [], "observation_ids": [f"{film[:16]}:{k}"],
                                                 "limits": f"mandatory reinspection for {g['phenomenon_id']}", "dimensions": rel.get("dimensions") or [],
                                                 "pts_time": idx[k]["pts_time"], "evidence_origin": self.p.evidence_origin})
            (resolved if ok else open_).append({**g, "reinspection_task": tid2, "witnesses": [f"{wid}-{i}" for i in range(len(ok))]})
        audit = {"run_id": self.run_id, "sequence_id": seq, "film_sha256": film, "interval": [a, b], "expected": expected,
                 "sources": sorted({e["source"] for e in expected}), "adversarial_rejected": rejected, "resolved_by_reinspection": resolved,
                 "gaps": [{**g, "gap": g["gap"]} for g in open_], "observer_was_not_the_auditor": True}
        st.put("PhenomenonAudit", f"{self.run_id}:{seq}", audit)
        return {"reinspected": done, "pending": pending, "open": len(open_)}

    def _register_phenomena(self, st, film, seq, obs) -> None:
        """A28 pass 1/6: salient visual behaviour the vision model could not place in the atlas becomes a VisualPhenomenon
        that completeness must explain or explicitly leave unresolved (not hidden by a filled category)."""
        for o in obs:
            for i, ph in enumerate(o.get("unexplained_phenomena") or []):
                if not isinstance(ph, dict) or not ph.get("phenomenon"):
                    continue
                k = int(str(o["frame_id"]).split(":")[1])
                dims = sorted(d for d in ph.get("connected_dimensions", []) if isinstance(d, str))
                pid = "VP-" + digest([" ".join(ph["phenomenon"].lower().split()), dims])[:14]    # same behaviour seen again = same phenomenon
                prev = st.get("VisualPhenomenon", pid)
                sighting = {"film_sha256": film, "sequence_id": seq, "frame_index": k, "frame_id": o["frame_id"], "region": ph.get("region")}
                if prev:
                    if sighting not in prev["sightings"]:
                        st.put("VisualPhenomenon", pid, {**prev, "sightings": prev["sightings"] + [sighting]})
                    continue
                st.put("VisualPhenomenon", pid, {"phenomenon_id": pid, "phenomenon": ph["phenomenon"], "film_sha256": film, "sequence_id": seq,
                                                 "frame_index": k, "frame_id": o["frame_id"], "why": ph.get("why", ""),
                                                 "connected_dimensions": dims, "sightings": [sighting],
                                                 "region": ph.get("region"), "status": "UNEXPLAINED", "evidence_origin": self.p.evidence_origin})

    # ---- S2/S3: multi-gap investigation with evidence-backed answers and decision authoring -------------
    def _ledger(self, st, plan: dict, frame_state: str) -> dict:
        from ..style.coverage import new_ledger, set_dimension, set_relation, DIMENSIONS
        wits = st.list("Witness")
        rels = st.list("ObservedRelation")
        decs = [d for d in st.list("ConditionalVisualDecision") if d.get("status") != "RESEARCH_ONLY" and not d.get("synthetic")]
        L = new_ledger(f"{self.run_id}-scope", sorted({w["sequence_id"] for w in wits}))
        L["frame_coverage_state"] = frame_state
        seen: dict[str, list] = {}
        for w in wits:
            for d in w.get("dimensions", []):
                seen.setdefault(d, []).append(w)
        for r in rels:
            for d in r["dimensions"]:
                seen.setdefault(d, []).append({"film_sha256": "", "sequence_id": r["relation_id"], "frame_start": 0, "frame_end": 0})
        ev = lambda ws_: [{"source_hash": w.get("film_sha256") or "RELATION", "sequence_id": w["sequence_id"], "frame_start": w["frame_start"],
                           "frame_end": w["frame_end"], "evidence_kind": "FULL_FRAME"} for w in ws_[:3]]
        from ..style.coverage import owns
        for d in DIMENSIONS:
            owners = [x for x in decs if d in x.get("dimension_tags", [])]
            needing = [c for c in plan["choices"] if d in c["dimensions"]]
            unowned = [c["choice_id"] for c in needing if not any(owns(x, c["choice_id"], c["dimensions"]) for x in decs)]
            if owners and unowned and d in seen:
                set_dimension(L, d, "RELEVANT_UNKNOWN", evidence=ev(seen[d]), why_relevant="some production choices using this dimension are owned, "
                              "others are not (category presence is not coverage)", missing_decisions=unowned)
            elif owners:
                ops = sorted({o for x in owners for b in x["branches"] for o in b["operation_node_ids"]})
                set_dimension(L, d, "RELEVANT_SUPPORTED", evidence=ev(seen.get(d, [])), why_relevant="every production choice using it is owned",
                              production_consumers=ops)
            elif d in seen and d not in plan["required_dimensions"]:
                set_dimension(L, d, "NOT_APPLICABLE_WITH_REASON", evidence=ev(seen[d]), why_relevant="observed in sources",
                              inapplicability_reason="observed in selected windows but not required by this original scope "
                                                     "(production-decision coverage is scoped; kept as evidence for later scopes)")
            elif d in seen:
                set_dimension(L, d, "RELEVANT_UNKNOWN", evidence=ev(seen[d]), why_relevant="observed in selected windows; no decision yet",
                              missing_decisions=[c["choice_id"] for c in needing] or [f"decision for {d}"])
            elif d in plan["required_dimensions"]:
                set_dimension(L, d, "PENDING_SOURCE", evidence=[], why_relevant="required by the original scope, not observed in selected windows")
            else:
                set_dimension(L, d, "NOT_APPLICABLE_WITH_REASON", evidence=[], why_relevant="not required by scope",
                              inapplicability_reason="not required by the original scope and not observed")
        for j in plan["joint_choices"]:
            dims = set(j["dimensions"])
            # R10: a joint relation is SUPPORTED only by actual witnesses that show ALL participating dimensions together
            wids = sorted({w["witness_id"] for w in wits if dims <= set(w.get("dimensions", []))} |
                          {x for r in rels if dims <= set(r["dimensions"]) for x in r.get("witness_ids", [])})
            ev_ = [{"witness_id": x} for x in wids[:12]]
            set_relation(L, j["joint_id"], j["dimensions"], "SUPPORTED" if wids else "UNKNOWN", evidence=ev_,
                         producing_effect="joint construction must be decided together", missing_decisions=[] if wids else [j["joint_id"]])
        return L

    def _phenomena_gaps(self, st, plan: dict) -> list[dict]:
        """Unexplained VisualPhenomenon records relevant to the original scope → explicit gaps (not category checkmarks)."""
        decs = [d for d in st.list("ConditionalVisualDecision") if not d.get("synthetic") and d.get("status") != "RESEARCH_ONLY"]
        explained = {p for d in decs for p in d.get("owned_choice_ids", []) if p.startswith("VP-")}
        out = []
        for ph in st.list("VisualPhenomenon"):
            if ph["phenomenon_id"] in explained or ph.get("status") == "SCOPED_OUT_WITH_REASON":
                continue
            if not set(ph["connected_dimensions"]) & set(plan["required_dimensions"]):
                continue
            out.append(ph)
        return out

    def _s2(self, st):
        from ..style.coverage import OriginalScope, review_visual_model_completeness, reverse_plan, cluster_gaps
        from ..investigation.controller import ActiveArtProblem, LoopController, ProblemContext
        from ..skills.operators import registered
        from ..style.authoring import author_decision, production_choice_id
        s1 = self._out(st, "S1")
        brief = self._brief(st)
        if not brief.get("scope"):
            raise Blocked("BRIEF_WITHOUT_SCOPE", "the original brief must declare its typed scope")
        scope = OriginalScope(scope_id=brief["brief_id"], **brief["scope"])
        plan = reverse_plan(scope)
        vis = self._vision()
        cs = self._character_study(st, vis)                  # Addendum 29: the drawn entity BEFORE any character rule
        if cs["invalid"]:
            return "STOPPED", {"stop_reason": "CHARACTER_SOURCE_STUDY_INCOMPLETE", "dossiers": cs["invalid"][:5]}
        frame_state = "ALL_TARGET_FRAMES_SEEN" if s1["frames_verified"] else "PARTIAL"
        attempts: dict[str, int] = {}
        trace = st.get("RealInvestigationTrace", self.run_id) or {"steps": []}
        for _ in range(self.cfg.max_questions):
            L = self._ledger(st, plan, frame_state)
            decs = [d for d in st.list("ConditionalVisualDecision") if not d.get("synthetic")]
            phen = self._phenomena_gaps(st, plan)
            rev = review_visual_model_completeness(L, scope, decs, registered())
            for ph in phen:      # unexplained phenomena are gaps of their own, owned by the phenomenon id
                rev["gap_details"].append({"gap_id": f"GP_{ph['phenomenon_id']}", "kind": "MISSING_DECISION", "salience": "HIGH",
                                           "what": f"unexplained phenomenon {ph['phenomenon']!r} at {ph['frame_id']}",
                                           "dimensions": sorted(set(ph["connected_dimensions"]) & set(plan["required_dimensions"])),
                                           "choice_id": ph["phenomenon_id"], "phenomenon_id": ph["phenomenon_id"],
                                           "conditions": {}})
            if phen:
                from ..style.coverage import choose_controlling_gap
                rev["controlling_gap"] = choose_controlling_gap(rev["gap_details"])
                rev["review"]["image_trial_ready"] = False
                rev["review"]["state"] = "BLOCKED_MISSING_STYLE_DECISION" if rev["review"]["state"] == "READY_FOR_ORIGINAL_IMAGE_TRIAL" \
                    else rev["review"]["state"]
                rev["review"]["gaps"] = rev["review"]["gaps"] + [g["gap_id"] for g in rev["gap_details"] if g["gap_id"].startswith("GP_")]
            st.put("CoverageReview", self.run_id, rev)
            st.put("VisualModelCoverageLedger", self.run_id, L)
            # a decision reopened by a human art rejection is re-investigated FIRST and keeps its identity, even if other
            # decisions still cover its choices — rejection must revise the responsible choice, not silently drop it (R12/ST28-21)
            reopened = [d for d in decs if str(d.get("research_only_reason", "")).startswith("REOPENED_BY_HUMAN")]
            forced = reopened[0] if reopened else None
            if forced is None and rev["review"]["image_trial_ready"]:
                for r_ in st.list("ArtRevision"):
                    if r_["run_id"] == self.run_id and r_["status"] == "OPEN":
                        st.put("ArtRevision", r_["revision_id"], {**r_, "status": "CLOSED", "closed_at": now_iso()})
                st.put("RealInvestigationTrace", self.run_id, trace)
                return "COMPLETED", {"coverage_state": rev["review"]["state"], "questions": len(trace["steps"]),
                                     "decisions": [d["decision_id"] for d in decs if d["status"] != "RESEARCH_ONLY"],
                                     "resolved_gaps": sorted({s["gap_signature"] for s in trace["steps"] if s.get("decision_changed")})}
            if forced is not None:
                rev["controlling_gap"] = {"gap_id": f"GR_{forced['decision_id']}", "kind": "MISSING_DECISION", "salience": "HIGH",
                                          "what": "human-rejected original art: " + "; ".join(x.get("symptom", "") for x in forced.get("reopened_defects", [])),
                                          "dimensions": forced["dimension_tags"], "choice_id": (forced.get("owned_choice_ids") or [None])[0],
                                          "reopened_decision_id": forced["decision_id"], "conditions": {}}
            g = rev["controlling_gap"]
            sig = f"{g['kind']}|{'+'.join(g['dimensions'])}|{g.get('joint_id') or g.get('choice_id')}"
            st.put("GapQueue", self.run_id, {"controlling_gap": g, "queued": [x for x in rev["gap_details"] if x["gap_id"] != g["gap_id"]],
                                             "clusters": rev.get("clusters"), "at": now_iso()})
            if g["kind"] in ("MISSING_OPERATION", "PROMPT_AUTHORITY") or (g["kind"] == "MISSING_SOURCE" and g.get("source_scope") == "frames"):
                # engineering / frame-coverage faults route to engineering, not to a new source-art question (A28 P3)
                st.put("RealInvestigationTrace", self.run_id, trace)
                return "STOPPED", {"stop_reason": f"BLOCKER_{g['kind']}", "gap": g, "ticket": rev["question_ticket"], "questions": len(trace["steps"])}
            if g["kind"] in ("MISSING_SOURCE", "CONTRADICTED"):
                attempts[sig] = attempts.get(sig, 0) + 1
                r = self._reinspect(st, vis, g, attempts[sig], trace)
                st.put("RealInvestigationTrace", self.run_id, trace)
                if r["status"] != "NEW_WITNESSES":
                    return "STOPPED", {"stop_reason": "SOURCE_UNKNOWN_REMAINS_UNRESOLVED" if r["status"] == "NO_NEW_EVIDENCE" else r["status"],
                                       "gap": g, "reinspection": r, "questions": len(trace["steps"])}
                continue
            attempts[sig] = attempts.get(sig, 0) + 1
            if attempts[sig] > self.cfg.max_attempts_per_gap * 3:
                st.put("RealInvestigationTrace", self.run_id, trace)
                return "STOPPED", {"stop_reason": "GAP_NOT_CLOSED_BY_EVIDENCE", "gap": g, "questions": len(trace["steps"])}
            comp = next((c for c in cluster_gaps(rev["gap_details"]) if g["gap_id"] in c), [g["gap_id"]])
            cl = [x for x in rev["gap_details"] if x["gap_id"] in comp]
            if g["kind"] == "MISSING_DECISION" and not (g.get("choice_id") or g.get("joint_id") or g.get("phenomenon_id")):
                from ..style.coverage import owns
                cands_ = [c for c in plan["choices"] if set(g["dimensions"]) & set(c["dimensions"])
                          and not any(owns(d_, c["choice_id"], c["dimensions"]) for d_ in decs)]
                if cands_:
                    c0 = cands_[0]
                    g = {**g, "choice_id": c0["choice_id"], "dimensions": sorted(c0["dimensions"]), "conditions": c0["conditions"],
                         "mapped_from_dimension_gap": g["gap_id"]}
            dims = sorted(set(g["dimensions"]))
            owned_key = g.get("joint_id") or g.get("choice_id") or ("dimension:" + "+".join(dims))
            req = [r for r in self._required_branches(plan, dims)
                   if r["choice_id"] == owned_key or set(next(c["dimensions"] for c in plan["choices"] if c["choice_id"] == r["choice_id"])) <= set(dims)]
            if g.get("choice_id") and not g.get("phenomenon_id"):
                req = [r for r in req if r["choice_id"] == g["choice_id"]] or req
            if g.get("phenomenon_id") and not req:
                # a phenomenon outside every planned choice still needs its own conditional production branch
                env = (brief["scope"].get("world") or {}).get("kind")
                req = [{"conditions": {"environment": env} if env else {"subject_kind": "any"}, "operation_ids": ["op.whole_scene"],
                        "choice_id": g["phenomenon_id"]}]
            phenomenon = (st.get("VisualPhenomenon", g["phenomenon_id"]) or {}).get("phenomenon") if g.get("phenomenon_id") else owned_key
            did = production_choice_id(owned_key, phenomenon or owned_key)
            owned = sorted({owned_key} | {r["choice_id"] for r in req})
            if forced is not None:
                did, phenomenon = forced["decision_id"], forced.get("phenomenon") or forced["decision_id"]
                owned = list(forced.get("owned_choice_ids") or [owned_key])
                req = [r for r in self._required_branches(plan, dims) if r["choice_id"] in owned] or \
                      [{"conditions": b["when"], "operation_ids": b["operation_node_ids"], "choice_id": owned[0]} for b in forced["branches"]
                       if b["operation_node_ids"]]
            refs, contrast = self._pick_witnesses(st, dims, phenomenon_id=g.get("phenomenon_id"))
            if not refs:
                return "STOPPED", {"stop_reason": "BLOCKER_NO_WITNESS_FOR_DIMENSIONS", "dimensions": dims}
            p = st.get("ActiveArtProblem", f"{self.run_id}:{did}")
            p = ActiveArtProblem(**p) if p else ActiveArtProblem(
                cluster_id=f"{self.run_id}:{did}", version=1, original_output_id_or_initial_reference_only="INITIAL_REFERENCE_ONLY",
                reference_full_frame_ids=refs, affected_original_subject_classes=sorted({s.get("subject_kind", "?") for s in brief["scope"].get("subjects", [])}),
                high_impact_visible_difference=g["what"], whole_scene_consequence=f"{len(cl)} connected gap(s): " + "; ".join(x["what"] for x in cl)[:400],
                connected_artistic_relations=[st.get("Witness", w)["visible_relation"][:120] for w in refs],
                next_required_producer_decision_id=did, required_conditions=(req[0]["conditions"] if req else {}),
                expected_original_visual_improvement=f"new subject shows the evidenced {' + '.join(dims)} relation", source_evidence_version=digest(refs)[:12])
            wits = {w["witness_id"]: w for w in st.list("Witness")}
            ctx = ProblemContext(bundles={"B": {"witnesses": [{"witness_id": r} for r in refs], "contrasting_witness_ids": contrast}},
                                 witnesses=wits, decisions={d["decision_id"]: d for d in decs}, registered_operators=registered(),
                                 provider_capabilities=["whole_scene", "canonical_character", "guided_pose_edit", "region_edit"])
            lc = LoopController(st, ctx)
            q = lc.step_question(p, gap_id=g["gap_id"])
            if q.owner_stage in ("PROMPT_COMPILATION", "PROVIDER_RESULT", "HUMAN_REVIEW"):
                # decision exists and is executable for this gap; remaining gap is relational → ask joint question via conditions stage
                p.current_explanation_and_support = p.current_explanation_and_support or [{"claim": "joint", "witness_ids": refs}]
                st.put("ActiveArtProblem", p.cluster_id, p.to_dict())
                ctx.decisions.pop(did, None)
                q = lc.step_question(p, gap_id=g["gap_id"])
            imgs = []
            send_ids = []
            for wid in (q.observed_contrast_with_witness_ids or refs):
                par = (wits.get(wid) or {}).get("parent_full_frame_witness") if (wits.get(wid) or {}).get("evidence_kind") == "AUDIO_SIGNAL" else None
                need = [wid] + ([par] if par and par not in send_ids and par in wits else [])
                if par and par not in wits:
                    continue                      # audio evidence without its frame context is never sent alone
                if len(send_ids) + len([x for x in need if x not in send_ids]) > 6:
                    break
                send_ids += [x for x in need if x not in send_ids]
            for wid in send_ids:
                w = wits[wid]
                _, idx, cache = self._film(w["film_sha256"])
                fr = cache.frame(w["frame_start"])
                if w.get("evidence_kind") == "NATIVE_CROP" and w.get("region"):
                    from ..reference.frames import native_crop as _nc
                    rr = w["region"]
                    cr = _nc(fr, int(rr["x"]), int(rr["y"]), int(rr["w"]), int(rr["h"]))
                    imgs.append(self._img("WITNESS", w["film_sha256"], fr, wid=wid, png=cr.png_bytes, region=rr, w=cr.output_width, h=cr.output_height,
                                          label=f"WITNESS {wid} frame={w['film_sha256'][:16]}:{w['frame_start']} pts_time={w.get('pts_time')} NATIVE_CROP"))
                else:
                    imgs.append(self._img("WITNESS", w["film_sha256"], fr, wid=wid,
                                          label=f"WITNESS {wid} frame={w['film_sha256'][:16]}:{w['frame_start']} pts_time={w.get('pts_time')}"))
            prev_d = st.get("ConditionalVisualDecision", did) or {}
            defects = prev_d.get("reopened_defects") if str(prev_d.get("research_only_reason", "")).startswith("REOPENED_BY_HUMAN") else None
            if defects and q.owner_stage != "STYLE_CONDITIONS":
                q.owner_stage = "STYLE_CONDITIONS"          # the source evidence exists; the CONDITIONAL ACTION failed in original art
            payload = {"question": q.to_dict(), "dimensions": dims, "required_branches": req if q.owner_stage == "STYLE_CONDITIONS" else [],
                       "human_art_defects": defects or [],
                       "allowed_operations": sorted({o for r in req for o in r["operation_ids"]}) or ["op.whole_scene"]}
            task = custom_id_for("question_answer", {"question_sha": digest(q.question_text), "witnesses": q.planned_witness_or_input_ids,
                                                     "image_labels": [i["label"] for i in imgs], "dims": dims, "model": vis.caps.model_id,
                                                     "system_sha": digest(QA_SYSTEM)})
            p3 = self._p3_record(st, q, g, dims, payload)          # P3: one discriminating question with >=2 distinct operator outcomes
            ans, prep = self._src_request(vis, task, "question_answer", "P4", QA_SHAPE, imgs, payload,
                                          selection={"gap_id": g["gap_id"], "decision_id": did, "question_id": q.question_id},
                                          controlling_problem={"question_id": q.question_id, "missing_choice": q.exact_artistic_unknown,
                                                               "p3_record": p3["record_id"]},
                                          active_cluster={"cluster_id": p.cluster_id, "linked_gaps": [x["gap_id"] for x in cl]},
                                          competing=[{"claim": c.get("claim"), "witness_ids": c.get("witness_ids")}
                                                     for c in (p.current_explanation_and_support or [])][:5])

            maybe_crash("real_s2_after_answer_before_decision")      # raw answer is journaled; the decision is not yet published
            if q.owner_stage == "STYLE_CONDITIONS":
                from ..vision.protocol import assess_sufficiency
                asm = assess_sufficiency(ans, producing_operator=payload["allowed_operations"], known_witness_ids=set(wits))
                if asm["verdict"] != "SUFFICIENT_FOR_PRODUCING_CHOICE":
                    st.put("InsufficientAnswer", task, {"task": task, "question_id": q.question_id, "decision_id": did, "assessment": asm,
                                                        "receipt": ans.get("receipt"), "at": now_iso()})
                    trace["steps"].append({"question_id": q.question_id, "stage": q.owner_stage, "gap": g["gap_id"], "gap_signature": sig,
                                           "decision_id": did, "task": task, "answer_status": "INSUFFICIENT_FOR_PRODUCING_CHOICE",
                                           "assessment": asm, "decision_changed": False})
                    st.put("RealInvestigationTrace", self.run_id, trace)
                    continue

            from ..vision.dispatch import submitted_manifest
            sent_manifest = submitted_manifest(vis, task)       # LOCAL journal of what was actually sent (R3 F04), not the reply

            def writer(qq, aa, _dims=dims, _req=req, _did=did, _owned=owned, _ph=phenomenon, _man=sent_manifest):
                if qq.owner_stage != "STYLE_CONDITIONS":       # earlier stages record observations/hypotheses only (R3 F10)
                    return None
                return author_decision(st, qq.to_dict(), aa, dims=_dims, registered_ops=registered(), required_branches=_req,
                                       decision_id=_did, owned_choice_ids=_owned, phenomenon=_ph or _did,
                                       authorized_submission_manifest=_man)
            try:
                eff = lc.apply_answer(p, q, ans, decision_writer=writer)
            except Blocked as b:
                eff = {"status": "UNKNOWN", "decision_changed": False, "blocked": b.code}
            if q.owner_stage == "STYLE_CONDITIONS" or eff.get("decision_changed"):
                from ..style.authoring import register_relations_from_answer
                if q.answer_status in ("OBSERVED", "INFERRED"):
                    register_relations_from_answer(st, q.to_dict(), ans, dims)
            if g.get("phenomenon_id"):
                dd = st.get("ConditionalVisualDecision", did)
                ph = st.get("VisualPhenomenon", g["phenomenon_id"])
                if dd and dd.get("status") != "RESEARCH_ONLY":       # explained only by an EXECUTABLE owning decision
                    st.put("VisualPhenomenon", g["phenomenon_id"], {**ph, "status": "EXPLAINED", "explained_by": did})
            trace["steps"].append({"question_id": q.question_id, "stage": q.owner_stage, "gap": g["gap_id"], "gap_signature": sig,
                                   "decision_id": did, "owned_choice_ids": owned, "queued_gaps": len(rev["gap_details"]) - 1,
                                   "dims": dims, "question": q.question_text[:400], "task": task, "witnesses": [i["label"] for i in imgs],
                                   "answer_status": q.answer_status, "effect": eff, "decision_changed": bool(eff.get("decision_changed"))})
            st.put("RealInvestigationTrace", self.run_id, trace)
        return "STOPPED", {"stop_reason": "QUESTION_BUDGET_EXHAUSTED", "questions": len(trace["steps"])}

    @staticmethod
    def _required_branches(plan: dict, dims: list[str]) -> list[dict]:
        out: list[dict] = []
        for c in plan["choices"]:
            if not set(c["dimensions"]) & set(dims) or not c["conditions"]:
                continue
            kind = c["operation_kind"]
            op = OP_FOR_KIND.get(kind) or ("op.hand_prop_contact" if c["conditions"].get("action") == "grip" else "op.face_view_state")
            ent = {"conditions": c["conditions"], "operation_ids": [op], "choice_id": c["choice_id"]}
            if not any(e["conditions"] == ent["conditions"] and e["operation_ids"] == ent["operation_ids"] for e in out):
                out.append(ent)
        return out

    def _intervals(self, st) -> list[tuple]:
        man = st.get("SelectedSequenceManifest", "REAL:15") or {"selected": []}
        out = [(x["film_sha"], x["start_frame_index"], x["end_frame_index_inclusive"], x["candidate_id"]) for x in man["selected"]]
        six = st.get("SpecialIntroSelection", "REAL")
        if six and six.get("status") == "LOCKED":
            out.append((six["clip_sha256"], six["start_frame_index"], six["end_frame_index_inclusive"], "SIXTH"))
        return out

    def _entity_frames(self, intervals: list[tuple]) -> dict:
        """(film, entity) → [(seq, frame_index, region)] from the committed per-frame records."""
        out: dict = {}
        pass_id = f"{self.run_id}-L0"
        st = self.ws.store()
        try:
            for film, a, b, seq in intervals:
                rows = st.conn.execute("SELECT DISTINCT packet_id FROM frame_vision WHERE film_sha256=? AND pass_id=? AND frame_index "
                                       "BETWEEN ? AND ?", (film, pass_id, a, b)).fetchall()
                for (pk,) in rows:
                    f = self.ws.vision_dir / pass_id / pk / "frames.jsonl"
                    for line in (f.read_text(encoding="utf-8").splitlines() if f.exists() else []):
                        if not line.strip():
                            continue
                        o = json.loads(line)
                        k = int(str(o["frame_id"]).split(":")[1])
                        reg = next((r.get("region") for r in o.get("visible_design_relations") or [] if isinstance(r, dict) and r.get("region")), None)
                        for e in o.get("actually_visible_actor_and_object_ids") or []:
                            eid = e if isinstance(e, str) else str((e or {}).get("id"))
                            out.setdefault((film, eid), []).append((seq, k, reg))
        finally:
            st.close()
        return out

    def _character_study(self, st, vis) -> dict:
        """Addendum 29 C0–C10 per (film, drawn entity): whole frames from different states, a native crop, and an UNLIKE contrast entity
        from another film, through P2. Validated against the LOCAL submission manifest; invalid studies block character rules."""
        from ..style.source_ledger import validate_character_art_study
        from ..vision.dispatch import submitted_manifest
        ents = self._entity_frames(self._intervals(st))
        invalid, made = [], 0
        for (film, eid), frames in sorted(ents.items()):
            did = "CD-" + digest([film, eid])[:16]
            prev = st.get("CharacterArtDossier", did)
            if prev and prev.get("status") == "VALIDATED":
                continue
            seqs: set = set()
            picks: list = []
            for seq, k, reg in sorted(frames, key=lambda x: (x[0], x[1])):
                if seq not in seqs or len(picks) < 2:
                    if (seq, k) not in [(x[0], x[1]) for x in picks]:
                        picks.append((seq, k, reg))
                        seqs.add(seq)
                if len(picks) >= 3:
                    break
            contrast = next(((f2, fr2[0]) for (f2, e2), fr2 in sorted(ents.items()) if f2 != film), None)
            _, idx, cache = self._film(film)
            imgs = []
            for seq, k, reg in picks:
                fr = cache.frame(k)
                imgs.append(self._img("TARGET", film, fr, wid=f"W-{film[:10]}-{k}-0" if st.get("Witness", f"W-{film[:10]}-{k}-0") else None,
                                      label=f"STATE {eid} frame={film[:16]}:{k} seq={seq}"))
            if picks:
                seq, k, reg = picks[0]
                fr = cache.frame(k)
                r = reg or {"x": fr.width // 4, "y": fr.height // 4, "w": fr.width // 2, "h": fr.height // 2}
                r = {kk: int(r[kk]) for kk in ("x", "y", "w", "h")}
                from ..reference.frames import native_crop
                cr = native_crop(fr, r["x"], r["y"], r["w"], r["h"])
                imgs.append(self._img("NATIVE_CROP", film, fr, wid=f"{film[:16]}:{k}:crop:{r['x']},{r['y']},{r['w']},{r['h']}", png=cr.png_bytes,
                                      region=r, w=cr.output_width, h=cr.output_height, label=f"NATIVE_CROP {eid} frame={film[:16]}:{k}"))
            if contrast:
                f2, (seq2, k2, _r2) = contrast
                _, idx2, cache2 = self._film(f2)
                fr2 = cache2.frame(k2)
                imgs.append(self._img("CONTRAST", f2, fr2, wid=f"W-{f2[:10]}-{k2}-0" if st.get("Witness", f"W-{f2[:10]}-{k2}-0") else None,
                                      label=f"CONTRAST other-entity frame={f2[:16]}:{k2}"))
            if len(picks) < 2 or not contrast:
                rec = {"dossier_id": did, "entity_id": eid, "films": [film], "status": "INSUFFICIENT_SOURCE_DIVERSITY",
                       "problems": ["UNRESOLVED_BY_CURRENT_WITNESSES: need >=2 drawn states and an unlike contrast entity"],
                       "next": "select an interval with another drawn state of this entity / a contrasting entity", "at": now_iso()}
                st.put("CharacterArtDossier", did, rec)
                invalid.append(rec)
                continue
            tid = custom_id_for("character_dossier", {"film": film, "entity": eid, "images": [i["image_bytes_sha256"] for i in imgs],
                                                      "model": vis.caps.model_id, "system_sha": digest(CHARACTER_DOSSIER_SYSTEM)})
            resp, _prep = self._src_request(vis, tid, "character_dossier", "P2", CHARACTER_DOSSIER_SHAPE, imgs, {"entity_id": eid},
                                            selection={"film_sha256": film, "entity_id": eid, "frames": [x[1] for x in picks]})
            made += 1
            allowed = set(submitted_manifest(vis, tid)["submitted_witness_ids"])
            problems = validate_character_art_study(resp if isinstance(resp, dict) else {}, allowed)
            rec = {"dossier_id": did, "entity_id": eid, "films": sorted({i["source_sha256"] for i in imgs}), "task": tid,
                   "witness_ids": sorted(allowed), "study": {k: (resp or {}).get(k) for k in ("study_basis", "fields", "identity_across_drawings",
                                                                                           "contrasting_examples", "scope_class")},
                   "status": "VALIDATED" if not problems else "INVALID", "problems": problems,
                   "source_art_truth": "UNREVIEWED (needs human native-detail review)", "evidence_origin": self.p.evidence_origin, "at": now_iso()}
            rec["films"] = [film]
            st.put("CharacterArtDossier", did, rec)
            if problems:
                invalid.append(rec)
        return {"invalid": invalid, "requests": made}

    def _p3_record(self, st, q, g: dict, dims: list, payload: dict) -> dict:
        """P3 contract, recorded even though a deterministic DAG chose the question: ONE discriminating question whose possible
        evidence outcomes lead to at least two DIFFERENT producer operations/inputs (else it is not discriminating)."""
        from ..vision.protocol import PASSES, PROTOCOL_SHA as _PS
        outcomes = list(q.possible_answer_consequences_for_operation or [])
        if len(outcomes) < 2:
            raise Blocked("P3_QUESTION_NOT_DISCRIMINATING", q.question_id)
        rec = {"record_id": f"P3-{q.question_id}", "protocol_sha": _PS, "p3_text_sha": digest(PASSES["P3"][1]), "question_id": q.question_id,
               "question": q.question_text, "gap_id": g["gap_id"], "dimensions": dims, "outcomes": outcomes,
               "planned_witnesses": q.planned_witness_or_input_ids, "allowed_operations": payload.get("allowed_operations"), "at": now_iso()}
        st.put("P3QuestionRecord", rec["record_id"], rec)
        return rec

    def _reinspect(self, st, vis, g: dict, attempt: int, trace: dict) -> dict:
        """R11 / A28 P5: for a source-grounded gap, re-open the ORIGINAL imagery at its true resolution — the most relevant
        full frames, region crops and temporal neighbours — and ask ONE targeted question. New relations become witnesses."""
        from ..reference.frames import native_crop
        used = int((st.get("ReinspectionBudget", self.run_id) or {}).get("used", 0))
        if used >= self.cfg.reinspection_budget:
            return {"status": "REINSPECTION_BUDGET_EXHAUSTED", "used": used}
        if attempt > self.cfg.max_attempts_per_gap:
            return {"status": "NO_NEW_EVIDENCE", "attempts": attempt - 1}
        dims = g["dimensions"]
        if g.get("phenomenon_id"):
            ph = st.get("VisualPhenomenon", g["phenomenon_id"])
            anchors = [(x["film_sha256"], x["frame_index"], x.get("region")) for x in ph.get("sightings", [])[:2]] or \
                      [(ph["film_sha256"], ph["frame_index"], ph.get("region"))]
        else:
            ws = sorted(st.list("Witness"), key=lambda w: (-len(set(w.get("dimensions", [])) & set(dims)), w["witness_id"]))
            seen_frames, anchors = set(), []
            for w in ws:
                key = (w["film_sha256"], w["frame_start"])
                if key in seen_frames or w.get("evidence_kind") != "FULL_FRAME":
                    continue
                seen_frames.add(key)
                anchors.append((w["film_sha256"], w["frame_start"], w.get("region")))
                if len(anchors) >= 2:
                    break
        if not anchors:
            return {"status": "NO_SOURCE_FRAMES_TO_REINSPECT"}
        imgs, req_items = [], []
        for film, k, region in anchors:
            _, idx, cache = self._film(film)
            full = cache.frame(k)
            r = region or {"x": full.width // 4, "y": full.height // 4, "w": full.width // 2, "h": full.height // 2}
            r = {kk: int(r[kk]) for kk in ("x", "y", "w", "h")}
            crop = native_crop(full, r["x"], r["y"], r["w"], r["h"])
            nbs = [cache.frame(j) for j in (max(0, k - 1), min(len(idx) - 1, k + 1)) if j != k]
            imgs.append(self._img("TARGET", film, full, label=f"FULL {film[:16]}:{k}"))
            imgs.append(self._img("NATIVE_CROP", film, full, wid=f"{film[:16]}:{k}:crop:{r['x']},{r['y']},{r['w']},{r['h']}", png=crop.png_bytes,
                                  region=r, w=crop.output_width, h=crop.output_height,
                                  label=f"NATIVE_CROP {film[:16]}:{k} x={r['x']} y={r['y']} w={r['w']} h={r['h']}"))
            imgs += [self._img("NEIGHBOUR", film, x, label=f"NEIGHBOUR {film[:16]}:{x.presentation_index}") for x in nbs]
            req_items.append({"film": film, "frame": k, "region": r, "crop_sha": crop.crop_png_sha256, "neighbours": [x.presentation_index for x in nbs]})
        question = (f"Gap {g['gap_id']} ({g['kind']}): {g['what']}. In these full frames, native crops and neighbours, which visible "
                    f"relations involving {' + '.join(dims) or 'the unexplained behaviour'} does a producer need to decide for a NEW subject? "
                    "Return UNKNOWN for anything the pixels do not show.")
        tid = custom_id_for("reinspection", {"gap": g["gap_id"], "what": g["what"], "attempt": attempt, "items": req_items,
                                             "model": vis.caps.model_id})
        resp, _prep = self._src_request(vis, tid, "native_detail", "P5", NATIVE_SHAPE, imgs,
                                        {"reason": question, "dimensions": dims, "gap": g, "items": req_items},
                                        selection={"gap_id": g["gap_id"], "anchors": [[a[0], a[1]] for a in anchors]},
                                        controlling_problem={"gap": g["gap_id"], "what": g["what"]})
        st.put("ReinspectionBudget", self.run_id, {"used": used + 1, "budget": self.cfg.reinspection_budget})
        new = []
        for j, rel in enumerate(resp.get("relations") or []):
            rd = [d for d in (rel.get("dimensions") or []) if isinstance(d, str)]
            if is_vague_statement(rel.get("relation", "")) or not set(rd) & set(dims or rd):
                continue
            film, k, _ = anchors[0]
            item = req_items[0]
            wid = f"W-{film[:10]}-{k}-reinspect-{digest([g['gap_id'], attempt, j])[:8]}"
            _, idx, _c = self._film(film)
            st.put("Witness", wid, {"witness_id": wid, "film_sha256": film, "sequence_id": f"reinspect:{g['gap_id']}", "frame_start": k,
                                    "frame_end": k, "evidence_kind": "NATIVE_CROP", "observer": "VLM", "visible_relation": rel["relation"],
                                    "image_sha256": item["crop_sha"], "region": item["region"],
                                    "parent_full_frame_witness": f"W-{film[:10]}-{k}-0",
                                    "temporal_neighbor_witnesses": [f"W-{film[:10]}-{x}-0" for x in item["neighbours"]],
                                    "subject_class": None, "scene_specific_facts": [], "observation_ids": [f"{film[:16]}:{k}"],
                                    "limits": "gap-driven reinspection at true source resolution", "dimensions": sorted(set(rd) | set(dims)),
                                    "pts_time": idx[k]["pts_time"], "evidence_origin": self.p.evidence_origin, "from_gap": g["gap_id"]})
            new.append(wid)
        if g.get("phenomenon_id") and resp.get("phenomenon_dimensions"):
            ph = st.get("VisualPhenomenon", g["phenomenon_id"])
            st.put("VisualPhenomenon", g["phenomenon_id"], {**ph, "connected_dimensions": sorted(set(ph["connected_dimensions"]) |
                                                                                                  set(resp["phenomenon_dimensions"]))})
        trace["steps"].append({"stage": "SOURCE_REINSPECTION", "gap": g["gap_id"], "gap_kind": g["kind"], "task": tid, "question": question[:400],
                               "requested_items": req_items, "witnesses": [i["label"] for i in imgs], "new_witness_ids": new,
                               "remaining_unknown": resp.get("uncertainty", []), "decision_changed": False})
        return {"status": "NEW_WITNESSES" if new else "NO_NEW_EVIDENCE", "new_witness_ids": new, "task": tid}

    @staticmethod
    def _pick_witnesses(st, dims: list[str], phenomenon_id: str | None = None) -> tuple[list, list]:
        ws = [w for w in st.list("Witness") if set(w.get("dimensions", [])) & set(dims)]
        if phenomenon_id:
            ph = st.get("VisualPhenomenon", phenomenon_id)
            near = [w for w in st.list("Witness") if w["film_sha256"] == ph["film_sha256"] and abs(w["frame_start"] - ph["frame_index"]) <= 1]
            ws = near + [w for w in ws if w not in near]
        ws.sort(key=lambda w: (-len(set(w["dimensions"]) & set(dims)), w["witness_id"]))
        refs: list[str] = []
        films: set[str] = set()
        for w in ws:
            if w["film_sha256"] not in films and w["evidence_kind"] in ("FULL_FRAME", "NATIVE_CROP", "AUDIO_SIGNAL") and len(refs) < 3:
                refs.append(w["witness_id"])
                films.add(w["film_sha256"])
            if len(refs) >= 3:
                break
        for r_ in list(refs):              # an AUDIO_SIGNAL witness is only evidence together with its full-frame parent
            w_ = st.get("Witness", r_)
            if w_ and w_.get("evidence_kind") == "AUDIO_SIGNAL":
                par = w_.get("parent_full_frame_witness")
                if not par or not st.get("Witness", par):
                    refs.remove(r_)
                elif par not in refs:
                    refs.append(par)
        contrast = [w["witness_id"] for w in ws if w["witness_id"] not in refs and w["film_sha256"] not in films][:2] or \
                   [w["witness_id"] for w in ws if w["witness_id"] not in refs and w.get("subject_class") not in
                    {x.get("subject_class") for x in ws if x["witness_id"] in refs}][:2]
        return refs, contrast

    def _s3(self, st):
        decs = [d for d in st.list("ConditionalVisualDecision") if not d.get("synthetic")]
        ok = [d for d in decs if d["status"] != "RESEARCH_ONLY"]
        if not ok:
            return "STOPPED", {"stop_reason": "NO_EXECUTABLE_DECISIONS", "research_only": [d["decision_id"] for d in decs]}
        bad = [d["decision_id"] for d in ok if not d.get("observed_relation_ids") or not d.get("evidence_frame_ids")]
        if bad:
            return "STOPPED", {"stop_reason": "DECISION_WITHOUT_EVIDENCE", "decisions": bad}
        return "COMPLETED", {"decisions": {d["decision_id"]: {"status": d["status"], "branches": len(d["branches"]), "dims": d["dimension_tags"],
                                                              "witnesses": len(d["evidence_frame_ids"]), "visual_truth": d.get("visual_truth")} for d in ok},
                             "research_only": [d["decision_id"] for d in decs if d["status"] == "RESEARCH_ONLY"]}

    # ---- S4: author the real skill from decisions; completeness on the authored skill ---------------------
    def _s4(self, st):
        from ..style.source_ledger import source_art_ledger
        led = source_art_ledger(st, self.ws, self.run_id, self._intervals(st), f"{self.run_id}-L0")
        st.put("SourceArtLedger", self.run_id, led)
        if not led["complete_for_promotion"]:      # R3 F11: brief coverage never substitutes for source investigation
            return "STOPPED", {"stop_reason": "SOURCE_ART_LEDGER_OPEN",
                               "open": [{"scene": x["selected_scene"], "gaps": x["open_gaps"][:3]} for x in led["scenes"] if x["open_gaps"]][:8]}
        return self._s4_publish(st, led)

    def _s4_publish(self, st, led):
        from ..style.authoring import verify_structural_derivation
        from ..style.coverage import OriginalScope, review_visual_model_completeness
        from ..skills.operators import registered
        from ..style.authoring import publish_skill_version, current_skill
        decs = [d for d in st.list("ConditionalVisualDecision") if not d.get("synthetic") and d["status"] != "RESEARCH_ONLY"]
        version = f"0.{len(st.versions('RealSkillVersion', self.run_id)) + 1}"
        root = self.ws.skills_dir / f"real-{self.run_id.lower()}"
        oc = {"op.whole_scene": {"width": 1536, "height": 864, "format": "PNG", "asset_kind": "WHOLE_SCENE"},
              "op.world_plate": {"width": 1536, "height": 864, "format": "PNG", "asset_kind": "WORLD_PLATE"},
              **{k: {"width": 1024, "height": 1024, "format": "PNG", "asset_kind": "CHARACTER"} for k in
                 ("op.canonical_character", "op.face_view_state", "op.hand_prop_contact", "op.region_edit")}}
        cur = current_skill(root)
        if cur and Path(cur["folder"]).exists() and cur.get("decisions_sha") == digest(sorted(d["decision_id"] + str(d["version"]) for d in decs)):
            from ..skills.skill import skill_hash
            folder = Path(cur["folder"])
            res = {"folder": str(folder), "skill_hash": skill_hash(folder), "derivations": "UNCHANGED (same decisions → same immutable version)",
                   "references": None}
            version = cur.get("version") or version
        else:
            res = publish_skill_version(root, decs, skill_id=f"real-{self.run_id.lower()}", version=version,
                                        evidence_origin=self.p.evidence_origin, output_contracts=oc,
                                        exemplar_loader=self._exemplar_loader(st), consent_for=self._reference_consent(st))
            folder = Path(res["folder"])
            from ..util import atomic_write_json
            atomic_write_json(root / "CURRENT.json", {**current_skill(root),
                                                      "decisions_sha": digest(sorted(d["decision_id"] + str(d["version"]) for d in decs))})
        v = verify_structural_derivation(folder)
        if not v["ok"]:
            return "STOPPED", {"stop_reason": "CLAUSE_DERIVATION_BROKEN", "problems": v["problems"][:5]}
        brief = self._brief(st)
        scope = OriginalScope(scope_id=brief["brief_id"], **brief["scope"])
        L = st.get("VisualModelCoverageLedger", self.run_id)
        skill_decs = json.loads((folder / "decisions.json").read_text(encoding="utf-8"))
        rev = review_visual_model_completeness(L, scope, skill_decs, registered())
        st.put("RealSkillVersion", self.run_id, {"version": version, **{k: v for k, v in res.items() if k != "derivations"}})
        if res.get("reference_problems"):
            mand = [p for p in res["reference_problems"] if p.get("mandatory")]
            if mand:
                return "STOPPED", {"stop_reason": "MANDATORY_REFERENCE_BYTES_MISSING", "problems": mand[:5], "skill_folder": str(folder)}
        if not rev["review"]["image_trial_ready"]:
            return "STOPPED", {"stop_reason": rev["review"]["state"], "gap": rev["controlling_gap"]}
        from ..style.source_ledger import production_coverage_ledger
        from ..style.coverage import reverse_plan as _rp
        from ..skills.skill import load_skill as _ls
        pled = production_coverage_ledger(_rp(scope), skill_decs, _ls(folder), scope.scope_id)
        st.put("ProductionCoverageLedger", self.run_id, pled)
        return "COMPLETED", {"skill_folder": str(folder), "skill_hash": res["skill_hash"], "version": version, "derivations": res["derivations"],
                             "references": res.get("references"),
                             "coverage_state": rev["review"]["state"], "evidence_origin": self.p.evidence_origin,
                             "source_art_ledger_sha": led["ledger_sha"], "production_ledger_complete": pled["complete"],
                             "skill_status": "SKILL_CANDIDATE (no source-art review / transfer qualification)",
                             "artistic_quality": "ARTISTIC_QUALITY_UNPROVEN"}

    def _exemplar_loader(self, st):
        """witness id → exact source bytes (full frame, or the native crop region) + provenance, identity-verified."""
        from ..reference.frames import native_crop

        def load(wid: str):
            w = st.get("Witness", wid)
            if not w:
                raise Blocked("EXEMPLAR_WITNESS_MISSING", wid)
            _, idx, cache = self._film(w["film_sha256"])
            fr = cache.frame(w["frame_start"])
            r = w.get("region")
            if w.get("evidence_kind") == "NATIVE_CROP" and r:
                b = native_crop(fr, int(r["x"]), int(r["y"]), int(r["w"]), int(r["h"])).png_bytes
            else:
                b = fr.png_bytes
            return b, {"film_sha256": w["film_sha256"], "frame_index": w["frame_start"], "evidence_kind": w.get("evidence_kind"), "region": r}
        return load

    @staticmethod
    def _reference_consent(st):
        from ..state.authority import AuthorityRegistry
        reg = AuthorityRegistry(st)

        def lookup(film_sha: str, image_sha: str | None = None):
            return reg.upload_consent(film_sha, image_sha)       # trusted human authority, scoped to film / exemplar bytes
        return lookup

    # ---- S5: Runware probe (once) + skill execution through compiler and sole gateway -----------------
    def _gateway(self, st):
        from ..providers.gateway import StyleImageGateway
        from ..providers.runware import RunwareAdapter
        from ..providers.authorization import AuthorizationRegistry
        from .human import provider_state
        snap = provider_state(self.ws).get("runware")
        if not snap or not snap.get("user_confirmed_model"):
            raise Blocked("RUNWARE_MODEL_NOT_CONFIRMED", "run `vme provider confirm-runware --model <AIR id> --est-cost-usd X --by <name>`")
        ad = RunwareAdapter(snap, self.p.image_transport, kind="REAL", transport_kind=self.p.image_transport_kind)
        return StyleImageGateway(st, self.ws.artifacts_dir, ad, AuthorizationRegistry(self.ws.state_dir)), snap

    def _s5(self, st):
        from ..compiler.compiler import StyleProgramCompiler
        from ..review.approvals import GateKeeper
        from ..skills.runtime import execute
        from .human import record_runware_probe
        s4 = self._out(st, "S4")
        brief = self._brief(st)
        g, snap = self._gateway(st)
        if not snap.get("verified_by_probe"):
            probe = StyleProgramCompiler().compile_baseline(brief, caps=snap, output_contract={"width": 512, "height": 512, "format": "PNG",
                                                                                                 "asset_kind": "PROBE"})
            r = g.submit(probe, task_category="capability_probe", probe=True)
            o = r["outputs"][0]
            snap = record_runware_probe(self.ws, {"width": o["width"], "height": o["height"], "format": o["format"], "mode": o["pixel_mode"],
                                                  "nonopaque_alpha": o["has_nonopaque_alpha"], "cost_status": r["cost_status"],
                                                  "label": r["label"], "task_uuid": r["task_uuid"]})
            g, snap = self._gateway(st)
        gk = GateKeeper(st)
        if "S5" in getattr(self, "_invalidated", set()):
            gk.reopen(self.run_id, "ART", reason="S5 inputs changed (new skill/brief/provider) — previous art approvals no longer apply")
        if gk.state(self.run_id)["state"] in ("AWAITING_PROVIDER_OR_SOURCE", "ARTWORK_REJECTED"):
            gk.transition(self.run_id, "ART_GENERATING", reason="S5", synthetic=self.p.evidence_origin != "REAL_VLM")
        from ..skills.skill import load_skill
        have = {n["id"] for n in load_skill(s4["skill_folder"])["recipes"]["main"]["nodes"]}
        nodes = [n for n in ("n_world_plate", "n_whole_scene") if n in have]
        if "n_world_plate" not in have:
            return "STOPPED", {"stop_reason": "WORLD_PLATE_ROUTE_MISSING",
                               "note": "a clean world plate is required so a separate actor is never duplicated over a scene containing it (R18)"}
        res = execute(s4["skill_folder"], brief, gateway=g, caps=snap, node_ids=nodes, pinned_skill_hash=s4["skill_hash"], store=st)
        # R3 F12: every character actor gets ITS OWN canonical job (own content slots, own conditions, own approval) — never aliased
        actors = [x for x in brief["scope"]["subjects"] if x.get("kind") == "character"]
        if actors and "n_canonical_character" not in have:
            return "STOPPED", {"stop_reason": "CANONICAL_CHARACTER_ROUTE_MISSING"}
        for a in actors:
            over = self._actor_slots(brief, a)
            r = execute(s4["skill_folder"], brief, gateway=g, caps=snap, node_ids=["n_canonical_character"], pinned_skill_hash=s4["skill_hash"],
                        slot_overrides={"n_canonical_character": over}, store=st,
                        actor_scope={"actor_id": a["id"], "other_actor_ids": [x["id"] for x in actors if x["id"] != a["id"]]}
                        if len(actors) > 1 else None)["n_canonical_character"]
            res[f"n_canonical_character@{a['id']}"] = {**r, "actor_id": a["id"], "identity_slots": over}
        shas = [res[f"n_canonical_character@{a['id']}"]["sha"] for a in actors]
        if len(set(shas)) != len(shas):
            raise Blocked("ACTOR_IDENTITY_COLLISION", "two actors produced the same canonical bytes; identities must be distinct")
        if actors:
            res["n_canonical_character"] = res[f"n_canonical_character@{actors[0]['id']}"]      # legacy alias for the first actor
        if gk.state(self.run_id)["state"] == "ART_GENERATING":
            gk.transition(self.run_id, "AWAITING_ARTWORK_REVIEW", reason="full-resolution stills ready")
        return "COMPLETED", {k: {kk: vv for kk, vv in v.items() if kk != "result"} | {"label": v["result"]["label"],
                                                                                        "request_body_sha256": v["result"]["request_body_sha256"]}
                             for k, v in res.items()}

    @staticmethod
    def _actor_slots(brief: dict, actor: dict) -> dict:
        subj: dict = next((x for x in brief.get("subjects", []) if x.get("id") == actor["id"]), {})
        out = {"subject": subj.get("noun") or brief["slots"].get("subject")}
        for k in ("subject_kind", "view", "role"):
            if actor.get(k):
                out[k if k != "role" else "visual_role"] = actor[k]
        return out

    # ---- S6: human artwork verdict ------------------------------------------------------------------
    def _s6(self, st):
        from ..review.approvals import GateKeeper
        gk = GateKeeper(st)
        s = gk.state(self.run_id)
        if s["state"] in ("ARTWORK_APPROVED", "ASSET_PREPARING", "AWAITING_ASSET_REVIEW", "ASSETS_APPROVED", "VIDEO_RENDERING",
                          "AWAITING_VIDEO_REVIEW") and s["required_art_approval_ids"]:
            gk.verify_art_still_valid(self.run_id)
            return "COMPLETED", {"art_approval_id": s["required_art_approval_ids"][0]}
        if s["state"] == "ARTWORK_REJECTED":
            nq = self._question_from_human_review(st, "art")
            rev = self._open_revision(st)
            return "STOPPED", {"stop_reason": "ARTWORK_REJECTED_REVISION_OPEN" if rev and rev["reopened_decisions"] else "ARTWORK_REJECTED",
                               "revision": rev, "next_question": nq,
                               "human_next_step": None if rev and rev["reopened_decisions"] else
                               "attribute each defect to a decision_id so the responsible production choice can be reopened"}
        s5 = self._out(st, "S5")
        return "STOPPED", {"stop_reason": "AWAITING_ARTWORK_REVIEW", "images": sorted({v["image"] for v in s5.values()}),
                           "human_next_step": f"vme review serve --run {self.run_id}  (or vme art approve|reject)"}

    def _open_revision(self, st) -> dict | None:
        """Human art rejection → structured defects → the attributed production-choice decisions are REOPENED (new version,
        old evidence and rejected images kept) → S2..S5 inputs change → a NEW skill version and a DIFFERENT request (R12/ST28-21)."""
        rej = [a for a in st.list("ArtApproval") if a["run_id"] == self.run_id and a["verdict"] == "REJECTED"]
        if not rej:
            return None
        a = rej[-1]
        rid = f"{self.run_id}:{a['approval_id']}"
        ex = st.get("ArtRevision", rid)
        if ex:
            return ex
        reopened = []
        for d in a.get("defects") or []:
            did = d.get("decision_id")
            dec = st.get("ConditionalVisualDecision", did) if did else None
            if not dec:
                continue
            st.put("ConditionalVisualDecision", did, {**dec, "version": dec["version"] + 1, "status": "RESEARCH_ONLY",
                                                      "research_only_reason": f"REOPENED_BY_HUMAN_ART_REJECTION:{a['approval_id']}",
                                                      "reopened_defects": [x for x in a["defects"] if x.get("decision_id") == did],
                                                      "claim_state": "UNRESOLVED", "rejected_image_hashes": a["image_hashes"]})
            reopened.append(did)
        rev = {"revision_id": rid, "run_id": self.run_id, "approval_id": a["approval_id"], "defects": a.get("defects") or [],
               "rejected_image_hashes": a["image_hashes"], "reopened_decisions": sorted(set(reopened)), "status": "OPEN", "at": now_iso()}
        st.put("ArtRevision", rid, rev)
        return rev

    def _question_from_human_review(self, st, stage: str) -> dict | None:
        from ..investigation.controller import ActiveArtProblem, LoopController, ProblemContext
        from ..skills.operators import registered
        revs = [r for r in st.list("VisualReview") if r["run_id"] == self.run_id and r.get("stage", stage) == stage]
        if not revs or not revs[-1].get("findings"):
            return None
        probs = [p for p in st.list("ActiveArtProblem") if p["cluster_id"].startswith(self.run_id)]
        if not probs:
            return None
        p = ActiveArtProblem(**probs[-1])
        wits = {w["witness_id"]: w for w in st.list("Witness")}
        decs = {d["decision_id"]: d for d in st.list("ConditionalVisualDecision") if not d.get("synthetic")}
        lc = LoopController(st, ProblemContext(witnesses=wits, decisions=decs, registered_operators=registered(),
                                               compile_trace={"selected_decisions": list(decs), "skill_present_but_not_compiled": []}))
        lc.observe_new_output(p, {"output_id": revs[-1]["review_id"], "findings": revs[-1]["findings"]})
        return lc.step_question(p, gap_id=f"human:{revs[-1]['review_id']}").to_dict()

    # ---- S7: every planned asset demand → real operator → verified artifact → consumer, or a named blocker (R17/R19) -----
    STATE_NODE = {"view": ("n_face_view_state", lambda v: {"view": v}), "grip": ("n_hand_prop_contact", lambda v: {"action": "grip"}),
                  "expr": ("n_face_view_state", None)}

    def _s7(self, st):
        from ..review.approvals import GateKeeper
        from ..artwork.character import derive_animation_demand, character_construction_plan
        from ..artwork.raster import decode_raster
        from ..skills.runtime import execute
        from ..skills.skill import load_skill
        from ..util import sha256_file, atomic_write_json
        gk = GateKeeper(st)
        s = gk.state(self.run_id)
        prev = (st.get("LoopTransition", f"{self.run_id}:S7") or {}).get("outputs", {})
        stale = "S7" in getattr(self, "_invalidated", set()) or prev.get("shot_plan_sha") != digest(self._brief(st).get("shot_plan"))
        if not stale and s["state"] in ("ASSETS_APPROVED", "VIDEO_RENDERING", "AWAITING_VIDEO_REVIEW") and s["required_asset_approval_ids"]:
            return "COMPLETED", {**prev, "asset_approval_id": s["required_asset_approval_ids"][0]}
        if not stale and s["state"] == "AWAITING_ASSET_REVIEW":
            return "STOPPED", {**prev, "stop_reason": "AWAITING_ASSET_REVIEW"}
        if stale:
            self._invalidated.add("S7") if hasattr(self, "_invalidated") else None
        if s["state"] == "ASSETS_REJECTED":
            return "STOPPED", {"stop_reason": "ASSETS_REJECTED", "next_question": self._question_from_human_review(st, "asset")}
        s4, s5 = self._out(st, "S4"), self._out(st, "S5")
        brief = self._brief(st)
        sp = brief["shot_plan"]
        actors = [x for x in brief["scope"]["subjects"] if x.get("kind") == "character"]
        if "S7" in getattr(self, "_invalidated", set()) and gk.state(self.run_id)["state"] in (
                "AWAITING_ASSET_REVIEW", "ASSETS_APPROVED", "AWAITING_VIDEO_REVIEW", "ASSETS_REJECTED"):
            gk.reopen(self.run_id, "ASSET", reason="S7 inputs changed (shot plan / art) — previous asset approval no longer applies")
        if s["state"] == "ARTWORK_APPROVED":
            gk.transition(self.run_id, "ASSET_PREPARING", reason="S7")
        g, snap = self._gateway(st)
        have = {n["id"] for n in load_skill(s4["skill_folder"])["recipes"]["main"]["nodes"]}
        demands, assets, blocked = [], {}, []
        consumers = {}
        for ev in sp.get("events", []):
            consumers.setdefault(f"{ev.get('actor')}:{ev['state']}", []).append(ev.get("event_id") or f"{ev['from']}-{ev['to']}")

        def contract(path, kind, actor, state, extra=None, canon=None):
            ra = decode_raster(Path(path).read_bytes(), asset_id=state, owner=actor, skill_version=s4["skill_hash"])
            return {"path": path, "sha256": ra.sha256, "width": ra.width, "height": ra.height, "pixel_mode": ra.pixel_mode,
                    "alpha": "NONOPAQUE_ALPHA" if ra.has_nonopaque_alpha else "OPAQUE_NO_MASK",
                    "coordinate_frame": {"origin": "top-left pixel of this canvas", "anchor": "bottom-centre of canvas", "units": "px"},
                    "kind": kind, "actor_id": actor, "state": state, "identity_source_sha256": (canon or {}).get("sha"),
                    "art_skill_hash": s4["skill_hash"],
                    "depth": (extra or {}).get("depth", 1), "consumers": consumers.get(f"{actor}:{state}", []), **(extra or {})}
        assets["world_plate"] = contract(s5["n_world_plate"]["image"], "WORLD_PLATE", None, "world_plate",
                                         {"depth": 0, "contains_actor": False, "consumers": ["background"]})
        canon_by_actor = {}
        for actor in actors:
            canon = s5.get(f"n_canonical_character@{actor['id']}")
            if canon is None:
                raise Blocked("ACTOR_WITHOUT_INDEPENDENT_CANONICAL", actor["id"])
            cra = decode_raster(Path(canon["image"]).read_bytes(), asset_id="canon", owner=actor["id"], skill_version=s4["skill_hash"])
            demand = derive_animation_demand(actor["id"], sp.get("actions", []))
            plan = character_construction_plan(actor["id"], brief["brief_id"], s4["skill_hash"], demand)
            st.put("CharacterConstructionPlan", f"{self.run_id}:{actor['id']}", plan)
            ident = {f"{actor['id']}:canonical": {"path": canon["image"], "sha256": canon["sha"], "approved": True}}
            b = dict(brief)
            b["subjects"] = [dict(x, identity_asset_id=f"{actor['id']}:canonical") for x in brief["subjects"] if x["id"] == actor["id"]]
            aslots = self._actor_slots(brief, actor)
            for step in plan["generation_sequence"]:
                d = {"step": step["step"], "operator": step["operator"], "kind": step["kind"], "actor": actor["id"]}
                demands.append(d)
                if step["kind"] == "CHARACTER_CANONICAL":
                    assets[f"{actor['id']}:canonical"] = contract(canon["image"], "CHARACTER_CANONICAL", actor["id"], "canonical", canon=canon)
                    canon_by_actor[actor["id"]] = assets[f"{actor['id']}:canonical"]
                    d["status"] = "PRODUCED_IN_S5"
                    continue
                if step["kind"] in ("LAYER", "CLEAN_PLATE"):
                    # no verified segmentation / hidden-surface / clean-plate capability: block, never fake layers (R19)
                    d.update(status="BLOCKED_ROUTE_NOT_IMPLEMENTED",
                             reason=f"{step['operator']} needs a verified mask/segmentation route; WHOLE_STATE_SWAP cannot provide it")
                    blocked.append(d)
                    continue
                fam, val = step["step"].split(":", 1)
                nid, over = self.STATE_NODE.get(fam, (None, None))
                if nid is None or nid not in have or over is None:
                    d.update(status="BLOCKED_NO_DECISION_OR_OPERATOR", reason=f"no evidenced decision/condition produces state {step['step']}",
                             ticket={"question": f"Which source-evidenced decision produces the {step['step']} drawing state for "
                                                 f"{actor['id']} from the approved canonical art?", "operator": step["operator"]})
                    blocked.append(d)
                    continue
                try:
                    r = execute(s4["skill_folder"], b, gateway=g, caps=snap, node_ids=[nid], pinned_skill_hash=s4["skill_hash"],
                                identity_assets=ident, slot_overrides={nid: {**aslots, **over(val)}}, store=st)[nid]
                except Blocked as e:
                    d.update(status="BLOCKED_PROVIDER_OR_DECISION", reason=e.code, ticket=e.data.get("ticket"))
                    blocked.append(d)
                    continue
                c = contract(r["image"], "CHARACTER_STATE", actor["id"], step["step"],
                             {"reference_shas": r["reference_shas"], "clause_ids": r["clause_ids"],
                              "contact": {"prop": step.get("prop_id"), "hand_side": step.get("hand_side")} if fam == "grip" else None,
                              "view": val if fam == "view" else None}, canon=canon)
                if (c["width"], c["height"]) != (cra.width, cra.height):
                    d.update(status="BLOCKED_STATE_CANVAS_MISMATCH")
                    blocked.append(d)
                    continue
                if canon["sha"] not in r["reference_shas"]:
                    d.update(status="BLOCKED_NOT_CONDITIONED_ON_CANONICAL")
                    blocked.append(d)
                    continue
                assets[f"{actor['id']}:{step['step']}"] = c
                d.update(status="PRODUCED", artifact_sha256=c["sha256"], consumers=c["consumers"])
        pack = {"method": "WHOLE_STATE_SWAP", "method_reason": "no verified segmentation/inpainting capability; whole drawings swap, no pretend layers",
                "method_limits": "does NOT provide separated arms, clean plates, IK, hidden surfaces or part continuity",
                "world_plate": assets["world_plate"], "canonical_by_actor": canon_by_actor,
                "canonical": next(iter(canon_by_actor.values()), None),
                "states": {k: v for k, v in assets.items() if v["kind"] == "CHARACTER_STATE"}, "demands": demands, "blocked": blocked,
                "art_direction_still": s5.get("n_whole_scene", {}).get("image"),
                "art_direction_still_use": "human art review only; never a render background (it already contains the actor)"}
        pack_path = self.dir / "asset_pack.json"
        atomic_write_json(pack_path, pack)
        files = [v["path"] for v in assets.values()]
        out = {"pack": str(pack_path), "states": sorted(pack["states"]), "demands": demands, "blocked": blocked,
               "shot_plan_sha": digest(sp),
               "files": files, "file_shas": [sha256_file(f) for f in files]}
        if blocked:
            return "STOPPED", {**out, "stop_reason": "ASSET_DEMAND_BLOCKED",
                               "exact_blockers": [{"step": x["step"], "status": x["status"], "reason": x.get("reason")} for x in blocked]}
        if gk.state(self.run_id)["state"] == "ASSET_PREPARING":
            gk.transition(self.run_id, "AWAITING_ASSET_REVIEW", reason="every planned demand produced (WHOLE_STATE_SWAP)")
        return "STOPPED", {**out, "stop_reason": "AWAITING_ASSET_REVIEW"}

    # ---- S8: render the DIRECTED shot plan from approved assets only (R18/R20) ------------------------------------
    def _s8(self, st):
        """Render the DIRECTED shot plan with a SKILL-OWNED event program (R3 F12/F13), mux approved original audio (F14) and refuse any
        technical/AV failure (F15). Diagnostic silent clips use a different route and never satisfy this one."""
        from ..render.renderer import render_video
        from ..render.motion_program import compile_event_program, apply_program
        from ..review.approvals import GateKeeper
        from ..style.coverage import OriginalScope
        gk = GateKeeper(st)
        if gk.state(self.run_id)["state"] == "AWAITING_VIDEO_REVIEW":
            prev = (st.get("LoopTransition", f"{self.run_id}:S8") or {}).get("outputs", {})
            return "COMPLETED", prev
        s7 = (st.get("LoopTransition", f"{self.run_id}:S7") or {})["outputs"]
        pack = read_json(s7["pack"])
        brief = self._brief(st)
        sp = brief["shot_plan"]
        R = self.cfg.render
        W, H, fps, n = R["width"], R["height"], sp.get("fps", R["fps"]), sp.get("frames")
        problems = []
        if not n:
            problems.append("shot_plan.frames missing")
        if not sp.get("actors"):
            problems.append("shot_plan.actors missing: every actor's placement/size/depth/keyframes must be directed (no default x=55%)")
        if problems:
            return "STOPPED", {"stop_reason": "SHOT_PLAN_NOT_DIRECTED", "problems": problems}
        # R3-C02/C04: no local scaling here — ONE ShotCoordinateSpace inside compile_event_program maps every coordinate; world
        # layers are the shot plan's declared depth layers, each bound to an approved world asset (a single plate is one layer).
        assets = {"world_plate.png": pack["world_plate"]["path"]}
        wls = sp.get("world_layers") or [{"id": "world", "depth": None}]
        layers = []
        for i, wl in enumerate(wls):
            if wl["id"] != "world" and wl["id"] not in (pack.get("world_layers") or {}):
                return "STOPPED", {"stop_reason": "WORLD_LAYER_ASSET_MISSING", "layer": wl["id"],
                                   "note": "a depth layer needs its own approved world asset; one plate is never sliced by guesswork"}
            src = "world_plate.png" if wl["id"] == "world" else f"world_{wl['id']}.png"
            if wl["id"] != "world":
                assets[src] = pack["world_layers"][wl["id"]]["path"]
            layers.append({"id": wl["id"], "src": src, "x": 0, "y": 0, "w": W, "h": H, "z": -len(wls) + i})
        event_trace = []
        cba = pack.get("canonical_by_actor") or {}
        for a in sp["actors"]:
            canon = cba.get(a["id"])
            if canon is None:
                return "STOPPED", {"stop_reason": "ACTOR_ASSET_NOT_APPROVED", "actor": a["id"],
                                   "note": "each actor needs its own approved canonical; actors never alias another actor's art"}
            name = f"{a['id']}_canonical.png"
            assets[name] = canon["path"]
            lay = {"id": a["id"], "src": name, "x": 0, "y": 0, "w": 0, "h": 0,       # geometry set ONLY by apply_program (coords)
                   "z": int(a["z"]), "keyframes": [], "states": [], "identity_sha256": canon["sha256"]}
            for ev in [e for e in sp.get("events", []) if e.get("actor", a["id"]) == a["id"] and e.get("state")]:
                stt = pack["states"].get(f"{a['id']}:{ev['state']}")
                if stt is None:
                    return "STOPPED", {"stop_reason": "EVENT_STATE_NOT_PRODUCED", "event": ev,
                                       "note": "a missing drawing state is never replaced by a transform of another drawing"}
                if stt.get("identity_source_sha256") != canon["sha256"]:
                    raise Blocked("STATE_IDENTITY_ALIASES_ANOTHER_ACTOR", f"{a['id']}:{ev['state']}")
                sname = f"{a['id']}_{ev['state'].replace(':', '_')}.png"
                assets[sname] = stt["path"]
                lay["states"].append({"from_frame": ev["from"], "to_frame": ev["to"], "src": sname})
                event_trace.append({"event": ev.get("event_id"), "actor": a["id"], "state": ev["state"], "asset_sha256": stt["sha256"],
                                    "frames": [ev["from"], ev["to"]]})
            layers.append(lay)
        s4 = self._out(st, "S4")
        scope = OriginalScope(scope_id=brief["brief_id"], **brief["scope"])
        skill_decs = json.loads((Path(s4["skill_folder"]) / "decisions.json").read_text(encoding="utf-8"))
        prog = compile_event_program(decisions=skill_decs, scope=scope, brief=brief, pack=pack, width=W, height=H)
        st.put("EventProgram", self.run_id, prog)
        scene = apply_program({"width": W, "height": H, "fps": fps, "durationInFrames": n, "background": "#000000",
                               "layers": sorted(layers, key=lambda l: l["z"])}, prog)
        silent = self.dir / "integrated_video_only.mp4"
        rep = render_video(scene, assets, silent, gate=gk, run_id=self.run_id, transition_on_success=False)
        out_mp4, av = silent, {"ok": None, "status": "AUDIO_NOT_REQUIRED_BY_SHOT_PLAN"}
        audio = sp.get("audio") or {}
        try:
            if audio.get("required"):
                av = self._mux_audio(st, silent, prog, audio, fps=fps, frames=n)
                if not av["ok"]:
                    raise Blocked("AUDIOVISUAL_SYNC_FAILED", ";".join(av["problems"][:4]))
                out_mp4 = Path(av["mp4"])
        except Blocked:
            gk.transition(self.run_id, "ASSETS_APPROVED", reason="integrated AV gate failed; film not released for review")
            raise
        gk.transition(self.run_id, "AWAITING_VIDEO_REVIEW", reason="render + AV gates passed")
        from ..util import sha256_file
        st.put("RenderReport", self.run_id, {**rep, "event_trace": event_trace, "event_program_sha": prog["program_sha"], "av": av,
                                             "final_mp4": str(out_mp4)})
        return "COMPLETED", {"mp4": str(out_mp4), "mp4_sha256": sha256_file(out_mp4), "motion": rep["motion"]["verdict"],
                             "ffprobe_ok": rep["ffprobe"]["ok"], "state_swaps": len(event_trace), "event_trace": event_trace,
                             "event_program_sha": prog["program_sha"], "tracks": [{k: t.get(k) for k in ("kind", "actor_id", "owner_decision_id",
                                                                                                        "method")} for t in prog["tracks"]],
                             "contacts": prog["contacts"], "av": {k: av.get(k) for k in ("ok", "status", "problems", "measured_onsets",
                                                                                         "scheduled_cues")},
                             "background": "WORLD_PLATE (no actor)", "actors": [a["id"] for a in sp["actors"]],
                             "label": rep["quality_claim"],
                             "animation_claim": "SKILL-OWNED EVENT PROGRAM over approved whole-state drawings; professional quality UNPROVEN"}

    def _mux_audio(self, st, video: Path, prog: dict, audio: dict, *, fps: float, frames: int) -> dict:
        from ..reference.audio import build_cue_track, mux, verify_av
        from ..state.authority import AuthorityRegistry
        sha = audio.get("approved_asset_sha256")
        path = audio.get("asset_path")
        if not sha or not path or not Path(path).exists():
            raise Blocked("NO_APPROVED_SOUND_ASSET", "the shot plan requires audio but names no local original sound asset")
        from ..util import sha256_file
        if sha256_file(path) != sha:
            raise Blocked("SOUND_ASSET_BYTES_CHANGED", path)
        if not AuthorityRegistry(st).sound_asset(sha):
            raise Blocked("NO_APPROVED_SOUND_ASSET", f"{sha[:12]} has no human SOUND_ASSET_APPROVAL")
        cues = sorted({c["frame"] for c in prog["audio_cues"]})     # coinciding semantic cues share one measurable onset
        wav = build_cue_track(path, cues, fps=fps, frames=frames, out_wav=self.dir / "audio_program.wav")
        out = mux(video, wav, self.dir / "integrated.mp4")
        v = verify_av(out, cue_frames=cues, fps=fps, frames=frames)
        return {**v, "mp4": str(out), "status": "AV_VERIFIED" if v["ok"] else "AV_FAILED", "asset_sha256": sha}

    # ---- S9: human video review, frozen-skill transfer on a sealed unseen brief, next question --------------
    def _s9(self, st):
        from ..experiments.experiments import HoldoutRegistry
        from ..skills.runtime import execute
        revs = [r for r in st.list("VisualReview") if r["run_id"] == self.run_id and r.get("stage") == "video"]
        if not revs:
            return "STOPPED", {"stop_reason": "AWAITING_VIDEO_REVIEW", "human_next_step": f"vme video verdict --run {self.run_id} ..."}
        s4 = self._out(st, "S4")
        if not (Path(s4["skill_folder"]) / "FROZEN.json").exists():
            return "STOPPED", {"stop_reason": "AWAITING_SKILL_FREEZE", "human_next_step": f"vme skill freeze --folder {s4['skill_folder']} --by <name>"}
        hr = HoldoutRegistry(self.ws.state_dir / "HOLDOUTS.json")
        sealed = [k for k, v in hr._d()["holdouts"].items() if v["status"] == "SEALED"]
        nq = self._question_from_human_review(st, "video")   # derived BEFORE the holdout is unsealed
        if not sealed:
            return "STOPPED", {"stop_reason": "AWAITING_UNSEEN_BRIEF", "human_next_step": "vme brief add --holdout --file <unseen.json> --by <name>"}
        brief = hr.access(sealed[0], by_role="transfer_runner", skill_frozen_hash=s4["skill_hash"])
        g, snap = self._gateway(st)
        r = execute(s4["skill_folder"], brief, gateway=g, caps=snap, node_ids=["n_whole_scene"], pinned_skill_hash=s4["skill_hash"], store=st)
        rec = hr.record_result(sealed[0], skill_hash_used=s4["skill_hash"])
        st.put("TransferRecord", self.run_id, {"holdout": sealed[0], "status": rec["status"], "output": r["n_whole_scene"]["sha"], "next_question": nq,
                                               "still_transfer": "STILL_TRANSFER_PENDING_AWAITING_REVIEW",
                                               "animated_transfer": "NOT_ATTEMPTED (needs a frozen-skill animated holdout + human video review)",
                                               "scope_note": "one unseen still never certifies character/world/acting/animation transfer (R23)"})
        from ..review.qualification import capability_verdict
        st.put("CapabilityVerdict", self.run_id, capability_verdict(st, self.run_id))     # R3 F17: separate statuses, never averaged
        return "COMPLETED", {"transfer": "STILL_TRANSFER_PENDING_AWAITING_REVIEW", "animated_transfer": "NOT_ATTEMPTED",
                             "audiovisual_qualification": "NOT_QUALIFIED (still-only holdout never grants motion/AV)",
                             "holdout": sealed[0], "output_sha": r["n_whole_scene"]["sha"],
                             "next_question_stage": (nq or {}).get("owner_stage"), "next_question": (nq or {}).get("question_text")}


def describe_call_graph() -> list[dict]:
    """Line-specific REAL-path call graph (used by the audit export)."""
    import inspect
    rows = []
    for s in STAGES:
        fn = getattr(RealLoopRunner, f"_{s.lower()}")
        src, start = inspect.getsourcelines(fn)
        calls = []
        for i, line in enumerate(src):
            t = line.strip()
            for name in ("request_json", "propose_selection", "PacketRunner", "resume(", "plan_packets", "_extract_witnesses", "_native_followups",
                         "review_visual_model_completeness", "step_question", "apply_answer", "author_decision", "author_skill",
                         "verify_structural_derivation", "compile_baseline", "submit(", "execute(", "transition(", "render_video",
                         "character_construction_plan", "derive_animation_demand", "decode_raster", "access(", "record_result",
                         "_question_from_human_review", "verify_art_still_valid"):
                if name in t and not t.startswith("#"):
                    calls.append({"line": start + i, "call": name.rstrip("("), "code": t[:140]})
        rows.append({"stage": s, "handler": f"vme/loop/real.py:{start}", "consumer": CONSUMERS[s], "calls": calls})
    return rows
