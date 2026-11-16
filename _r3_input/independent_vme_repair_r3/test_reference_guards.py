"""Standalone adversarial cases, no third-party dependencies, no paid calls."""
import copy
import unittest

from reference_guards import (IntegrityStop, artifact_fingerprint, build_locked_control_plan, canonical_hash,
                              validate_character_art_study, validate_native_frame_coverage,
                              validate_original_animated_scene, validate_release_claim, validate_skill_ownership,
                              verify_submitted_witnesses)


SOURCE = "a" * 64
IMAGE = "b" * 64
W = "W1"
CONDITIONS = {"view": "three_quarter", "action": "grip"}
ACTION = "Draw contacted silhouette using approved state layer"
TEXT_REVIEW_SCOPE = {"source_sha256": SOURCE, "condition_sha": canonical_hash(CONDITIONS),
                     "action_sha": canonical_hash(ACTION), "status": "APPROVED"}
AUTH = {"text_only_transfer_reviews": {
    "HUMAN-REVIEW-1": {**TEXT_REVIEW_SCOPE, "skill_id": "S1"},
    "HUMAN-REVIEW-2": {**TEXT_REVIEW_SCOPE, "skill_id": "S2"}},
    "provider_reference_capabilities": {"positive_view": {"verified": True}},
    "source_upload_consents": {W: {"source_sha256": SOURCE,
                                   "image_bytes_sha256": IMAGE, "authorized": True}}}


def witnessed():
    return {"source_sha256": SOURCE, "target_witness_ids": [W], "submitted_images": [
        {"witness_id": W, "source_sha256": SOURCE, "image_bytes_sha256": IMAGE,
         "frame_index": 12, "pts": "12/30", "actual_submission": True}]}


def observation():
    return {"target_observations": [{"target_witness_id": W,
             "investigation_state": "ARTISTICALLY_EXAMINED",
             "whole_artwork": {"focal_design": "observed priority", "scene_organisation": "layer order",
                              "attention_relationship": "contrast focus", "temporal_continuity": "stable state"}}],
            "source_visible_facts": [{"claim_id": "C1", "witness_ids": [W], "status": "VISIBLE",
               "visual_relation": "The foreground shape overlaps the farther shape at the contact",
               "consequence": "Need layered alternate contact art"}]}


def skill():
    return {"skill_id": "S1", "status": "CANDIDATE", "source_sha256": SOURCE,
            "source_witness_ids": [W], "tested_consumer_operation_ids": ["image.actor_state"],
            "branches": [{"when": CONDITIONS, "operation_id": "image.actor_state",
                          "micro_specific_construction_action": ACTION,
                          "reference_policy": {"mode": "TEXT_ONLY_DEMONSTRATED",
                           "reviewed_source_to_text_transfer_test": "HUMAN-REVIEW-1"}}]}


def character():
    fields = ("whole_design", "outer_contour_and_taper", "negative_spaces",
              "visual_piece_junctions", "fills_edges_materials", "lighting_and_shadows",
              "view_and_pose_redraws", "contact_and_occlusion", "world_integration")
    return {"study_basis": "SOURCE_FIRST_DRAWN_ENTITY",
            "identity_across_drawings": ["same identity in two poses"],
            "contrasting_examples": ["character near/far"],
            **{f: {"state": "OBSERVED", "witness_ids": [W], "visible_relation": f"source-specific {f}",
                   "reconstruction_impact": "controls rendering"} for f in fields}}


