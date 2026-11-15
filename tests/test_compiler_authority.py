"""Skill-exclusive prompt authority, causality and no-bypass (A33–A37, A53–A57, A68, B16–B22, C13–C16, C29,
ADD25-P01..P06, ADD26-P01..P03, ADD27-6/7/8)."""
import re

import pytest

from conftest import ROOT, compile_job
from vme.util import Blocked, read_json, atomic_write_json
from vme.fixtures import loop_fixtures as fx
from vme.compiler.compiler import StyleProgramCompiler, CompiledImageJob, recompile
from vme.experiments.experiments import causal_mutation_test, assert_causal


@pytest.mark.req("A33", "A54", "C15", "C16")
def test_every_span_owned_content_or_skill(skill, brief, caps):
    j = compile_job(skill, brief, caps)
    segs = j.trace["segments"]
    assert "\n".join(s["text"] for s in segs) == j.logical_payload["positivePrompt"]
    for s in segs:
        if s["authority"] == "STYLE":
            assert s["skill_hash"] == skill[1] and s["clause_id"] and s["skill_decision_id"]
        else:
            assert s["authority"] == "CONTENT" and s["brief_field_path"].startswith("slots.")
    assert j.trace["interface_two_audit"]["ok"]
    assert all(v for v in j.trace["field_ownership"].values())


@pytest.mark.req("A36", "B17", "C29", "ADD25-P03", "ADD26-P02")
def test_changing_selected_decision_changes_payload(skill, brief, caps):
    def mutate(folder):
        p = folder / "prompt_templates" / "whole_scene.json"
        t = read_json(p)
        for c in t["clauses"]:
            if c["id"].startswith("K-SYN-WORLD-01"):
                c["template"] = c["template"].replace("repeat one construction system", "repeat one construction system with clustered rhythm")
        atomic_write_json(p, t)
    r = causal_mutation_test(skill[0], brief, caps, recipe_id="character_world", node_id="n1_scene", mutate=mutate, label="world clause edit")
    assert_causal(r, expect_change=True)
    assert any("clustered rhythm" in x for x in r["diff"]["positivePrompt"]["added"])


@pytest.mark.req("B18", "ADD25-P04")
def test_changing_nonselected_prose_does_not_change_payload(skill, brief, caps):
    def mutate(folder):
        (folder / "SKILL.md").write_text("totally different prose: make it cinematic and glossy", encoding="utf-8")
        (folder / "notes" / "observations.md").write_text("new adjectives: stunning, polished", encoding="utf-8")
    r = causal_mutation_test(skill[0], brief, caps, recipe_id="character_world", node_id="n1_scene", mutate=mutate, label="prose only")
    assert_causal(r, expect_change=False)
    assert not r["skill_hash_changed"]


@pytest.mark.req("ADD25-P02", "A54", "B15")
def test_removing_required_decision_blocks_with_ticket(skill, brief, caps):
    def mutate(folder):
        d = [x for x in read_json(folder / "decisions.json") if x["decision_id"] != "D-SYN-WORLD"]
        atomic_write_json(folder / "decisions.json", d)
    r = causal_mutation_test(skill[0], brief, caps, recipe_id="character_world", node_id="n1_scene", mutate=mutate, label="remove world")
    assert r["blocked_after"]["code"] == "MISSING_STYLE_DECISION"
    t = r["blocked_after"]["ticket"]
    assert t["missing_art_decision"] == "D-SYN-WORLD" and t["required_source_question"]


@pytest.mark.req("A53", "ADD25-P01", "ADD26-P01", "C14", "B19")
def test_runtime_style_append_and_raw_prompt_refused(tmp_path, store, skill, brief, caps):
    from conftest import offline_gateway
    g, t = offline_gateway(store, tmp_path, caps)
    j = compile_job(skill, brief, caps)
    j.logical_payload["positivePrompt"] += "\nadd shiny Pixar-style lighting"   # dict is mutable; job identity is not
    with pytest.raises(Blocked) as e:
        g.submit(j)
    assert e.value.code == "COMPILED_JOB_MUTATED" and t.billed() == 0
    with pytest.raises(Blocked) as e2:
        g.submit({"positivePrompt": "a cute scientist", "model": "runware:400@4"})
    assert e2.value.code == "RAW_PROMPT_GATEWAY_BYPASS"
    with pytest.raises(Blocked):
        CompiledImageJob("x", {"positivePrompt": "x"}, (), {}, {}, False, False, "0", object())
    assert not hasattr(g, "submit_prompt") and not any(n for n in dir(g) if "prompt" in n.lower())


