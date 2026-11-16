"""Human source-role confirmation (audit P0-5). Roles change only by explicit user statement, keyed by SHA256.

Never infers authority from filename or duration; never re-indexes or modifies source bytes.
"""
from __future__ import annotations

from ..util import Blocked, atomic_write_json, atomic_write_text, now_iso, read_json
from ..state.workspace import Workspace

ROLES = ("BASE_FILM", "SIXTH_SPECIAL", "EXCLUDED")
CONTRACT_TITLES = ("A.I. – Humanity's Final Invention", "How Are Memories Stored Inside Your Brain", "Why Your Brain Blinds You",
                   "How Nuclear Flies Protect You", "Why Humanity Will Never Leave Solar System")


def confirm_role(ws: Workspace, *, sha256: str, role: str, confirmed_by: str, statement: str) -> dict:
    if role not in ROLES:
        raise Blocked("BAD_ROLE", role)
    if not confirmed_by or confirmed_by.lower() in ("agent", "claude", "model", "auto"):
        raise Blocked("HUMAN_CONFIRMATION_REQUIRED")
    lock = read_json(ws.state_dir / "SOURCE_LOCK.json")
    hit = [s for s in lock["sources"] if s["sha256"] == sha256]
    if not hit:
        raise Blocked("UNKNOWN_SOURCE_SHA", sha256[:12])
    s = hit[0]
    s.update(role=role, basis="USER_CONFIRMED", confirmed_by=confirmed_by, confirmed_at=now_iso(), confirmation_statement=statement)
    if role == "SIXTH_SPECIAL":
        for o in lock["sources"]:
            if o is not s and o["role"] == "SIXTH_SPECIAL":
                o.update(role="BASE_FILM", basis="DEFAULT_NON_SIXTH")
    lock["sixth_status"] = "SIXTH_SOURCE_PRESENT" if any(x["role"] == "SIXTH_SPECIAL" for x in lock["sources"]) else "SIXTH_SOURCE_NOT_AVAILABLE"
    atomic_write_json(ws.state_dir / "SOURCE_LOCK.json", lock)
    cfg = ws.root / "config" / "source_roles.json"
    roles = read_json(cfg) if cfg.exists() else {}
    roles[sha256] = {"role": role, "confirmed_by": confirmed_by, "at": now_iso(), "statement": statement}
    atomic_write_json(cfg, roles)
    st = ws.store()
    try:
        st.put("SourceLock", sha256, s)
        st.event("SOURCE_ROLE_CONFIRMED", sha256, {"role": role, "by": confirmed_by})
    finally:
        st.close()
    return s


def role_status(ws: Workspace) -> dict:
    lock = read_json(ws.state_dir / "SOURCE_LOCK.json")
    base = [s for s in lock["sources"] if s["role"] == "BASE_FILM"]
    six = [s for s in lock["sources"] if s["role"] == "SIXTH_SPECIAL"]
    base_ok = len(base) == 5 and all(s.get("basis") == "USER_CONFIRMED" for s in base)
    six_ok = len(six) == 1 and six[0].get("basis") == "USER_CONFIRMED"
    return {"base_five_confirmed": base_ok, "sixth_confirmed": six_ok,
            "unconfirmed": [s["file_name"] for s in lock["sources"] if s.get("basis") != "USER_CONFIRMED"],
            "resolutions": {s["file_name"]: f"{s['width']}x{s['height']}" for s in lock["sources"]}}


def write_role_report(ws: Workspace, out_path) -> str:
    lock = read_json(ws.state_dir / "SOURCE_LOCK.json")
    six_status = ws.state_dir / "SIXTH_LOCATOR_STATUS.json"
    loc = read_json(six_status) if six_status.exists() else {}
    lines = ["# Source role confirmation report (human action required)", "", f"Generated {now_iso()}. Identity = SHA256 of the bytes on disk; "
             "files were not renamed, modified or re-indexed.", "",
             "| File | SHA256 (12) | Resolution | Frames source | Current role | Basis | Confirmed by |", "|---|---|---|---|---|---|---|"]
    for s in lock["sources"]:
        lines.append(f"| {s['file_name']} | `{s['sha256'][:12]}` | {s['width']}x{s['height']} | {s['avg_frame_rate']} fps | {s['role']} | "
                     f"{s.get('basis')} | {s.get('confirmed_by', '—')} |")
    lines += ["", "## Mismatch with the contract", "", "01_IMPLEMENTATION_CONTRACT.md §0.3 names: " + "; ".join(CONTRACT_TITLES) + ".",
              "Only the first title has a matching file here. The other four BASE_FILM files are different videos and are **UNCONFIRMED**:",
              "they are quarantined from study until you confirm them (or supply the intended films).", "",
              "## Resolution", "", "All six local files are **1280×720**. Native-detail claims are limited to 720p pixels. If 1080p originals exist, "
              "supply them; they would be NEW sources (new SHA256, new index) — the existing 720p indexes stay as they are.", "",
              "## Sixth clip", "", "Role: confirmed by the user in chat on 2026-11-15 (\"the sixth clip is the Kurzgesagt 1200 Hours video\").",
              f"Volcano-start / Earth-logo boundaries: **UNCONFIRMED** (locator status `{loc.get('status', 'NOT_RUN')}`). They must be chosen from "
              "actually viewed frames: open the local witness packet PNGs and run `vme selection sixth-lock --start N --end M --confirmed-by NAME "
              f"--witness-sha {loc.get('witness_packet_sha', '<sha>')}`.", "",
              "## Commands to confirm", "", "```bash", "python -m vme sources confirm-role --sha <sha256> --role BASE_FILM --by \"<your name>\"",
              "```"]
    text = "\n".join(lines) + "\n"
    atomic_write_text(out_path, text)
    return text
