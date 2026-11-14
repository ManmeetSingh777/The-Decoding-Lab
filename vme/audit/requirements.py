"""Master requirement catalog: every ID from 03 (A01–A68), 13 (C01–C38), 22 (B01–B36), Addenda 24–27.

`needs` names what a POSITIVE demonstration requires beyond offline engineering:
PAID (authorized provider spend / source upload), ART (real original artwork), HUMAN (user verdict).
Requirements with `needs` are reported BLOCKED even when their offline refusal/wiring tests pass.
"""
from __future__ import annotations

A = {
    "A01": ("Fresh repo; no prior AnimationLab inputs", ""), "A02": ("Ingest sources: ffprobe, SHA256, decode", ""),
    "A03": ("Targeted retrieval + native crops + adjacent sequence", ""), "A04": ("Provider capability call returns real file + cost", "PAID"),
    "A05": ("No paid call without budget; no upload without consent", ""), "A06": ("Scene/asset schema validation", ""),
    "A07": ("Renderer refuses before approvals; ffprobe-verified MP4 after", ""), "A08": ("Several ranked gaps with source+original witnesses", "ART"),
    "A09": ("Connected cluster with dependencies and exclusions", ""), "A10": ("Specific observation with full context and producing decision", "PAID"),
    "A11": ("Skill conversion: executable recipe consumed by producer", ""), "A12": ("Causality: disable/enable method changes intended output", "PAID+ART"),
    "A13": ("Multi-change attribution via toggles", "ART"), "A14": ("Multiple-root diagnosis separates causes", ""),
    "A15": ("Controlled anchor A/B without confounds", "PAID+ART"), "A16": ("Rotating development brief, no manual rescue", "PAID+ART"),
    "A17": ("Blind transfer after freeze", "PAID+ART"), "A18": ("Human review sees stills/MP4/gaps; feedback saved", "HUMAN+ART"),
    "A19": ("Kill/restart after partial provider request; no duplicate bill", ""), "A20": ("Per-run cost accounting, unknown costs explicit", ""),
    "A21": ("Image-to-motion identity consistency", "ART"), "A22": ("Unsupported capability → named stop", ""),
    "A23": ("Separate PASS/FAIL/UNTESTED statuses", ""), "A24": ("Integrated approved iteration with 12–20 s MP4", "PAID+ART+HUMAN"),
    "A25": ("20–30 s multi-shot film under frozen skills", "PAID+ART+HUMAN"), "A26": ("Every decoded frame + PTS indexed; VFR kept", ""),
    "A27": ("Coverage ledger separates indexed/sent/verified/native", ""), "A28": ("All-frame VLM estimate + gated segmented execution", "PAID"),
    "A29": ("Corrupt/skipped/VFR/last-frame injection caught", ""), "A30": ("Style mechanism vs source fact", ""),
    "A31": ("Cross-subject conditions and counterexamples", ""), "A32": ("Originality vs clone discrimination on outputs", "ART"),
    "A33": ("Every style clause traces to skill; content to brief", ""), "A34": ("Clause coverage/contradiction; nothing silently dropped", ""),
    "A35": ("Prompt length/reference count/dimension validation", ""), "A36": ("Skill change → request change (and output where feasible)", ""),
    "A37": ("Visual prompt-output review on real images", "ART"), "A38": ("Canonical character human verdict tied to hashes", "HUMAN+ART"),
    "A39": ("Coherent multi-view/face identity", "ART"), "A40": ("Limb/hand/prop/ground relationship validation", ""),
    "A41": ("Layer/mask/clean-plate recomposition", ""), "A42": ("Artwork approval gate; rejected art cannot render", ""),
    "A43": ("Asset pack approval gate", ""), "A44": ("Reapproval after replacement", ""),
    "A45": ("First cycles emphasise characters with real art", "ART"), "A46": ("Independent multi-failure diagnosis", ""),
    "A47": ("Resume keeps approvals/pending reviews/idempotency", ""), "A48": ("Separate claim statuses; tests ≠ mastery", ""),
    "A49": ("Scene facts separated before skill writing", ""), "A50": ("Question ladder does not stop on adjectives", ""),
    "A51": ("Decisions carry applicability/variants/exclusions/freedoms", ""), "A52": ("Design plan + recipe exist before provider call", ""),
    "A53": ("Runtime style insertion cannot change request", ""), "A54": ("Missing essential decision blocks; no default style", ""),
    "A55": ("Stage-specific operations (canonical vs pose vs grip)", ""), "A56": ("Style-like language in brief separated/rejected", ""),
    "A57": ("Reference slots by skill rules and capability; identity bytes", ""), "A58": ("Character generated first as whole canonical art", "ART"),
    "A59": ("Canonical-conditioned face/pose/hand states", "ART"), "A60": ("AnimationDemandPlan before art generation", ""),
    "A61": ("Every frame decoded; per-frame VLM truthfully separate", ""), "A62": ("Per-frame semantic entries; summary rejected", ""),
    "A63": ("Boundary state across packets", ""), "A64": ("Semantic replay across new session", ""),
    "A65": ("Idempotent/reconciled paid requests", ""), "A66": ("Two-film-first vs all-five accurate reporting", ""),
    "A67": ("User review on full-size art before layers/motion", "ART+HUMAN"),
    "A68": ("reference_impl tests pass; app pinned-skill→real request→real image", "ART"),
}
B = {f"B{i:02d}": (t, n) for i, (t, n) in enumerate([
    ("Only allowed MP4s in provenance", ""), ("Frame index+PTS hash exact", ""), ("Index all, VLM exactly zero", ""),
    ("Missing frame in vision result → no commit", ""), ("Input hash mismatch → quarantine", ""), ("Kill around paid request; no duplicate", ""),
    ("Kill after response before commit", ""), ("New session from CONTINUE_HERE+DB", ""), ("Vague 'polished' → targeted cause", ""),
    ("Source noun in decision demoted", ""), ("Single source stays conditional", ""), ("Connected world/character/colour cluster", ""),
    ("Question lacking producing unknown parked", ""), ("No exceptions/adaptations → not frozen", ""), ("No operation → research-only", ""),
    ("SKILL.md-only refused", ""), ("Selected clause change changes prompt", ""), ("Non-selected prose change no effect", ""),
    ("Raw positivePrompt refused", ""), ("Style rewrite in brief → ticket/block", ""), ("Pose edit without identity refused", ""),
    ("Reference overflow staged or blocked", ""), ("'7B' without verified model refused", ""), ("No consent → network refused", ""),
    ("Opaque PNG never transparent", ""), ("Layer dimension/origin mismatch caught", ""), ("Hand/prop whole pose before layers", ""),
    ("Alternate view identity drift → route reexamined", "ART"), ("Weak actor art → no render", "ART"), ("Approved hash change invalidates", ""),
    ("Multiple failures → separate trails", ""), ("One-scene improvement not transferable", "ART"), ("Skill can't produce visual difference reported", "PAID+ART"),
    ("Rich still but flat motion → no pan-only proof", "ART"), ("Audit ZIP contents", ""), ("Claims map to function/test/evidence", "")], start=1)}
