"""Phase-2 REAL-PATH REPAIR audit artefacts — every JSON produced by executing the code (drill uses SIMULATED transports)."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..util import atomic_write_json, atomic_write_text, digest, read_json, sha256_file
from ..state.workspace import Workspace

ROOT = Path(__file__).resolve().parents[2]
PRIOR_AUDIT_COMMIT = "6d794c9"
PRIOR_AUDIT_ZIP_SHA = "7fa6ad8e5ff9a3759801bd6bd7a7505a6c89e17a64036920cbee0829e37d837f"


def _strip(o):
    if isinstance(o, dict):
        return {k: _strip(v) for k, v in o.items() if k != "referenceImages"}
    if isinstance(o, list):
        return [_strip(x) for x in o]
    return o


def generate_repair_artifacts(audit: Path, real_ws: Workspace) -> dict:
    from ..loop.real import describe_call_graph
    from ..testing.drill import build_drill_workspace, drill_providers, drive, enable_network_flag
    from ..experiments.experiments import causal_mutation_test
    from ..loop.human import provider_state
    W = {}

    def put(name, obj):
        p = audit / name
        if name.endswith(".md"):
            atomic_write_text(p, obj)
        else:
            atomic_write_json(p, _strip(obj))
        W[name] = str(p)

    put("REAL_PATH_CALL_GRAPH.json", {"handlers": describe_call_graph(), "note": "line numbers are vme/loop/real.py lines at export time"})
    tmp = Path(tempfile.mkdtemp(prefix="vme_repair_"))
    prev_net = os.environ.get("VME_ALLOW_NETWORK")
    enable_network_flag()
    try:
        d = build_drill_workspace(tmp)
        ws = d["ws"]
        prov, client = drill_providers(tmp)
        res = drive(ws, prov, run_id="REAL-AUDIT-DRILL")
        d2 = build_drill_workspace(tmp / "crash")
        prov2, client2 = drill_providers(tmp / "crash")
        res2 = drive(d2["ws"], prov2, run_id="REAL-AUDIT-CRASH", crash_at=[f"S{i}" for i in range(10)], max_rounds=60)
    finally:
        if prev_net is None:
            os.environ.pop("VME_ALLOW_NETWORK", None)
    st = ws.store()
    T = {t["stage"]: t for t in st.list("LoopTransition") if t["run_id"] == "REAL-AUDIT-DRILL"}
    put("REAL_PATH_DRILL_TRACE.json", {"label": "REAL handlers + SIMULATED transports (fixture). Wiring evidence only — not learning, not art.",
                                       "result": res["result"], "human_and_stop_log": res["log"], "transitions": [T[s] for s in sorted(T)],
                                       "simulated_vision_requests_billed_once_each": client.billed_requests(),
                                       "duplicate_batch_creates": client.duplicate_creates()})
    put("REAL_PATH_CRASH_EACH_STAGE.json", {"result": res2["result"], "log": res2["log"],
                                            "crashes": [x for x in res2["log"] if "crash" in x], "duplicate_batch_creates": client2.duplicate_creates()})
    trace = st.get("RealInvestigationTrace", "REAL-AUDIT-DRILL")
    put("REAL_INVESTIGATION_TRACE.json", {"steps": trace["steps"], "coverage_review": st.get("CoverageReview", "REAL-AUDIT-DRILL"),
                                          "closed_gaps": sorted({s["gap_signature"] for s in trace["steps"] if s["decision_changed"]}),
                                          "questions": len(trace["steps"])})
    s4 = T["S4"]["outputs"]
    from ..skills.skill import load_skill
    sk = load_skill(s4["skill_folder"])
    wits = {w["witness_id"]: w for w in st.list("Witness")}
    rels = {r["relation_id"]: r for r in st.list("ObservedRelation")}
    chains = []
    for j in st.list("CompiledImageJob"):
        for seg in j["trace"]["segments"]:
            if seg["authority"] != "STYLE":
                continue
            c = next(x for x in sk["clauses"] if x["id"] == seg["clause_id"])
            dec = next(x for x in sk["decisions"] if x["decision_id"] == c["derivation"]["decision_id"])
            chains.append({"job": j["job_id"], "node": j.get("node_id"), "clause_id": c["id"], "clause_text_in_payload": seg["text"],
                           "payload_sha256": digest(j["payload"]), "decision_id": dec["decision_id"], "branch": dec["branches"][c["derivation"]["branch_index"]]["when"],
                           "observed_relations": [{"id": r, "relation": rels[r]["relation"][:160], "witness_ids": rels[r]["witness_ids"]}
                                                  for r in dec["observed_relation_ids"] if r in rels][:3],
                           "witness_frames": [{"id": w, "film": wits[w]["film_sha256"][:16], "frame": wits[w]["frame_start"], "pts_time": wits[w].get("pts_time"),
                                               "frame_sha256": wits[w]["image_sha256"]} for w in dec["evidence_frame_ids"] if w in wits][:4],
                           "reference_byte_shas": j["ref_shas"]})
    put("SOURCE_TO_SKILL_TO_PAYLOAD_TRACE.json", {"skill_hash": s4["skill_hash"], "evidence_origin": sk["manifest"]["evidence_origin"],
                                                  "chains": chains, "decisions": len(sk["decisions"]), "clauses": len(sk["clauses"])})
    brief = st.get("OriginalBrief", "BRIEF-DRILL-ANCHOR")["brief"]
    copy = tmp / "ablation_skill"
    shutil.copytree(s4["skill_folder"], copy)
    (copy / "FROZEN.json").unlink()
    caps = provider_state(ws)["runware"]
    abl = []
    for did in [d["decision_id"] for d in sk["decisions"]][:3]:
        def drop(f, did=did):
            atomic_write_json(f / "decisions.json", [x for x in read_json(f / "decisions.json") if x["decision_id"] != did])
        abl.append(causal_mutation_test(copy, brief, caps, recipe_id="main", node_id="n_whole_scene", mutate=drop, label=f"ablate {did}"))
    put("SKILL_ABLATION_EFFECTS.json", {"ablations": abl})
    s5, s7, s8 = T["S5"]["outputs"], T["S7"]["outputs"], T["S8"]["outputs"]
    pack = read_json(s7["pack"])
    put("CANONICAL_TO_VARIANT_IDENTITY.json", {"canonical_sha": s5["n_canonical_character"]["sha"], "method": pack["method"], "method_reason": pack["method_reason"],
                                               "states": {k: {"sha": v["sha256"], "conditioned_on": v["reference_shas"], "clause_ids": v["clause_ids"]}
                                                          for k, v in pack["states"].items()}, "not_generated": pack["not_generated"],
                                               "render": s8, "asset_approval": T["S7"]["outputs"].get("asset_approval_id")})
    st.close()
    # source index invariance on the REAL workspace
    summ = read_json(real_ws.state_dir / "FRAME_INDEX_SUMMARY.json")
    inv = [{"film": f["file_name"], "index_sha256_recorded": f["index_sha256"],
            "index_sha256_now": sha256_file(f["index_path"]), "unchanged": sha256_file(f["index_path"]) == f["index_sha256"]} for f in summ["films"]]
    put("SOURCE_INDEX_HASHES_UNCHANGED.json", {"films": inv, "all_unchanged": all(x["unchanged"] for x in inv)})
    from ..reference.roles import write_role_report, role_status
    write_role_report(real_ws, audit / "SOURCE_ROLE_CONFIRMATION_REPORT.md")
    put("SOURCE_ROLE_STATUS.json", role_status(real_ws))
    from ..loop.real import RealLoopRunner, RealProviders
    put("REAL_WORKSPACE_REAL_LOOP_STATUS.json", RealLoopRunner(real_ws, run_id="REAL-001", providers=RealProviders.production(real_ws)).run(until="S0"))
    diff = subprocess.run(["git", "diff", "--stat", PRIOR_AUDIT_COMMIT, "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout
    names = subprocess.run(["git", "diff", "--name-status", PRIOR_AUDIT_COMMIT, "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout
    put("DIFF_FROM_PRIOR_AUDIT.md", f"# Differences from the prior audit\n\nPrior audit ZIP SHA256 `{PRIOR_AUDIT_ZIP_SHA}` = commit `{PRIOR_AUDIT_COMMIT}`.\n\n"
        f"```\n{names}\n```\n\n```\n{diff}\n```\n")
    shutil.rmtree(tmp, ignore_errors=True)
    return W
