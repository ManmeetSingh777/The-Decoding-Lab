"""Integration-level red team against actual vme modules (no paid calls).

Run with PYTHONPATH=<live repo> python3 -m unittest discover -s <packet> -p test_archived_wiring.py -v
Unlike standalone reference_guards, these exercise imported production functions.
The archived copy plus corrected_modules is expected to pass these narrow cases.
They do NOT replace the required new S2→authoring→skill→render integration tests.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class ProductionWiringRedTeam(unittest.TestCase):
    def test_actual_source_analysis_system_messages_contain_p0_and_pass(self):
        from vme.loop.real import QA_SYSTEM, RATIONALE_SYSTEM, NATIVE_SYSTEM
        from vme.vision.protocol import P0, PROTOCOL_SHA
        for txt, pass_id in ((QA_SYSTEM, "P4"), (RATIONALE_SYSTEM, "P2"), (NATIVE_SYSTEM, "P5")):
            self.assertIn(P0[:80], txt)
            self.assertIn(PROTOCOL_SHA, txt)
            self.assertIn(f"pass={pass_id}", txt)

    def test_live_packet_id_changes_on_unchanged_version_changed_prompt(self):
        import vme.vision.runner as runner
        index = [{"pts": str(i), "frame_content_sha256": (str(i) * 64)} for i in range(3)]
        kw = dict(index=index, start=0, end_inclusive=2, film_sha="f" * 64,
                  pass_id="P1", cluster_id="C", model_version="MOCK", max_images=4)
        p1 = runner.plan_packets(**kw)[0].packet_id
        with patch.object(runner, "VISION_PROMPT_SHA", "artistic_instruction_changed_without_version_bump"):
            p2 = runner.plan_packets(**kw)[0].packet_id
        self.assertNotEqual(p1, p2)

    def _mock_render(self, *, ffprobe_ok: bool, motion_ok: bool, motion_expected: bool | None,
                     diagnostic: bool):
        from vme.render import renderer
        from vme.util import Blocked
        scene = {"width": 16, "height": 16, "fps": 30, "durationInFrames": 2,
                 "camera": {}, "layers": [], "events": []}
        if motion_expected is not None:
            scene["motion_contract"] = {"expected_independent_motion": motion_expected}
        gate = SimpleNamespace(authorize_render=lambda *a, **kw: None,
                               transition=lambda *a, **kw: None)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "remotion"
            (root / "node_modules" / "remotion").mkdir(parents=True)
            with patch.object(renderer, "REMOTION_DIR", root), \
                 patch.object(renderer, "require_tool", return_value="node"), \
                 patch.object(renderer.subprocess, "run", return_value=SimpleNamespace(returncode=0,
                                                                                      stderr="", stdout="")), \
                 patch.object(renderer, "ffprobe_verify", return_value={"ok": ffprobe_ok,
                                                                       "problems": ["MOCK_INVALID"]}), \
                 patch.object(renderer, "motion_evidence", return_value={"ok": motion_ok,
                                                                         "verdict": "STATIC"}), \
                 patch.object(renderer, "sha256_file", return_value="TEST_SHA"):
                return renderer.render_video(scene, {}, Path(tmp) / "clip.mp4", gate=gate,
                                             run_id="REAL-test",
                                             diagnostic_label="DIAGNOSTIC_NOT_APPROVED" if diagnostic else None)

    def test_actual_renderer_rejects_ffprobe_bad_even_diagnostic(self):
        from vme.util import Blocked
        with self.assertRaises(Blocked) as cm:
            self._mock_render(ffprobe_ok=False, motion_ok=True, motion_expected=True, diagnostic=True)
        self.assertEqual(cm.exception.code, "TECHNICAL_RENDER_FAILED")

    def test_actual_integrated_renderer_rejects_unobserved_motion(self):
        from vme.util import Blocked
        with self.assertRaises(Blocked) as cm:
            self._mock_render(ffprobe_ok=True, motion_ok=False, motion_expected=True, diagnostic=False)
        self.assertEqual(cm.exception.code, "TECHNICAL_MOTION_FAILED")

    def test_actual_integrated_renderer_requires_motion_contract(self):
        from vme.util import Blocked
        with self.assertRaises(Blocked) as cm:
            self._mock_render(ffprobe_ok=True, motion_ok=True, motion_expected=None, diagnostic=False)
        self.assertEqual(cm.exception.code, "MOTION_CONTRACT_MISSING")


if __name__ == "__main__":
    unittest.main(verbosity=2)
