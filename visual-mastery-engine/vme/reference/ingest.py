"""`vme sources ingest/probe/index`: register exact source bytes, roles and full-frame index."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..state.workspace import Workspace
from ..util import Blocked, atomic_write_json, read_json, now_iso, sha256_file
from .frame_index import index_every_frame
from .probe import discover_sources, probe_source, make_read_only

# Titles named in 01 §0.3 (an earlier collection). The user's actual files are matched by bytes;
# a mismatch is reported, never silently "corrected".
CONTRACT_EXPECTED_TITLES = (
    "AI Humanity's Final Invention", "How Are Memories Stored Inside Your Brain", "Why Your Brain Blinds You",
    "How Nuclear Flies Protect You", "Why Humanity Will Never Leave Solar System",
)
SIXTH_DURATION_WINDOW_S = (300.0, 480.0)  # "approximately six minutes" (Addendum 26 §2)


def propose_roles(probes: list[dict], user_roles: dict | None = None) -> dict:
    """Return {sha: {role, basis}}. User mapping always wins; heuristics are labelled as proposals."""
    roles: dict = {}
    if user_roles:
        for p in probes:
            r = user_roles.get(p["sha256"]) or user_roles.get(p["file_name"])
            if r:
                roles[p["sha256"]] = {"role": r, "basis": "USER_MAPPING"}
    unassigned = [p for p in probes if p["sha256"] not in roles]
    if not any(v["role"] == "SIXTH_SPECIAL" for v in roles.values()):
        lo, hi = SIXTH_DURATION_WINDOW_S
        six = [p for p in unassigned if p.get("format_duration_s") and lo <= p["format_duration_s"] <= hi]
        if len(six) == 1:
            roles[six[0]["sha256"]] = {"role": "SIXTH_SPECIAL",
                                       "basis": "PROPOSED_BY_DURATION_PENDING_USER_CONFIRMATION"}
            unassigned = [p for p in unassigned if p is not six[0]]
    for p in unassigned:
        roles[p["sha256"]] = {"role": "BASE_FILM", "basis": "DEFAULT_NON_SIXTH"}
    base = [s for s, r in roles.items() if r["role"] == "BASE_FILM"]
    sixth = [s for s, r in roles.items() if r["role"] == "SIXTH_SPECIAL"]
    return {"roles": roles, "base_count": len(base), "sixth_count": len(sixth),
            "base_five_ok": len(base) == 5,
            "sixth_status": "SIXTH_SOURCE_PRESENT" if len(sixth) == 1 else (
                "SIXTH_SOURCE_NOT_AVAILABLE" if not sixth else "SIXTH_SOURCE_AMBIGUOUS")}


def ingest(ws: Workspace, folder: str | Path, *, user_roles: dict | None = None) -> dict:
    files = discover_sources(folder)
    if not files:
        raise Blocked("SOURCE_ACCESS", f"no videos in {folder}")
    probes = []
    for f in files:
        p = probe_source(f).to_dict()
        p["read_only_after_ingest"] = make_read_only(f)
        probes.append(p)
    shas = [p["sha256"] for p in probes]
    if len(set(shas)) != len(shas):
        raise Blocked("DUPLICATE_SOURCE_BYTES", "two files share identical bytes")
    if user_roles is None and (ws.root / "config" / "source_roles.json").exists():
        user_roles = read_json(ws.root / "config" / "source_roles.json")
    role_info = propose_roles(probes, user_roles)
    titles = [p["file_name"].rsplit(".", 1)[0] for p in probes]
    expected_matched = [t for t in CONTRACT_EXPECTED_TITLES if any(t.lower()[:18] in x.lower().replace("‐", "-").replace(".", "") for x in titles)]
    lock = {
        "schema": "vme.source_lock/1", "locked_at": now_iso(), "folder": str(Path(folder)),
        "sources": [{**{k: p[k] for k in ("file_name", "sha256", "size_bytes", "width", "height", "r_frame_rate",
                                          "avg_frame_rate", "time_base", "start_pts", "format_duration_s",
                                          "stream_duration_s", "metadata_nb_frames", "audio_streams", "codec",
                                          "rotation", "vfr_suspected")},
                     "relative_path": Path(p["path"]).name, **role_info["roles"][p["sha256"]]} for p in probes],
        "base_five_ok": role_info["base_five_ok"], "sixth_status": role_info["sixth_status"],
        "contract_expected_titles_found": expected_matched,
        "contract_title_note": ("01 §0.3 names an earlier five-title collection; the user's supplied files differ in "
                                "title. Identity is by SHA256 of the supplied bytes; roles need user confirmation."),
    }
    atomic_write_json(ws.state_dir / "SOURCE_LOCK.json", lock)
    st = ws.store()
    try:
        for s in lock["sources"]:
            st.put("SourceLock", s["sha256"], s)
        st.event("SOURCES_INGESTED", None, {"count": len(probes), "sixth_status": lock["sixth_status"]})
    finally:
        st.close()
    return lock


def index_all(ws: Workspace, folder: str | Path, *, workers: int = 6) -> list[dict]:
    lock = read_json(ws.state_dir / "SOURCE_LOCK.json")
    folder = Path(folder)

    def _one(src: dict) -> dict:
        path = folder / src["relative_path"]
        if sha256_file(path) != src["sha256"]:
            raise Blocked("SOURCE_HASH_MISMATCH", src["file_name"])
        s = index_every_frame(path, src["sha256"], ws.frames_dir / src["sha256"], width=src["width"],
                              height=src["height"], stream_duration_s=src["stream_duration_s"],
                              metadata_nb_frames=src["metadata_nb_frames"])
        return {**s.to_dict(), "file_name": src["file_name"], "role": src["role"]}

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        results = list(ex.map(_one, lock["sources"]))
    st = ws.store()
    try:
        for r in results:
            st.put("FrameIndexSummary", r["film_sha256"], {k: v for k, v in r.items() if k != "pts_discontinuities"})
        st.event("FRAMES_INDEXED", None, {"films": len(results), "total": sum(r["frame_count_decoded"] for r in results)})
    finally:
        st.close()
    atomic_write_json(ws.state_dir / "FRAME_INDEX_SUMMARY.json", {
        "indexed_at": now_iso(), "films": [{k: v for k, v in r.items() if k not in ("pts_discontinuities", "duplicate_pts")} for r in results],
        "total_frames_decoded": sum(r["frame_count_decoded"] for r in results),
        "base_five_total": sum(r["frame_count_decoded"] for r in results if r["role"] == "BASE_FILM"),
    })
    return results