def _ast_scan(text: str) -> dict:
    """AST call-target scan (R24): who BUILDS a positivePrompt dict, who CALLS a provider send/transport/urlopen,
    and who merely CONSTRUCTS the http transport factory (construction is not a send)."""
    import ast
    tree = ast.parse(text)
    out = {"builds_prompt": False, "sends": [], "constructs_http_transport": False}
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "positivePrompt" for k in n.keys):
            out["builds_prompt"] = True
        if isinstance(n, ast.Call):
            f = n.func
            name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None
            if name in ("send", "urlopen") or (isinstance(f, ast.Attribute) and f.attr == "transport"):
                out["sends"].append(ast.unparse(f))
            if name == "http_transport":
                out["constructs_http_transport"] = True
    return out


@pytest.mark.req("C14", "ADD26-A01", "R24")
def test_static_scan_only_compiler_builds_positive_prompt_and_only_gateway_sends():
    src = ROOT / "vme"
    builders, senders, constructors = [], {}, []
    for p in src.rglob("*.py"):
        rel = p.relative_to(src).as_posix()
        r = _ast_scan(p.read_text(encoding="utf-8"))
        if r["builds_prompt"]:
            builders.append(rel)
        if r["sends"]:
            senders[rel] = r["sends"]
        if r["constructs_http_transport"]:
            constructors.append(rel)
    # audit/export.py is an explicit NEGATIVE DRILL: it hands a raw positivePrompt dict to the gateway to record the refusal.
    drills = {"audit/export.py"}
    assert sorted(set(builders) - drills) == ["compiler/compiler.py"]
    drill_src = (src / "audit" / "export.py").read_text(encoding="utf-8")
    assert re.search(r'g\.submit\(\{"positivePrompt"', drill_src), "drill must only feed the raw dict to the gateway (expected refusal)"
    # the ONLY provider send call sites: gateway (adapter.send) and the adapter/transport itself
    # vision/providers.py calls a VISION transport (source analysis, separately authorized); it must not touch Runware
    vision_src = (src / "vision" / "providers.py").read_text(encoding="utf-8")
    assert "runware" not in vision_src.lower() and "RunwareAdapter" not in vision_src
    assert senders.get("vision/providers.py", []) in ([], ["self.transport"])
    senders.pop("vision/providers.py", None)
    assert set(senders) <= {"providers/gateway.py", "providers/runware.py"}, senders
    assert all(c in ("self.adapter.send",) for c in senders.get("providers/gateway.py", []))
    # the http transport may be CONSTRUCTED only by the production provider bundle, which hands it to the gateway's adapter
    assert set(constructors) <= {"loop/real.py", "providers/runware.py"}
    real_src = (src / "loop" / "real.py").read_text(encoding="utf-8")
    assert re.search(r"image_transport=http_transport\(api\)", real_src)


@pytest.mark.req("R24")
def test_static_scanner_still_catches_an_unauthorized_send():
    bad = "from vme.providers.runware import RunwareAdapter\nRunwareAdapter({}, t).send(b'[]')\n"
    assert _ast_scan(bad)["sends"] == ["RunwareAdapter({}, t).send"]
    assert _ast_scan("x = {'positivePrompt': 'p'}")["builds_prompt"]
    assert _ast_scan("import urllib.request\nurllib.request.urlopen('https://api.runware.ai')")["sends"]
    assert not _ast_scan("# .send( http_transport( runware")["sends"]          # comments/strings are not calls


