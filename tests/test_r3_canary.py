"""R3 offline two-actor canary — a NOVEL original scene (lighthouse keeper + giant moth) driven S0→S9 through the REAL loop with
simulated transports only (no network socket, no paid call, no source upload).

Checks identity, character continuity, interactions (hand/prop contact), timing (overlapping events), motion, appearance routing,
the AV gate, the capture index (F06), ablations and counterfactuals. Artistic quality is NOT judged here: it stays UNPROVEN.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

from vme.util import Blocked

@pytest.fixture(scope="module")
def canary(tmp_path_factory):
    from vme.testing.drill import (build_drill_workspace, drill_providers, drive, enable_network_flag, two_actor_brief,
                                   two_actor_unseen_brief, DRILL_HUMAN)
    from vme.loop.human import add_brief
    from vme.state.workspace import Workspace
    enable_network_flag()
    reuse = os.environ.get("VME_CANARY_REUSE_ROOT")        # dev-only: resume an already-driven canary workspace (still re-verified below)
    root = Path(reuse) if reuse else tmp_path_factory.mktemp("canary")
    if not (root / "ws" / "state" / "SOURCE_LOCK.json").exists():
        build_drill_workspace(root)
        add_brief(Workspace(root / "ws").ensure(), two_actor_brief(), added_by=DRILL_HUMAN)
    ws = Workspace(root / "ws").ensure()
    prov, client = drill_providers(root)
    out = drive(ws, prov, run_id="REAL-CANARY", families=["keeper", "moth"], anchor_brief_id="BRIEF-CANARY-2ACTOR",
                unseen_brief=two_actor_unseen_brief, max_rounds=40)
    st = ws.store()
    o = {s: (st.get("LoopTransition", f"REAL-CANARY:{s}") or {}).get("outputs") for s in ("S4", "S5", "S7", "S8", "S9")}
    prog = st.get("EventProgram", "REAL-CANARY")
    jobs = {r["job_id"]: r for r in st.list("CompiledImageJob")}
    st.close()
    pack = json.loads(Path(o["S7"]["pack"]).read_text(encoding="utf-8"))
    return {"root": root, "ws": ws, "out": out, "o": o, "prog": prog, "pack": pack, "jobs": jobs, "client": client}


def test_canary_reaches_s9_offline(canary):
    assert canary["out"]["result"].get("completed_through") == "S9", canary["out"]["log"]
    assert canary["client"].duplicate_creates() == 0
    assert canary["client"].billed_requests() > 0                  # simulated transport did answer (no real socket was opened)


def test_identity_each_actor_has_its_own_canonical_job_and_bytes(canary):
    s5 = canary["o"]["S5"]
    k, m = s5["n_canonical_character@keeper"], s5["n_canonical_character@moth"]
    assert k["actor_id"] == "keeper" and m["actor_id"] == "moth"
    assert k["sha"] != m["sha"] and k["job_id"] != m["job_id"]
    assert k["identity_slots"]["subject"].startswith("lighthouse keeper") and m["identity_slots"]["subject"].startswith("giant friendly moth")
    # each actor's job is governed by its own decisions: decisions owned only by the other actor are excluded, never silently merged
    kj, mj = canary["jobs"][k["job_id"]], canary["jobs"][m["job_id"]]
    assert kj["trace"]["actor_scope"] == {"actor_id": "keeper", "other_actor_ids": ["moth"]}
    assert set(kj["trace"]["excluded_other_actor_decisions"]) & set(mj["trace"]["selected_decisions"])
    assert not set(kj["trace"]["excluded_other_actor_decisions"]) & set(kj["trace"]["selected_decisions"])
    assert "lighthouse keeper" in kj["payload"]["positivePrompt"] and "moth" not in kj["payload"]["positivePrompt"].split("Subject:")[-1].split("\n")[0]


def test_continuity_every_state_redraw_is_bound_to_its_own_actor_canonical(canary):
    pack = canary["pack"]
    canon = {a: v["sha256"] for a, v in pack["canonical_by_actor"].items()}
    assert set(canon) == {"keeper", "moth"} and len(set(canon.values())) == 2
    assert set(pack["states"]) == {"keeper:grip:lantern_handle", "moth:view:front"}
    for key, s in pack["states"].items():
        actor = key.split(":", 1)[0]
        assert s["actor_id"] == actor and s["identity_source_sha256"] == canon[actor]


def test_per_actor_jobs_recompile_identically_from_their_pinned_inputs(canary):
    """The gateway's tamper check: each per-actor job recompiles to the same id/payload with its actor scope (F12 provenance)."""
    from vme.compiler.compiler import StyleProgramCompiler
    from vme.loop.human import provider_state
    st = canary["ws"].store()
    brief = st.get("OriginalBrief", "BRIEF-CANARY-2ACTOR")["brief"]
    st.close()
    s4 = canary["o"]["S4"]
    for actor, other in (("keeper", "moth"), ("moth", "keeper")):
        rec = canary["o"]["S5"][f"n_canonical_character@{actor}"]
        b = dict(brief, slots={**brief["slots"], **rec["identity_slots"]})
        j = StyleProgramCompiler().compile(b, s4["skill_folder"], pinned_skill_hash=s4["skill_hash"], recipe_id="main",
                                           node_id="n_canonical_character", caps=provider_state(canary["ws"])["runware"],
                                           actor_scope={"actor_id": actor, "other_actor_ids": [other]})
        assert j.job_id == rec["job_id"] and j.trace["selected_decisions"] == rec["selected_decisions"]
        from vme.compiler.compiler import recompile
        assert recompile(j).job_id == j.job_id                     # the gateway's tamper re-check sees the same actor-scoped job


