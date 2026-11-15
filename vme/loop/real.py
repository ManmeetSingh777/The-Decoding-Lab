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
OP_FOR_KIND = {"whole_scene": "op.whole_scene", "canonical_character": "op.canonical_character", "layer_extract": "op.layer_extract",
               "motion_render": "op.motion_render"}
RATIONALE_SYSTEM = """SOURCE ANALYSIS ONLY. You see 3 actual frames (start, middle, end) of one contiguous window of a source film.
Return strict JSON: {"whole_visual_quality_statement": str (a specific visible relationship between designed forms, world, light or motion;
no standalone adjectives), "selection_role_candidates": subset of ["C","W","T"] (C=character identity/acting, W=complete illustrated world,
T=changing viewpoint/state/choreography), "opportunities": subset of [character_shape, body_face_relation, whole_body_acting, hand_prop,
complete_world, integrated_object_artwork, colour_material_finish, viewpoint, state_substitution, choreographed_coexistence,
spatial_transformation], "visible_proof_for_each_opportunity": {opportunity: frame-anchored description}, "actor_class": str|null,
"content_label": "MAIN_FILM"|"SPONSOR"|"OUTRO"|"CREDITS"|"INTRO_CARD", "new_question_contributed": str, "known_limitations": [str]}.
Say UNKNOWN when the frames do not show something. Never claim proprietary production methods."""
QA_SYSTEM = """SOURCE ANALYSIS ONLY — answer ONE investigation question using ONLY the labelled source images provided
(each image is preceded by its witness id). Separate OBSERVED from INFERRED; if the images cannot settle it, answer_status=UNKNOWN.
Return strict JSON with keys: answer_status (OBSERVED|INFERRED|UNKNOWN|REFUTED), SOURCE_VISIBLE_FACTS [{relation, witness_ids}],
IMPORTANT_LINKED_CHANGES [str], CONSTRUCTION_EXPLANATION str, WHY_THE_DECISION_MATTERS str, WHEN_APPLICABLE {}, WHEN_NOT_APPLICABLE [str],
ACTUAL_PRODUCING_OPERATION {operation_id}, WHERE_IT_ENTERS_COMPILED_REQUEST {decision, operator}, REMAINING_UNKNOWN [str],
answer_evidence_ids [witness ids], and when the question asks for conditional production choices: BRANCHES
[{when:{condition:value}, construction_action: str written for a NEW subject using the placeholders {subject} and {setting}, never source
nouns, operation_id}], INVARIANT str, ADAPTS_WITH [str], CREATIVE_FREEDOM [str], FORBIDDEN_SOURCE_SPECIFIC [str].
One BRANCH is required for each entry of required_branches (same conditions, one of its operation_ids)."""
NATIVE_SYSTEM = """SOURCE ANALYSIS ONLY. Image 1 is a full frame, image 2 a NATIVE-resolution crop of it (no resampling), images 3-4
the neighbouring frames. Describe only what the crop shows in relation to the whole frame and the neighbours. Return strict JSON:
{"relations": [{"relation": str, "dimensions": [str]}], "changes_vs_neighbours": str, "uncertainty": [str]}."""