@pytest.mark.req("ADD25-P05", "A56", "B20", "ADD27-9")
def test_style_smuggled_through_brief_rejected_with_ticket(skill, caps):
    b = fx.synthetic_brief(slots={"subject": "explorer, use thick outlines and yellow highlights"})
    with pytest.raises(Blocked) as e:
        compile_job(skill, b, caps)
    assert e.value.code == "STYLE_INJECTION_IN_CONTENT"
    assert e.value.data["ticket"]["kind"] == "SKILL_REVISION_REQUIRED"
    b2 = dict(fx.synthetic_brief())
    b2["aesthetic_prompt"] = "cinematic"
    with pytest.raises(Blocked) as e2:
        compile_job(skill, b2, caps)
    assert e2.value.code == "UNTYPED_BRIEF_FIELD"
    ok = compile_job(skill, fx.synthetic_brief(), caps)  # 'red laboratory coat' is legitimate content
    assert "red laboratory coat" in ok.logical_payload["positivePrompt"]


@pytest.mark.req("B21", "A57", "A59")
def test_pose_edit_without_identity_reference_refused(skill, brief, caps):
    with pytest.raises(Blocked) as e:
        compile_job(skill, brief, caps, node="n3_view")
    assert e.value.code == "CHARACTER_IDENTITY_REFERENCE_MISSING"


@pytest.mark.req("A55", "A57", "A59")
def test_stage_specific_operations_and_identity_bytes_sent(tmp_path, skill, caps):
    from PIL import Image
    canon = tmp_path / "canon.png"
    Image.new("RGB", (64, 64), (10, 20, 30)).save(canon)
    from vme.util import sha256_file
    ida = {"explorer:canonical": {"path": str(canon), "sha256": sha256_file(canon), "approved": True}}
    b = fx.synthetic_brief(subjects=[{**fx.synthetic_brief()["subjects"][0], "identity_asset_id": "explorer:canonical"}])
    scene = compile_job(skill, b, caps, node="n1_scene")
    view = compile_job(skill, b, caps, node="n3_view", identity_assets=ida)
    grip = compile_job(skill, fx.synthetic_brief(subjects=b["subjects"], slots={"action": "grip"}), caps, node="n4_grip", identity_assets=ida)
    assert scene.trace["operator"] == "op.whole_scene" and view.trace["operator"] == "op.face_view_state"
    assert grip.trace["operator"] == "op.hand_prop_contact"
    assert view.reference_images[0][0] == "canonical_identity" and view.reference_images[0][1] == sha256_file(canon)
    assert view.logical_payload["inputs"]["referenceImages"][0].startswith("data:image/png;base64,")
    assert any("K-SYN-GRIP-01" in c for c in grip.trace["clause_ids"])
    assert scene.logical_payload["positivePrompt"] != view.logical_payload["positivePrompt"]
    ida2 = {k: dict(v, approved=False) for k, v in ida.items()}
    with pytest.raises(Blocked):
        compile_job(skill, b, caps, node="n3_view", identity_assets=ida2)


@pytest.mark.req("B22", "ADD25-P06", "A35")
def test_reference_overflow_staged_or_blocked(tmp_path, brief, caps):
    from vme.fixtures.synthetic import build_synthetic_skill
    f1 = tmp_path / "s1"
    h1 = build_synthetic_skill(f1, extra_refs=4)
    with pytest.raises(Blocked) as e:
        StyleProgramCompiler().compile(brief, f1, pinned_skill_hash=h1, recipe_id="character_world", node_id="n1_scene", caps=caps)
    assert e.value.code == "PROVIDER_REF_LIMIT"
    f2 = tmp_path / "s2"
    h2 = build_synthetic_skill(f2, extra_refs=4, overflow_policy="STAGED_EDIT")
    j = StyleProgramCompiler().compile(brief, f2, pinned_skill_hash=h2, recipe_id="character_world", node_id="n1_scene", caps=caps)
    assert len(j.trace["stages"]) == 2 and len(j.logical_payload["inputs"]["referenceImages"]) == caps["max_reference_images"]
    assert j.trace["stages"][1]["reference_count"] == 6 - caps["max_reference_images"] + 1


