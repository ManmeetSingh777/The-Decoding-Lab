"""Production-choice identity, phenomenon/choice-level completeness, exemplar references → payload,
gap-driven reinspection and the mandatory sixteenth interval (repair R08–R11, R13, R15, R16, R21; ST28-03/04/09/10/11/13/22).

Every witness/answer here is SYNTHETIC test data (film ids are made-up hashes); nothing describes a real film.
"""
from __future__ import annotations

import io
import json

import pytest
from PIL import Image

from vme.util import Blocked
from vme.skills.operators import registered

FA, FB = "a" * 64, "b" * 64
HUMAN = "TEST_FIXTURE_HUMAN_SIMULATION"


def _png(rgb, size=(64, 36)) -> bytes:
    b = io.BytesIO()
    Image.new("RGB", size, rgb).save(b, format="PNG")
    return b.getvalue()


def _witness(st, wid, film, k, dims, rel, cls="biped", kind="FULL_FRAME", region=None):
    st.put("Witness", wid, {"witness_id": wid, "film_sha256": film, "sequence_id": f"seq-{film[:4]}", "frame_start": k, "frame_end": k,
                            "evidence_kind": kind, "observer": "VLM", "visible_relation": rel, "image_sha256": f"{k:064x}",
                            "region": region, "subject_class": cls, "scene_specific_facts": [], "observation_ids": [f"{film[:16]}:{k}"],
                            "limits": "SYNTHETIC test witness", "dimensions": dims, "evidence_origin": "SIMULATED_VLM_TRANSPORT"})


def _answer(wids, action, *, op="op.canonical_character", when=None, ref=True):
    return {"answer_status": "INFERRED", "REFERENCE_REQUIRED": ref,
            "SOURCE_VISIBLE_FACTS": [{"relation": f"SYNTHETIC: in {w} the near contour overlaps the far brow while the light stays fixed",
                                      "witness_ids": [w]} for w in wids],
            "CONSTRUCTION_EXPLANATION": "SYNTHETIC: the head contour and the eye occlusion are redrawn together as the view turns",
            "WHY_THE_DECISION_MATTERS": "SYNTHETIC: keeps identity readable across the turn", "WHEN_NOT_APPLICABLE": ["diagram frames"],
            "ADAPTS_WITH": ["anatomy"], "CREATIVE_FREEDOM": ["identity"], "FORBIDDEN_SOURCE_SPECIFIC": ["source character"],
            "REMAINING_UNKNOWN": ["profile view"], "INVARIANT": "SYNTHETIC: occlusion order follows the turn",
            "BRANCHES": [{"when": when or {"subject_kind": "biped"}, "operation_id": op, "construction_action": action}]}


def _q(qid, contrast=()):
    return {"question_id": qid, "exact_artistic_unknown": "SYNTHETIC unknown", "observed_contrast_with_witness_ids": list(contrast)}


def _two_same_category_decisions(st):
    from vme.style.authoring import author_decision, production_choice_id
    _witness(st, "W-A", FA, 10, ["CHARACTER_FACE_ACTING"], "SYNTHETIC: far eye partly hidden behind the near cheek contour")
    _witness(st, "W-B", FB, 20, ["CHARACTER_FACE_ACTING"], "SYNTHETIC: skull contour widens on the near side as the head turns", cls="creature")
    d1 = production_choice_id("hero:face/three_quarter/eye_occlusion", "far eye hidden behind near cheek")
    d2 = production_choice_id("hero:face/three_quarter/skull_contour", "near skull contour widens")
    a = author_decision(st, _q("Q1", ["W-B"]), _answer(["W-A"], "SYNTHETIC: draw the {subject} so its far eye tucks behind the near cheek contour"),
                        dims=["CHARACTER_FACE_ACTING"], registered_ops=registered(), required_branches=[], decision_id=d1,
                        owned_choice_ids=["hero:face/three_quarter/eye_occlusion"], phenomenon="far eye hidden behind near cheek")
    b = author_decision(st, _q("Q2", ["W-A"]), _answer(["W-B"], "SYNTHETIC: draw the {subject} with the near skull contour widened against the {setting}"),
                        dims=["CHARACTER_FACE_ACTING"], registered_ops=registered(), required_branches=[], decision_id=d2,
                        owned_choice_ids=["hero:face/three_quarter/skull_contour"], phenomenon="near skull contour widens")
    return a, b


