"""R3 F16/F17 — source-art review of candidate decisions and SEPARATE per-capability statuses (never averaged into one 'ready').

* `review_source_claim`: a named human compares a decision's cited native witnesses with its claims. REFUTED reopens it
  (RESEARCH_ONLY, new version, kept history); APPROVED only records SOURCE_ART_REVIEWED — still a SKILL_CANDIDATE, never transfer-qualified.
  A provider echoing hashes / valid JSON never reaches this state.
* `capability_verdict`: one status per capability from the R3 enum, derived from stored evidence only.
"""
from __future__ import annotations

from ..util import Blocked, now_iso
from ..state.authority import AuthorityRegistry

STATUS = ("NOT_IMPLEMENTED", "IMPLEMENTED_UNTESTED", "OFFLINE_VERIFIED", "REAL_SOURCE_UNCALIBRATED", "SOURCE_ART_REVIEWED", "SKILL_CANDIDATE",
          "SKILL_TRANSFER_QUALIFIED", "ORIGINAL_AUDIOVISUAL_QUALIFIED")
CAPABILITIES = ("OBSERVATION", "SOURCE_ART_TRUTH", "SOURCE_CHARACTER_ART", "TEMPORAL_SCENES", "AV_MEANING", "CLUSTER_QUESTION",
                "CONDITIONAL_SKILL", "REFERENCE_AUTHORITY", "IMAGE_COMPILER", "CHARACTER_ASSET", "MULTIACTOR_MOTION", "CAMERA_ATTENTION",
                "AUDIO_MUX", "RENDER_GATE", "COLD_REPLAY", "HELDOUT_TRANSFER")


def review_source_claim(store, decision_id: str, *, verdict: str, by: str, statement: str, checked_witness_ids: list[str]) -> dict:
    d = store.get("ConditionalVisualDecision", decision_id)
    if d is None:
        raise Blocked("UNKNOWN_DECISION", decision_id)
    if not set(checked_witness_ids) or not set(checked_witness_ids) <= set(d.get("authorized_witness_ids") or d.get("evidence_frame_ids") or []):
        raise Blocked("REVIEW_MUST_CHECK_THE_CITED_NATIVE_WITNESSES", decision_id)
    rec = AuthorityRegistry(store).issue("SOURCE_ART_REVIEW", scope={"decision_id": decision_id, "version": int(d["version"])},
                                         verdict=verdict, by=by, statement=statement, evidence={"witness_ids": sorted(checked_witness_ids)})
    if verdict == "REFUTED":
        store.put("ConditionalVisualDecision", decision_id, {**d, "version": d["version"] + 1, "status": "RESEARCH_ONLY",
                                                              "research_only_reason": f"SOURCE_ART_REVIEW_REFUTED:{rec['authority_id']}",
                                                              "claim_state": "REFUTED_BY_SOURCE_REVIEW", "refuted_at": now_iso()})
    elif verdict == "APPROVED":
        store.put("ConditionalVisualDecision", decision_id, {**d, "source_art_review": f"SOURCE_ART_REVIEWED:{rec['authority_id']}"})
    return rec


def capability_verdict(store, run_id: str) -> dict:
    t = {x["stage"]: x for x in store.list("LoopTransition") if x["run_id"] == run_id}
    origin = next((x.get("evidence_origin") for x in t.values()), "UNKNOWN")
    real = origin == "REAL_VLM"
    done = lambda s: t.get(s, {}).get("status") == "COMPLETED"
    decs = [d for d in store.list("ConditionalVisualDecision") if not d.get("synthetic")]
    reviewed = [d for d in decs if str(d.get("source_art_review", "")).startswith("SOURCE_ART_REVIEWED")]
    dossiers = [x for x in store.list("CharacterArtDossier") if x.get("status") == "VALIDATED"]
    audio = [x for x in store.list("SourceAudioStudy")]
    s8 = t.get("S8", {}).get("outputs") or {}
    off = "OFFLINE_VERIFIED" if done("S1") else "IMPLEMENTED_UNTESTED"
    v = {
        "OBSERVATION": ("REAL_SOURCE_UNCALIBRATED" if real else off),
        "SOURCE_ART_TRUTH": ("SOURCE_ART_REVIEWED" if real and decs and len(reviewed) == len(decs) else
                             "BLOCKED:NO_HUMAN_NATIVE_SOURCE_REVIEW" if real else "BLOCKED:SIMULATED_EVIDENCE_ONLY"),
        "SOURCE_CHARACTER_ART": ("OFFLINE_VERIFIED" if dossiers and not real else "REAL_SOURCE_UNCALIBRATED" if dossiers else
                                 "BLOCKED:NO_VALIDATED_CHARACTER_DOSSIER"),
        "TEMPORAL_SCENES": off,
        "AV_MEANING": "BLOCKED:AUDIO_MEANING_UNSTUDIED (energy onsets only; no consented transcript)" if audio else "BLOCKED:AUDIO_UNSTUDIED",
        "CLUSTER_QUESTION": "OFFLINE_VERIFIED" if store.list("P3QuestionRecord") else "IMPLEMENTED_UNTESTED",
        "CONDITIONAL_SKILL": "SKILL_CANDIDATE" if done("S4") else "IMPLEMENTED_UNTESTED",
        "REFERENCE_AUTHORITY": "OFFLINE_VERIFIED" if done("S5") else "IMPLEMENTED_UNTESTED",
        "IMAGE_COMPILER": "OFFLINE_VERIFIED" if done("S5") else "IMPLEMENTED_UNTESTED",
        "CHARACTER_ASSET": "OFFLINE_VERIFIED" if done("S7") else "IMPLEMENTED_UNTESTED",
        "MULTIACTOR_MOTION": ("OFFLINE_VERIFIED" if done("S8") and len(s8.get("actors") or []) > 1 else
                              "IMPLEMENTED_UNTESTED (single actor in this run)" if done("S8") else "IMPLEMENTED_UNTESTED"),
        "CAMERA_ATTENTION": "OFFLINE_VERIFIED" if any(x.get("kind") in ("CAMERA", "ATTENTION") for x in s8.get("tracks") or []) else "IMPLEMENTED_UNTESTED",
        "AUDIO_MUX": "OFFLINE_VERIFIED" if (s8.get("av") or {}).get("ok") else "IMPLEMENTED_UNTESTED",
        "RENDER_GATE": "OFFLINE_VERIFIED" if done("S8") else "IMPLEMENTED_UNTESTED",
        "COLD_REPLAY": "IMPLEMENTED_UNTESTED (see capsule tests)",
        "HELDOUT_TRANSFER": "BLOCKED:STILL_ONLY_TRANSFER (no animated multi-subject held-out film reviewed)",
    }
    return {"run_id": run_id, "evidence_origin": origin, "capabilities": v,
            "ready_for_15_plus_1": False,
            "ready_for_15_plus_1_blockers": ["source roles and sixth boundaries locked by the user", "authorized native source bytes + upload consent",
                                             "human native-detail review of a real canary", "real source→skill→payload causal chain",
                                             "source-first character redraw review"],
            "note": "statuses are independent; nothing is averaged into an overall 'ready'"}
