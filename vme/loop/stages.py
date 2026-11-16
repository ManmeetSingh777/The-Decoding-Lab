"""S0–S9 closed learning loop with real handlers, durable transitions and crash/resume (Addendum 26 §5).

Each stage reads persisted artefacts from the previous stage, calls the real module
functions, persists typed outputs and a `LoopTransition` naming its code consumer.
mode=SYNTHETIC_FIXTURE drives the whole chain offline with labelled fixtures (mock VLM,
offline recording image transport, fixture human-review simulation). mode=REAL runs on the
actual source films and stops truthfully at the first consent/authorization barrier.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path


from ..util import Blocked, now_iso, read_json
from ..state.workspace import Workspace
from ..vision.runner import maybe_crash

STAGES = ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9")
CONSUMERS = {
    "S0": "vme.selection.first15:propose_selection + vme.selection.sixth:locate_sixth_intro",
    "S1": "vme.vision.runner:PacketRunner.run + vme.investigation.evidence:build_event_graph",
    "S2": "vme.investigation.controller:LoopController.step_question/apply_answer",
    "S3": "vme.style.decisions:witness_to_decision",
    "S4": "vme.skills.skill:write_skill/freeze_skill + vme.style.coverage:review_visual_model_completeness",
    "S5": "vme.compiler.compiler:StyleProgramCompiler.compile + vme.providers.gateway:StyleImageGateway.submit",
    "S6": "vme.review.approvals:GateKeeper.submit_art_verdict",
    "S7": "vme.artwork.character:character_construction_plan + vme.artwork.assets:verify_pack + GateKeeper.submit_asset_verdict",
    "S8": "vme.render.renderer:render_video (after GateKeeper.authorize_render)",
    "S9": "vme.experiments.experiments:HoldoutRegistry + controller.observe_new_output",
}


class LoopRunner:
    def __init__(self, ws: Workspace, *, run_id: str, mode: str = "SYNTHETIC_FIXTURE", simulate_human: bool = False,
                 sources_folder: str | None = None):
        if mode == "REAL":
            raise Blocked("REAL_MODE_MOVED", "the REAL path lives in vme.loop.real.RealLoopRunner (no fixtures)")
        if mode != "SYNTHETIC_FIXTURE":
            raise Blocked("BAD_MODE")
        if simulate_human and mode != "SYNTHETIC_FIXTURE":
            raise Blocked("HUMAN_SIMULATION_ONLY_FOR_FIXTURES")
        self.ws, self.run_id, self.mode, self.sim = ws, run_id, mode, simulate_human
        self.sources = sources_folder
        self.dir = ws.root / "runs" / run_id
        self.dir.mkdir(parents=True, exist_ok=True)

    # ---- persistence -------------------------------------------------------------------------
    def _done(self, st) -> dict:
        out = {}
        for t in st.list("LoopTransition"):
            if t["run_id"] == self.run_id and t["status"] == "COMPLETED":  # STOPPED stages are re-attempted
                out[t["stage"]] = t
        return out

    def _commit(self, st, stage: str, status: str, outputs: dict, stop_reason: str | None = None) -> dict:
        t = {"run_id": self.run_id, "stage": stage, "status": status, "consumer": CONSUMERS[stage], "outputs": outputs,
             "stop_reason": stop_reason, "mode": self.mode, "at": now_iso()}
        st.put("LoopTransition", f"{self.run_id}:{stage}", t)
        self.ws.update_state(current_stage=stage, last_completed_unit=f"{self.run_id}:{stage}:{status}")
        maybe_crash(f"loop_after_{stage}")
        return t

    def run(self, *, until: str = "S9") -> dict:
        st = self.ws.store()
        try:
            done = self._done(st)
            trace = []
            for s in STAGES:
                if s in done:
                    trace.append({"stage": s, "status": done[s]["status"], "resumed_from_store": True})
                    if s == until:
                        break
                    continue
                handler = getattr(self, f"_{s.lower()}")
                try:
                    status, outputs = handler(st)
                except Blocked as b:
                    self._commit(st, s, "STOPPED", {"blocked": b.to_dict()}, stop_reason=b.code)
                    trace.append({"stage": s, "status": "STOPPED", "reason": b.code})
                    return {"run_id": self.run_id, "stopped_at": s, "reason": b.code, "trace": trace}
                self._commit(st, s, status, outputs, stop_reason=outputs.get("stop_reason"))
                trace.append({"stage": s, "status": status})
                if status == "STOPPED":
                    return {"run_id": self.run_id, "stopped_at": s, "reason": outputs.get("stop_reason"), "trace": trace}
                if s == until:
                    break
            return {"run_id": self.run_id, "completed_through": trace[-1]["stage"] if trace else None, "trace": trace}
        finally:
            st.close()

    def _out(self, st, stage: str) -> dict:
        t = st.get("LoopTransition", f"{self.run_id}:{stage}")
        if not t:
            raise Blocked("MISSING_UPSTREAM_STAGE", stage)
        return t["outputs"]

    # ---- S0 ----------------------------------------------------------------------------------
    def _s0(self, st):
        from ..selection.first15 import propose_selection
        from ..selection.sixth import locate_sixth_intro
        from ..fixtures import loop_fixtures as fx
        cands = fx.synthetic_candidates()
        man = propose_selection(cands, fx.SYNTHETIC_BASE_FILMS)
        st.put("SelectedSequenceManifest", f"{self.run_id}:15", man)
        clip = fx.make_sixth_clip(self.dir / "synthetic_sixth.mp4", segments=[("gray", 10), ("red", 31), ("blue", 21)])
        idx, loader = fx.index_and_loader(clip, self.dir / "sixth_idx")
        res = locate_sixth_intro(clip, idx[0]["film_sha256"], idx, classifier=fx.colour_classifier_factory(loader),
                                 classifier_kind="SYNTHETIC_COLOUR_FIXTURE", search_window_s=(0, 10))
        st.put("SixthIntroLocatorResult", self.run_id, res.to_dict())
        return "COMPLETED", {"selection": f"{self.run_id}:15", "selection_status": man["status"], "selected_count": man["selected_count"],
                             "sixth_status": res.status, "sixth_interval": res.proposed_interval}

    # ---- S1 ----------------------------------------------------------------------------------
    def _s1(self, st):
        from ..vision.runner import PacketRunner, plan_packets, coverage_for_range
        from ..vision.providers import MockVisionProvider
        from ..investigation.evidence import build_event_graph, reverse_timeline_check
        from ..vision.contracts import frame_id_for
        from ..fixtures import loop_fixtures as fx
        clip = fx.make_clip(self.dir / "synthetic_seq.mp4", frames=20)
        idx, loader = fx.index_and_loader(clip, self.dir / "seq_idx")
        film = idx[0]["film_sha256"]
        prov = MockVisionProvider(self.dir / "mock_remote", max_images=8)
        plans = plan_packets(idx, 0, len(idx) - 1, film_sha=film, pass_id=f"{self.run_id}-pass1", cluster_id="CL-SYN-01",
                             model_version="mock-vlm-1", max_images=prov.caps.max_images_per_request, target_per_packet=6)
        pr = PacketRunner(st, self.ws.vision_dir, idx, loader, prov, source_is_synthetic=True,
                          active_questions=[{"question_id": "Q-SEED", "text": "SYNTHETIC: how does the focal subject change across frames?"}])
        pr.register(plans)
        pr.resume(plans)
        cov = coverage_for_range(st, film, f"{self.run_id}-pass1", 0, len(idx) - 1)
        obs = []
        for p in plans:
            fp = self.ws.vision_dir / p.pass_id / p.packet_id / "frames.jsonl"
            if fp.exists():
                obs += [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines() if l.strip()]
        g = build_event_graph(obs)
        rv = reverse_timeline_check(g, [frame_id_for(film, i) for i in range(len(idx))])
        st.put("CrossFrameEventGraph", self.run_id, g)
        if not cov["complete"]:
            return "STOPPED", {"coverage": cov, "stop_reason": "SELECTED_RANGE_NOT_FULLY_SEEN"}
        return "COMPLETED", {"coverage": cov, "packets": [p.packet_id for p in plans], "event_graph_sha": g["graph_sha"],
                             "reverse_timeline": rv, "witness_bundle_ids": ["WB-SYN-01"], "provider_kind": "MOCK",
                             "coverage_label": "MOCK_VERIFIED_SYNTHETIC (not VLM_SEEN of any real film)"}

    # ---- S2 ----------------------------------------------------------------------------------
    def _ctx(self, st):
        from ..investigation.controller import ProblemContext
        from ..skills.operators import registered
        from ..fixtures import loop_fixtures as fx
        ws_ = fx.synthetic_witnesses()
        decs = {}
        t4 = st.get("LoopTransition", f"{self.run_id}:S4")
        if t4 and t4["outputs"].get("skill_folder") and Path(t4["outputs"]["skill_folder"], "decisions.json").exists():
            decs.update({d["decision_id"]: d for d in json.loads(Path(t4["outputs"]["skill_folder"], "decisions.json").read_text(encoding="utf-8"))})
        decs.update({d["decision_id"]: d for d in st.list("ConditionalVisualDecision") if d.get("run_id") == self.run_id})
        return ProblemContext(bundles={"WB-SYN-01": fx.synthetic_bundle().to_dict()}, witnesses=ws_, decisions=decs,
                              registered_operators={k: v for k, v in registered().items()},
                              provider_capabilities=["whole_scene", "canonical_character", "guided_pose_edit", "region_edit"])

    def _s2(self, st):
        from ..investigation.controller import ActiveArtProblem, LoopController
        from ..investigation.gaps import rank_gaps, select_cluster
        from ..fixtures import loop_fixtures as fx
        gaps = fx.synthetic_gaps()
        rk = rank_gaps(gaps)
        cl = select_cluster(gaps, rk["ranked_ids"], first_iteration=True)
        st.put("GapRanking", self.run_id, {"ranking": rk, "cluster": cl})
        ctx = self._ctx(st)
        lc = LoopController(st, ctx)
        p = ActiveArtProblem(**fx.synthetic_problem())
        lc.save(p)
        qs = []
        for _ in range(3):  # resolve sequentially; each question derives from the updated problem
            q = lc.step_question(p, gap_id=cl["cluster_gap_ids"][0])
            ans = fx.fixture_answer(q)
            eff = lc.apply_answer(p, q, ans, decision_writer=lambda q_, a_: self._write_decision(st, q_, a_))
            qs.append({"question_id": q.question_id, "stage": q.owner_stage, "text": q.question_text, "effect": eff})
            if eff.get("decision_changed"):
                break
        st.put("QuestionDerivationTrace", self.run_id, {"questions": qs, "problem_cluster": p.cluster_id})
        return "COMPLETED", {"questions": [x["question_id"] for x in qs], "stages": [x["stage"] for x in qs],
                             "cluster": cl["cluster_gap_ids"], "active_problem": p.cluster_id}

    def _write_decision(self, st, q, ans) -> dict | None:
        from ..style.decisions import witness_to_decision
        from ..skills.operators import registered
        from ..fixtures import loop_fixtures as fx
        if q.owner_stage != "STYLE_CONDITIONS":
            return None
        prop = fx.face_view_proposal_from_answer(ans)
        d = witness_to_decision(fx.synthetic_bundle(), prop, registered_operators=registered(),
                                substitutes=[{"noun": "robot engineer", "subject_kind": "machine"},
                                             {"noun": "tidal creature", "subject_kind": "creature"}]).to_dict()
        d["run_id"] = self.run_id
        st.put("ConditionalVisualDecision", d["decision_id"], d)
        return d

    # ---- S3 ----------------------------------------------------------------------------------
    def _s3(self, st):
        decs = [d for d in st.list("ConditionalVisualDecision") if d.get("run_id") == self.run_id]
        if not decs:
            return "STOPPED", {"stop_reason": "NO_DECISION_ENABLED_BY_ANSWERS"}
        ra = [d["decision_id"] for d in decs if d["status"] == "RESEARCH_ONLY"]
        if ra:
            return "STOPPED", {"stop_reason": f"RESEARCH_ONLY:{ra}"}
        return "COMPLETED", {"decisions": [d["decision_id"] for d in decs], "statuses": {d["decision_id"]: d["status"] for d in decs},
                             "evidence_scope": {d["decision_id"]: d["evidence_scope"] for d in decs}}

    # ---- S4 ----------------------------------------------------------------------------------
    def _s4(self, st):
        from ..skills.skill import freeze_skill
        from ..style.coverage import review_visual_model_completeness
        from ..skills.operators import registered
        from ..fixtures import loop_fixtures as fx
        folder = self.ws.skills_dir / f"{fx.SKILL_ID}__{self.run_id}"
        shutil.rmtree(folder, ignore_errors=True)
        s3_decs = [d for d in st.list("ConditionalVisualDecision") if d.get("run_id") == self.run_id]
        h = fx.build_synthetic_skill(folder, face_light_joint=True, grip_light_joint=True, decision_overrides=s3_decs)
        frz = freeze_skill(folder, observed_relations=fx.OBSERVED_RELATIONS, approved_by=fx.FIXTURE_REVIEWER)
        ledger, scope = fx.complete_ledger_and_scope()
        decisions = json.loads((folder / "decisions.json").read_text(encoding="utf-8"))
        rev = review_visual_model_completeness(ledger, scope, decisions, registered())
        st.put("CoverageReview", self.run_id, rev)
        if not rev["review"]["image_trial_ready"]:
            return "STOPPED", {"stop_reason": rev["review"]["state"], "coverage": rev["review"]}
        return "COMPLETED", {"skill_folder": str(folder), "skill_hash": h, "freeze": frz["result"], "coverage_state": rev["review"]["state"],
                             "scope_claim": rev["scope_claim"]}

    # ---- S5 ----------------------------------------------------------------------------------
    def _gateway(self, st, caps):
        from ..providers.gateway import StyleImageGateway, OfflineRecordingTransport
        from ..providers.runware import RunwareAdapter
        from ..providers.authorization import AuthorizationRegistry
        return StyleImageGateway(st, self.ws.artifacts_dir, RunwareAdapter(caps, OfflineRecordingTransport(self.dir / "offline_runware"),
                                                                          kind="OFFLINE_RECORDING"), AuthorizationRegistry(self.ws.state_dir))

    def _s5(self, st):
        from ..compiler.compiler import StyleProgramCompiler
        from ..review.approvals import GateKeeper
        from ..fixtures import loop_fixtures as fx
        s4 = self._out(st, "S4")
        caps = fx.fixture_caps()
        c = StyleProgramCompiler()
        g = self._gateway(st, caps)
        gk = GateKeeper(st)
        if gk.state(self.run_id)["state"] == "AWAITING_PROVIDER_OR_SOURCE":   # idempotent on resume after a kill mid-S5
            gk.transition(self.run_id, "ART_GENERATING", reason="S5", synthetic=True)
        out = {}
        for node in ("n1_scene", "n2_canonical"):
            job = c.compile(fx.synthetic_brief(), s4["skill_folder"], pinned_skill_hash=s4["skill_hash"], recipe_id="character_world",
                            node_id=node, caps=caps)
            st.put("CompiledImageJob", job.job_id, {"job_id": job.job_id, "payload": {k: v for k, v in job.logical_payload.items() if k != "inputs"},
                                                     "ref_shas": [r[1] for r in job.reference_images], "trace": job.trace})
            r = g.submit(job)
            out[node] = {"job_id": job.job_id, "image": r["outputs"][0]["path"], "sha": r["outputs"][0]["sha256"], "label": r["label"]}
        if gk.state(self.run_id)["state"] == "ART_GENERATING":
            gk.transition(self.run_id, "AWAITING_ARTWORK_REVIEW", reason="stills ready")
        return "COMPLETED", out

    # ---- S6 ----------------------------------------------------------------------------------
    def _s6(self, st):
        from ..review.approvals import GateKeeper, FIXTURE_SIGNER
        s5 = self._out(st, "S5")
        gk = GateKeeper(st)
        g = gk.state(self.run_id)
        if g["state"] == "ARTWORK_APPROVED" and g["required_art_approval_ids"]:   # a real human verdict arrived (CLI/review page)
            gk.verify_art_still_valid(self.run_id)
            return "COMPLETED", {"art_approval_id": g["required_art_approval_ids"][0], "synthetic_fixture": g.get("synthetic", False)}
        if g["state"] == "ARTWORK_REJECTED":
            return "STOPPED", {"stop_reason": "ARTWORK_REJECTED: return to the earliest failing stage; no animation"}
        if not self.sim:
            return "STOPPED", {"stop_reason": "AWAITING_ARTWORK_REVIEW", "review_images": [v["image"] for v in s5.values()]}
        a = gk.submit_art_verdict(self.run_id, image_paths=[v["image"] for v in s5.values()], brief_id="BRIEF-SYN-ANCHOR-01",
                                  skill_versions=[self._out(st, "S4")["skill_hash"]], verdict="APPROVED", defects=[],
                                  signed_by=FIXTURE_SIGNER)
        return "COMPLETED", {"art_approval_id": a["approval_id"], "signed_by": a["signed_by"], "synthetic_fixture": True}

    # ---- S7 ----------------------------------------------------------------------------------
    def _s7(self, st):
        from ..artwork.character import derive_animation_demand, character_construction_plan
        from ..artwork.assets import verify_pack
        from ..compiler.compiler import StyleProgramCompiler
        from ..review.approvals import GateKeeper, FIXTURE_SIGNER
        from ..fixtures import loop_fixtures as fx
        s4, s5 = self._out(st, "S4"), self._out(st, "S5")
        gk = GateKeeper(st)
        g = gk.state(self.run_id)
        if g["state"] == "ASSETS_APPROVED" and g["required_asset_approval_ids"]:
            prev = st.get("LoopTransition", f"{self.run_id}:S7") or {}
            return "COMPLETED", {**prev.get("outputs", {}), "asset_approval_id": g["required_asset_approval_ids"][0]}
        if g["state"] == "AWAITING_ASSET_REVIEW":
            return "STOPPED", {"stop_reason": "AWAITING_ASSET_REVIEW", **(st.get("LoopTransition", f"{self.run_id}:S7") or {}).get("outputs", {})}
        if g["state"] == "ASSETS_REJECTED":
            return "STOPPED", {"stop_reason": "ASSETS_REJECTED: repair canonical-conditioned variants; no animation"}
        if g["state"] != "ASSET_PREPARING":      # resuming after a kill mid-S7 keeps the already-entered state
            gk.transition(self.run_id, "ASSET_PREPARING", reason="S7")
        demand = derive_animation_demand("explorer", fx.synthetic_shot_actions())
        plan = character_construction_plan("explorer", "BRIEF-SYN-ANCHOR-01", s4["skill_hash"], demand)
        st.put("CharacterConstructionPlan", f"{self.run_id}:explorer", plan)
        canon = s5["n2_canonical"]
        identity = {"explorer:canonical": {"path": canon["image"], "sha256": canon["sha"], "approved": True}}
        brief = fx.synthetic_brief(subjects=[{**fx.synthetic_brief()["subjects"][0], "identity_asset_id": "explorer:canonical"}])
        caps = fx.fixture_caps()
        c, g = StyleProgramCompiler(), self._gateway(st, caps)
        states = {}
        for node in ("n3_view", "n4_grip"):
            slots = {"action": "grip"} if node == "n4_grip" else {}
            b = fx.synthetic_brief(subjects=brief["subjects"], slots=slots) if slots else brief
            job = c.compile(b, s4["skill_folder"], pinned_skill_hash=s4["skill_hash"], recipe_id="character_world", node_id=node,
                            caps=caps, identity_assets=identity)
            r = g.submit(job)
            states[node] = {"job_id": job.job_id, "image": r["outputs"][0]["path"], "sha": r["outputs"][0]["sha256"],
                            "identity_ref": canon["sha"]}
        pack = fx.fixture_layer_pack(self.dir / "pack", canonical_path=canon["image"], canonical_sha=canon["sha"], states=states)
        rep = verify_pack(pack)
        st.put("AssetReport", self.run_id, rep)
        if gk.state(self.run_id)["state"] == "ASSET_PREPARING":
            gk.transition(self.run_id, "AWAITING_ASSET_REVIEW", reason="pack ready")
        if not rep["ok"]:
            return "STOPPED", {"stop_reason": "ASSET_PACK_DEFECTS", "problems": rep["problems"]}
        if not self.sim:
            return "STOPPED", {"stop_reason": "AWAITING_ASSET_REVIEW"}
        files = sorted({l["image_path"] for l in pack["layers"]} | {s["path"] for s in pack["states"]} | {pack["clean_plate"]})
        a = gk.submit_asset_verdict(self.run_id, pack_manifest={"files": files}, verdict="APPROVED", signed_by=FIXTURE_SIGNER,
                                    character_family_ids=["explorer"])
        return "COMPLETED", {"asset_approval_id": a["approval_id"], "pack_files": files, "states": states, "pack": pack["pack_path"]}

    # ---- S8 ----------------------------------------------------------------------------------
    def _s8(self, st):
        from ..render.renderer import render_video
        from ..review.approvals import GateKeeper
        from ..fixtures import loop_fixtures as fx
        s7 = self._out(st, "S7")
        pack = read_json(s7["pack"])
        scene, assets = fx.fixture_scene_from_pack(pack)
        # R3 F15: an integrated render must state its motion expectation; this SYNTHETIC fixture scene is built to move
        scene["motion_contract"] = {"expected_independent_motion": True,
                                    "source": "SYNTHETIC fixture scene graph (engineering loop; not learned motion)"}
        rep = render_video(scene, assets, self.dir / "integrated_fixture.mp4", gate=GateKeeper(st), run_id=self.run_id)
        st.put("RenderReport", self.run_id, rep)
        if not rep["motion"]["ok"]:
            return "STOPPED", {"stop_reason": rep["motion"]["verdict"], "render": rep}
        return "COMPLETED", {"mp4": rep["mp4"], "mp4_sha256": rep["mp4_sha256"], "motion": rep["motion"]["verdict"],
                             "ffprobe_ok": rep["ffprobe"]["ok"], "label": "ANIMATION_FIXTURE_ONLY"}

    # ---- S9 ----------------------------------------------------------------------------------
    def _s9(self, st):
        from ..compiler.compiler import StyleProgramCompiler
        from ..experiments.experiments import HoldoutRegistry
        from ..investigation.controller import ActiveArtProblem, LoopController
        from ..fixtures import loop_fixtures as fx
        s4 = self._out(st, "S4")
        hr = HoldoutRegistry(self.dir / "holdouts.json")
        hid = hr.seal(fx.holdout_brief())
        brief = hr.access(hid, by_role="transfer_runner", skill_frozen_hash=s4["skill_hash"])
        caps = fx.fixture_caps()
        job = StyleProgramCompiler().compile(brief, s4["skill_folder"], pinned_skill_hash=s4["skill_hash"], recipe_id="character_world",
                                             node_id="n1_scene", caps=caps)
        r = self._gateway(st, caps).submit(job)
        rec = hr.record_result(hid, skill_hash_used=s4["skill_hash"])
        ctx = self._ctx(st)
        lc = LoopController(st, ctx)
        p = ActiveArtProblem(**st.get("ActiveArtProblem", "CL-SYN-01"))
        ctx.compile_trace = {"selected_decisions": job.trace["selected_decisions"], "skill_present_but_not_compiled": []}
        prev_q = p.current_question_id_or_null
        lc.observe_new_output(p, fx.synthetic_output_review(r["outputs"][0]["sha256"]))
        q = lc.step_question(p, gap_id="G-SYN-OUT-01")
        prev = st.get("NextQuestion", prev_q) if prev_q else None
        trec = {"holdout_id": hid, "status": rec["status"], "job_id": job.job_id, "output_sha": r["outputs"][0]["sha256"],
                "transfer_status": "TRANSFER_PENDING_AWAITING_REVIEW", "next_question": q.to_dict(),
                "previous_question_text": prev["question_text"] if prev else None,
                "question_changed": (prev is None) or prev["question_text"] != q.question_text}
        st.put("TransferRecord", self.run_id, trec)
        return "COMPLETED", {"transfer": trec["transfer_status"], "next_question_id": q.question_id, "next_stage": q.owner_stage,
                             "question_changed": trec["question_changed"]}
