"""Typed original content brief with style-smuggling rejection (15 §2, A56, B20, ADD25-P05, ADD27 §7).

The brief controls WHAT (subjects, setting, action, view, focus, content attributes).
It can never carry aesthetic/rendering instructions. Explicit content attributes (e.g. a
red laboratory coat the story requires) are allowed only inside `content_attributes`
and are themselves screened for rendering-style vocabulary.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict, field

from ..util import Blocked, digest, new_id, now_iso

CONTENT_SLOTS = ("subject", "setting", "action", "visual_role", "view", "original_prop", "subject_kind", "material",
                 "scale", "environment")
BRIEF_FIELDS = ("brief_id", "shot_id", "subjects", "actions", "world", "visual_focus", "camera_or_view_requirement",
                "novelty_constraints", "animation_requirements", "content_provenance", "slots", "scope", "shot_plan")
# Rendering/aesthetic vocabulary that belongs to the skill, never to content.
STYLE_LEXICON = re.compile(
    r"\b(kurzgesagt|in the style of|art style|style|stylized|stylised|vector|flat (design|shading|colou?rs?)|cel[- ]?shad\w*|"
    r"outlines?|line ?weight|lineart|linework|thick lines?|strokes?|shading|shaded|gradients?|highlights?|rim light\w*|"
    r"glow(ing)? edges|palette|colou?r scheme|saturat\w*|pastel|neon|cinematic|pixar|disney|anime|ghibli|photoreal\w*|"
    r"render(ed|ing)? style|lighting style|beautiful|stunning|gorgeous|polished|vibrant|masterpiece|award[- ]winning|"
    r"trending|ultra[- ]detailed|highly detailed|8k|4k|bokeh|dramatic lighting|soft lighting|shiny)\b", re.I)


@dataclass
class OriginalContentBrief:
    brief_id: str
    shot_id: str
    subjects: list                 # [{id, noun, subject_kind, role, content_attributes: [..], identity_asset_id?}]
    actions: list
    world: dict                    # {setting, environment}
    visual_focus: str
    camera_or_view_requirement: str
    novelty_constraints: list
    animation_requirements: list
    content_provenance: str        # who authored the content (USER/DIRECTOR/FIXTURE)
    slots: dict                    # typed values for CONTENT_SLOTS used by templates
    scope: dict = field(default_factory=dict)       # typed OriginalScope fields (subjects/world/camera) — content, not style
    shot_plan: dict = field(default_factory=dict)   # {actions, events, camera, fps, frames} — content/motion requirements
    pool: str = "rotating_development"   # comparison_anchor | rotating_development | unseen_transfer

    def to_dict(self) -> dict:
        return asdict(self)


def _scan(path: str, value) -> list[dict]:
    hits = []
    if isinstance(value, str):
        for m in STYLE_LEXICON.finditer(value):
            hits.append({"field_path": path, "term": m.group(0), "text": value[:120]})
    elif isinstance(value, list):
        for i, v in enumerate(value):
            hits += _scan(f"{path}[{i}]", v)
    elif isinstance(value, dict):
        for k, v in value.items():
            hits += _scan(f"{path}.{k}", v)
    return hits


def validate_brief(raw: dict) -> OriginalContentBrief:
    extra = set(raw) - set(BRIEF_FIELDS) - {"pool"}
    if extra:
        raise Blocked("UNTYPED_BRIEF_FIELD", f"free-text fields are not accepted: {sorted(extra)}")
    missing = [f for f in ("brief_id", "shot_id", "subjects", "actions", "world", "visual_focus", "slots") if not raw.get(f)]
    if missing:
        raise Blocked("CONTENT_BRIEF_INCOMPLETE", str(missing))
    bad_slots = set(raw["slots"]) - set(CONTENT_SLOTS)
    if bad_slots:
        raise Blocked("UNKNOWN_CONTENT_SLOT", str(sorted(bad_slots)))
    for k, v in raw["slots"].items():
        if not isinstance(v, str) or "{" in v or "}" in v or "\n" in v or len(v) > 200:
            raise Blocked("CONTENT_SLOT_UNSAFE", k)
    hits = _scan("brief", {k: v for k, v in raw.items() if k not in ("brief_id", "shot_id", "content_provenance", "pool", "shot_plan")})
    if hits:
        raise Blocked("STYLE_INJECTION_IN_CONTENT", f"{len(hits)} style term(s) in content fields",
                      hits=hits, ticket=style_revision_ticket(raw.get("brief_id", "?"), hits))
    return OriginalContentBrief(**{k: raw.get(k, [] if k in ("novelty_constraints", "animation_requirements", "actions") else
                                              ({} if k in ("scope", "shot_plan") else "")) for k in BRIEF_FIELDS},
                                pool=raw.get("pool", "rotating_development"))


def style_revision_ticket(brief_id: str, hits: list[dict]) -> dict:
    """B20: an unapproved style rewrite in content is separated into a style-revision ticket."""
    return {"ticket_id": new_id("srt"), "kind": "SKILL_REVISION_REQUIRED", "brief_id": brief_id,
            "requested_aesthetic_terms": sorted({h["term"].lower() for h in hits}), "field_paths": [h["field_path"] for h in hits],
            "reason_for_block": "aesthetic wishes in content must be resolved by an evidence-grounded skill revision",
            "created_at": now_iso()}


def brief_hash(b: OriginalContentBrief) -> str:
    return digest(b.to_dict())