C = {f"C{i:02d}": (t, n) for i, (t, n) in enumerate([
    ("Fresh source allowlist", ""), ("Accurate film/time/frames", ""), ("True every-frame VLM availability", ""), ("Native-detail inspection", ""),
    ("Scene+temporal understanding (boundary, adjacency)", ""), ("High-impact question selection", ""), ("Deep observation, not slogans", ""),
    ("Self-correcting questions", ""), ("Style independent of source subject", ""), ("Style isn't just recurrence", ""),
    ("Integration across disciplines", ""), ("Manufacture plan exists", ""), ("Skill is a working producer", ""),
    ("Style-exclusive prompt authority", ""), ("New content vs learned style", ""), ("Specific prompts without bloat", ""),
    ("Correct actual provider (live catalog/probe)", "PAID"), ("Real image bytes", "PAID"), ("Artwork appealing at construction", "ART"),
    ("Character identity across poses", "ART"), ("Face/expression language", "ART"), ("Limb/hand/contact logic", ""),
    ("Part & layer usability", ""), ("Coordinate handoff", ""), ("Correct render tool", ""), ("Motion-aware art; no pan disguise", ""),
    ("Simultaneous world activity", "ART"), ("Perspective/attention continuity", "ART"), ("Source→skill causality", ""),
    ("Multiple connected gaps", ""), ("Root-cause diagnosis", ""), ("Reliable transfer", "PAID+ART"), ("User approval before motion", ""),
    ("Complete evidence+budget", ""), ("Crash and timeout resume", ""), ("User can audit build", ""), ("Honest qualification", ""),
    ("No unauthorized source upload", "")], start=1)}
ADD24 = {
    "ADD24-E1": ("Five-film mapping + cross-film sequence selection as code contracts", ""),
    "ADD24-E2": ("Character witness grouping, question traces, skill clauses, C1→C7 on synthetic fixtures", ""),
    "ADD24-E3": ("Persistent semantic work units + export/import cold start", ""),
    "ADD24-B1": ("Cross-actor witness groups (a)–(f)", ""), "ADD24-B2": ("Ten question families with required record fields", ""),
    "ADD24-D1": ("Disk-owned workspace layout", ""), "ADD24-D2": ("Atomic persistence at reasoning boundaries", ""),
    "ADD24-D3": ("status/checkpoint/export-handoff/import-handoff/resume commands", ""),
    "ADD24-D4-1": ("Kill mid-frame sequence; fresh process resumes exact next PTS", ""),
    "ADD24-D4-2": ("Kill after provider submission; reconcile, no double charge", ""),
    "ADD24-D4-3": ("Kill between observation and skill conversion", ""), "ADD24-D4-4": ("Kill during character pose generation", ""),
    "ADD24-D4-5": ("Corrupt/drop asset or MP4 → import refuses complete", ""),
    "ADD24-D4-6": ("Switch environment via handoff ZIP; reproduce compiled prompt bytes", ""),
    "ADD24-D4-7": ("Review approval/rejection survives import", ""),
    "ADD24-S0S4-REAL": ("First real learning iteration S0–S4 (after audit + consent)", "PAID+ART+HUMAN"),
}
ADD25 = {k: (k, "") for k in ["ADD25-S01", "ADD25-S02", "ADD25-S03", "ADD25-S04", "ADD25-S05", "ADD25-F01", "ADD25-F02", "ADD25-F03",
                              "ADD25-F04", "ADD25-F05", "ADD25-F06", "ADD25-F07", "ADD25-F08", "ADD25-Q01", "ADD25-Q02", "ADD25-Q03",
                              "ADD25-Q04", "ADD25-Q05", "ADD25-P01", "ADD25-P02", "ADD25-P03", "ADD25-P04", "ADD25-P05", "ADD25-P06",
                              "ADD25-R01", "ADD25-R02", "ADD25-A01", "ADD25-A02"]}
