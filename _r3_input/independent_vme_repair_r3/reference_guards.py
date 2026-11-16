"""VME R3 independent, dependency-free fail-closed reference contracts.

These guards are an EXECUTABLE REFERENCE for the live vme adapter, not a claim
that copying this file alone integrates it into the existing engine.
All successes are local structural/causal-authority checks, not pixel truth.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter


class IntegrityStop(ValueError):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        super().__init__(f"{code}: {detail}")


def insist(ok: bool, code: str, detail: str = "") -> None:
    if not ok:
        raise IntegrityStop(code, detail)


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def artifact_fingerprint(*, protocol_text: str, parser_contract: object,
                         selection: object, source_manifest: object,
                         image_transform: object, provider_profile: object,
                         question: object, prior_boundary: object) -> str:
    """Exact semantic inputs; changing text with an unchanged label invalidates."""
    insist(bool(protocol_text.strip()), "EMPTY_PROTOCOL")
    return canonical_hash({"protocol_text": protocol_text, "parser_contract": parser_contract,
                           "selection": selection, "source_manifest": source_manifest,
                           "image_transform": image_transform, "provider_profile": provider_profile,
                           "question": question, "prior_boundary": prior_boundary})


def verify_submitted_witnesses(request: dict, response: dict) -> set[str]:
    """Only locally submitted, content-addressed source bytes authorize citations.

    ``request`` is written by the sender, NOT copied from a model response.
    A provider cannot certify that it visually understood pixels via echoing IDs.
    """
    sent = request.get("submitted_images")
    insist(isinstance(sent, list) and bool(sent), "NO_ACTUAL_SUBMISSION_MANIFEST")
    allowed: set[str] = set()
    for img in sent:
        insist(isinstance(img, dict), "BAD_IMAGE_MANIFEST")
        wid = img.get("witness_id")
        insist(isinstance(wid, str) and wid and wid not in allowed, "DUPLICATE_OR_MISSING_WITNESS")
        insist(img.get("source_sha256") == request.get("source_sha256"), "CROSS_SOURCE_WITNESS", wid)
        insist(isinstance(img.get("image_bytes_sha256"), str)
               and len(img["image_bytes_sha256"]) == 64, "UNHASHED_IMAGE_BYTES", wid)
        insist(img.get("frame_index") is not None and img.get("pts") is not None,
               "WITNESS_WITHOUT_TEMPORAL_ID", wid)
        insist(img.get("actual_submission") is True, "NOT_ACTUALLY_SUBMITTED", wid)
        allowed.add(wid)
    claims = response.get("source_visible_facts", [])
    insist(isinstance(claims, list), "BAD_FACT_LIST")
    for claim in claims:
        ids = claim.get("witness_ids") or []
        insist(bool(ids), "UNCITED_ARTISTIC_CLAIM", str(claim.get("claim_id")))
        insist(set(ids).issubset(allowed), "MODEL_SELF_AUTHORIZED_WITNESS", str(set(ids) - allowed))
        insist(claim.get("status") in ("VISIBLE", "INFERRED", "UNCERTAIN"), "FACT_STATUS_MISSING")
        insist(bool(str(claim.get("visual_relation", "")).strip()), "EMPTY_VISUAL_RELATION")
        insist(bool(str(claim.get("consequence", "")).strip()), "NO_PRODUCING_CONSEQUENCE")
    return allowed


def validate_native_frame_coverage(request: dict, response: dict) -> None:
    """No frame may be counted as artistically examined just for being hashed."""
    ids = verify_submitted_witnesses(request, response)
    targets = set(request.get("target_witness_ids") or [])
    insist(bool(targets) and targets.issubset(ids), "TARGET_NOT_SENT")
    observations = response.get("target_observations") or []
    by_id = Counter(x.get("target_witness_id") for x in observations)
    insist(set(by_id) == targets and all(v == 1 for v in by_id.values()),
           "TARGET_FRAME_OBSERVATIONS_NOT_BIJECTIVE")
    for obs in observations:
        wid = obs["target_witness_id"]
        status = obs.get("investigation_state")
        insist(status in ("ARTISTICALLY_EXAMINED", "NEEDS_NATIVE_CROP", "UNKNOWN"),
               "ILLEGAL_FRAME_INVESTIGATION_STATE", wid)
        if status == "ARTISTICALLY_EXAMINED":
            whole = obs.get("whole_artwork") or {}
            insist(all(whole.get(k) for k in ("focal_design", "scene_organisation",
                                                "attention_relationship", "temporal_continuity")),
                   "WHOLE_ARTWORK_NOT_OBSERVED", wid)
            rels = [x for x in response.get("source_visible_facts", [])
                    if wid in (x.get("witness_ids") or []) and x.get("status") == "VISIBLE"]
            insist(bool(rels), "ARTISTICALLY_EXAMINED_WITHOUT_VISIBLE_FACT", wid)
        else:
            insist(bool(obs.get("exact_reinspection_request")), "UNKNOWN_WITHOUT_REINSPECTION_PLAN", wid)


def validate_character_art_study(dossier: dict, authorized: set[str]) -> None:
    """Study how the character is DRAWN before imposing generic anatomy."""
    insist(dossier.get("study_basis") == "SOURCE_FIRST_DRAWN_ENTITY", "GENERIC_ANATOMY_TEMPLATE_FORBIDDEN")
    for field in ("whole_design", "outer_contour_and_taper", "negative_spaces",
                  "visual_piece_junctions", "fills_edges_materials", "lighting_and_shadows",
                  "view_and_pose_redraws", "contact_and_occlusion", "world_integration"):
        part = dossier.get(field)
        insist(isinstance(part, dict), "MISSING_CHARACTER_ART_RELATION", field)
        ids = set(part.get("witness_ids") or [])
        insist(bool(ids) and ids.issubset(authorized), "CHARACTER_ART_WITHOUT_WITNESS", field)
        insist(part.get("state") in ("OBSERVED", "UNKNOWN"), "CHARACTER_ART_STATE_UNKNOWN", field)
        if part["state"] == "OBSERVED":
            insist(bool(part.get("visible_relation")) and bool(part.get("reconstruction_impact")),
                   "CHARACTER_ART_NOT_CONSTRUCTION_GRADE", field)
        else:
            insist(bool(part.get("precise_next_witness")), "CHARACTER_ART_UNKNOWN_WITHOUT_TARGET", field)
    insist(bool(dossier.get("identity_across_drawings")), "NO_MULTI_STATE_IDENTITY_PROOF")
    insist(bool(dossier.get("contrasting_examples")), "NO_CHARACTER_CONTRAST")


def _branch_applies(when: dict, request_conditions: dict) -> bool:
    return bool(when) and all(k in request_conditions and request_conditions[k] == v
                              for k, v in when.items())


def validate_skill_ownership(skill: dict, request_conditions: dict, authorized: set[str],
                             trusted_authority: dict | None = None) -> dict:
    """No disjoint-branch coverage or silent reference-choice default.

    An invariant may be broad only if the skill explicitly provides independently
    reviewed witnesses and a test for each axis across its declared domain.
    """
    # A model answer MUST NOT supply its own approvals. This registry must be
    # populated by the locally trusted witness/reviewer/consent store.
    authority = trusted_authority or {}
    insist(skill.get("status") in ("CANDIDATE", "QUALIFIED"), "UNPROMOTABLE_SKILL")
    insist(bool(skill.get("source_sha256")) and skill.get("source_witness_ids"), "UNSOURCED_SKILL")
    insist(set(skill["source_witness_ids"]).issubset(authorized), "SKILL_CITES_UNSEEN_SOURCE")
    insist(bool(skill.get("tested_consumer_operation_ids")), "SKILL_HAS_NO_REAL_CONSUMER")
    branches = skill.get("branches") or []
    selected = [b for b in branches if _branch_applies(b.get("when") or {}, request_conditions)]
    # A single branch must own the FULL condition unless independently proven invariants cover omitted axes.
    full = [b for b in selected if set(request_conditions).issubset(b.get("when", {}))]
    if not full:
        proven = skill.get("independent_invariance_proofs") or {}
        for b in selected:
            omitted = set(request_conditions) - set(b.get("when", {}))
            if omitted and all(proven.get(axis, {}).get("review_id") in
                               authority.get("invariance_approvals", set())
                               and set(proven[axis].get("witness_ids") or []).issubset(authorized)
                               and len(proven[axis].get("witness_ids") or []) >= 2
                               for axis in omitted):
                full.append(b)
    insist(len(full) == 1, "NO_UNAMBIGUOUS_JOINT_CONDITIONAL_BRANCH")
    b = full[0]
    insist(b.get("operation_id") in skill["tested_consumer_operation_ids"], "BRANCH_HAS_NO_TESTED_CONSUMER")
    insist(bool(b.get("micro_specific_construction_action")), "VAGUE_OR_EMPTY_BRANCH_ACTION")
    policy = b.get("reference_policy")
    insist(isinstance(policy, dict), "REFERENCE_REQUIREMENT_NOT_DECIDED")
    insist(policy.get("mode") in ("REQUIRED", "TEXT_ONLY_DEMONSTRATED", "NOT_APPLICABLE"),
           "REFERENCE_POLICY_UNKNOWN")
    if policy["mode"] == "REQUIRED":
        refs = policy.get("reference_roles") or []
        insist(bool(refs), "REQUIRED_REF_WITHOUT_ROLES")
        for role in refs:
            insist(role.get("witness_id") in authorized, "REQUIRED_REF_UNSEEN")
            insist(bool(role.get("image_bytes_sha256")), "REQUIRED_REF_NO_BYTES")
            consent = authority.get("source_upload_consents", {}).get(role.get("witness_id")) or {}
            insist(consent.get("source_sha256") == skill["source_sha256"]
                   and consent.get("image_bytes_sha256") == role["image_bytes_sha256"]
                   and consent.get("authorized") is True, "REQUIRED_REF_NO_CONSENT")
            verified = authority.get("provider_reference_capabilities", {}).get(role.get("role")) or {}
            insist(verified.get("verified") is True, "REQUIRED_REF_PROVIDER_UNVERIFIED")
    if policy["mode"] == "TEXT_ONLY_DEMONSTRATED":
        review_id = policy.get("reviewed_source_to_text_transfer_test")
        proof = authority.get("text_only_transfer_reviews", {}).get(review_id) or {}
        insist(proof.get("skill_id") == skill["skill_id"]
               and proof.get("source_sha256") == skill["source_sha256"]
               and proof.get("condition_sha") == canonical_hash(b["when"])
               and proof.get("action_sha") == canonical_hash(b["micro_specific_construction_action"])
               and proof.get("status") == "APPROVED", "TEXT_ONLY_NOT_PROVEN")
    if policy["mode"] == "NOT_APPLICABLE":
        insist(bool(policy.get("source_grounded_reason")), "NOT_APPLICABLE_UNJUSTIFIED")
    if skill["status"] == "QUALIFIED":
        proofs = authority.get("qualification_reviews", {}).get(skill["skill_id"]) or {}
        insist(proofs.get("candidate_sha") == canonical_hash({"id": skill["skill_id"],
               "source": skill["source_sha256"], "branches": skill["branches"]})
               and all(proofs.get(k) == "APPROVED" for k in ("source_art_review", "original_asset_review",
                                                       "local_ablation", "cross_subject_transfer")),
               "SKILL_NOT_ARTISTICALLY_QUALIFIED")
    return b


def build_locked_control_plan(skills: list[dict], conditions: dict,
                              authorized: set[str], output_contract: dict,
                              trusted_authority: dict | None = None) -> dict:
    """One owner per operative choice. Image text is only ONE of several consumers."""
    insist(bool(conditions), "NO_PRODUCTION_CONDITIONS")
    expected = set(output_contract.get("required_operation_ids") or [])
    insist(bool(expected), "EMPTY_OUTPUT_OPERATION_CONTRACT")
    plan: dict[str, dict] = {}
    for skill in skills:
        branch = validate_skill_ownership(skill, conditions, authorized, trusted_authority)
        op = branch["operation_id"]
        insist(op not in plan, "CONFLICTING_OPERATION_OWNERS", op)
        plan[op] = {"owner_skill_id": skill["skill_id"], "skill_sha": canonical_hash(skill),
                    "action": branch["micro_specific_construction_action"],
                    "reference_policy": branch["reference_policy"], "conditions": conditions,
                    "witness_ids": skill["source_witness_ids"]}
    insist(set(plan) == expected, "UNCONTROLLED_OR_EXTRA_PRODUCTION_OPERATIONS",
           f"missing={expected - set(plan)} unexpected={set(plan) - expected}")
    required_kinds = set(output_contract.get("required_kinds") or [])
    kind_by_op = output_contract.get("operation_kinds") or {}
    insist({kind_by_op.get(op) for op in plan} == required_kinds,
           "OPERATION_KIND_UNCONTROLLED")
    return {"status": "LOCKED", "condition_sha": canonical_hash(conditions),
            "operations": plan, "output_contract_sha": canonical_hash(output_contract)}


def validate_original_animated_scene(scene: dict, proven_skill_ids: set[str]) -> None:
    """Original audiovisual scene must have independently owned ACTING, not sprite drift.

    This enforces the GRAPH structure; separate real render and human reviews
    must establish artistic results. Diagnostic-only silent clips use a different
    explicit contract and cannot satisfy this audiovisual one.
    """
    insist(scene.get("kind") == "ORIGINAL_AUDIOVISUAL_FILM", "NOT_FULL_AUDIOVISUAL_PRODUCTION")
    duration = scene.get("duration_frames")
    insist(isinstance(duration, int) and duration > 0, "INVALID_FILM_DURATION")
    actors = scene.get("actors") or []
    identities = [a.get("actor_id") for a in actors]
    insist(bool(actors) and len(set(identities)) == len(identities) and all(identities),
           "ACTOR_IDENTITY_COLLISION")
    actor_set = set(identities)
    for actor in actors:
        insist(actor.get("identity_sha256") and actor.get("approved_canonical_sha256"),
               "ACTOR_WITHOUT_INDEPENDENT_CANONICAL", str(actor.get("actor_id")))
        states = actor.get("drawn_states") or []
        insist(bool(states) and all(s.get("asset_sha256") and s.get("pose_state") for s in states),
               "UNVERIFIED_CHARACTER_DRAWING_STATES", str(actor.get("actor_id")))
    tracks = scene.get("tracks") or []
    required = {"ACTOR_DRAWING_STATE", "ACTOR_ACTING", "WORLD", "CAMERA", "ATTENTION", "AUDIO"}
    kinds = {t.get("kind") for t in tracks}
    insist(required.issubset(kinds), "MISSING_MOTION_OR_AV_GRAMMAR", str(required - kinds))
    for track in tracks:
        insist(track.get("source_derived_skill_id") in proven_skill_ids,
               "UNLEARNED_OR_UNOWNED_SCENE_TRACK", str(track.get("kind")))
        insist(track.get("interpolation_or_redraw_method") not in (None, "DEFAULT_LINEAR", "WHOLE_STATE_SWAP_ONLY"),
               "UNCONTROLLED_MOTION_METHOD", str(track.get("kind")))
        insist(isinstance(track.get("start_frame"), int) and isinstance(track.get("end_frame"), int)
               and 0 <= track["start_frame"] <= track["end_frame"] < duration,
               "TRACK_OUTSIDE_SCENE_TIMEBASE")
        if track.get("actor_id") is not None:
            insist(track["actor_id"] in actor_set, "TRACK_FOR_UNKNOWN_ACTOR")
    for contact in scene.get("contacts") or []:
        insist(contact.get("source_derived_skill_id") in proven_skill_ids, "UNOWNED_CONTACT")
        insist(contact.get("owner_actor_id") in actor_set, "CONTACT_OWNER_MISSING")
        other = contact.get("other_actor_id")
        insist(other is None or other in actor_set, "CONTACT_PARTNER_MISSING")
        insist(bool(contact.get("world_anchor_or_prop_id")) and bool(contact.get("occlusion_and_grip_state_sha")),
               "CONTACT_WITHOUT_DRAWING_AND_OCCLUSION_PROOF")
    audio = scene.get("audio_program") or {}
    insist(bool(audio.get("source_timing_study_id")) and bool(audio.get("approved_tracks")),
           "AUDIO_PROGRAM_NOT_SOURCE_GROUNDED")
    insist(audio.get("mux_expected") is True and audio.get("sync_validation_plan"),
           "AUDIO_NOT_MUXED_OR_VALIDATED")
    insist(scene.get("render_gate") == "FAIL_ON_FFPROBE_OR_FRAME_COUNT_OR_MUX_OR_SYNC",
           "RENDER_TECHNICAL_FAILURE_NOT_FATAL")


def validate_release_claim(report: dict) -> None:
    """Keep local engineering passes separate from artistic/AV source truth."""
    offline = report.get("offline_engineering") or {}
    insist(offline.get("full_repo_test_result") == "PASS", "NO_FINAL_REPO_GREEN")
    insist(offline.get("clean_extract_test_result") == "PASS", "NO_FINAL_CLEAN_REPLAY")
    insist(offline.get("guard_mutation_result") == "PASS", "NO_MUTATION_PROOF")
    if report.get("ready_for_15_plus_1") is True:
        art = report.get("real_artistic_canary") or {}
        sources = report.get("source_selection") or {}
        insist(sources.get("all_roles_and_boundaries_locked") is True, "SOURCE_SELECTION_UNLOCKED")
        insist(sources.get("authorized_native_bytes_available") is True, "SOURCE_NATIVE_BYTES_ABSENT")
        insist(art.get("human_reviewed_native_detail") is True, "NO_REAL_SOURCE_ART_CALIBRATION")
        insist(art.get("source_to_skill_to_payload_causal_chain") is True,
               "NO_REAL_CAUSAL_ART_CHAIN")
        insist(art.get("source_character_redraw_review") is True, "NO_SOURCE_FIRST_CHARACTER_PROOF")
        insist(art.get("known_unknowns_explicit") is True, "UNKNOWN_SCOPE_UNTRACKED")