def _loader(colours):
    def load(wid):
        return _png(colours[wid]), {"film_sha256": FA if wid == "W-A" else FB, "frame_index": 1, "evidence_kind": "FULL_FRAME"}
    return load


def _compile(folder, h):
    from vme.compiler.compiler import StyleProgramCompiler
    from vme.testing.drill import drill_brief
    from vme.fixtures.synthetic import fixture_caps
    return StyleProgramCompiler().compile(drill_brief(), folder, pinned_skill_hash=h, recipe_id="main", node_id="n_canonical_character",
                                          caps=fixture_caps())


OC = {"op.canonical_character": {"width": 1024, "height": 1024, "format": "PNG", "asset_kind": "CHARACTER"},
      "op.whole_scene": {"width": 1536, "height": 864, "format": "PNG", "asset_kind": "WHOLE_SCENE"}}


@pytest.mark.req("R09", "R15", "ST28-10", "ST28-03")
def test_two_same_category_findings_are_two_decisions_into_skill_and_payload(store, tmp_path):
    from vme.style.authoring import publish_skill_version
    a, b = _two_same_category_decisions(store)
    assert a["decision_id"] != b["decision_id"] and a["dimension_tags"] == b["dimension_tags"]
    assert a["status"] == b["status"] == "EXECUTABLE_CANDIDATE" and a["claim_state"] == "METHOD_CANDIDATE"
    res = publish_skill_version(tmp_path / "sk", [a, b], skill_id="t", version="0.1", evidence_origin="SIMULATED_VLM_TRANSPORT",
                                output_contracts=OC, exemplar_loader=_loader({"W-A": (200, 10, 10), "W-B": (10, 200, 10)}),
                                consent_for=lambda sha: {"status": "CONSENTED", "consented_by": HUMAN})
    job = _compile(res["folder"], res["skill_hash"])
    assert {s["skill_decision_id"] for s in job.trace["segments"] if s["authority"] == "STYLE"} == {a["decision_id"], b["decision_id"]}
    refs = [r for r in job.trace["reference_trace"] if r["authority"] == "SKILL_REFERENCE"]
    assert {r["decision_id"] for r in refs} == {a["decision_id"], b["decision_id"]} and len({r["sha256"] for r in refs}) == 2
    assert len(job.logical_payload["inputs"]["referenceImages"]) == 2
    assert job.logical_payload["inputs"]["referenceImages"][0].startswith("data:image/png;base64,")
    (tmp_path / "trace.json").write_text(json.dumps({"skill": res["skill_hash"], "refs": refs}), encoding="utf-8")