def test_canary_survives_a_fresh_directory_capsule_restore(canary, tmp_path):
    """Acceptance §E: export the two-actor run, cold-import in a fresh directory, and replay both actors' canonical jobs identically."""
    from vme.state.capsule import export_capsule, import_and_verify
    e = export_capsule(canary["ws"], "REAL-CANARY", tmp_path / "canary_capsule.zip")
    reh = e["capsule"]["pinned_rehearsal"]
    assert set(reh["actors"]) == {"keeper", "moth"} and all("logical_sha256" in v for v in reh["actors"].values())
    assert reh["actors"]["keeper"]["job_id"] == canary["o"]["S5"]["n_canonical_character@keeper"]["job_id"]
    assert reh["actors"]["moth"]["job_id"] == canary["o"]["S5"]["n_canonical_character@moth"]["job_id"]
    v = import_and_verify(tmp_path / "canary_capsule.zip", tmp_path / "fresh_env", sources_folder=canary["root"] / "drill_sources")
    assert v["status"] == "VERIFIED_READY_TO_RESUME", v
    assert v["rehearsal"]["byte_identical_logical_payload"] is True
    assert v["rehearsal"]["recomputed"]["actors"] == reh["actors"]


def test_interaction_contact_is_owned_and_anchored_to_the_prop(canary):
    c = canary["o"]["S8"]["contacts"]
    assert len(c) == 1 and c[0]["owner_actor_id"] == "keeper" and c[0]["world_anchor_or_prop_id"] == "lantern_handle"
    assert c[0]["hand_side"] == "right" and c[0]["owner_clause_ids"] and all(x.endswith("@hand_prop_contact") for x in c[0]["owner_clause_ids"])
    assert c[0]["occlusion_and_grip_state_sha"] == canary["pack"]["states"]["keeper:grip:lantern_handle"]["sha256"]


def test_timing_overlapping_events_and_every_track_inside_the_timebase(canary):
    prog, s8 = canary["prog"], canary["o"]["S8"]
    ev = {e["event"]: e for e in s8["event_trace"]}
    k, m = ev["k1"]["frames"], ev["m1"]["frames"]
    assert k[0] < m[0] <= k[1]                    # the moth turns WHILE the keeper is still gripping (simultaneous action)
    for t in prog["tracks"]:
        assert 0 <= t["start_frame"] <= t["end_frame"] < prog["frames"]


def test_motion_every_track_is_skill_owned_for_both_actors_and_scene(canary):
    tr = canary["o"]["S8"]["tracks"]
    kinds = {(t["kind"], t["actor_id"]) for t in tr}
    assert {("ACTOR_ACTING", "keeper"), ("ACTOR_ACTING", "moth"), ("ACTOR_DRAWING_STATE", "keeper"), ("ACTOR_DRAWING_STATE", "moth"),
            ("CAMERA", None), ("ATTENTION", None), ("WORLD", None), ("AUDIO", None)} <= kinds
    assert all(t["owner_decision_id"] and t["owner_decision_id"].startswith("PC-") for t in tr)
    acting = [t for t in canary["prog"]["tracks"] if t["kind"] == "ACTOR_ACTING"]
    assert acting[0]["owner_decision_id"] != acting[1]["owner_decision_id"]       # per-actor ownership, not one shared default
    assert canary["o"]["S8"]["motion"] == "INDEPENDENT_MOTION_PRESENT" and canary["o"]["S8"]["ffprobe_ok"] is True
    att = next(t for t in canary["prog"]["tracks"] if t["kind"] == "ATTENTION")
    assert att["targets"] == ["keeper", "moth"]


