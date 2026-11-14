"""Versioned skill folders: load, hash, freeze (with Interface I provenance gate) and validate (C13, B15, B16).

Authoritative (hashed) artefacts: manifest.json, decisions.json, prompt_templates/*.json,
references/manifest.json, recipes/*.json. Non-authoritative: SKILL.md, notes/*.md — editing
them can never change compiled production (B18, ADD25-P04).
"""
from __future__ import annotations

import json
from pathlib import Path

from ..util import Blocked, atomic_write_json, digest, now_iso, read_json, sha256_file
from ..style.provenance import interface_one_gate
from .operators import OPERATORS

AUTHORITATIVE = ("manifest.json", "decisions.json", "references/manifest.json")
COMPILABLE_STATUSES = ("CANDIDATE_EXPERIMENT", "FROZEN")
CLAIM_STATES = ("OBSERVATION", "METHOD_CANDIDATE", "EXECUTABLE", "IMPROVING", "TRANSFER_QUALIFIED", "RESEARCH_ONLY",
                "SYNTHETIC_FIXTURE_NOT_LEARNED")


def _authoritative_files(folder: Path) -> list[Path]:
    files = [folder / f for f in AUTHORITATIVE if (folder / f).exists()]
    files += sorted((folder / "prompt_templates").glob("*.json")) if (folder / "prompt_templates").is_dir() else []
    files += sorted((folder / "recipes").glob("*.json")) if (folder / "recipes").is_dir() else []
    return files


def skill_hash(folder: str | Path) -> str:
    folder = Path(folder)
    parts = []
    for f in _authoritative_files(folder):
        parts.append({"path": f.relative_to(folder).as_posix(), "json": read_json(f)})
    return digest(parts)


def load_skill(folder: str | Path) -> dict:
    folder = Path(folder)
    if not folder.is_dir():
        raise Blocked("SKILL_NOT_FOUND", str(folder))
    present = {p.name for p in folder.iterdir()}
    if present <= {"SKILL.md", "notes", "examples"}:
        raise Blocked("SKILL_HAS_NO_PRODUCING_ARTIFACTS", "SKILL.md alone has zero art-producing authority")
    for f in AUTHORITATIVE:
        if not (folder / f).exists():
            raise Blocked("SKILL_INCOMPLETE", f"missing {f}")
    manifest = read_json(folder / "manifest.json")
    decisions = read_json(folder / "decisions.json")
    clauses, negatives = [], []
    for t in sorted((folder / "prompt_templates").glob("*.json")):
        d = read_json(t)
        clauses += d.get("clauses", [])
        negatives += d.get("negative_clauses", [])
    recipes = {r.stem: read_json(r) for r in sorted((folder / "recipes").glob("*.json"))}
    if not clauses:
        raise Blocked("SKILL_HAS_NO_PROMPT_TEMPLATES")
    if not recipes:
        raise Blocked("SKILL_HAS_NO_RECIPES", "no operation DAG")
    refs = read_json(folder / "references" / "manifest.json")
    for r in refs:
        p = folder / "references" / r["path"]
        if not p.exists():
            raise Blocked("REFERENCE_BYTES_MISSING", r["ref_id"])
        if sha256_file(p) != r["sha256"]:
            raise Blocked("REFERENCE_HASH_MISMATCH", r["ref_id"])
    for rid, rec in recipes.items():
        for n in rec.get("nodes", []):
            if n["operator"] not in OPERATORS:
                raise Blocked("UNKNOWN_OPERATOR", f"{rid}:{n['operator']}")
    h = skill_hash(folder)
    frozen = read_json(folder / "FROZEN.json") if (folder / "FROZEN.json").exists() else None
    status = manifest.get("status", "CANDIDATE_EXPERIMENT")
    if frozen:
        if frozen["skill_hash"] != h:
            raise Blocked("FROZEN_SKILL_MODIFIED", f"frozen {frozen['skill_hash'][:12]} != current {h[:12]}")
        status = "FROZEN"
    return {"skill_id": manifest["skill_id"], "version": manifest["version"], "status": status,
            "claim_state": manifest.get("claim_state", "METHOD_CANDIDATE"), "synthetic": bool(manifest.get("synthetic")),
            "manifest": manifest, "decisions": decisions, "clauses": clauses, "negative_clauses": negatives,
            "references": refs, "recipes": recipes, "folder": str(folder), "skill_hash": h, "frozen": frozen,
            "provider_parameters": manifest.get("provider_parameters", {}),
            "reference_overflow_policy": manifest.get("reference_overflow_policy", "BLOCK")}