@pytest.mark.req("A35")
def test_prompt_length_and_dimension_limits(skill, brief, caps):
    big = dict(caps, max_prompt_chars=100)
    with pytest.raises(Blocked) as e:
        compile_job(skill, brief, big)
    assert e.value.code == "PROMPT_LIMIT"
    with pytest.raises(Blocked) as e2:
        compile_job(skill, brief, caps, output_contract={"width": 1920, "height": 1080, "format": "PNG", "asset_kind": "WHOLE_SCENE"})
    assert e2.value.code == "PROVIDER_DIMENSION_MULTIPLE"


@pytest.mark.req("B16", "C13")
def test_skill_md_only_has_no_authority(tmp_path):
    from vme.skills.skill import load_skill
    f = tmp_path / "s"
    f.mkdir()
    (f / "SKILL.md").write_text("# a style essay", encoding="utf-8")
    with pytest.raises(Blocked) as e:
        load_skill(f)
    assert e.value.code == "SKILL_HAS_NO_PRODUCING_ARTIFACTS"


@pytest.mark.req("A34", "ADD27-8")
def test_compiler_bug_dropping_clause_is_caught_with_before_after_bytes(skill, brief, caps):
    def buggy(template, slots):
        out = StyleProgramCompiler._default_render(template, slots)
        return out.replace("densest internal divisions", "")
    with pytest.raises(Blocked) as e:
        StyleProgramCompiler(clause_renderer=buggy).compile(brief, skill[0], pinned_skill_hash=skill[1], recipe_id="character_world",
                                                            node_id="n1_scene", caps=caps)
    assert e.value.code == "SELECTED_CLAUSE_ALTERED_IN_PAYLOAD"
    assert "densest internal divisions" in e.value.data["payload_prompt_before"]
    assert "densest internal divisions" not in e.value.data["payload_prompt_after"]


@pytest.mark.req("C15", "ADD26-P03", "A51")
def test_unlike_subject_selects_different_branch_same_grammar(skill, caps):
    a = compile_job(skill, fx.synthetic_brief(), caps)
    b = compile_job(skill, fx.holdout_brief(), caps)
    assert a.trace["selected_branches"]["D-SYN-CHAR-WHOLE"]["subject_kind"] == "biped"
    assert b.trace["selected_branches"]["D-SYN-CHAR-WHOLE"]["subject_kind"] == "creature"
    assert "orange jacket" not in b.logical_payload["positivePrompt"] and "six legs" not in b.logical_payload["positivePrompt"]


@pytest.mark.req("C16", "A37")
def test_deterministic_logical_request(skill, brief, caps):
    a, b = compile_job(skill, brief, caps), compile_job(skill, brief, caps)
    assert a.logical_sha256 == b.logical_sha256 and recompile(a).logical_payload == a.logical_payload


@pytest.mark.req("A33")
def test_unpinned_or_modified_frozen_skill_refused(tmp_path, skill, brief, caps):
    from vme.skills.skill import freeze_skill
    with pytest.raises(Blocked) as e:
        StyleProgramCompiler().compile(brief, skill[0], pinned_skill_hash="0" * 64, recipe_id="character_world", node_id="n1_scene", caps=caps)
    assert e.value.code == "SKILL_NOT_PINNED"
    freeze_skill(skill[0], observed_relations=fx.OBSERVED_RELATIONS, approved_by="reviewer")
    p = skill[0] / "decisions.json"
    d = read_json(p)
    d[0]["exceptions"].append("late edit")
    atomic_write_json(p, d)
    with pytest.raises(Blocked) as e2:
        compile_job(skill, brief, caps)
    assert e2.value.code == "FROZEN_SKILL_MODIFIED"


@pytest.mark.req("A68")
def test_reference_impl_suites_pass():
    import subprocess, sys
    spec = ROOT.parent / "Visual_Mastery_Engine_Build_Spec_v1_3"
    for d, n in (("reference_impl", 7), ("reference_impl_v13", 29)):
        r = subprocess.run([sys.executable, "-m", "unittest", "-q"], cwd=spec / d, capture_output=True, text=True)
        assert r.returncode == 0 and f"Ran {n} tests" in r.stderr, r.stderr[-500:]