ADD25["ADD25-L0-REAL"] = ("Real first-15 per-frame VLM study (PHASE L0)", "PAID")
ADD26 = {k: (k, "") for k in ["ADD26-D01", "ADD26-D02", "ADD26-D03", "ADD26-D04", "ADD26-D05", "ADD26-Q01", "ADD26-Q02", "ADD26-Q03",
                              "ADD26-Q04", "ADD26-Q05", "ADD26-Q06", "ADD26-F01", "ADD26-F02", "ADD26-F03", "ADD26-F04", "ADD26-S01",
                              "ADD26-S02", "ADD26-P01", "ADD26-P02", "ADD26-P03", "ADD26-I01", "ADD26-I02", "ADD26-I03", "ADD26-R01",
                              "ADD26-R02", "ADD26-A01", "ADD26-A02", "ADD26-S0S9"]}
ADD27 = {
    "ADD27-1": ("VisualModelCoverageLedger typed per schema", ""), "ADD27-2": ("READY_FOR_ORIGINAL_IMAGE_TRIAL scoped/provisional", ""),
    "ADD27-3": ("Investigator finds multiple gaps; re-review after each fix", ""),
    "ADD27-4": ("Missing face/viewpoint; colour w/o light/world link; disconnected world/camera", ""),
    "ADD27-5": ("Joint-relation fixtures incl. pose/contact+lighting and all-NA contradiction", ""),
    "ADD27-6": ("Model-authored clause blocked at observation→skill boundary", ""),
    "ADD27-7": ("Every appearance-affecting provider field classified (Interface II)", ""),
    "ADD27-8": ("Lost skill clause in payload fails with before/after bytes", ""),
    "ADD27-9": ("Free-text style via brief rejected", ""), "ADD27-10": ("Unexpected phenomenon → dynamic extension", ""),
    "ADD27-11": ("SOURCE_FACT/INFERRED/ENGINEERING distinctions recorded", ""),
    "ADD27-12": ("Ungoverned output appearance not credited to skill", ""), "ADD27-13": ("Provenance DAG lineage", ""),
    "ADD27-14": ("Crash during completeness/provenance commit recovers", ""),
}
ORIGINAL_13 = {
    "P01": ("Six connected responsibilities", ["vme.reference", "vme.investigation.gaps", "vme.investigation.controller", "vme.skills", "vme.providers.gateway", "vme.review"]),
    "P02": ("High-impact gap identification", ["vme.investigation.gaps:rank_gaps/select_cluster"]),
    "P03": ("Question engine", ["vme.investigation.controller:derive_next_question"]),
    "P04": ("Working skill conversion", ["vme.style.decisions", "vme.skills.skill", "vme.compiler.compiler"]),
    "P05": ("Sequential lead + bounded parallel", ["vme.investigation.controller:LoopController", "vme.reference.ingest:index_all (bounded threads)"]),
    "P06": ("Iteration protocol with user review gates", ["vme.loop.stages", "vme.review.approvals"]),
    "P07": ("Fast learning, persistence", ["vme.state.store", "vme.state.handoff", "vme.vision.runner"]),
    "P08": ("Visual first, animation-aware", ["vme.artwork.character:derive_animation_demand", "vme.render.renderer"]),
    "P09": ("No overfitting (anchor/rotating/unseen)", ["vme.experiments.experiments:HoldoutRegistry"]),
    "P10": ("Concrete engineering modules + CLI", ["vme.cli"]),
    "P11": ("First real learning cycle", ["vme.loop.stages (REAL mode stops at consent)"]),
    "P12": ("Failure diagnosis and stop policies", ["vme.diagnose.diagnose", "vme.util.Blocked"]),
    "P13": ("Success gates (art/transfer/animation/integrated)", ["vme.review.approvals", "vme.experiments.experiments:transfer_status"]),
}


def all_requirements() -> dict:
    out = {}
    for group, d in (("A", A), ("B", B), ("C", C), ("ADD24", ADD24), ("ADD25", ADD25), ("ADD26", ADD26), ("ADD27", ADD27)):
        for k, (t, n) in d.items():
            out[k] = {"group": group, "text": t, "needs": n}
    return out
