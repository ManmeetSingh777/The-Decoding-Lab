"""Addendum 28 §5 — portable Investigation Capsule and cold-start verification (ST28-17..20).

`build_capsule` records, from durable state only: protocol version/sha, source lock + sixth lock state, per-frame coverage and the
first uncommitted frame, the active problem (controlling question + queued linked gaps + counterevidence), the latest committed
observation, every conditional decision, the operation DAG, provenance hashes (witnesses, raw model results, skill versions,
reference bytes), external-job/billing state, a pinned compile rehearsal hash and ONE exact next operation.

`import_and_verify` runs the cold-start algorithm in a fresh destination: hash-verify every artifact, verify the protocol
(identical or explicitly migrated), rebind films by SHA only, reconcile uncertain paid submissions (block), recompile the pinned
job and compare its logical hash byte-for-byte, write a factual reconstruction (no new style rules) and return the first
uncommitted operation. A missing artifact is a named blocker, never a smooth continuation.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..util import Blocked, atomic_write_json, digest, now_iso, read_json, sha256_file
from .workspace import Workspace

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "config" / "schemas" / "investigation_capsule_v28.json"


def _sdk_version() -> str:
    try:
        import anthropic
        return anthropic.__version__
    except Exception:  # pragma: no cover
        return "NOT_INSTALLED"


def _rebase(p: str, old_root: str, new_root: Path) -> Path:
    s = str(p).replace("\\", "/")
    o = str(old_root).replace("\\", "/")
    return Path(s.replace(o, str(new_root).replace("\\", "/"), 1)) if s.startswith(o) else Path(s)


def _uncertain_jobs(ws: Workspace, st) -> list[dict]:
    out = [{"provider": "runware", "job_key": k, "state": s, "task_uuid": t}
           for k, s, t in st.conn.execute("SELECT job_key, state, task_uuid FROM jobs WHERE state IN "
                                          "('INTENT_PERSISTED','IN_FLIGHT','RESPONSE_SAVED','UNKNOWN_BILLING')").fetchall()]
    vdir = ws.root / "providers" / "anthropic"
    for p in sorted(vdir.glob("task_*.json")) if vdir.exists() else []:
        j = read_json(p)
        if j.get("state") in ("SUBMISSION_ATTEMPTED", "SUBMISSION_UNCERTAIN", "SUBMITTED"):
            out.append({"provider": "anthropic-claude", "custom_id": j["task_id"], "state": j["state"], "batch_id": j.get("batch_id"),
                        "reservation_id": j.get("reservation_id")})
    return out


def build_capsule(ws: Workspace, run_id: str) -> dict:
    from ..vision.protocol import PROTOCOL_SHA, PROTOCOL_VERSION
    from ..vision.runner import coverage_for_range
    from .handoff import exact_next_operation
    st = ws.store()
    try:
        lock = read_json(ws.state_dir / "SOURCE_LOCK.json")
        t = {x["stage"]: x for x in st.list("LoopTransition") if x["run_id"] == run_id}
        origin_raw = next((x.get("evidence_origin") for x in t.values()), "UNKNOWN")
        origin = "REAL_SOURCE" if origin_raw == "REAL_VLM" else "SIMULATED"
        man = st.get("SelectedSequenceManifest", "REAL:15") or {"selected": []}
        six = st.get("SpecialIntroSelection", "REAL")
        seqs = [(s["film_sha"], s["start_frame_index"], s["end_frame_index_inclusive"], s["candidate_id"]) for s in man.get("selected", [])]
        if six and six.get("status") == "LOCKED":
            seqs.append((six["clip_sha256"], six["start_frame_index"], six["end_frame_index_inclusive"], "SIXTH"))
        pass_id = f"{run_id}-L0"
        covs = []
        for film, a, b, sid in seqs:
            c = coverage_for_range(st, film, pass_id, a, b)
            rows = st.conn.execute("SELECT frame_index FROM frame_vision WHERE film_sha256=? AND pass_id=? AND frame_index BETWEEN ? AND ?",
                                   (film, pass_id, a, b)).fetchall()
            done = sorted(r[0] for r in rows)
            first = next((i for i in range(a, b + 1) if i not in set(done)), None)
            pk = [r[0] for r in st.conn.execute("SELECT packet_id FROM packets WHERE film_sha256=? AND pass_id=? AND start_frame>=? AND end_frame<=?"
                                                " ORDER BY start_frame", (film, pass_id, a, b)).fetchall()]
            covs.append({"film": film, "a": a, "b": b, "sid": sid, "cov": c, "done": done, "first": first, "packets": pk})
        active = next((c for c in covs if c["first"] is not None), covs[-1] if covs else None)
        if active is None:
            raise Blocked("CAPSULE_NO_SEQUENCE", "no selected sequence in state")
        pend_native = (st.get("PendingNativeFollowups", run_id) or {}).get("pending", [])
        gq = st.get("GapQueue", run_id) or {}
        trace = st.get("RealInvestigationTrace", run_id) or {"steps": []}
        last_q = next((s for s in reversed(trace["steps"]) if s.get("question_id")), None)
        cg = gq.get("controlling_gap") or {}
        decs = [d for d in st.list("ConditionalVisualDecision") if not d.get("synthetic")]
        ctrl_q = {"question_id": (last_q or {}).get("question_id") or f"pending:{cg.get('gap_id', 'NONE')}",
                  "missing_artistic_choice": (cg.get("what") or (last_q or {}).get("question") or "no open gap recorded")[:400].ljust(15, "."),
                  "observed_contrast_witness_ids": [w.split()[1] for w in (last_q or {}).get("witnesses", []) if len(w.split()) > 1][:6],
                  "new_subject_conditions": cg.get("conditions") or {},
                  "possible_answer_effect_on_operator": "answer selects/changes the conditional branch of the owning production choice "
                                                        "and therefore the compiled clause/reference set of its operator",
                  "source_evidence_to_request": [i[0] if isinstance(i, list) else i for i in (last_q or {}).get("witnesses", [])][:6],
                  "status": "OPEN" if cg else "ANSWERED"}
        fr = None
        for p in reversed(active["packets"]):
            f = ws.vision_dir / pass_id / p / "frames.jsonl"
            if f.exists():
                lines = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]
                if lines:
                    fr = lines[-1]
                    break
        wits = [w for w in st.list("Witness") if w["film_sha256"] == active["film"]]
        obs = {"witness_ids": [w["witness_id"] for w in wits][:12],
               "actual_visible_facts": [w["visible_relation"] for w in wits][:8],
               "full_frame_effect": (fr or {}).get("focal_whole_artwork_state") or "NO_COMMITTED_FRAME_RECORD_YET",
               "linked_design_relations": [r.get("relation") for r in (fr or {}).get("visible_design_relations", []) if isinstance(r, dict)],
               "temporal_relations": [c.get("what") for c in (fr or {}).get("changed_since_prior_frame", []) if isinstance(c, dict)]
               + ([fr["no_significant_change_reason"]] if fr and fr.get("no_significant_change_reason") else []),
               "whole_to_detail_to_whole": "whole frame record → witness relations (full frame + native crops) → decision branch → compiled "
                                           "whole-image request",
               "hypotheses": [d.get("observed_vs_inferred", {}).get("inferred_mechanism") for d in decs if d.get("observed_vs_inferred")][:6],
               "counterevidence": [json.dumps(c)[:300] for d in decs for c in d.get("contradictions", [])][:6],
               "source_vs_inference": {"observed": "Witness.visible_relation + ObservedRelation (cited witness ids)",
                                       "inferred": "ConditionalVisualDecision.observed_vs_inferred.inferred_mechanism",
                                       "status": "all UNVERIFIED_UNTIL_ORIGINAL_ART_REVIEW"}}
        smap = {"EXECUTABLE_CANDIDATE": "EXECUTABLE_CANDIDATE", "RESEARCH_ONLY": "HYPOTHESIS"}
        cdec = [{"decision_id": d["decision_id"], "witness_ids": d.get("evidence_frame_ids", []), "conditional_branches": d["branches"],
                 "exceptions": d.get("exceptions", []), "operator_ids": sorted({o for b in d["branches"] for o in b["operation_node_ids"]}),
                 "owned_prompt_clause_ids": sorted({c for b in d["branches"] for c in b.get("clause_ids", [])}),
                 "status": smap.get(d["status"], "OBSERVATION"), "version": d["version"], "owned_choice_ids": d.get("owned_choice_ids", [])}
                for d in decs]
        s4 = (t.get("S4") or {}).get("outputs") or {}
        skill_folder = s4.get("skill_folder")
        ops, ref_shas, skill_hashes, rehearsal = [], [], [], None
        if skill_folder and Path(skill_folder).exists():
            from ..skills.skill import load_skill
            from ..skills.operators import OPERATORS
            sk = load_skill(skill_folder)
            skill_hashes.append(sk["skill_hash"])
            ref_shas = sorted({r["sha256"] for r in sk["references"]})
            for n in sk["recipes"]["main"]["nodes"]:
                ok = n["operator"] in OPERATORS
                ops.append({"operator_id": n["operator"], "input_ref_ids": n.get("inputs", []), "output_contract": n.get("output_contract") or {},
                            "consumer_id": "|".join(x["id"] for x in sk["recipes"]["main"]["nodes"] if n["id"] in x.get("depends_on", []))
                            or "human_art_review", "status": "IMPLEMENTED" if ok else "MISSING"})
            rehearsal = pinned_rehearsal(ws, st, skill_folder, sk["skill_hash"])
        for v in st.list("RealSkillVersion"):
            if v.get("skill_hash") and v["skill_hash"] not in skill_hashes:
                skill_hashes.append(v["skill_hash"])
        raws = sorted((ws.root / "providers" / "anthropic").glob("raw_*.json")) if (ws.root / "providers" / "anthropic").exists() else []
        raw_sha = sha256_file(max(raws, key=lambda p: p.stat().st_mtime)) if raws else digest("NO_RAW_RESULT")
        nxt = exact_next_operation(ws)
        stopped = sorted((x for x in t.values() if x["status"] == "STOPPED"), key=lambda x: x["stage"])
        stage = stopped[0]["stage"] if stopped else ("S9" if t.get("S9", {}).get("status") == "COMPLETED" else "S0")
        prov = read_json(ws.state_dir / "PROVIDER_STATE.json") if (ws.state_dir / "PROVIDER_STATE.json").exists() else {}
        vis = prov.get("vision", {})
        cap = {"protocol_version": PROTOCOL_VERSION, "protocol_sha256": PROTOCOL_SHA, "origin": origin, "film_sha256": active["film"],
               "sequence": {"sequence_id": active["sid"], "start_index": active["a"], "end_index_inclusive": active["b"], "stream_id": "0:v:0",
                            "film_role_lock_state": "LOCKED" if any(s["sha256"] == active["film"] and s.get("role") for s in lock["sources"]) else "UNLOCKED"},
               "coverage": {"target_frame_count": active["b"] - active["a"] + 1, "verified_vision_frames": active["done"],
                            "first_uncommitted_frame": active["first"], "packet_ids": active["packets"],
                            "native_detail_unresolved": [f"{x['film'][:16]}:{x['frame']}" for x in pend_native]},
               "active_problem": {"cluster_id": cg.get("gap_id") or "NO_OPEN_CLUSTER", "linked_missing_decision_ids":
                                  [g.get("choice_id") or g.get("joint_id") or g["gap_id"] for g in gq.get("queued", [])][:20],
                                  "controlling_question": ctrl_q,
                                  "counterevidence_ids": sorted({w for d in decs for c in d.get("contradictions", []) for w in c.get("later_witness_ids", [])})},
               "observation": obs, "conditional_decisions": cdec, "operation_dependencies": ops,
               "provenance": {"source_witness_ids": sorted({w for d in decs for w in d.get("evidence_frame_ids", [])}),
                              "raw_model_result_sha256": raw_sha, "skill_hashes": skill_hashes, "reference_image_sha256s": ref_shas},
               "next_operation": {"stage": stage, "operation": nxt.get("kind", "UNKNOWN"),
                                  "input_hashes": [x for x in [(t.get(stage) or {}).get("input_key"), skill_hashes[0] if skill_hashes else None] if x],
                                  "why": (stopped[0].get("stop_reason") if stopped else "no stopped stage") or "see exact_next_operation",
                                  "consent_state": "NO_PAID_CALLS_AUTHORIZED_THIS_RUN" if origin != "REAL_SOURCE" else "SEE_AUTHORIZATIONS",
                                  "expected_artifact": nxt.get("command", "")},
               "model_profile": {"model_id": vis.get("model_id", "UNCONFIRMED"), "provider": vis.get("provider", "anthropic-claude"),
                                 "prompt_protocol_sha": PROTOCOL_SHA, "image_resolution_policy": "native source PNG at indexed resolution "
                                 "(720p sources stay 720p; provider-resized copies are never labelled native)", "sdk_version": _sdk_version()},
               # beyond the schema minimum
               "run_id": run_id, "workspace_root_at_export": str(ws.root), "source_lock": [{"sha256": s["sha256"], "file_name": s["file_name"],
                                                                                            "role": s.get("role"), "width": s.get("width"),
                                                                                            "height": s.get("height")} for s in lock["sources"]],
               "sixth_lock_state": (six or {}).get("status", "UNLOCKED"),
               "all_sequences": [{"sequence_id": c["sid"], "film": c["film"], "range": [c["a"], c["b"]], "verified": len(c["done"]),
                                  "first_uncommitted_frame": c["first"]} for c in covs],
               "external_jobs": _uncertain_jobs(ws, st), "pinned_rehearsal": rehearsal,
               "unexplained_phenomena": [p["phenomenon_id"] for p in st.list("VisualPhenomenon") if p.get("status") != "EXPLAINED"],
               "created_at": now_iso()}
        cap["capsule_sha256"] = digest({k: v for k, v in cap.items() if k != "created_at"})
        return cap
    finally:
        st.close()


def pinned_rehearsal(ws: Workspace, st, skill_folder: str, skill_hash: str) -> dict | None:
    """Deterministic dry rehearsal: compile the pinned skill's world/whole-scene node for the active brief; record the logical hash."""
    from ..compiler.compiler import StyleProgramCompiler
    a = st.get("ActiveBrief", "anchor")
    snap = (read_json(ws.state_dir / "PROVIDER_STATE.json") if (ws.state_dir / "PROVIDER_STATE.json").exists() else {}).get("runware")
    if not a or not snap:
        return None
    brief = st.get("OriginalBrief", a["brief_id"])["brief"]
    from ..skills.skill import load_skill
    nodes = [n["id"] for n in load_skill(skill_folder)["recipes"]["main"]["nodes"] if n["id"] in ("n_world_plate", "n_whole_scene")]
    if not nodes:
        return None
    job = StyleProgramCompiler().compile(brief, skill_folder, pinned_skill_hash=skill_hash, recipe_id="main", node_id=nodes[0], caps=snap)
    return {"node": nodes[0], "skill_hash": skill_hash, "logical_sha256": job.logical_sha256,
            "reference_shas": [r[1] for r in job.reference_images], "brief_id": a["brief_id"]}


