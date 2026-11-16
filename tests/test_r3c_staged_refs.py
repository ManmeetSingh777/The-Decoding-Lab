"""R3-C01 — multi-stage reference use is an EXECUTED chain of compiled provider requests, checked on the actual bytes sent."""
from __future__ import annotations

import base64
import hashlib
import json

import pytest

from conftest import offline_gateway
from vme.util import Blocked

uri_sha = lambda b: hashlib.sha256(("data:image/png;base64," + base64.b64encode(b).decode()).encode()).hexdigest()


def _setup(tmp_path, caps, *, extra=2, limit=2, policy="STAGED_EDIT"):
    from vme.fixtures.synthetic import build_synthetic_skill, synthetic_brief
    from vme.compiler.compiler import StyleProgramCompiler
    f = tmp_path / "skill"
    h = build_synthetic_skill(f, extra_refs=extra, overflow_policy=policy)
    c = dict(caps, max_reference_images=limit)
    job = StyleProgramCompiler().compile(synthetic_brief(), f, pinned_skill_hash=h, recipe_id="character_world", node_id="n1_scene", caps=c)
    refs = {hashlib.sha256(p.read_bytes()).hexdigest(): p.read_bytes() for p in (f / "references").glob("*.png")}
    return job, c, refs, f, h


def _sent_ref_uris(t):
    return [((b.get("task") or {}).get("inputs") or {}).get("referenceImages_sha256", []) for b in t.sent_bodies()]


@pytest.mark.req("R3-C01")
def test_limit_two_with_four_mandatory_refs_executes_three_bound_stages(store, tmp_path, caps):
    job, c, refs, *_ = _setup(tmp_path, caps)
    assert [len(s["ref_shas"]) for s in job.trace["stage_plan"]] == [2, 1, 1]
    g, t = offline_gateway(store, tmp_path, c)
    res = g.submit(job)
    sent = _sent_ref_uris(t)
    assert len(sent) == 3                                                       # three actual provider requests
    required = {uri_sha(refs[s]) for s in job.trace["required_reference_shas"]}
    assert required <= {s for x in sent for s in x}                             # every mandatory reference's exact bytes were sent
    rec = res["stage_receipts"]
    assert [r["stage"] for r in rec] == [1, 2, 3] and res["staged"] and not res["intermediate"]
    sent = [json.loads((t.dir / f"req_{r['task_uuid']}.json").read_text(encoding="utf-8"))["task"]["inputs"]["referenceImages_sha256"]
            for r in rec]                                                       # each stage's request, by ITS task uuid
    for k in (1, 2):                                                            # stage k+1's FIRST image = stage k's returned bytes
        prior_png = open(store.get("GeneratedRaster", rec[k - 1]["job_id"])["outputs"][0]["path"], "rb").read()
        assert hashlib.sha256(prior_png).hexdigest() == rec[k]["prior_output_sha256"] == rec[k - 1]["output_sha256"]
        assert sent[k][0] == uri_sha(prior_png) and len(sent[k]) <= c["max_reference_images"]
    assert res["outputs"][0]["sha256"] == rec[2]["output_sha256"] != rec[0]["output_sha256"]   # finished asset = LAST stage
    assert store.get("GeneratedRaster", rec[0]["job_id"])["intermediate"] is True
    assert store.get("StagedImageResult", job.job_id)["final_stage_job_id"] == rec[2]["job_id"]


@pytest.mark.req("R3-C01")
def test_later_stage_prompt_is_only_its_own_skill_clauses(store, tmp_path, caps):
    job, c, *_ = _setup(tmp_path, caps)
    g, t = offline_gateway(store, tmp_path, c)
    res = g.submit(job)
    req1 = json.loads(open(g.art / "provider" / res["stage_receipts"][0]["job_id"] / "request_body.json", encoding="utf-8").read())[0]
    req2 = json.loads(open(g.art / "provider" / res["stage_receipts"][1]["job_id"] / "request_body.json", encoding="utf-8").read())[0]
    assert "outer silhouette unified" in req1["positivePrompt"]               # stage 1 = the node operator's own clauses
    assert "apply the referenced construction system" in req2["positivePrompt"]
    assert "outer silhouette unified" not in req2["positivePrompt"]          # stage-1 operator clauses are NOT re-sent in stage 2


