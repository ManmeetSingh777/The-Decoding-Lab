"""A/B, ablation, causal mutation, freeze/holdout integrity and transfer (01 §9, A12/A13/A15–A17, A36, B17/B18, B32, C29, C32).

Causality is structural at offline stage: a changed selected decision MUST change the
provider-visible request; a non-selected prose change MUST NOT. Visual improvement needs
real outputs and review (ART phase, BLOCKED offline).
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from ..util import Blocked, digest, now_iso, read_json, atomic_write_json
from ..compiler.compiler import StyleProgramCompiler, payload_diff
from ..skills.skill import skill_hash

POOLS = ("comparison_anchor", "rotating_development", "unseen_transfer")


def causal_mutation_test(skill_folder: str | Path, brief: dict, caps: dict, *, recipe_id: str, node_id: str,
                         mutate: Callable[[Path], None], label: str, identity_assets: dict | None = None) -> dict:
    """Compile → mutate a copy of the skill → recompile; report the exact payload difference."""
    c = StyleProgramCompiler()
    h0 = skill_hash(skill_folder)
    before = c.compile(brief, skill_folder, pinned_skill_hash=h0, recipe_id=recipe_id, node_id=node_id, caps=caps,
                       identity_assets=identity_assets)
    tmp = Path(str(skill_folder) + f"__mut_{digest(label)[:8]}")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(skill_folder, tmp)
    mutate(tmp)
    h1 = skill_hash(tmp)
    try:
        after = c.compile(brief, tmp, pinned_skill_hash=h1, recipe_id=recipe_id, node_id=node_id, caps=caps,
                          identity_assets=identity_assets)
        after_payload, blocked = after.logical_payload, None
    except Blocked as b:
        after_payload, blocked = None, {"code": b.code, "detail": b.detail, "ticket": b.data.get("ticket")}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    changed = blocked is not None or after_payload != before.logical_payload
    return {"label": label, "skill_hash_before": h0, "skill_hash_after": h1, "skill_hash_changed": h0 != h1,
            "payload_before": before.logical_payload["positivePrompt"], "payload_after": None if after_payload is None else after_payload["positivePrompt"],
            "diff": None if after_payload is None else payload_diff(before.logical_payload, after_payload),
            "blocked_after": blocked, "request_changed_or_blocked": changed, "at": now_iso()}


def assert_causal(result: dict, *, expect_change: bool) -> None:
    if expect_change and not result["request_changed_or_blocked"]:
        raise Blocked("CAUSAL_EFFECT_MISSING", f"{result['label']}: selected skill change did not alter the request — disconnected consumer")
    if not expect_change and result["request_changed_or_blocked"]:
        raise Blocked("NONSELECTED_CHANGE_ALTERED_REQUEST", result["label"])


def ab_confound_check(baseline: dict, intervention: dict) -> dict:
    """A15 / 03 negative: different provider versions/briefs/seeds → CONFOUNDED."""
    keys = ("brief_hash", "model", "provider_version", "seed", "width", "height")
    diffs = {k: (baseline.get(k), intervention.get(k)) for k in keys if baseline.get(k) != intervention.get(k)}
    return {"status": "CONFOUNDED" if diffs else "CONTROLLED", "differences": diffs}


class HoldoutRegistry:
    """Unseen-transfer briefs are sealed until skill freeze; exposure or post-test patches contaminate (A17)."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _d(self) -> dict:
        return read_json(self.path) if self.path.exists() else {"holdouts": {}}

    def seal(self, brief: dict) -> str:
        d = self._d()
        hid = brief["brief_id"]
        d["holdouts"][hid] = {"brief_sha": digest(brief), "sealed_at": now_iso(), "exposures": [], "frozen_skill_hash": None,
                              "status": "SEALED", "brief": brief}
        atomic_write_json(self.path, d)
        return hid

    def access(self, hid: str, *, by_role: str, skill_frozen_hash: str | None) -> dict:
        d = self._d()
        h = d["holdouts"][hid]
        h["exposures"].append({"by": by_role, "at": now_iso(), "frozen": skill_frozen_hash})
        if by_role == "skill_builder" or skill_frozen_hash is None:
            h["status"] = "CONTAMINATED"
        atomic_write_json(self.path, d)
        if h["status"] == "CONTAMINATED":
            raise Blocked("HOLDOUT_CONTAMINATED", "exposed before freeze or to the skill builder: generate a new challenge")
        h["frozen_skill_hash"] = skill_frozen_hash
        atomic_write_json(self.path, d)
        return h["brief"]

    def record_result(self, hid: str, *, skill_hash_used: str) -> dict:
        d = self._d()
        h = d["holdouts"][hid]
        if h["frozen_skill_hash"] != skill_hash_used:
            h["status"] = "CONTAMINATED"
            atomic_write_json(self.path, d)
            raise Blocked("SKILL_PATCHED_AFTER_TEST", "recipe changed after seeing the challenge; becomes training data")
        h["status"] = "TRANSFER_RUN_RECORDED_AWAITING_REVIEW"
        atomic_write_json(self.path, d)
        return h


def transfer_status(review_verdicts: list[str], frozen: bool, distinct_subjects: int) -> str:
    if not frozen:
        return "NOT_TRANSFERABLE_UNFROZEN"
    if distinct_subjects < 2:
        return "TRANSFER_PENDING_NEEDS_DISTINCT_SUBJECTS"
    if not review_verdicts:
        return "TRANSFER_PENDING_AWAITING_REVIEW"
    return "TRANSFER_QUALIFIED" if all(v == "APPROVED_IMPROVEMENT" for v in review_verdicts) else "IMPROVING_NOT_TRANSFERABLE"