@pytest.mark.req("R08", "R16", "R21", "ST28-13")
def test_reference_change_changes_payload_and_missing_consent_or_bytes_refuses(store, tmp_path):
    from vme.style.authoring import publish_skill_version, current_skill
    a, b = _two_same_category_decisions(store)
    kw = dict(skill_id="t", version="0.1", evidence_origin="SIMULATED_VLM_TRANSPORT", output_contracts=OC,
              consent_for=lambda sha: {"status": "CONSENTED", "consented_by": HUMAN})
    r1 = publish_skill_version(tmp_path / "sk", [a, b], exemplar_loader=_loader({"W-A": (200, 10, 10), "W-B": (10, 200, 10)}), **kw)
    r2 = publish_skill_version(tmp_path / "sk", [a, b], exemplar_loader=_loader({"W-A": (201, 10, 10), "W-B": (10, 200, 10)}), **kw)
    assert r1["skill_hash"] != r2["skill_hash"] and r1["folder"] != r2["folder"]
    j1, j2 = _compile(r1["folder"], r1["skill_hash"]), _compile(r2["folder"], r2["skill_hash"])
    assert j1.logical_sha256 != j2.logical_sha256                   # altered exemplar bytes → causal payload difference
    assert j1.logical_payload["positivePrompt"] == j2.logical_payload["positivePrompt"]
    assert current_skill(tmp_path / "sk")["history"] == [r1["skill_hash"]]
    from vme.skills.skill import skill_hash
    assert skill_hash(r1["folder"]) == r1["skill_hash"]               # older version immutable, still compilable
    r3 = publish_skill_version(tmp_path / "sk3", [a, b], exemplar_loader=_loader({"W-A": (1, 1, 1), "W-B": (2, 2, 2)}),
                               **{**kw, "consent_for": lambda sha: None})
    with pytest.raises(Blocked) as e:
        _compile(r3["folder"], r3["skill_hash"])
    assert e.value.code == "STYLE_REFERENCE_CONSENT_MISSING"
    r4 = publish_skill_version(tmp_path / "sk4", [a, b], exemplar_loader=None, **kw)
    assert [p["reason"] for p in r4["reference_problems"]] == ["NO_EXEMPLAR_SOURCE"] * 2
    with pytest.raises(Blocked) as e:
        _compile(r4["folder"], r4["skill_hash"])
    assert e.value.code == "REQUIRED_STYLE_REFERENCE_MISSING"


@pytest.mark.req("R08", "R16")
def test_more_mandatory_references_than_provider_limit_is_named_refusal(store, tmp_path):
    from vme.style.authoring import author_decision, production_choice_id, publish_skill_version
    decs = []
    for i in range(5):
        wid = f"W-{i}"
        _witness(store, wid, FA if i % 2 else FB, 30 + i, ["CHARACTER_WHOLE_DESIGN"], f"SYNTHETIC: relation {i} between torso and limbs")
        did = production_choice_id(f"hero:part{i}", f"p{i}")
        decs.append(author_decision(store, _q(f"Q{i}"), _answer([wid], f"SYNTHETIC: draw the {{subject}} with part {i} attached to the torso mass"),
                                    dims=["CHARACTER_WHOLE_DESIGN"], registered_ops=registered(), required_branches=[], decision_id=did,
                                    owned_choice_ids=[f"hero:part{i}"], phenomenon=f"p{i}"))
    res = publish_skill_version(tmp_path / "sk", decs, skill_id="t", version="0.1", evidence_origin="SIMULATED_VLM_TRANSPORT",
                                output_contracts=OC, exemplar_loader=lambda w: (_png((int(w[-1]) * 40, 5, 5)),
                                                                                {"film_sha256": FA, "frame_index": 1}),
                                consent_for=lambda sha: {"status": "CONSENTED"})
    with pytest.raises(Blocked) as e:
        _compile(res["folder"], res["skill_hash"])
    assert e.value.code == "PROVIDER_REF_LIMIT"           # never silently dropped


@pytest.mark.req("R09", "ST28-19")
def test_reanswering_same_choice_keeps_contradiction_instead_of_overwriting(store):
    from vme.style.authoring import author_decision, production_choice_id
    _witness(store, "W-A", FA, 10, ["CHARACTER_FACE_ACTING"], "SYNTHETIC: far eye hidden")
    _witness(store, "W-C", FB, 12, ["CHARACTER_FACE_ACTING"], "SYNTHETIC: far eye stays visible", cls="creature")
    did = production_choice_id("hero:face", "eye occlusion")
    kw = dict(dims=["CHARACTER_FACE_ACTING"], registered_ops=registered(), required_branches=[], decision_id=did,
              owned_choice_ids=["hero:face"], phenomenon="eye occlusion")
    author_decision(store, _q("Q1"), _answer(["W-A"], "SYNTHETIC: draw the {subject} with the far eye tucked behind the cheek"), **kw)
    d = author_decision(store, _q("Q2"), _answer(["W-C"], "SYNTHETIC: draw the {subject} with both eyes kept fully visible"), **kw)
    assert d["version"] == 2 and d["status"] == "RESEARCH_ONLY"
    assert d["research_only_reason"] == "OPEN_CONTRADICTION_NEEDS_DISCRIMINATING_EVIDENCE"
    c = d["contradictions"][0]
    assert c["earlier_witness_ids"] == ["W-A"] and c["later_witness_ids"] == ["W-C"]
    assert "tucked" in c["earlier_action"] and "fully visible" in c["later_action"]