@dataclass
class RealLoopConfig:
    max_window_s: float = 12.0
    min_window_s: float = 2.0
    max_windows_per_film: int = 10
    target_per_packet: int = 8
    native_followups_per_sequence: int = 3
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
    def run(self, *, until: str = "S9") -> dict:
        st = self.ws.store()
        try:
            done = {t["stage"]: t for t in st.list("LoopTransition") if t["run_id"] == self.run_id and t["status"] == "COMPLETED"}
            trace = []
            for s in STAGES:
                if s in done:
                    trace.append({"stage": s, "status": "COMPLETED", "resumed_from_store": True})
                    if s == until:
                        break
                    continue
                try:
                    status, out = getattr(self, f"_{s.lower()}")(st)
                except Blocked as b:
                    status, out = "STOPPED", {"stop_reason": b.code, "blocked": b.to_dict()}
                self._commit(st, s, status, out)
                trace.append({"stage": s, "status": status, "reason": out.get("stop_reason")})
                if status != "COMPLETED":
                    return {"run_id": self.run_id, "stopped_at": s, "reason": out.get("stop_reason"), "trace": trace}
                if s == until:
                    break
            return {"run_id": self.run_id, "completed_through": trace[-1]["stage"] if trace else None, "trace": trace}
        finally:
            st.close()

    def _commit(self, st, stage, status, outputs):
        st.put("LoopTransition", f"{self.run_id}:{stage}", {"run_id": self.run_id, "stage": stage, "status": status,
                                                              "consumer": CONSUMERS[stage], "outputs": outputs, "mode": "REAL",
                                                              "evidence_origin": self.p.evidence_origin,
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
        if len(out) > self.cfg.max_windows_per_film:
            step = len(out) / self.cfg.max_windows_per_film
            out = [out[int(i * step)] for i in range(self.cfg.max_windows_per_film)]
        return out

    def _s0(self, st):
        from ..reference.roles import role_status
        from ..selection.first15 import propose_selection, validate_candidate
        rs = role_status(self.ws)
        if not rs["base_five_confirmed"]:
            return "STOPPED", {"stop_reason": "SOURCE_ROLES_UNCONFIRMED", "unconfirmed": rs["unconfirmed"], "resolutions": rs["resolutions"]}
        lock = self._lock()
        base = [s["sha256"] for s in lock["sources"] if s["role"] == "BASE_FILM"]
        vis = self._vision()
        made, rejected = 0, []
        for sha in base:
            sv = st.get("FilmSurvey", sha)
            if not sv:
                raise Blocked("NO_SURVEY", sha[:12])
            src, idx, cache = self._film(sha)
            for (a, b) in self._windows(idx, sv):
                cid = f"win_{sha[:10]}_{a}_{b}"
                if st.get("CandidateSequence", cid):
                    continue
                keys = [a, (a + b) // 2, b]
                imgs = [(f"FRAME {sha[:16]}:{k} pts_time={idx[k]['pts_time']:.6f}", cache(idx[k])["png"], src["width"], src["height"]) for k in keys]
                resp = vis.request_json(f"rat-{cid}", "window_rationale", RATIONALE_SYSTEM,
                                        json.dumps({"window": {"start": a, "end": b}, "frames": keys, "window_index": made}), imgs,
                                        source_shas=[sha])
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
        cands = [c for c in st.list("CandidateSequence") if c.get("observer") == "VLM" and c["film_sha"] in base]
        lens = {sha: len(self._film(sha)[1]) for sha in base}
        man = propose_selection(cands, base, index_lengths=lens)
        st.put("SelectedSequenceManifest", "REAL:15", man)
        out = {"candidates": len(cands), "new_rationales": made, "selection_status": man["status"], "selected": man.get("selected_count"),
               "manifest_sha": man.get("manifest_sha"), "rejected": len(man.get("rejected", []))}
        if man["status"] != "PROPOSED_AWAITING_USER_REVIEW":
            return "STOPPED", {**out, "stop_reason": "SELECTION_INCOMPLETE"}
        if not st.get("SelectionApproval", man["manifest_sha"]):
            return "STOPPED", {**out, "stop_reason": "AWAITING_SELECTION_APPROVAL",
                               "human_next_step": f"vme selection approve --manifest-sha {man['manifest_sha']} --by <name>"}
        six = st.get("SpecialIntroSelection", "REAL")
        out["sixth"] = "LOCKED" if six and six.get("status") == "LOCKED" else "PENDING_HUMAN_BOUNDARY_LOCK"
        return "COMPLETED", out

    # ---- S1: every frame of the selected windows, witnesses, native-detail follow-ups ------------------
    def _s1(self, st):
        from ..vision.runner import PacketRunner, plan_packets, coverage_for_range
        from ..investigation.evidence import build_event_graph
        man = st.get("SelectedSequenceManifest", "REAL:15")
        intervals = [(s["film_sha"], s["start_frame_index"], s["end_frame_index_inclusive"], s["candidate_id"]) for s in man["selected"]]
        six = st.get("SpecialIntroSelection", "REAL")
        if six and six.get("status") == "LOCKED":
            intervals.append((six["clip_sha256"], six["start_frame_index"], six["end_frame_index_inclusive"], "SIXTH"))
        vis = self._vision()
        pass_id = f"{self.run_id}-L0"
        cov_all, pending, wit, native = {}, [], 0, 0
        for film, a, b, seq in intervals:
            src, idx, cache = self._film(film)
            plans = plan_packets(idx, a, b, film_sha=film, pass_id=pass_id, cluster_id=seq, model_version=vis.caps.model_id,
                                 max_images=vis.caps.max_images_per_request, target_per_packet=self.cfg.target_per_packet)
            pr = PacketRunner(st, self.ws.vision_dir, idx, cache, vis, source_is_synthetic=False,
                              active_questions=[{"question_id": f"QC-{seq}", "text": "Which visible relations make this window's art and "
                                                 "motion work, and what must a producer decide for a NEW subject?"}])
            pr.register(plans)
            res = pr.resume(plans)
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
            native += self._native_followups(st, vis, film, seq, obs, idx, cache, src)
        if pending:
            codes = {s for p in pending for s in p["packets"].values()}
            reason = "BLOCKED_AUTHORIZATION" if "BLOCKED_CONSENT" in codes else "PROVIDER_PENDING_OR_REINSPECTION"
            return "STOPPED", {"stop_reason": reason, "pending": pending[:5], "states": sorted(codes)}
        incomplete = [k for k, v in cov_all.items() if not v["complete"]]
        if incomplete:
            return "STOPPED", {"stop_reason": "SELECTED_RANGE_NOT_FULLY_SEEN", "sequences": incomplete}
        return "COMPLETED", {"sequences": len(intervals), "frames_verified": sum(v["verified"] for v in cov_all.values()),
                             "statuses": sorted({s for v in cov_all.values() for s in v["statuses"]}), "witnesses": wit,
                             "native_followups": native, "sixth_included": any(i[3] == "SIXTH" for i in intervals),
                             "evidence_origin": self.p.evidence_origin}

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

    def _native_followups(self, st, vis, film, seq, obs, idx, cache, src) -> int:
        from ..reference.frames import native_crop
        done = 0
        for o in obs:
            for f in o.get("native_detail_followups") or []:
                if done >= self.cfg.native_followups_per_sequence or not isinstance(f, dict) or not f.get("region"):
                    continue
                k = int(str(o["frame_id"]).split(":")[1])
                r = f["region"]
                wid = f"W-{film[:10]}-{k}-native-{r['x']}-{r['y']}"
                if st.get("Witness", wid):
                    done += 1
                    continue
                full = cache.frame(k)
                crop = native_crop(full, int(r["x"]), int(r["y"]), int(r["w"]), int(r["h"]))
                nb = [cache.frame(j) for j in (max(0, k - 1), min(len(idx) - 1, k + 1))]
                imgs = [(f"FULL {film[:16]}:{k}", full.png_bytes, full.width, full.height),
                        (f"NATIVE_CROP {film[:16]}:{k} x={r['x']} y={r['y']} w={r['w']} h={r['h']}", crop.png_bytes, crop.output_width, crop.output_height)]
                imgs += [(f"NEIGHBOUR {film[:16]}:{x.presentation_index}", x.png_bytes, x.width, x.height) for x in nb]
                resp = vis.request_json(f"nd-{wid}", "native_detail", NATIVE_SYSTEM, json.dumps({"reason": f.get("reason"), "frame": k}), imgs,
                                        source_shas=[film])
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
                done += 1
        return done

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
        for d in DIMENSIONS:
            owners = [x for x in decs if d in x.get("dimension_tags", [])]
            if owners:
                ops = sorted({o for x in owners for b in x["branches"] for o in b["operation_node_ids"]})
                set_dimension(L, d, "RELEVANT_SUPPORTED", evidence=ev(seen.get(d, [])), why_relevant="evidenced decision exists", production_consumers=ops)
            elif d in seen and d not in plan["required_dimensions"]:
                set_dimension(L, d, "NOT_APPLICABLE_WITH_REASON", evidence=ev(seen[d]), why_relevant="observed in sources",
                              inapplicability_reason="observed in selected windows but not required by this original scope "
                                                     "(production-decision coverage is scoped; kept as evidence for later scopes)")
            elif d in seen:
                set_dimension(L, d, "RELEVANT_UNKNOWN", evidence=ev(seen[d]), why_relevant="observed in selected windows; no decision yet",
                              missing_decisions=[f"decision for {d}"])
            elif d in plan["required_dimensions"]:
                set_dimension(L, d, "PENDING_SOURCE", evidence=[], why_relevant="required by the original scope, not observed in selected windows")
            else:
                set_dimension(L, d, "NOT_APPLICABLE_WITH_REASON", evidence=[], why_relevant="not required by scope",
                              inapplicability_reason="not required by the original scope and not observed")
        for j in plan["joint_choices"]:
            dims = set(j["dimensions"])
            sup = [w for w in wits if dims <= set(w.get("dimensions", []))] + [r for r in rels if dims <= set(r["dimensions"])]
            set_relation(L, j["joint_id"], j["dimensions"], "SUPPORTED" if sup else "UNKNOWN", evidence=[],
                         producing_effect="joint construction must be decided together", missing_decisions=[] if sup else [j["joint_id"]])
        return L

    def _s2(self, st):
        from ..style.coverage import OriginalScope, review_visual_model_completeness, reverse_plan, cluster_gaps
        from ..investigation.controller import ActiveArtProblem, LoopController, ProblemContext
        from ..skills.operators import registered
        from ..style.authoring import author_decision, decision_id_for
        s1 = self._out(st, "S1")
        brief = self._brief(st)
        if not brief.get("scope"):
            raise Blocked("BRIEF_WITHOUT_SCOPE", "the original brief must declare its typed scope")
        scope = OriginalScope(scope_id=brief["brief_id"], **brief["scope"])
        plan = reverse_plan(scope)
        vis = self._vision()
        frame_state = "ALL_TARGET_FRAMES_SEEN" if s1["frames_verified"] else "PARTIAL"
        attempts: dict[str, int] = {}
        trace = st.get("RealInvestigationTrace", self.run_id) or {"steps": []}
        for _ in range(self.cfg.max_questions):
            L = self._ledger(st, plan, frame_state)
            decs = [d for d in st.list("ConditionalVisualDecision") if not d.get("synthetic")]
            rev = review_visual_model_completeness(L, scope, decs, registered())
            st.put("CoverageReview", self.run_id, rev)
            st.put("VisualModelCoverageLedger", self.run_id, L)
            if rev["review"]["image_trial_ready"]:
                st.put("RealInvestigationTrace", self.run_id, trace)
                return "COMPLETED", {"coverage_state": rev["review"]["state"], "questions": len(trace["steps"]),
                                     "decisions": [d["decision_id"] for d in decs if d["status"] != "RESEARCH_ONLY"],
                                     "resolved_gaps": sorted({s["gap_signature"] for s in trace["steps"] if s.get("decision_changed")})}
            g = rev["controlling_gap"]
            sig = f"{g['kind']}|{'+'.join(g['dimensions'])}|{g.get('joint_id') or g.get('choice_id')}"
            if g["kind"] in ("MISSING_SOURCE", "CONTRADICTED", "MISSING_OPERATION", "PROMPT_AUTHORITY"):
                st.put("RealInvestigationTrace", self.run_id, trace)
                return "STOPPED", {"stop_reason": f"BLOCKER_{g['kind']}", "gap": g, "ticket": rev["question_ticket"], "questions": len(trace["steps"])}
            attempts[sig] = attempts.get(sig, 0) + 1
            if attempts[sig] > self.cfg.max_attempts_per_gap * 3:
                st.put("RealInvestigationTrace", self.run_id, trace)
                return "STOPPED", {"stop_reason": "GAP_NOT_CLOSED_BY_EVIDENCE", "gap": g, "questions": len(trace["steps"])}
            comp = next((c for c in cluster_gaps(rev["gap_details"]) if g["gap_id"] in c), [g["gap_id"]])
            cl = [x for x in rev["gap_details"] if x["gap_id"] in comp]
            dims = sorted(set(g["dimensions"]))
            req = self._required_branches(plan, dims)
            did = decision_id_for(dims)
            refs, contrast = self._pick_witnesses(st, dims)
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
            for wid in (q.observed_contrast_with_witness_ids or refs)[:6]:
                w = wits[wid]
                _, idx, cache = self._film(w["film_sha256"])
                fr = cache.frame(w["frame_start"])
                imgs.append((f"WITNESS {wid} frame={w['film_sha256'][:16]}:{w['frame_start']} pts_time={w.get('pts_time')}", fr.png_bytes, fr.width, fr.height))
            payload = {"question": q.to_dict(), "dimensions": dims, "required_branches": req if q.owner_stage == "STYLE_CONDITIONS" else [],
                       "allowed_operations": sorted({o for r in req for o in r["operation_ids"]}) or ["op.whole_scene"]}
            task = "qa-" + digest([q.question_text, q.planned_witness_or_input_ids, dims])[:24]
            ans = vis.request_json(task, "question_answer", QA_SYSTEM, json.dumps(payload), imgs,
                                   source_shas=sorted({wits[w]["film_sha256"] for w in (q.observed_contrast_with_witness_ids or refs)[:6]}))

            def writer(qq, aa, _dims=dims, _req=req):
                return author_decision(st, qq.to_dict(), aa, dims=_dims, registered_ops=registered(), required_branches=_req)
            try:
                eff = lc.apply_answer(p, q, ans, decision_writer=writer)
            except Blocked as b:
                eff = {"status": "UNKNOWN", "decision_changed": False, "blocked": b.code}
            if q.owner_stage == "STYLE_CONDITIONS" or eff.get("decision_changed"):
                from ..style.authoring import register_relations_from_answer
                if q.answer_status in ("OBSERVED", "INFERRED"):
                    register_relations_from_answer(st, q.to_dict(), ans, dims)
            trace["steps"].append({"question_id": q.question_id, "stage": q.owner_stage, "gap": g["gap_id"], "gap_signature": sig,
                                   "dims": dims, "question": q.question_text[:400], "task": task, "witnesses": [i[0] for i in imgs],
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

    @staticmethod
    def _pick_witnesses(st, dims: list[str]) -> tuple[list, list]:
        ws = [w for w in st.list("Witness") if set(w.get("dimensions", [])) & set(dims)]
        ws.sort(key=lambda w: (-len(set(w["dimensions"]) & set(dims)), w["witness_id"]))
        refs, films = [], set()
        for w in ws:
            if w["film_sha256"] not in films and w["evidence_kind"] == "FULL_FRAME":
                refs.append(w["witness_id"])
                films.add(w["film_sha256"])
            if len(refs) >= 3:
                break
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
        from ..style.authoring import author_skill, verify_structural_derivation
        from ..style.coverage import OriginalScope, review_visual_model_completeness
        from ..skills.operators import registered
        decs = [d for d in st.list("ConditionalVisualDecision") if not d.get("synthetic") and d["status"] != "RESEARCH_ONLY"]
        version = f"0.{len(st.versions('RealSkillVersion', self.run_id)) + 1}"
        folder = self.ws.skills_dir / f"real-{self.run_id.lower()}"
        oc = {"op.whole_scene": {"width": 1536, "height": 864, "format": "PNG", "asset_kind": "WHOLE_SCENE"},
              **{k: {"width": 1024, "height": 1024, "format": "PNG", "asset_kind": "CHARACTER"} for k in
                 ("op.canonical_character", "op.face_view_state", "op.hand_prop_contact", "op.region_edit")}}
        if not (folder / "FROZEN.json").exists():
            res = author_skill(folder, decs, skill_id=f"real-{self.run_id.lower()}", version=version, evidence_origin=self.p.evidence_origin,
                               output_contracts=oc)
        else:
            from ..skills.skill import skill_hash
            res = {"folder": str(folder), "skill_hash": skill_hash(folder), "derivations": "FROZEN (unchanged)"}
        v = verify_structural_derivation(folder)
        if not v["ok"]:
            return "STOPPED", {"stop_reason": "CLAUSE_DERIVATION_BROKEN", "problems": v["problems"][:5]}
        brief = self._brief(st)
        scope = OriginalScope(scope_id=brief["brief_id"], **brief["scope"])
        L = st.get("VisualModelCoverageLedger", self.run_id)
        skill_decs = json.loads((folder / "decisions.json").read_text(encoding="utf-8"))
        rev = review_visual_model_completeness(L, scope, skill_decs, registered())
        st.put("RealSkillVersion", self.run_id, {"version": version, **{k: v for k, v in res.items() if k != "derivations"}})
        if not rev["review"]["image_trial_ready"]:
            return "STOPPED", {"stop_reason": rev["review"]["state"], "gap": rev["controlling_gap"]}
        return "COMPLETED", {"skill_folder": str(folder), "skill_hash": res["skill_hash"], "version": version, "derivations": res["derivations"],
                             "coverage_state": rev["review"]["state"], "evidence_origin": self.p.evidence_origin,
                             "artistic_quality": "ARTISTIC_QUALITY_UNPROVEN"}

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
        if gk.state(self.run_id)["state"] == "AWAITING_PROVIDER_OR_SOURCE":
            gk.transition(self.run_id, "ART_GENERATING", reason="S5", synthetic=self.p.evidence_origin != "REAL_VLM")
        from ..skills.skill import load_skill
        have = {n["id"] for n in load_skill(s4["skill_folder"])["recipes"]["main"]["nodes"]}
        nodes = [n for n in ("n_whole_scene", "n_canonical_character") if n in have]
        res = execute(s4["skill_folder"], brief, gateway=g, caps=snap, node_ids=nodes, pinned_skill_hash=s4["skill_hash"], store=st)
        if gk.state(self.run_id)["state"] == "ART_GENERATING":
            gk.transition(self.run_id, "AWAITING_ARTWORK_REVIEW", reason="full-resolution stills ready")
        return "COMPLETED", {k: {kk: vv for kk, vv in v.items() if kk != "result"} | {"label": v["result"]["label"],
                                                                                        "request_body_sha256": v["result"]["request_body_sha256"]}
                             for k, v in res.items()}

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
            return "STOPPED", {"stop_reason": "ARTWORK_REJECTED", "next_question": nq}
        s5 = self._out(st, "S5")
        return "STOPPED", {"stop_reason": "AWAITING_ARTWORK_REVIEW", "images": [v["image"] for v in s5.values()],
                           "human_next_step": f"vme review serve --run {self.run_id}  (or vme art approve|reject)"}

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

    # ---- S7: identity-conditioned states, WHOLE_STATE_SWAP pack, human asset verdict --------------------
    def _s7(self, st):
        from ..review.approvals import GateKeeper
        from ..artwork.character import derive_animation_demand, character_construction_plan
        from ..artwork.raster import decode_raster
        from ..skills.runtime import execute
        from ..util import sha256_file
        gk = GateKeeper(st)
        s = gk.state(self.run_id)
        prev = (st.get("LoopTransition", f"{self.run_id}:S7") or {}).get("outputs", {})
        if s["state"] in ("ASSETS_APPROVED", "VIDEO_RENDERING", "AWAITING_VIDEO_REVIEW") and s["required_asset_approval_ids"]:
            return "COMPLETED", {**prev, "asset_approval_id": s["required_asset_approval_ids"][0]}
        if s["state"] == "AWAITING_ASSET_REVIEW":
            return "STOPPED", {**prev, "stop_reason": "AWAITING_ASSET_REVIEW"}
        if s["state"] == "ASSETS_REJECTED":
            return "STOPPED", {"stop_reason": "ASSETS_REJECTED", "next_question": self._question_from_human_review(st, "asset")}
        s4, s5 = self._out(st, "S4"), self._out(st, "S5")
        brief = self._brief(st)
        actor = next(x for x in brief["scope"]["subjects"] if x.get("kind") == "character")
        demand = derive_animation_demand(actor["id"], brief["shot_plan"].get("actions", []))
        plan = character_construction_plan(actor["id"], brief["brief_id"], s4["skill_hash"], demand)
        st.put("CharacterConstructionPlan", f"{self.run_id}:{actor['id']}", plan)
        if s["state"] == "ARTWORK_APPROVED":
            gk.transition(self.run_id, "ASSET_PREPARING", reason="S7")
        canon = s5["n_canonical_character"]
        ident = {f"{actor['id']}:canonical": {"path": canon["image"], "sha256": canon["sha"], "approved": True}}
        b = dict(brief)
        b["subjects"] = [dict(x, identity_asset_id=f"{actor['id']}:canonical") if x["id"] == actor["id"] else x for x in brief["subjects"]]
        g, snap = self._gateway(st)
        states, not_made = {}, []
        for step in plan["generation_sequence"]:
            if step["kind"] != "CHARACTER_STATE":
                continue
            if step["step"].startswith("view:"):
                nid, over = "n_face_view_state", {"view": step["step"].split(":", 1)[1]}
            elif step["step"].startswith("grip:"):
                nid, over = "n_hand_prop_contact", {"action": "grip"}
            else:
                not_made.append({"state": step["step"], "reason": "NO_DECISION_CONDITION_FOR_EXPRESSION (open targeted question)"})
                continue
            try:
                r = execute(s4["skill_folder"], b, gateway=g, caps=snap, node_ids=[nid], pinned_skill_hash=s4["skill_hash"],
                            identity_assets=ident, slot_overrides={nid: over}, store=st)[nid]
            except Blocked as e:
                not_made.append({"state": step["step"], "reason": e.code, "ticket": e.data.get("ticket")})
                continue
            states[step["step"]] = {"path": r["image"], "sha256": r["sha"], "identity_reference_sha256": canon["sha"],
                                    "reference_shas": r["reference_shas"], "clause_ids": r["clause_ids"]}
        cra = decode_raster(Path(canon["image"]).read_bytes(), asset_id="canon", owner=actor["id"], skill_version=s4["skill_hash"])
        problems = []
        for k, v in states.items():
            ra = decode_raster(Path(v["path"]).read_bytes(), asset_id=k, owner=actor["id"], skill_version=s4["skill_hash"])
            if (ra.width, ra.height) != (cra.width, cra.height):
                problems.append(f"STATE_CANVAS_MISMATCH:{k}")
            if canon["sha"] not in v["reference_shas"]:
                problems.append(f"STATE_NOT_CONDITIONED_ON_CANONICAL:{k}")
        pack = {"method": "WHOLE_STATE_SWAP", "method_reason": "no verified segmentation/inpainting capability; whole drawings swap, no pretend layers",
                "canonical": {"path": canon["image"], "sha256": canon["sha"], "width": cra.width, "height": cra.height},
                "background": s5["n_whole_scene"]["image"], "states": states, "not_generated": not_made, "problems": problems}
        pack_path = self.dir / "asset_pack.json"
        from ..util import atomic_write_json
        atomic_write_json(pack_path, pack)
        if gk.state(self.run_id)["state"] == "ASSET_PREPARING":
            gk.transition(self.run_id, "AWAITING_ASSET_REVIEW", reason="WHOLE_STATE_SWAP pack ready")
        files = [canon["image"], s5["n_whole_scene"]["image"]] + [v["path"] for v in states.values()]
        out = {"pack": str(pack_path), "states": list(states), "not_generated": not_made, "problems": problems,
               "files": files, "file_shas": [sha256_file(f) for f in files]}
        if problems:
            return "STOPPED", {**out, "stop_reason": "ASSET_PACK_DEFECTS"}
        return "STOPPED", {**out, "stop_reason": "AWAITING_ASSET_REVIEW"}

    # ---- S8: render approved art + states ----------------------------------------------------------
    def _s8(self, st):
        from ..render.renderer import render_video
        from ..review.approvals import GateKeeper
        gk = GateKeeper(st)
        if gk.state(self.run_id)["state"] == "AWAITING_VIDEO_REVIEW":
            prev = (st.get("LoopTransition", f"{self.run_id}:S8") or {}).get("outputs", {})
            return "COMPLETED", prev
        s7 = (st.get("LoopTransition", f"{self.run_id}:S7") or {})["outputs"]
        pack = read_json(s7["pack"])
        brief = self._brief(st)
        sp = brief["shot_plan"]
        R = self.cfg.render
        W, H, fps, n = R["width"], R["height"], sp.get("fps", R["fps"]), sp.get("frames", 60)
        ch = int(H * 0.8)
        actor = {"id": "actor", "src": "canonical.png", "x": int(W * 0.55), "y": H - ch, "w": ch, "h": ch, "z": 1,
                 "keyframes": sp.get("actor_keyframes") or [{"frame": 0, "x": int(W * 0.55)}, {"frame": n - 1, "x": int(W * 0.5)}], "states": []}
        assets = {"background.png": pack["background"], "canonical.png": pack["canonical"]["path"]}
        for ev in sp.get("events", []):
            st_id = ev["state"]
            if st_id in pack["states"]:
                name = f"state_{len(assets)}.png"
                assets[name] = pack["states"][st_id]["path"]
                actor["states"].append({"from_frame": ev["from"], "to_frame": ev["to"], "src": name})
        scene = {"width": W, "height": H, "fps": fps, "durationInFrames": n, "background": "#000000",
                 "camera": {"keyframes": sp.get("camera") or [{"frame": 0, "x": 0, "y": 0, "scale": 1.0}]},
                 "layers": [{"id": "bg", "src": "background.png", "x": 0, "y": 0, "w": W, "h": H, "z": 0}, actor]}
        rep = render_video(scene, assets, self.dir / "integrated.mp4", gate=gk, run_id=self.run_id)
        st.put("RenderReport", self.run_id, rep)
        out = {"mp4": rep["mp4"], "mp4_sha256": rep["mp4_sha256"], "motion": rep["motion"]["verdict"], "ffprobe_ok": rep["ffprobe"]["ok"],
               "state_swaps": len(actor["states"]), "label": rep["quality_claim"]}
        return "COMPLETED", out

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
        st.put("TransferRecord", self.run_id, {"holdout": sealed[0], "status": rec["status"], "output": r["n_whole_scene"]["sha"], "next_question": nq})
        return "COMPLETED", {"transfer": "TRANSFER_PENDING_AWAITING_REVIEW", "holdout": sealed[0], "output_sha": r["n_whole_scene"]["sha"],
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