@pytest.mark.req("R3-C01")
def test_a_silently_skipped_stage_is_refused(store, tmp_path, caps, monkeypatch):
    from vme.providers.gateway import StyleImageGateway
    job, c, *_ = _setup(tmp_path, caps)
    g, t = offline_gateway(store, tmp_path, c)
    monkeypatch.setattr(StyleImageGateway, "_stages_to_run", lambda self, plan: list(plan)[:2])
    with pytest.raises(Blocked) as e:
        g.submit(job)
    assert e.value.code == "REQUIRED_STAGE_NOT_EXECUTED"
    assert store.get("StagedImageResult", job.job_id) is None                 # no completed asset recorded


@pytest.mark.req("R3-C01")
def test_interrupted_chain_resumes_without_duplicate_billing(store, tmp_path, caps, monkeypatch):
    from vme.vision.runner import SimulatedCrash
    job, c, *_ = _setup(tmp_path, caps)
    g, t = offline_gateway(store, tmp_path, c)
    monkeypatch.setenv("VME_CRASH_AT", "gateway_before_stage_3")
    with pytest.raises(SimulatedCrash):
        g.submit(job)
    assert t.billed() == 2
    monkeypatch.delenv("VME_CRASH_AT")
    res = g.submit(job)
    assert t.billed() == 3 and t.duplicate_bills() == 0 and len(res["stage_receipts"]) == 3
    again = g.submit(job)                                                      # fully committed chain: no request at all
    assert t.billed() == 3 and again["outputs"][0]["sha256"] == res["outputs"][0]["sha256"]


@pytest.mark.req("R3-C01")
def test_provider_without_edit_capability_blocks_before_any_charge(store, tmp_path, caps):
    from vme.fixtures.synthetic import build_synthetic_skill, synthetic_brief
    from vme.compiler.compiler import StyleProgramCompiler
    f = tmp_path / "skill"
    h = build_synthetic_skill(f, extra_refs=2, overflow_policy="STAGED_EDIT")
    c = dict(caps, max_reference_images=2, supported_capabilities=[x for x in caps["supported_capabilities"] if x != "imageEdit"])
    with pytest.raises(Blocked) as e:
        StyleProgramCompiler().compile(synthetic_brief(), f, pinned_skill_hash=h, recipe_id="character_world", node_id="n1_scene", caps=c)
    assert e.value.code == "PROVIDER_REF_LIMIT" and "staged reference edit" in e.value.detail


@pytest.mark.req("R3-C01")
def test_a_reference_no_decision_authorises_to_stage_is_a_research_ticket(tmp_path, caps):
    from vme.fixtures.synthetic import build_synthetic_skill, synthetic_brief
    from vme.compiler.compiler import StyleProgramCompiler
    from vme.skills.skill import load_skill
    f = tmp_path / "skill"
    build_synthetic_skill(f, extra_refs=2, overflow_policy="STAGED_EDIT")
    p = f / "decisions.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    for x in d:
        for br in x["branches"]:
            br["operation_node_ids"] = [o for o in br["operation_node_ids"] if o != "op.reference_staged_edit"]
    p.write_text(json.dumps(d), encoding="utf-8")
    h = load_skill(f)["skill_hash"]
    with pytest.raises(Blocked) as e:
        StyleProgramCompiler().compile(synthetic_brief(), f, pinned_skill_hash=h, recipe_id="character_world", node_id="n1_scene",
                                       caps=dict(caps, max_reference_images=2))
    assert e.value.code == "STAGE_EDIT_NOT_OWNED"


@pytest.mark.req("R3-C01")
def test_stage_bound_to_changed_prior_bytes_is_refused(store, tmp_path, caps):
    from vme.compiler.compiler import StyleProgramCompiler
    job, c, *_ = _setup(tmp_path, caps)
    bogus = tmp_path / "bogus.png"
    bogus.write_bytes(b"\x89PNG not the prior output")
    i = job.inputs
    with pytest.raises(Blocked) as e:
        StyleProgramCompiler().compile(i["brief"], i["skill_folder"], pinned_skill_hash=i["pinned_skill_hash"], recipe_id=i["recipe_id"],
                                       node_id=i["node_id"], caps=i["caps"], stage={"index": 2, "prior_output": {"sha256": "0" * 64, "path": str(bogus)}})
    assert e.value.code == "STAGE_PRIOR_OUTPUT_MISSING_OR_CHANGED"