def validate_capsule(cap: dict) -> list[str]:
    import jsonschema
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    v = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(str(x) for x in e.path)}: {e.message}" for e in v.iter_errors(cap)]


def export_capsule(ws: Workspace, run_id: str, out_zip: str | Path) -> dict:
    from .handoff import export_handoff
    cap = build_capsule(ws, run_id)
    errs = validate_capsule(cap)
    if errs:
        raise Blocked("CAPSULE_SCHEMA_INVALID", "; ".join(errs[:5]))
    atomic_write_json(ws.state_dir / "INVESTIGATION_CAPSULE.json", cap)
    rep = export_handoff(ws, out_zip, reason=f"investigation-capsule {run_id}")
    return {**rep, "capsule_sha256": cap["capsule_sha256"], "capsule": cap}


def import_and_verify(zip_path: str | Path, new_root: str | Path, *, sources_folder: str | Path | None = None,
                      protocol_migration: dict | None = None) -> dict:
    """Cold start in a fresh destination (A28 §5.2). Returns the verification report; raises Blocked on corruption/drift."""
    from .handoff import import_handoff, exact_next_operation
    from ..vision.protocol import verify_protocol
    new_root = Path(new_root)
    rep = import_handoff(zip_path, new_root, sources_folder=sources_folder)
    cap = read_json(new_root / "state" / "INVESTIGATION_CAPSULE.json")
    errs = validate_capsule(cap)
    if errs:
        raise Blocked("CAPSULE_SCHEMA_INVALID", "; ".join(errs[:5]))
    proto = verify_protocol(cap["protocol_version"], cap["protocol_sha256"], migration=protocol_migration)
    ws = Workspace(new_root)
    old = cap["workspace_root_at_export"]
    st = ws.store()
    missing = []
    try:
        # rebase absolute artifact paths recorded by the previous environment
        for t in st.list("LoopTransition"):
            o = t.get("outputs") or {}
            if o.get("skill_folder"):
                o["skill_folder"] = str(_rebase(o["skill_folder"], old, new_root))
                st.put("LoopTransition", f"{t['run_id']}:{t['stage']}", {**t, "outputs": o})
        s4 = (st.get("LoopTransition", f"{cap['run_id']}:S4") or {}).get("outputs") or {}
        skill_folder = s4.get("skill_folder")
        from ..skills.skill import skill_hash
        for h in cap["provenance"]["skill_hashes"][:1]:
            if not skill_folder or not Path(skill_folder).exists():
                missing.append({"artifact": "skill_version", "sha256": h, "expected_path": skill_folder})
            elif skill_hash(skill_folder) != h:
                raise Blocked("CAPSULE_SKILL_HASH_MISMATCH", f"{skill_folder}: {skill_hash(skill_folder)[:12]} != {h[:12]}")
        have_refs = {sha256_file(p) for p in (Path(skill_folder) / "references").glob("*.png")} if skill_folder and Path(skill_folder).exists() else set()
        for r in cap["provenance"]["reference_image_sha256s"]:
            if r not in have_refs:
                missing.append({"artifact": "reference_image", "sha256": r})
        raws = {sha256_file(p) for p in (new_root / "providers" / "anthropic").glob("raw_*.json")} if (new_root / "providers" / "anthropic").exists() else set()
        if cap["provenance"]["raw_model_result_sha256"] not in raws and raws:
            missing.append({"artifact": "raw_model_result", "sha256": cap["provenance"]["raw_model_result_sha256"]})
        uncertain = [j for j in _uncertain_jobs(ws, st) if j["state"] in ("UNKNOWN_BILLING", "SUBMISSION_UNCERTAIN", "SUBMISSION_ATTEMPTED",
                                                                          "IN_FLIGHT")]
        rehearsal: dict | None = None
        if cap.get("pinned_rehearsal") and skill_folder and Path(skill_folder).exists():
            try:
                rehearsal = pinned_rehearsal(ws, st, skill_folder, cap["pinned_rehearsal"]["skill_hash"])
            except Blocked as b:                       # e.g. REFERENCE_BYTES_MISSING: report it, never continue on a guess
                rehearsal = {"error": b.code, "detail": b.detail, "logical_sha256": None, "reference_shas": None}
        same = False
        if rehearsal is not None:
            same = rehearsal["logical_sha256"] == cap["pinned_rehearsal"]["logical_sha256"] \
                and rehearsal["reference_shas"] == cap["pinned_rehearsal"]["reference_shas"]
        decs = [d for d in st.list("ConditionalVisualDecision") if not d.get("synthetic")]
        recon = {"observed": sorted({r for d in decs for r in d.get("observed_vs_inferred", {}).get("observed", []) if r})[:20],
                 "inferred": [d.get("observed_vs_inferred", {}).get("inferred_mechanism") for d in decs][:20],
                 "contradicted": [c for d in decs for c in d.get("contradictions", [])][:10],
                 "unknown": sorted({u for d in decs for u in d.get("uncertainty", [])})[:20] + cap.get("unexplained_phenomena", []),
                 "frozen_skills": cap["provenance"]["skill_hashes"], "blocked": [j for j in uncertain],
                 "next_decision": cap["active_problem"]["controlling_question"],
                 "note": "factual reconstruction from committed records; no style rule was authored from this recap"}
        st.put("HandoffReconstruction", cap["capsule_sha256"][:16], recon)
    finally:
        st.close()
    nxt = exact_next_operation(ws)
    status = ("BLOCKED_MISSING_EVIDENCE" if missing else "BLOCKED_UNCERTAIN_EXTERNAL_CHARGE" if uncertain else
              "BLOCKED_REHEARSAL_MISMATCH" if cap.get("pinned_rehearsal") and not same else
              "BLOCKED_SOURCE_REBIND_REQUIRED" if rep["sources_unbound"] else "VERIFIED_READY_TO_RESUME")
    out = {"status": status, "protocol": proto, "import": {k: rep[k] for k in ("status", "hash_mismatches", "missing_artifacts", "sqlite_integrity")},
           "sources_unbound": [s["sha256"] for s in rep["sources_unbound"]], "missing_capsule_artifacts": missing,
           "uncertain_external_jobs": uncertain, "rehearsal": {"recorded": cap.get("pinned_rehearsal"), "recomputed": rehearsal,
                                                               "byte_identical_logical_payload": same},
           "first_uncommitted_frame": cap["coverage"]["first_uncommitted_frame"], "committed_frames": len(cap["coverage"]["verified_vision_frames"]),
           "controlling_question": cap["active_problem"]["controlling_question"], "next_operation": nxt, "capsule_sha256": cap["capsule_sha256"],
           "verified_at": now_iso()}
    atomic_write_json(new_root / "state" / "CAPSULE_VERIFICATION.json", out)
    return out