def scene():
    kinds = ("ACTOR_DRAWING_STATE", "ACTOR_ACTING", "WORLD", "CAMERA", "ATTENTION", "AUDIO")
    return {"kind": "ORIGINAL_AUDIOVISUAL_FILM", "duration_frames": 90,
            "actors": [{"actor_id": "a1", "identity_sha256": "ID1", "approved_canonical_sha256": "CAN1",
                        "drawn_states": [{"pose_state": "grip", "asset_sha256": "STATE1"}]},
                       {"actor_id": "a2", "identity_sha256": "ID2", "approved_canonical_sha256": "CAN2",
                        "drawn_states": [{"pose_state": "react", "asset_sha256": "STATE2"}]}],
            "tracks": [{"kind": kind, "source_derived_skill_id": "SK" + kind,
                        "start_frame": 0, "end_frame": 89,
                        "interpolation_or_redraw_method": "EVIDENCED_DRAW_AND_TIMING"} for kind in kinds],
            "contacts": [{"source_derived_skill_id": "SKCONTACT", "owner_actor_id": "a1",
                          "other_actor_id": "a2", "world_anchor_or_prop_id": "object1",
                          "occlusion_and_grip_state_sha": "GRIPDRAW"}],
            "audio_program": {"source_timing_study_id": "AUD1", "approved_tracks": ["VOICE1"],
                              "mux_expected": True, "sync_validation_plan": "PTS check"},
            "render_gate": "FAIL_ON_FFPROBE_OR_FRAME_COUNT_OR_MUX_OR_SYNC"}


SKILLS = {"SKACTOR_DRAWING_STATE", "SKACTOR_ACTING", "SKWORLD", "SKCAMERA",
          "SKATTENTION", "SKAUDIO", "SKCONTACT"}