def test_appearance_world_plate_has_no_actor_and_labels_stay_honest(canary):
    s8, pack = canary["o"]["S8"], canary["pack"]
    assert pack["world_plate"]["contains_actor"] is False and s8["background"].startswith("WORLD_PLATE")
    assert "UNPROVEN" in s8["animation_claim"] and s8["label"].startswith("TECHNICAL_RENDER_ONLY")
    assert pack["method"] == "WHOLE_STATE_SWAP" and "does NOT provide" in pack["method_limits"]


def test_av_gate_measures_every_scheduled_cue(canary):
    av = canary["o"]["S8"]["av"]
    assert av["status"] == "AV_VERIFIED" and av["ok"] is True and av["measured_onsets"] == av["scheduled_cues"]
    starts = {e["frames"][0] for e in canary["o"]["S8"]["event_trace"]}
    assert starts <= set(av["scheduled_cues"])            # each event onset carries a cue (CUE_ON_EVENT)


def test_heldout_still_transfer_never_grants_motion_or_av(canary):
    s9 = canary["o"]["S9"]
    assert s9["holdout"].startswith("BRIEF-CANARY-UNSEEN")
    assert s9["animated_transfer"] == "NOT_ATTEMPTED" and s9["audiovisual_qualification"].startswith("NOT_QUALIFIED")


def test_f06_capture_index_every_sent_source_request_carries_p0_and_its_pass(canary):
    from vme.vision.protocol import P0, PROTOCOL_SHA
    journals = sorted((canary["ws"].root / "providers" / "anthropic").rglob("task_*.json"))
    assert journals, "no request journals"
    passes = set()
    for p in journals:
        j = json.loads(p.read_text(encoding="utf-8"))
        man = j.get("manifest") or {}
        assert man.get("request_sha") and man.get("pass_id"), p.name
        assert P0[:80] in man["system"] and PROTOCOL_SHA in man["system"] and f"pass={man['pass_id']}" in man["system"], p.name
        passes.add(man["pass_id"])
    assert {"P1", "P4"} <= passes


# ---- ablations / counterfactuals on the canary's own frozen skill + program -----------------------------------------------

def _decs(canary):
    return json.loads((Path(canary["o"]["S4"]["skill_folder"]) / "decisions.json").read_text(encoding="utf-8"))


def _program(canary, decisions, brief=None):
    from vme.render.motion_program import compile_event_program
    from vme.style.coverage import OriginalScope
    st = canary["ws"].store()
    try:
        b = brief or st.get("OriginalBrief", "BRIEF-CANARY-2ACTOR")["brief"]
    finally:
        st.close()
    scope = OriginalScope(scope_id=b["brief_id"], **b["scope"])
    return compile_event_program(decisions=decisions, scope=scope, brief=b, pack=canary["pack"], width=320, height=180, scale=0.25)


def test_baseline_program_reproduces_the_rendered_program(canary):
    assert _program(canary, _decs(canary))["program_sha"] == canary["prog"]["program_sha"]


@pytest.mark.parametrize("kind,actor", [("ACTOR_ACTING", "moth"), ("ACTOR_ACTING", "keeper"), ("CAMERA", None), ("ATTENTION", None),
                                        ("AUDIO", None)])
def test_ablation_removing_the_owner_refuses_instead_of_defaulting(canary, kind, actor):
    base = _program(canary, _decs(canary))
    t = next(t for t in base["tracks"] if t["kind"] == kind and t.get("actor_id") == actor)
    owners = {t["owner_decision_id"], *t["co_owner_decision_ids"]}
    if t["co_owner_decision_ids"]:                 # corroborated: dropping ONE owner keeps the same program from the others
        p = _program(canary, [d for d in _decs(canary) if d["decision_id"] != t["owner_decision_id"]])
        t2 = next(x for x in p["tracks"] if x["kind"] == kind and x.get("actor_id") == actor)
        assert t2["method"] == t["method"] and t2["owner_decision_id"] in t["co_owner_decision_ids"]
    with pytest.raises(Blocked) as e:
        _program(canary, [d for d in _decs(canary) if d["decision_id"] not in owners])
    assert e.value.code == "MOTION_TRACK_UNOWNED"


