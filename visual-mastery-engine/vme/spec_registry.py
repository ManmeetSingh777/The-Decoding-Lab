"""Which specification documents are authoritative for this build (ADD26-D01) and their hashes."""
from __future__ import annotations

from pathlib import Path

from .util import sha256_file

AUTHORITATIVE = (
    "01_IMPLEMENTATION_CONTRACT.md", "02_DATA_SCHEMAS.json", "03_ACCEPTANCE_TEST_PLAN.md", "04_USER_REVIEW_PACKET.md",
    "05_APPROVED_13_PART_REFERENCE.txt", "06_BUILD_AUDIT_MAP.md", "07_STYLE_FRAME_PROMPT_CHARACTER_GATES.md",
    "08_PROMPT_PIPELINE_EXAMPLE.md", "09_STYLE_OBSERVATION_TO_PRODUCTION_ALGORITHM.md", "10_EXHAUSTIVE_FRAME_VISION_AND_CRASH_RESUME.md",
    "11_CONCRETE_SKILL_CONTROLLED_IMAGE_PRODUCTION.md", "12_EXACT_LAUNCH_AND_PROGRESS_CONTRACT.md",
    "13_CRITICAL_PATH_AND_FAILURE_PREVENTION.md", "14_OBSERVATION_TO_SKILL_IMPLEMENTATION_MANUAL.md",
    "15_STYLE_AUTHORITY_AND_PROMPT_PRODUCTION.md", "16_CHARACTER_CONSTRUCTION_AND_ACTING_ART.md",
    "17_IMAGE_ASSET_TO_ANIMATION_INTERFACES.md", "18_BUILD_FIRST_INDEPENDENT_AUDIT_PROTOCOL.md",
    "19_RUNWARE_MODEL_AND_SPEND_DISCOVERY.md", "20_FULL_WORKED_SYNTHETIC_SKILL_CONSTRUCTION_EXAMPLE.md",
    "21_V13_TYPED_CONTRACTS.schema.json", "22_NEW_ACCEPTANCE_AND_AUDIT_CROSSWALK.md", "23_INDEPENDENT_SPEC_GAP_FINDINGS.md",
    "24_CHARACTER_STYLE_DISCOVERY_AND_PORTABLE_CONTINUITY_ADDENDUM.md", "25_FIFTEEN_SEQUENCE_DEEP_VISION_AND_QUESTION_ENGINE_ADDENDUM.md",
    "26_DYNAMIC_QUESTIONS_SIXTH_SEQUENCE_AND_CLOSED_LEARNING_LOOP.md", "27_COMPLETE_VISUAL_MODEL_AND_PROVENANCE_ADDENDUM.md",
    "27_TYPED_COVERAGE_AND_PROVENANCE.schema.json", "27_SYNTHETIC_COVERAGE_EXAMPLE.json",
)
AUTHORITATIVE_LAUNCH = "00_COMPLETE_LAUNCH_V13_ADDENDA_24_25_26_27_PASTE_THIS.txt"
SUPERSEDED = ("00_PASTE_INTO_CLAUDE_OR_CODEX.md", "00_PREVIOUS_V12_LAUNCH_REFERENCE_DO_NOT_PASTE.md",
              "00_LAUNCH_V13_WITH_ADDENDA_24_AND_25_PASTE_THIS.txt", "00_COMPLETE_LAUNCH_V13_ADDENDA_24_25_26_PASTE_THIS.txt")
PRECEDENCE_OVERRIDES = (
    "1 OFFLINE BUILD → audit ZIP → STOP overrides any immediate paid research/generation instruction",
    "2 full-res ARTWORK approval → CHARACTER/ASSET approval → final MP4 approval supersede early mandatory video",
    "3 Addendum 25 controls the first 15 (3x5) + every frame; Addendum 26 adds a distinct sixth interval (15+1)",
    "4 Addendum 26: one evidence-derived next question per bottleneck; Q0–Q7 are reasoning functions",
    "5 Addendum 27: comprehensive coverage sweep before first bundle approval; one controlling question per dependency",
    "6 Addendum 27 provenance classes; never claim pixel-level knowledge of provider decisions",
)


def authority_report(spec_dir: str | Path) -> dict:
    d = Path(spec_dir)
    present = {p.name for p in d.iterdir()} if d.exists() else set()
    parent = {p.name for p in d.parent.iterdir()} if d.exists() else set()
    return {"spec_dir": str(d), "authoritative": {n: sha256_file(d / n) for n in AUTHORITATIVE if n in present},
            "missing_authoritative": [n for n in AUTHORITATIVE if n not in present],
            "authoritative_launch": next((str(p) for p in (d / AUTHORITATIVE_LAUNCH, d.parent / AUTHORITATIVE_LAUNCH,
                                                            d / "_addenda_27" / AUTHORITATIVE_LAUNCH) if p.exists()), "MISSING"),
            "superseded_present": sorted(n for n in SUPERSEDED if n in present or n in parent),
            "precedence_overrides": list(PRECEDENCE_OVERRIDES)}