class RedTeamReferenceContract(unittest.TestCase):
    def blocked(self, code, call):
        with self.assertRaises(IntegrityStop) as cm:
            call()
        self.assertEqual(code, cm.exception.code)

    def test_valid_native_observation(self):
        validate_native_frame_coverage(witnessed(), observation())

    def test_model_cannot_authorize_invented_witness(self):
        x = observation()
        x["source_visible_facts"][0]["witness_ids"].append("NEVER_SENT")
        self.blocked("MODEL_SELF_AUTHORIZED_WITNESS", lambda: verify_submitted_witnesses(witnessed(), x))

    def test_witness_must_really_be_submitted(self):
        x = witnessed()
        x["submitted_images"][0]["actual_submission"] = False
        self.blocked("NOT_ACTUALLY_SUBMITTED", lambda: verify_submitted_witnesses(x, observation()))

    def test_witness_must_bind_to_correct_source(self):
        x = witnessed()
        x["submitted_images"][0]["source_sha256"] = "different"
        self.blocked("CROSS_SOURCE_WITNESS", lambda: verify_submitted_witnesses(x, observation()))

    def test_missing_or_duplicate_target_not_artistically_covered(self):
        x = observation()
        x["target_observations"].append(copy.deepcopy(x["target_observations"][0]))
        self.blocked("TARGET_FRAME_OBSERVATIONS_NOT_BIJECTIVE",
                     lambda: validate_native_frame_coverage(witnessed(), x))

    def test_empty_whole_picture_does_not_qualify(self):
        x = observation()
        x["target_observations"][0]["whole_artwork"]["focal_design"] = ""
        self.blocked("WHOLE_ARTWORK_NOT_OBSERVED",
                     lambda: validate_native_frame_coverage(witnessed(), x))

    def test_unknown_must_have_exact_reinspection(self):
        x = observation()
        x["target_observations"][0]["investigation_state"] = "NEEDS_NATIVE_CROP"
        self.blocked("UNKNOWN_WITHOUT_REINSPECTION_PLAN",
                     lambda: validate_native_frame_coverage(witnessed(), x))
        x["target_observations"][0]["exact_reinspection_request"] = "crop exact prop contact at source PTS"
        validate_native_frame_coverage(witnessed(), x)

    def test_source_first_character_complete(self):
        validate_character_art_study(character(), {W})

    def test_generic_skeleton_character_rejected(self):
        x = character()
        x["study_basis"] = "GENERATE_GENERIC_HUMAN_RIG"
        self.blocked("GENERIC_ANATOMY_TEMPLATE_FORBIDDEN", lambda: validate_character_art_study(x, {W}))

    def test_missing_artistic_shading_rejected(self):
        x = character()
        x["lighting_and_shadows"] = {}
        self.blocked("CHARACTER_ART_WITHOUT_WITNESS", lambda: validate_character_art_study(x, {W}))

    def test_joint_condition_branch(self):
        validate_skill_ownership(skill(), CONDITIONS, {W}, AUTH)

    def test_two_partial_branches_cannot_fake_joint(self):
        x = skill()
        b = x["branches"][0]
        x["branches"] = [{**b, "when": {"view": "three_quarter"}},
                          {**b, "when": {"action": "grip"}}]
        self.blocked("NO_UNAMBIGUOUS_JOINT_CONDITIONAL_BRANCH",
                     lambda: validate_skill_ownership(x, CONDITIONS, {W}, AUTH))

    def test_unknown_reference_policy_rejected(self):
        x = skill()
        x["branches"][0]["reference_policy"] = {}
        self.blocked("REFERENCE_POLICY_UNKNOWN", lambda: validate_skill_ownership(x, CONDITIONS, {W}, AUTH))

    def test_text_only_needs_proof(self):
        x = skill()
        x["branches"][0]["reference_policy"].pop("reviewed_source_to_text_transfer_test")
        self.blocked("TEXT_ONLY_NOT_PROVEN", lambda: validate_skill_ownership(x, CONDITIONS, {W}, AUTH))

    def test_required_reference_needs_upload_consent(self):
        x = skill()
        x["branches"][0]["reference_policy"] = {"mode": "REQUIRED", "reference_roles": [
             {"role": "positive_view", "witness_id": W, "image_bytes_sha256": IMAGE}]}
        self.blocked("REQUIRED_REF_NO_CONSENT", lambda: validate_skill_ownership(x, CONDITIONS, {W}))

    def test_required_reference_provider_must_support(self):
        x = skill()
        x["branches"][0]["reference_policy"] = {"mode": "REQUIRED", "reference_roles": [
             {"role": "positive_view", "witness_id": W, "image_bytes_sha256": IMAGE}]}
        auth = {**AUTH, "provider_reference_capabilities": {}}
        self.blocked("REQUIRED_REF_PROVIDER_UNVERIFIED",
                     lambda: validate_skill_ownership(x, CONDITIONS, {W}, auth))

    def test_model_self_approval_is_not_authority(self):
        x = skill()
        x["branches"][0]["reference_policy"]["model_claims_reviewed"] = True
        self.blocked("TEXT_ONLY_NOT_PROVEN", lambda: validate_skill_ownership(x, CONDITIONS, {W}))

    def test_stale_text_only_review_does_not_authorize_new_art_action(self):
        x = skill()
        x["branches"][0]["micro_specific_construction_action"] = "Unreviewed new generic tube-arm action"
        self.blocked("TEXT_ONLY_NOT_PROVEN", lambda: validate_skill_ownership(x, CONDITIONS, {W}, AUTH))

    def test_required_reference_with_trusted_external_consent(self):
        x = skill()
        x["branches"][0]["reference_policy"] = {"mode": "REQUIRED", "reference_roles": [
            {"role": "positive_view", "witness_id": W, "image_bytes_sha256": IMAGE}]}
        validate_skill_ownership(x, CONDITIONS, {W}, AUTH)

    def test_qualified_needs_independent_artistic_proofs(self):
        x = skill()
        x["status"] = "QUALIFIED"
        self.blocked("SKILL_NOT_ARTISTICALLY_QUALIFIED",
                     lambda: validate_skill_ownership(x, CONDITIONS, {W}, AUTH))

    def test_all_typed_output_consumers_must_be_owned(self):
        s = skill()
        out = {"required_operation_ids": ["image.actor_state", "motion.contact"],
               "required_kinds": ["IMAGE", "MOTION"],
               "operation_kinds": {"image.actor_state": "IMAGE", "motion.contact": "MOTION"}}
        self.blocked("UNCONTROLLED_OR_EXTRA_PRODUCTION_OPERATIONS",
                     lambda: build_locked_control_plan([s], CONDITIONS, {W}, out, AUTH))
        s2 = skill()
        s2["skill_id"] = "S2"
        s2["tested_consumer_operation_ids"] = ["motion.contact"]
        s2["branches"][0]["operation_id"] = "motion.contact"
        s2["branches"][0]["reference_policy"]["reviewed_source_to_text_transfer_test"] = "HUMAN-REVIEW-2"
        plan = build_locked_control_plan([s, s2], CONDITIONS, {W}, out, AUTH)
        self.assertEqual(set(plan["operations"]), {"image.actor_state", "motion.contact"})

    def test_two_skills_cannot_own_same_operation(self):
        a = skill()
        b = skill()
        b["skill_id"] = "S2"
        b["branches"][0]["reference_policy"]["reviewed_source_to_text_transfer_test"] = "HUMAN-REVIEW-2"
        out = {"required_operation_ids": ["image.actor_state"],
               "required_kinds": ["IMAGE"], "operation_kinds": {"image.actor_state": "IMAGE"}}
        self.blocked("CONFLICTING_OPERATION_OWNERS",
                     lambda: build_locked_control_plan([a, b], CONDITIONS, {W}, out, AUTH))

    def test_multi_actor_scene_has_distinct_canonicals(self):
        validate_original_animated_scene(scene(), SKILLS)
        x = scene()
        x["actors"][1]["actor_id"] = "a1"
        self.blocked("ACTOR_IDENTITY_COLLISION", lambda: validate_original_animated_scene(x, SKILLS))

    def test_generic_linear_motion_cannot_masquerade_as_learned(self):
        x = scene()
        x["tracks"][1]["interpolation_or_redraw_method"] = "DEFAULT_LINEAR"
        self.blocked("UNCONTROLLED_MOTION_METHOD", lambda: validate_original_animated_scene(x, SKILLS))

    def test_unowned_camera_track_rejected(self):
        x = scene()
        self.blocked("UNLEARNED_OR_UNOWNED_SCENE_TRACK",
                     lambda: validate_original_animated_scene(x, SKILLS - {"SKCAMERA"}))

    def test_missing_audio_program_rejected(self):
        x = scene()
        x["audio_program"] = {}
        self.blocked("AUDIO_PROGRAM_NOT_SOURCE_GROUNDED",
                     lambda: validate_original_animated_scene(x, SKILLS))

    def test_failed_ffprobe_must_block_av_claim(self):
        x = scene()
        x["render_gate"] = "LOG_WARNING_ONLY"
        self.blocked("RENDER_TECHNICAL_FAILURE_NOT_FATAL",
                     lambda: validate_original_animated_scene(x, SKILLS))

    def test_prompt_content_change_invalidates_even_without_version_bump(self):
        args = dict(protocol_text="P0+P4 version=1", parser_contract={"schema": 1},
                    selection={"scene": 1}, source_manifest={"frames": [1]},
                    image_transform={"size": "native"}, provider_profile={"model": "fake"},
                    question={"q": 1}, prior_boundary={"open": []})
        original = artifact_fingerprint(**args)
        args["protocol_text"] += " VERY IMPORTANT NEW INSTRUCTION"
        self.assertNotEqual(original, artifact_fingerprint(**args))

    def test_video_analysis_ready_needs_real_source_calibration(self):
        report = {"offline_engineering": {"full_repo_test_result": "PASS",
                  "clean_extract_test_result": "PASS", "guard_mutation_result": "PASS"},
                  "ready_for_15_plus_1": True, "source_selection": {
                      "all_roles_and_boundaries_locked": True, "authorized_native_bytes_available": True},
                  "real_artistic_canary": {}}
        self.blocked("NO_REAL_SOURCE_ART_CALIBRATION", lambda: validate_release_claim(report))
        report["real_artistic_canary"] = {"human_reviewed_native_detail": True,
                "source_to_skill_to_payload_causal_chain": True,
                "source_character_redraw_review": True, "known_unknowns_explicit": True}
        validate_release_claim(report)


if __name__ == "__main__":
    unittest.main()
