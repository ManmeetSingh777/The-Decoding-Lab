"""`vme.skills.runtime:execute` — the skill entrypoint named in every skill's scripts/ENTRYPOINT.json.

Runs the skill's provider nodes through the ONE compile → gateway path. It never writes prompt text.
"""
from __future__ import annotations

from pathlib import Path

from ..compiler.compiler import StyleProgramCompiler
from ..skills.skill import load_skill


def execute(skill_folder: str | Path, brief: dict, *, gateway, caps: dict, node_ids: list[str], pinned_skill_hash: str,
            recipe_id: str = "main", identity_assets: dict | None = None, slot_overrides: dict | None = None,
            store=None, task_category: str = "image_generation", actor_scope: dict | None = None) -> dict:
    """actor_scope = {"actor_id": X, "other_actor_ids": [...]}: a per-actor job (R3 F12). Decisions owned ONLY by other actors'
    choices are not this actor's; every decision owning one of X's choices (or a shared camera/world choice) stays required."""
    sk = load_skill(skill_folder)
    if sk["skill_hash"] != pinned_skill_hash:
        from ..util import Blocked
        raise Blocked("SKILL_NOT_PINNED")
    c = StyleProgramCompiler()
    out = {}
    for nid in node_ids:
        b = dict(brief)
        if slot_overrides and nid in slot_overrides:
            b["slots"] = {**brief["slots"], **slot_overrides[nid]}
        job = c.compile(b, skill_folder, pinned_skill_hash=pinned_skill_hash, recipe_id=recipe_id, node_id=nid, caps=caps,
                        identity_assets=identity_assets, actor_scope=actor_scope)
        if store is not None:
            store.put("CompiledImageJob", job.job_id, {"job_id": job.job_id, "node_id": nid,
                                                       "payload": {k: v for k, v in job.logical_payload.items() if k != "inputs"},
                                                       "ref_shas": [r[1] for r in job.reference_images], "trace": job.trace})
        r = gateway.submit(job, task_category=task_category)
        out[nid] = {"job_id": job.job_id, "image": r["outputs"][0]["path"], "sha": r["outputs"][0]["sha256"], "result": r,
                    "clause_ids": job.trace["clause_ids"], "selected_decisions": job.trace["selected_decisions"],
                    "reference_shas": [x[1] for x in job.reference_images]}
    return out
