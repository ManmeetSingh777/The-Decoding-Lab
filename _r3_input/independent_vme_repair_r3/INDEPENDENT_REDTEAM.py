"""Zero-dependency adversarial tests against a VME checkout.

Usage: PYTHONPATH=<path-to-repo> python INDEPENDENT_REDTEAM.py
Tests describe REQUIRED future behavior. Against the November 15 audit ZIP they
must FAIL, exposing unsafe acceptance. This is an independent diagnostic, not a
claim of production readiness or real vision quality.
"""
from __future__ import annotations

import unittest


class IndependentRedTeam(unittest.TestCase):
    def test_vague_per_frame_observation_never_validated(self):
        from vme.vision.contracts import validate_packet_response
        m = {"frame_id": "A:0", "source_sha": "A", "pts_time": 0.0, "image_sha": "abc"}
        o = {
            "frame_id": "A:0", "source_sha": "A", "pts_time": 0.0,
            "request_id": "r", "submitted_image_sha": "abc",
            "active_question_ids": [], "scene_and_world_state": "unknown",
            "actually_visible_actor_and_object_ids": [],
            "focal_whole_artwork_state": "nice beautiful premium artwork",
            "visible_design_relations": [],
            "character_face_limb_contact_state": [],
            "visible_layer_depth_attention_state": "unknown",
            "changed_since_prior_frame": [],
            "no_significant_change_reason": "unknown",
            "simultaneous_event_links": [],
            "camera_vs_actor_vs_drawing_state": "unknown",
            "material_finish_or_colour_change": [],
            "native_detail_followups": [], "source_fact_statements": [],
            "hypothesis_or_uncertainty": [], "confidence_limitations": [],
            "persistent_state_ids": ["actor_1"], "unexplained_phenomena": [],
        }
        r = {"frame_observations": [o], "packet_transition_graph": {"edges": []},
             "boundary_state": {"active_objects": [], "open_events": []}, "reconciled_events": []}
        v = validate_packet_response(r, [m], None, images_actually_sent=1)
        self.assertFalse(v["ok"], "Vague observations with zero design relations must not be VERIFIED")
        o["focal_whole_artwork_state"] = "The near figure overlaps the far background while both remain in the frame"
        v2 = validate_packet_response(r, [m], None, images_actually_sent=1)
        self.assertFalse(v2["ok"], "A fluent whole-frame sentence cannot replace typed source design facts")

    def test_structured_boundary_object_ids_are_reconciled(self):
        from vme.vision.contracts import validate_packet_response, FRAME_OBSERVATION_FIELDS
        m = {"frame_id": "A:0", "source_sha": "A", "pts_time": 0.0, "image_sha": "abc"}
        o = {f: [] for f in FRAME_OBSERVATION_FIELDS}
        o.update(frame_id="A:0", source_sha="A", pts_time=0.0, request_id="r",
                 submitted_image_sha="abc", focal_whole_artwork_state="A near head contour overlaps a far collar edge",
                 visible_design_relations=[{"relation": "The near head contour overlaps the far collar edge",
                                            "dimensions": ["CHARACTER_WHOLE_DESIGN"]}],
                 changed_since_prior_frame=[{"kind": "OBSERVED_DIFF", "what": "the collar overlap shifts"}],
                 persistent_state_ids=["actor_1"])
        r = {"frame_observations": [o], "packet_transition_graph": {"edges": []},
             "boundary_state": {"active_objects": [], "open_events": []}, "reconciled_events": []}
        prior = {"active_objects": [{"id": "actor_1", "identity": "same person", "drawing_state": "front"}],
                 "open_events": []}
        v = validate_packet_response(r, [m], prior, images_actually_sent=1)
        self.assertTrue(v["ok"], "A correctly carried structured actor must not crash or be treated as lost")

    def test_unrelated_branch_cannot_cover_specific_choice(self):
        from vme.style.coverage import _owner_for
        c = {"choice_id": "actor:face", "dimensions": ["CHARACTER_FACE_ACTING"],
             "conditions": {"view": "profile"}}
        d = {"decision_id": "D", "owned_choice_ids": ["actor:face"],
             "dimension_tags": ["CHARACTER_FACE_ACTING"],
             "branches": [{"when": {"action": "grip"}, "operation_node_ids": ["op"]}]}
        _, problem = _owner_for(c, [d], {"op": {}})
        self.assertEqual(problem, "MISSING_DECISION", "Unrelated branch predicates must not pass by vacuous truth")

    def test_model_cannot_self_authorize_unshown_witness(self):
        from vme.investigation.controller import NextQuestion, validate_answer
        q = NextQuestion(
            question_id="q", cluster_id="c", from_evidence_version="x", gap_id="g",
            missing_decision_id="D", missing_producing_operation="op.whole_scene",
            observed_contrast_with_witness_ids=["W-actually-sent"], exact_artistic_unknown="x",
            question_text="Test D?", planned_witness_or_input_ids=[],
            possible_answer_consequences_for_operation=[], route="S3_CONDITIONS",
            owner_stage="STYLE_CONDITIONS", reasoning_dimensions={}, uncovered_reasoning_dimensions=[],
        )
        a = {
            "answer_status": "INFERRED", "SOURCE_VISIBLE_FACTS": [{"relation": "The near form overlaps the far form",
                                                                "witness_ids": ["W-never-sent"]}],
            "answer_evidence_ids": ["W-never-sent"],
            "CONSTRUCTION_EXPLANATION": "The near shape occludes the far shape when moving",
            "ACTUAL_PRODUCING_OPERATION": {"operation_id": "op.whole_scene"},
            "WHERE_IT_ENTERS_COMPILED_REQUEST": {"operator": "op.whole_scene"},
            "IMPORTANT_LINKED_CHANGES": [], "WHY_THE_DECISION_MATTERS": "x",
            "WHEN_APPLICABLE": {}, "WHEN_NOT_APPLICABLE": ["z"], "REMAINING_UNKNOWN": ["a"],
        }
        v = validate_answer(q, a, {"op.whole_scene": {}})
        self.assertFalse(v["ok"], "A model-supplied witness id is not proof the image was actually shown")

    def test_disjoint_predicates_do_not_qualify_joint_required_conditions(self):
        from vme.investigation.controller import ActiveArtProblem, ProblemContext, locate_earliest_missing_handoff
        p = ActiveArtProblem(
            cluster_id="c", version=1, original_output_id_or_initial_reference_only="r",
            reference_full_frame_ids=["w"], affected_original_subject_classes=[],
            high_impact_visible_difference="x", whole_scene_consequence="x", connected_artistic_relations=[],
            current_explanation_and_support=[{"claim": "x", "witness_ids": ["w"]}],
            next_required_producer_decision_id="D", required_conditions={"view": "profile", "action": "grip"},
        )
        d = {"status": "EXECUTABLE_CANDIDATE", "branches": [
            {"when": {"view": "profile"}, "operation_node_ids": ["op"]},
            {"when": {"action": "grip"}, "operation_node_ids": ["op"]},
        ]}
        ctx = ProblemContext(witnesses={"w": {"witness_id": "w"}}, decisions={"D": d},
                             registered_operators={"op": {"kind": "whole_scene"}},
                             provider_capabilities=["whole_scene"])
        loc = locate_earliest_missing_handoff(p, ctx)
        self.assertEqual(loc["stage"], "STYLE_CONDITIONS",
                         "Different partial branches do not prove the requested combined condition")


if __name__ == "__main__":
    unittest.main(verbosity=2)