def test_conflicting_equally_applicable_motion_owners_are_refused(canary):
    base = _program(canary, _decs(canary))
    t = next(t for t in base["tracks"] if t["kind"] == "CAMERA")
    assert t["co_owner_decision_ids"], "canary camera must have corroborating owners for this test"
    decs = copy.deepcopy(_decs(canary))
    co = next(d for d in decs if d["decision_id"] == t["co_owner_decision_ids"][0])
    for b in co["branches"]:
        if (b.get("motion_program") or {}).get("track_kind") == "CAMERA":
            b["motion_program"]["method"] = "STEPPED_REDRAW" if t["method"] != "STEPPED_REDRAW" else "EASE_IN_OUT"
    with pytest.raises(Blocked) as e:
        _program(canary, decs)
    assert e.value.code == "CONFLICTING_MOTION_OWNERS"


def test_counterfactual_learned_method_change_changes_only_that_actors_keyframes(canary):
    owner = next(t["owner_decision_id"] for t in canary["prog"]["tracks"] if t["kind"] == "ACTOR_ACTING" and t["actor_id"] == "moth")
    decs = copy.deepcopy(_decs(canary))
    d = next(x for x in decs if x["decision_id"] == owner)
    for b in d["branches"]:
        if (b.get("motion_program") or {}).get("track_kind") == "ACTOR_ACTING":
            b["motion_program"]["method"] = "HOLD_THEN_MOVE"
    p = _program(canary, decs)
    old = {(t["kind"], t.get("actor_id")): t for t in _program(canary, _decs(canary))["tracks"]}
    new = {(t["kind"], t.get("actor_id")): t for t in p["tracks"]}
    assert new[("ACTOR_ACTING", "moth")]["keyframes"] != old[("ACTOR_ACTING", "moth")]["keyframes"]
    assert new[("ACTOR_ACTING", "keeper")]["keyframes"] == old[("ACTOR_ACTING", "keeper")]["keyframes"]
    assert p["program_sha"] != canary["prog"]["program_sha"]


def test_counterfactual_brief_timing_moves_cues_and_tracks_with_the_event(canary):
    st = canary["ws"].store()
    b = copy.deepcopy(st.get("OriginalBrief", "BRIEF-CANARY-2ACTOR")["brief"])
    st.close()
    b["shot_plan"]["events"][1]["from"] = 35
    p = _program(canary, _decs(canary), brief=b)
    assert 35 in [c["frame"] for c in p["audio_cues"]] and 25 not in [c["frame"] for c in p["audio_cues"]]
    st_ = next(t for t in p["tracks"] if t["kind"] == "ACTOR_DRAWING_STATE" and t["actor_id"] == "moth")
    assert st_["start_frame"] == 35


def test_image_ablation_dropping_an_actors_decision_refuses_that_actors_job(canary):
    """Removing every branch of a keeper-owned decision from the frozen skill makes the keeper's compile refuse (no default art)."""
    import shutil
    from vme.compiler.compiler import StyleProgramCompiler
    from vme.skills.skill import load_skill
    from vme.loop.human import provider_state
    src = Path(canary["o"]["S4"]["skill_folder"])
    k = canary["o"]["S5"]["n_canonical_character@keeper"]
    kj = canary["jobs"][k["job_id"]]
    target = next(d for d in kj["trace"]["selected_decisions"])
    dst = canary["root"] / "ablated_skill"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    decs = json.loads((dst / "decisions.json").read_text(encoding="utf-8"))
    for d in decs:
        if d["decision_id"] == target:
            d["branches"] = [b for b in d["branches"] if b["when"].get("subject_kind") != "biped"]
    (dst / "decisions.json").write_text(json.dumps(decs), encoding="utf-8")
    try:
        sk = load_skill(dst)
    except Blocked as e:                                            # an edited frozen skill may already be refused as tampered
        assert e.code
        return
    st = canary["ws"].store()
    brief = st.get("OriginalBrief", "BRIEF-CANARY-2ACTOR")["brief"]
    st.close()
    b = dict(brief, slots={**brief["slots"], **k["identity_slots"]})
    with pytest.raises(Blocked) as e:
        StyleProgramCompiler().compile(b, dst, pinned_skill_hash=sk["skill_hash"], recipe_id="main", node_id="n_canonical_character",
                                       caps=provider_state(canary["ws"])["runware"],
                                       actor_scope={"actor_id": "keeper", "other_actor_ids": ["moth"]})
    assert e.value.code in ("MISSING_STYLE_DECISION", "SKILL_STATUS_DISALLOWED")