@pytest.mark.req("R10", "ST28-11")
def test_category_presence_is_not_choice_or_joint_coverage():
    from vme.style.coverage import owns, set_relation, new_ledger
    d = {"decision_id": "PC-x", "status": "EXECUTABLE_CANDIDATE", "dimension_tags": ["CHARACTER_FACE_ACTING", "DEPTH_VIEWPOINT"],
         "owned_choice_ids": ["hero:face"]}
    assert owns(d, "hero:face", ["CHARACTER_FACE_ACTING"])
    assert not owns(d, "hero:face+view", ["CHARACTER_FACE_ACTING", "DEPTH_VIEWPOINT"])   # same tags, different production choice
    with pytest.raises(Blocked) as e:
        set_relation(new_ledger("s", []), "hero:face+view", ["CHARACTER_FACE_ACTING", "DEPTH_VIEWPOINT"], "SUPPORTED", evidence=[],
                     producing_effect="x")
    assert e.value.code == "SUPPORTED_RELATION_WITHOUT_WITNESS"


@pytest.mark.req("R10", "ST28-11")
def test_case4_complete_grid_still_reports_missing_face_view_light_and_hand_prop(store):
    """Calibration case 4: every category has one decision, yet the face×view×light and hand×prop joint choices stay open."""
    from vme.style.coverage import OriginalScope, reverse_plan, VisualModelCompletenessInvestigator, new_ledger, set_dimension
    scope = OriginalScope(scope_id="S", subjects=[{"id": "hero", "kind": "character", "face_visible": True, "view_changes": ["front"],
                                                   "lighting_changes": True, "contact_props": ["ring"], "subject_kind": "creature"}],
                          world={"kind": "workshop", "lighting": "directional"})
    plan = reverse_plan(scope)
    decs = [{"decision_id": f"PC-{c['choice_id']}", "status": "EXECUTABLE_CANDIDATE", "dimension_tags": sorted(c["dimensions"]),
             "owned_choice_ids": [c["choice_id"]],
             "branches": [{"when": {k: str(v) for k, v in c["conditions"].items()}, "operation_node_ids": ["op.whole_scene"]}]}
            for c in plan["choices"]]
    L = new_ledger("S", ["x"])
    L["frame_coverage_state"] = "ALL_TARGET_FRAMES_SEEN"
    for d in plan["required_dimensions"]:
        set_dimension(L, d, "RELEVANT_SUPPORTED", evidence=[{"source_hash": FA, "sequence_id": "x", "frame_start": 0, "frame_end": 0,
                                                             "evidence_kind": "FULL_FRAME"}], why_relevant="t", production_consumers=["op.whole_scene"])
    gaps = VisualModelCompletenessInvestigator(registered()).investigate(L, plan, decs)
    joints = {g.get("joint_id") for g in gaps if g["kind"] == "MISSING_JOINT_DECISION"}
    assert {"hero:face+view+light", "hero:contact+light", "hero:face+view"} <= joints


@pytest.mark.req("R13", "ST28-22")
def test_s1_refuses_15_without_locked_sixteenth(ws):
    from vme.loop.real import RealLoopRunner, RealProviders
    st = ws.store()
    st.put("SelectedSequenceManifest", "REAL:15", {"selected": []})
    prov = RealProviders(vision_client_factory=lambda: None, vision_transport_kind="SIMULATED", image_transport=None,
                         image_transport_kind="SIMULATED")
    status, out = RealLoopRunner(ws, run_id="REAL-T", providers=prov)._s1(st)
    assert status == "STOPPED" and out["stop_reason"] == "SIXTH_BOUNDARY_NOT_LOCKED"
    st.close()


