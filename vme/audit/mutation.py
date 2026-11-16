"""R3 mutation suite — every guard the R3 contract relies on is weakened one at a time in a THROWAWAY copy of the repo, and the
targeted tests must then FAIL ("KILLED"). A mutant whose tests still pass is reported as SURVIVED (an honest gap, never hidden).

Each mutation is an exact textual replacement that must match exactly once in the source (otherwise ANCHOR_NOT_FOUND — the suite
is out of date and says so). The original tree is never modified. No network, no provider call.

    python -m vme.audit.mutation --out reports/R3_MUTATION_RESULTS.json [--only M01,M02] [--canary-root <driven canary ws root>]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# (id, guard / requirement, file, exact original text, mutant text, pytest node selector)
MUTATIONS: list[tuple[str, str, str, str, str, str]] = [
    ("M01", "F04/F10 unsent witness citation refused", "vme/style/authoring.py",
     "    if cited - allowed:\n        raise Blocked(\"UNSENT_WITNESS_CITATION\"", "    if False:\n        raise Blocked(\"UNSENT_WITNESS_CITATION\"",
     "tests/test_r3_contract.py -k f04_f10"),
    ("M02", "F04/F10 wrong-source witness refused", "vme/style/authoring.py",
     "        if w[\"film_sha256\"] != m[\"source_sha256\"]:", "        if False:", "tests/test_r3_contract.py -k f04_f10"),
    ("M03", "F04/F10 wrong-PTS witness refused", "vme/style/authoring.py",
     "        if int(w[\"frame_start\"]) != int(m[\"frame_index\"]):", "        if False:", "tests/test_r3_contract.py -k f04_f10"),
    ("M04", "F05 disjoint partial branches never own a joint condition", "vme/style/authoring.py",
     "            elif not authority.invariance(did, k):\n                return False", "            elif False:\n                return False",
     "tests/test_r3_contract.py -k f05_disjoint"),
    ("M05", "F05 conflicting equally applicable branches refused", "vme/style/authoring.py",
     "        if key in seen_keys and seen_keys[key] != b.get(\"construction_action\", \"\"):", "        if False:",
     "tests/test_r3_contract.py -k f05_conflicting"),
    ("M06", "F08 unknown reference policy blocks", "vme/style/authoring.py",
     "        return {\"mode\": \"UNKNOWN\"}, \"REFERENCE_POLICY_UNKNOWN\"", "        return {\"mode\": \"NOT_APPLICABLE\", \"reason\": \"mutant\"}, None",
     "tests/test_r3_contract.py -k f08_missing"),
    ("M07", "F14 audio decision requires a local source-audio witness", "vme/style/authoring.py",
     "        if not studied or not any(w.get(\"evidence_kind\") == \"AUDIO_SIGNAL\" for w in wrecs):", "        if False:",
     "tests/test_r3_contract.py -k f14_audio_decision"),
    ("M08", "F11/A29 character rule requires a validated source-first dossier", "vme/style/authoring.py",
     "        if not ok:                                   # Addendum 29", "        if False:                                   # Addendum 29",
     "tests/test_r3_contract.py -k f11_character_rule"),
    ("M09", "F11/A29 generic anatomy cannot substitute for the drawn form", "vme/style/source_ledger.py",
     "            if _GENERIC_ANATOMY.search(rel) or _GENERIC_ANATOMY.search(imp):", "            if False:",
     "tests/test_r3_contract.py -k f11_a29"),
    ("M10", "F11 open character state keeps the scene in NEEDS_SOURCE_REINSPECTION", "vme/style/source_ledger.py",
     "            elif dossier_open_fields(d):", "            elif False:", "tests/test_r3_contract.py -k f11_filled"),
    ("M11", "F01 relationless/generic frame record never validated", "vme/vision/contracts.py",
     "        if not relations and not facts:\n            problems.append(f\"NO_TYPED_SOURCE_VISUAL_FACTS",
     "        if False:\n            problems.append(f\"NO_TYPED_SOURCE_VISUAL_FACTS", "tests/test_r3_contract.py -k f01_generic"),
    ("M12", "F01 weak artistic observations block the packet", "vme/vision/contracts.py",
     "    if weak:\n        problems.append(f\"ARTISTIC_FRAME_OBSERVATIONS_INSUFFICIENT", "    if False:\n        problems.append(f\"ARTISTIC_FRAME_OBSERVATIONS_INSUFFICIENT",
     "tests/test_r3_contract.py -k f01"),
    ("M13", "F02 lost boundary identity fails", "vme/vision/contracts.py",
     "            if lost:\n                problems.append(f\"BOUNDARY_IDENTITY_NOT_RECONCILED", "            if False:\n                problems.append(f\"BOUNDARY_IDENTITY_NOT_RECONCILED",
     "tests/test_r3_contract.py -k f02"),
    ("M14", "F07 stale semantic commit refused", "vme/vision/runner.py",
     "            if (saved_.get(\"request\") or {}).get(\"request_sha\") != current_[\"request_sha\"]:", "            if False:",
     "tests/test_r3_contract.py -k f07_request_identity"),
    ("M15", "F06/F09 source request without verified manifest refused", "vme/vision/claude_adapter.py",
     "        if manifest is None:\n            raise Blocked(\"SOURCE_REQUEST_WITHOUT_VERIFIED_MANIFEST\"",
     "        if False:\n            raise Blocked(\"SOURCE_REQUEST_WITHOUT_VERIFIED_MANIFEST\"",
     "tests/test_provider_contracts.py -k without_verified_manifest"),
    ("M16", "F06 sent bytes must equal the verified byte manifest", "vme/vision/claude_adapter.py",
     "        if [sha256_bytes(b) for _, b, _, _ in labelled_images] != [m[\"image_bytes_sha256\"] for m in manifest[\"byte_manifest\"]]:",
     "        if False:", "tests/test_provider_contracts.py tests/test_r3_contract.py -k \"manifest or f06 or f09\""),
    ("M17", "F12 state drawn from another actor's canonical refused", "vme/loop/real.py",
     "                if stt.get(\"identity_source_sha256\") != canon[\"sha256\"]:", "                if False:", "tests/test_r3_contract.py -k f12"),
    ("M18", "F13 no default motion when the owner is missing", "vme/render/motion_program.py",
     "    if not hits:\n        raise Blocked(\"MOTION_TRACK_UNOWNED\"",
     "    if not hits:\n        return {\"decision_id\": \"DEFAULT\"}, {\"when\": {}, \"co_owner_decision_ids\": [], "
     "\"motion_program\": {\"method\": \"EASE_IN_OUT\", \"track_kind\": track}}\n        raise Blocked(\"MOTION_TRACK_UNOWNED\"",
     "tests/test_r3_contract.py -k f13"),
    ("M19", "F13/F05 disagreeing motion owners refused (never list order)", "vme/render/motion_program.py",
     "    if len(progs) > 1:", "    if False:", "tests/test_r3_contract.py -k f13_conflicting"),
    ("M20", "F15 technical render failure is fatal", "vme/render/renderer.py",
     "    if not verify.get(\"ok\"):", "    if False:", "tests/test_r3_contract.py -k f15"),
    ("M21", "F14/S2 audio onset needs a full-frame parent", "vme/investigation/evidence.py",
     "            if not parent or parent.evidence_kind not in (\"FULL_FRAME\", \"SYNTHETIC_FIXTURE\"):\n                problems.append(f\"AUDIO_WITHOUT",
     "            if False:\n                problems.append(f\"AUDIO_WITHOUT", "tests/test_r3_contract.py -k f14_audio_witness"),
    ("M22", "F14/S2 audio parent must be same film and ±1 frame", "vme/investigation/evidence.py",
     "            elif parent.film_sha256 != w.film_sha256 or abs(parent.frame_start - w.frame_start) > 1:", "            elif False:",
     "tests/test_r3_contract.py -k f14_audio_witness"),
    ("M23", "F14/S2 local-signal observer cannot vouch for visual evidence", "vme/investigation/evidence.py",
     "        if w.observer == \"LOCAL_SIGNAL_ANALYSIS\" and w.evidence_kind != \"AUDIO_SIGNAL\":", "        if False:",
     "tests/test_r3_contract.py -k f14_audio_witness"),
    ("M24", "F18 truncated packet is split, never silently dropped", "vme/loop/real.py",
     "            if not trunc:\n                break", "            if True:\n                break", "tests/test_r3_contract.py -k f18"),
    ("M25", "Authority records need a human signer", "vme/state/authority.py",
     "    if not isinstance(by, str) or by.strip().lower() in _NON_HUMAN:", "    if False:", "tests/test_r3_contract.py -k f05_disjoint"),
    ("M26", "F17 still-only held-out never qualifies motion/AV", "vme/review/qualification.py",
     "\"HELDOUT_TRANSFER\": \"BLOCKED:STILL_ONLY_TRANSFER", "\"HELDOUT_TRANSFER\": \"QUALIFIED\" or \"BLOCKED:STILL_ONLY_TRANSFER",
     "tests/test_r3_contract.py -k f17"),
    ("M27", "F12 per-actor job excludes ONLY decisions owned solely by other actors", "vme/compiler/compiler.py",
     "return bool(owned) and all(x.split(\":\", 1)[0] in others for x in owned)",
     "return bool(owned) and any(x.split(\":\", 1)[0] in others for x in owned)", "CANARY:tests/test_r3_canary.py -k recompile"),
    ("M28", "F12 gateway recompile keeps the actor scope", "vme/compiler/compiler.py",
     "                     actor_scope=i.get(\"actor_scope\"))", "                     actor_scope=None)", "CANARY:tests/test_r3_canary.py -k recompile"),
]


def _copy_repo(dst: Path) -> None:
    for name in ("vme", "tests", "config"):
        if (REPO / name).exists():
            shutil.copytree(REPO / name, dst / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))
    for f in ("pyproject.toml", "pytest.ini", "setup.cfg", "conftest.py", "requirements.lock"):
        if (REPO / f).exists():
            shutil.copy2(REPO / f, dst / f)
    rem = REPO / "render" / "remotion"                  # renderer project (code only; node_modules is linked, never copied)
    if rem.exists():
        shutil.copytree(rem, dst / "render" / "remotion", ignore=shutil.ignore_patterns("node_modules", "public", "public_jobs", "out"))
        nm = rem / "node_modules"
        if nm.exists():
            link = dst / "render" / "remotion" / "node_modules"
            try:
                os.symlink(nm, link, target_is_directory=True)
            except OSError:
                subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(nm)], capture_output=True)


def _run(copy: Path, selector: str, env: dict, timeout: int) -> tuple[int, str]:
    args = [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *_split(selector)]
    p = subprocess.run(args, cwd=copy, env=env, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr)[-1500:]


def _split(sel: str) -> list[str]:
    import shlex
    return shlex.split(sel, posix=True)


def run(out: Path, only: list[str] | None = None, canary_root: str | None = None, timeout: int = 900) -> dict:
    rows = []
    td = tempfile.mkdtemp(prefix="vme_mut_")
    try:
        base = Path(td) / "repo"
        _copy_repo(base)
        env = {**os.environ, "PYTHONPATH": str(base), "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("VME_ALLOW_NETWORK", None)
        if canary_root:
            env["VME_CANARY_REUSE_ROOT"] = canary_root
        probe = subprocess.run([sys.executable, "-c", "import vme,sys;print(vme.__file__)"], cwd=base, env=env, capture_output=True, text=True)
        if str(base).lower() not in probe.stdout.lower():
            raise SystemExit(f"mutation copy is not the imported package: {probe.stdout} {probe.stderr}")
        for mid, guard, rel, old, new, sel in MUTATIONS:
            if only and mid not in only:
                continue
            needs_canary = sel.startswith("CANARY:")
            sel = sel.split(":", 1)[1] if needs_canary else sel
            row: dict = {"id": mid, "guard": guard, "file": rel, "selector": sel}
            if needs_canary and not canary_root:
                rows.append({**row, "result": "NOT_RUN", "why": "needs --canary-root (a driven two-actor canary workspace)"})
                continue
            src = (base / rel).read_text(encoding="utf-8")
            n = src.count(old)
            if n != 1:
                rows.append({**row, "result": "ANCHOR_NOT_FOUND", "matches": n})
                continue
            t0 = time.time()
            rc0, _ = _run(base, sel, env, timeout)                          # the selector must PASS on the unmutated copy
            if rc0 != 0:
                rows.append({**row, "result": "BASELINE_FAILS", "baseline_rc": rc0})
                continue
            (base / rel).write_text(src.replace(old, new), encoding="utf-8")
            try:
                rc, tail = _run(base, sel, env, timeout)
            except subprocess.TimeoutExpired:
                rc, tail = -9, "TIMEOUT"
            finally:
                (base / rel).write_text(src, encoding="utf-8")
            rows.append({**row, "result": "KILLED" if rc != 0 else "SURVIVED", "mutant_rc": rc, "seconds": round(time.time() - t0, 1),
                         "failing_output_tail": tail[-600:] if rc != 0 else None})
            print(mid, rows[-1]["result"], flush=True)
    finally:
        link = Path(td) / "repo" / "render" / "remotion" / "node_modules"   # detach the link BEFORE cleanup (never recurse into it)
        if link.is_symlink() or (hasattr(os.path, "isjunction") and os.path.isjunction(link)):
            try:
                link.unlink()
            except OSError:
                os.rmdir(link)
        if not link.exists():
            shutil.rmtree(td, ignore_errors=True)
    summary = {k: sum(1 for r in rows if r["result"] == k) for k in ("KILLED", "SURVIVED", "ANCHOR_NOT_FOUND", "BASELINE_FAILS", "NOT_RUN")}
    res = {"suite": "R3_MUTATIONS", "python": sys.version.split()[0], "repo": str(REPO), "rows": rows, "summary": summary,
           "note": "each mutant weakens exactly one guard in a temporary copy; KILLED = the targeted tests failed against the mutant"}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "reports" / "R3_MUTATION_RESULTS.json"))
    ap.add_argument("--only", default="")
    ap.add_argument("--canary-root", default=None)
    a = ap.parse_args()
    r = run(Path(a.out), [x for x in a.only.split(",") if x] or None, a.canary_root)
    print(json.dumps(r["summary"]))
