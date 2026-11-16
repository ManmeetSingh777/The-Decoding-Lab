"""Source→inference→skill→provider→asset provenance (Addendum 27 §5).

Interfaces:
  I   OBSERVATION → SKILL: every frozen clause must follow from an observed relation; model-
      authored clauses without derivation stay RESEARCH_ONLY.
  II  SKILL → IMAGE REQUEST: every appearance-affecting provider-visible span/field is owned.
  III IMAGE → ART/ANIMATION: output regions classified controlled / content / provider-free.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict, field

from ..util import Blocked, digest, now_iso

ORIGIN_TYPES = ("SOURCE_OBSERVED", "CROSS_SOURCE_INFERRED", "PRODUCER_ENGINEERING_CHOICE", "ORIGINAL_BRIEF_CONTENT",
                "APPROVED_STYLE_REVISION", "MODEL_SUGGESTED_UNVERIFIED", "PROVIDER_GENERATED_UNDETERMINED", "UNKNOWN_ORIGIN")
NODE_TYPES = ("SOURCE_WITNESS", "SOURCE_OBSERVATION", "STYLE_INFERENCE", "STYLE_DECISION", "SKILL_CLAUSE", "REFERENCE_IMAGE",
              "OPERATION", "COMPILED_FIELD", "PROVIDER_RESULT", "ASSET", "RENDERED_FRAME_REGION", "ORIGINAL_BRIEF")
FREEZABLE_ORIGINS = ("SOURCE_OBSERVED", "CROSS_SOURCE_INFERRED", "APPROVED_STYLE_REVISION")
RESIDUAL_NOTICE = ("The image model's internal pixel decisions cannot be exhaustively attributed; provenance here is "
                   "structural (which governed inputs reached the provider), not pixel-level causality.")
_STOP = {"the", "and", "with", "that", "this", "from", "into", "each", "their", "while", "when", "then", "than", "same",
         "keep", "make", "draw", "draws", "drawn", "show", "shows", "have", "more", "less", "every", "only", "also", "they",
         "subject", "setting", "action", "view", "visual", "role", "original", "prop", "must", "should", "using", "use"}


@dataclass
class ProvenanceNode:
    node_id: str
    node_type: str
    origin_type: str
    content: str
    parent_ids: list
    status: str = "PROPOSED"
    source_evidence: list = field(default_factory=list)
    skill_hash: str | None = None
    provider_payload_path: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class ProvenanceGraph:
    def __init__(self):
        self.nodes: dict[str, ProvenanceNode] = {}

    def add(self, node: ProvenanceNode) -> ProvenanceNode:
        if node.node_type not in NODE_TYPES or node.origin_type not in ORIGIN_TYPES:
            raise Blocked("BAD_PROVENANCE_NODE", f"{node.node_type}/{node.origin_type}")
        for pid in node.parent_ids:
            if pid not in self.nodes:
                raise Blocked("DANGLING_PROVENANCE_PARENT", f"{node.node_id} → {pid}")
        self.nodes[node.node_id] = node
        return node

    def lineage(self, node_id: str) -> list[str]:
        out, stack = [], [node_id]
        while stack:
            n = stack.pop()
            if n in out:
                continue
            out.append(n)
            stack.extend(self.nodes[n].parent_ids)
        return out

    def roots_of_type(self, node_id: str, t: str) -> list[str]:
        return [n for n in self.lineage(node_id) if self.nodes[n].node_type == t]

    def to_dict(self) -> dict:
        return {"nodes": [n.to_dict() for n in self.nodes.values()], "sha": digest([n.to_dict() for n in self.nodes.values()])}

    @classmethod
    def from_dict(cls, d: dict) -> "ProvenanceGraph":
        g = cls()
        for n in d["nodes"]:
            g.nodes[n["node_id"]] = ProvenanceNode(**n)
        return g


def _content_words(text: str) -> set:
    text = re.sub(r"\$\{[a-z_]+\}", " ", text.lower())
    return {w for w in re.findall(r"[a-z]{4,}", text) if w not in _STOP}


def lexical_grounding(clause_text: str, grounding_texts: list[str]) -> dict:
    """Crude, executable derivation check: aesthetic words of the clause must appear in the
    observed relations / decision they claim to come from. Ungrounded words are reported."""
    cw = _content_words(clause_text)
    gw = set().union(*[_content_words(t) for t in grounding_texts]) if grounding_texts else set()
    ungrounded = sorted(cw - gw)
    ratio = 1.0 if not cw else (len(cw) - len(ungrounded)) / len(cw)
    return {"grounded_ratio": round(ratio, 3), "ungrounded_terms": ungrounded, "ok": ratio >= 0.7}


def interface_one_gate(clause: dict, decision: dict, observed_relations: dict) -> dict:
    """OBSERVATION → SKILL audit for one clause. Returns {verdict, reasons, ...}; never raises for content."""
    reasons = []
    origin = clause.get("origin_type", "UNKNOWN_ORIGIN")
    if origin not in FREEZABLE_ORIGINS:
        reasons.append(f"ORIGIN_{origin}_NOT_FREEZABLE")
    if clause.get("decision_id") != decision.get("decision_id"):
        reasons.append("CLAUSE_NOT_OWNED_BY_DECISION")
    rel_ids = decision.get("observed_relation_ids", [])
    missing_rel = [r for r in rel_ids if r not in observed_relations]
    if not rel_ids or missing_rel:
        reasons.append("NO_TRACEABLE_OBSERVED_RELATION")
    grounding = [observed_relations[r]["relation"] for r in rel_ids if r in observed_relations]
    grounding += [decision.get("invariant_visual_relation", "")] + [b.get("construction_action", "") for b in decision.get("branches", [])]
    lg = lexical_grounding(clause.get("template", ""), grounding)
    if not lg["ok"]:
        reasons.append("CLAUSE_TERMS_NOT_DERIVED_FROM_OBSERVATION")
    if decision.get("origin_type") == "MODEL_SUGGESTED_UNVERIFIED":
        reasons.append("DECISION_MODEL_SUGGESTED_UNVERIFIED")
    verdict = "FREEZABLE" if not reasons else "RESEARCH_ONLY"
    classified = origin if not reasons else ("MODEL_SUGGESTED_UNVERIFIED" if "CLAUSE_TERMS_NOT_DERIVED_FROM_OBSERVATION" in reasons
                                             or origin == "MODEL_SUGGESTED_UNVERIFIED" else "UNKNOWN_ORIGIN")
    return {"clause_id": clause.get("id"), "verdict": verdict, "classified_origin": classified, "reasons": reasons,
            "lexical_grounding": lg, "observed_relation_ids": rel_ids}


def interface_two_audit(payload: dict, field_ownership: dict, segment_provenance: list[dict]) -> dict:
    """SKILL → IMAGE REQUEST: classify every appearance-affecting provider field and prompt span."""
    problems, owned = [], []
    for k in payload:
        own = field_ownership.get(k)
        if own is None:
            problems.append({"field": k, "code": "UNOWNED_PROVIDER_FIELD"})
        else:
            owned.append({"field": k, "owner": own})
    prompt = payload.get("positivePrompt", "")
    covered = "".join(s["text"] + "\n" for s in segment_provenance).rstrip("\n")
    if prompt != covered:
        problems.append({"field": "positivePrompt", "code": "UNAUTHORIZED_STYLE_TEXT",
                         "detail": "prompt bytes differ from concatenated owned segments"})
    for s in segment_provenance:
        if s["authority"] == "STYLE" and not (s.get("skill_decision_id") and s.get("skill_hash") and s.get("clause_id")):
            problems.append({"segment": s.get("clause_id"), "code": "STYLE_SPAN_WITHOUT_SKILL_OWNER"})
        if s["authority"] == "CONTENT" and not s.get("brief_field_path"):
            problems.append({"segment": s.get("text", "")[:40], "code": "CONTENT_SPAN_WITHOUT_BRIEF_FIELD"})
    return {"ok": not problems, "problems": problems, "owned_fields": owned}


def style_authority_report(job_id: str, *, controlled: list, missing_from_skill: list, not_compiled: list,
                           outside_authority: list, model_inventions: list, ungoverned_output: list,
                           content_choices: list) -> dict:
    return {"job_id": job_id, "controlled_aesthetic_decisions": controlled,
            "source_supported_but_missing_from_skill": missing_from_skill, "skill_present_but_not_compiled": not_compiled,
            "provider_fields_outside_authority": outside_authority, "candidate_model_inventions": model_inventions,
            "ungoverned_output_appearance": ungoverned_output, "original_content_choices": content_choices,
            "provider_unobservable_residual_notice": RESIDUAL_NOTICE, "created_at": now_iso()}


def interface_three_attribution(output_regions: list[dict], compiled_controls: dict) -> dict:
    """IMAGE → ART: classify reviewed output regions. Unexpected attractive detail is NOT credited to the skill."""
    rows, ungoverned = [], []
    for r in output_regions:
        ctrl = [d for d in r.get("claimed_decision_ids", []) if d in compiled_controls.get("decision_ids", [])]
        content = [c for c in r.get("content_fields", []) if c in compiled_controls.get("content_fields", [])]
        if ctrl:
            origin = "CONTROLLED_BY_SKILL"
        elif content:
            origin = "ORIGINAL_BRIEF_CONTENT"
        else:
            origin = "PROVIDER_GENERATED_UNDETERMINED"
            if r.get("salience") in ("HIGH", "MEDIUM"):
                ungoverned.append(f"{r['region_id']}: {r['description']}")
        rows.append({"region_id": r["region_id"], "origin": origin, "decision_ids": ctrl, "content_fields": content,
                     "edits": r.get("edits", []), "credited_to_skill": bool(ctrl)})
    return {"regions": rows, "ungoverned_output_appearance": ungoverned,
            "status": "UNGOVERNED_OUTPUT_APPEARANCE" if ungoverned else "GOVERNED_WITH_RESIDUAL",
            "skill_success_credit": False if ungoverned else None, "notice": RESIDUAL_NOTICE}