class _StubFrames:
    def __init__(self, film, n=30):
        from vme.reference.frames import RetrievedFrame
        self.idx = [{"pts_time": i / 30} for i in range(n)]
        self.fr = {i: RetrievedFrame(film, i, i, i / 30, 64, 36, f"{i:064x}", True, _png((i * 5 % 255, 40, 90)), f"{i:064x}") for i in range(n)}

    def frame(self, k):
        return self.fr[k]


class _StubVision:
    def __init__(self, relations):
        from vme.vision.claude_adapter import default_caps
        self.caps = default_caps()
        self.relations = relations
        self.calls = []

    def request_json(self, task_id, kind, system, user_text, imgs, *, source_shas):
        from vme.providers.ids import validate_custom_id
        validate_custom_id(task_id)
        self.calls.append({"task": task_id, "labels": [i[0] for i in imgs], "user": json.loads(user_text), "system": system})
        return {"relations": self.relations, "uncertainty": ["SYNTHETIC: material cause unknown"], "phenomenon_dimensions": []}


@pytest.mark.req("R11", "ST28-03", "ST28-05")
def test_missing_source_gap_triggers_crop_and_neighbour_reinspection_not_a_stop(ws, monkeypatch):
    from vme.loop.real import RealLoopRunner, RealProviders
    st = ws.store()
    _witness(st, "W-x", FA, 10, ["WORLD_ASSEMBLY"], "SYNTHETIC: background layers recede behind the focal form", region={"x": 8, "y": 4, "w": 32, "h": 16})
    prov = RealProviders(vision_client_factory=lambda: None, vision_transport_kind="SIMULATED", image_transport=None, image_transport_kind="SIMULATED")
    r = RealLoopRunner(ws, run_id="REAL-T", providers=prov)
    frames = _StubFrames(FA)
    monkeypatch.setattr(r, "_film", lambda sha: ({}, frames.idx, frames))
    vis = _StubVision([{"relation": "SYNTHETIC: a foreground strut occludes the focal form while the far layer stays fixed",
                        "dimensions": ["DEPTH_VIEWPOINT"]}])
    trace = {"steps": []}
    g = {"gap_id": "G1", "kind": "MISSING_SOURCE", "what": "DEPTH_VIEWPOINT required by scope but never investigated",
         "dimensions": ["DEPTH_VIEWPOINT", "WORLD_ASSEMBLY"], "salience": "HIGH"}
    out = r._reinspect(st, vis, g, 1, trace)
    assert out["status"] == "NEW_WITNESSES"
    labels = vis.calls[0]["labels"]
    assert any(x.startswith("FULL") for x in labels) and any(x.startswith("NATIVE_CROP") and "x=8 y=4 w=32 h=16" in x for x in labels)
    assert sum(x.startswith("NEIGHBOUR") for x in labels) == 2
    assert "pass=P5" in vis.calls[0]["system"]
    w = st.get("Witness", out["new_witness_ids"][0])
    assert w["evidence_kind"] == "NATIVE_CROP" and w["from_gap"] == "G1" and "DEPTH_VIEWPOINT" in w["dimensions"]
    assert trace["steps"][0]["stage"] == "SOURCE_REINSPECTION" and trace["steps"][0]["requested_items"][0]["neighbours"] == [9, 11]
    vis2 = _StubVision([])
    assert r._reinspect(st, vis2, {**g, "gap_id": "G2"}, 1, trace)["status"] == "NO_NEW_EVIDENCE"   # unknown stays unresolved
    r.cfg.reinspection_budget = 2
    assert r._reinspect(st, vis2, {**g, "gap_id": "G3"}, 1, trace)["status"] == "REINSPECTION_BUDGET_EXHAUSTED"
    st.close()


@pytest.mark.req("R22")
def test_candidate_review_order_covers_every_window():
    from vme.loop.real import RealLoopRunner
    order = RealLoopRunner._review_order(23, 5)
    assert sorted(order) == list(range(23)) and len(set(order[:5])) == 5 and order[0] == 0
