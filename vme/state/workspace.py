"""Portable disk-owned workspace layout (Addendum 24 D1) and STATE/CONTINUE_HERE writers."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ..util import atomic_write_json, atomic_write_text, read_json, now_iso, append_jsonl
from .store import Store, open_store

LAYOUT = ("state", "store", "skills", "artifacts", "logs", "frames", "vision", "investigation", "runs", "reports")


@dataclass
class Workspace:
    root: Path

    @property
    def state_dir(self) -> Path: return self.root / "state"
    @property
    def store_path(self) -> Path: return self.root / "store" / "vme.sqlite"
    @property
    def skills_dir(self) -> Path: return self.root / "skills"
    @property
    def artifacts_dir(self) -> Path: return self.root / "artifacts"
    @property
    def logs_dir(self) -> Path: return self.root / "logs"
    @property
    def frames_dir(self) -> Path: return self.root / "frames"
    @property
    def vision_dir(self) -> Path: return self.root / "vision"
    @property
    def reports_dir(self) -> Path: return self.root / "reports"

    def ensure(self) -> "Workspace":
        for d in LAYOUT:
            (self.root / d).mkdir(parents=True, exist_ok=True)
        if not (self.state_dir / "STATE.json").exists():
            atomic_write_json(self.state_dir / "STATE.json", {
                "schema": "vme.state/1", "created_at": now_iso(), "current_stage": "S0",
                "last_completed_unit": None, "run_mode": "OFFLINE_BUILD",
                "paid_vlm_frames_seen": 0, "runware_real_calls": 0,
            })
        return self

    def store(self) -> Store:
        return open_store(self.store_path)

    def read_state(self) -> dict:
        return read_json(self.state_dir / "STATE.json")

    def update_state(self, **kv) -> dict:
        st = self.read_state()
        st.update(kv)
        st["updated_at"] = now_iso()
        atomic_write_json(self.state_dir / "STATE.json", st)
        return st

    def log(self, stream: str, record: dict) -> None:
        append_jsonl(self.logs_dir / f"{stream}.jsonl", {"at": now_iso(), **record})


def default_workspace() -> Workspace:
    root = Path(os.environ.get("VME_WORKSPACE", Path.cwd() / "workspace"))
    return Workspace(root).ensure()


def write_continue_here(ws: Workspace, *, next_command: str, details: dict) -> str:
    """One-screen cold-start reconstruction (spec 10 §5; Addendum 24 D3)."""
    lines = ["# CONTINUE_HERE", "", f"Generated: {now_iso()}", "",
             "## Exact next command", "", "```bash", next_command, "```", "",
             "## Current state (read the referenced records, not only this summary)", ""]
    for k in sorted(details):
        v = details[k]
        if isinstance(v, (list, tuple)):
            lines.append(f"- **{k}**:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            lines.append(f"- **{k}**: {v}")
    lines += ["", "## Truthful limits", "",
              "- Hidden model reasoning is NOT transferred; only committed records are.",
              "- Uncommitted work at interruption is reported as UNRESOLVED and must be redone from its stored inputs.",
              "- PAID_VLM_FRAMES_SEEN and RUNWARE_REAL_CALLS are read from STATE.json; zero unless separately authorized."]
    text = "\n".join(lines) + "\n"
    atomic_write_text(ws.state_dir / "CONTINUE_HERE.md", text)
    return text