def freeze_skill(folder: str | Path, *, observed_relations: dict, approved_by: str) -> dict:
    """Interface I gate: every clause must be derivable from observed relations. Otherwise refuse freeze."""
    sk = load_skill(folder)
    if not approved_by:
        raise Blocked("FREEZE_NEEDS_REVIEWER")
    by_dec = {d["decision_id"]: d for d in sk["decisions"]}
    audits = []
    for c in sk["clauses"] + sk["negative_clauses"]:
        dec = by_dec.get(c.get("decision_id"))
        if dec is None:
            audits.append({"clause_id": c.get("id"), "verdict": "RESEARCH_ONLY", "reasons": ["NO_OWNING_DECISION"],
                           "classified_origin": "UNKNOWN_ORIGIN"})
            continue
        audits.append(interface_one_gate(c, dec, observed_relations))
    blocked = [a for a in audits if a["verdict"] != "FREEZABLE"]
    research_decisions = [d["decision_id"] for d in sk["decisions"] if d.get("status") == "RESEARCH_ONLY"]
    report = {"skill_id": sk["skill_id"], "skill_hash": sk["skill_hash"], "clause_audits": audits,
              "research_only_clauses": [a["clause_id"] for a in blocked], "research_only_decisions": research_decisions,
              "approved_by": approved_by, "at": now_iso()}
    if blocked:
        report["result"] = "FREEZE_REFUSED_RESEARCH_ONLY_CLAUSES"
        atomic_write_json(Path(folder) / "FREEZE_REFUSAL.json", report)
        raise Blocked("FREEZE_REFUSED", f"clauses not derivable from observation: {report['research_only_clauses']}", report=report)
    report["result"] = "FROZEN"
    atomic_write_json(Path(folder) / "FROZEN.json", report)
    return report


def write_skill(folder: str | Path, *, manifest: dict, decisions: list, templates: dict, references: list,
                recipes: dict, skill_md: str, known_failures: list | None = None, notes: str = "") -> str:
    """Write a complete skill folder atomically (used by the S4 builder and fixtures)."""
    folder = Path(folder)
    (folder / "prompt_templates").mkdir(parents=True, exist_ok=True)
    (folder / "recipes").mkdir(parents=True, exist_ok=True)
    (folder / "references").mkdir(parents=True, exist_ok=True)
    (folder / "scripts").mkdir(parents=True, exist_ok=True)
    (folder / "examples").mkdir(parents=True, exist_ok=True)
    (folder / "notes").mkdir(parents=True, exist_ok=True)
    atomic_write_json(folder / "manifest.json", manifest)
    atomic_write_json(folder / "decisions.json", decisions)
    for name, t in templates.items():
        atomic_write_json(folder / "prompt_templates" / f"{name}.json", t)
    atomic_write_json(folder / "references" / "manifest.json", references)
    for name, r in recipes.items():
        atomic_write_json(folder / "recipes" / f"{name}.json", r)
    atomic_write_json(folder / "known_failures.json", known_failures or [])
    (folder / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (folder / "notes" / "observations.md").write_text(notes or "Non-authoritative notes.\n", encoding="utf-8")
    (folder / "scripts" / "ENTRYPOINT.json").write_text(json.dumps({"entrypoint": "vme.skills.runtime:execute",
                                                                     "operators": sorted(OPERATORS)}, indent=2), encoding="utf-8")
    return skill_hash(folder)
