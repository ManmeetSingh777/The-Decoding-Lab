"""Zero-cost LOCAL operations on the user's real source films (no upload, no vision model).

Sixth clip: candidate boundaries from local scene cuts + a witness packet of decoded frames saved
locally for HUMAN review. The agent does not view or upload these frames; the human decides.
"""
from __future__ import annotations

from pathlib import Path

from ..util import Blocked, atomic_write_bytes, atomic_write_json, digest, read_json
from ..state.workspace import Workspace
from ..selection.sixth import locate_sixth_intro
from .frame_index import read_index
from .frames import retrieve_frame


def run_real_sixth_locator(ws: Workspace, *, window_s: tuple = (0.0, 240.0)) -> dict:
    lock = read_json(ws.state_dir / "SOURCE_LOCK.json")
    six = [s for s in lock["sources"] if s["role"] == "SIXTH_SPECIAL"]
    st = ws.store()
    try:
        if not six:
            res = locate_sixth_intro(None, None, None).to_dict()
            st.put("SixthIntroLocatorResult", "REAL", res)
            return res
        s = six[0]
        clip = Path(lock["folder"]) / s["relative_path"]
        idx = read_index(ws.frames_dir / s["sha256"] / "index.jsonl.gz")
        sv = st.get("FilmSurvey", s["sha256"])
        if not sv:
            raise Blocked("NO_SURVEY_FOR_SIXTH", "run vme survey build first")
        cuts = [sh["start_frame_index"] for sh in sv["shots"]][1:]
        # The opening may use dissolves/zooms rather than hard cuts: add a more sensitive LOCAL pass for
        # candidate boundaries in the search window (still navigation-only; a human decides).
        from .survey import detect_scene_changes
        import bisect
        times = [r["pts_time"] for r in idx]
        for t, _score in detect_scene_changes(clip, threshold=0.12):
            if window_s[0] <= t <= window_s[1]:
                k = bisect.bisect_left(times, t - 1e-6)
                if 0 < k < len(idx) and k not in cuts:
                    cuts.append(k)
        cuts = sorted(set(cuts))
        res = locate_sixth_intro(clip, s["sha256"], idx, cut_frames=cuts, classifier=None, classifier_kind="NONE",
                                 search_window_s=window_s).to_dict()
        wdir = ws.frames_dir / s["sha256"] / "sixth_witness_packet"
        saved = []
        for w in res["witness_packet"]:
            fr = retrieve_frame(clip, idx[w["frame_index"]])
            p = wdir / f"f{w['frame_index']:06d}_{w['role']}.png"
            atomic_write_bytes(p, fr.png_bytes)
            saved.append({**w, "path": str(p), "png_sha256": fr.png_sha256, "pts_time": fr.pts_time, "raw_identity_verified": fr.identity_verified})
        res["witness_packet_files"] = saved
        res["witness_packet_sha"] = digest(res["witness_packet"])
        res["role_basis"] = s["basis"]
        res["viewed_by_agent_or_uploaded"] = False
        res["human_next_step"] = ("Open the PNGs in frames/<sha>/sixth_witness_packet/, pick the first frame where the volcano scene "
                                  "dominates and the first frame where the brand Earth logo has entered, then run: vme selection sixth-lock "
                                  "--start <idx> --end <idx> --confirmed-by <your name> --witness-sha " + res["witness_packet_sha"])
        st.put("SixthIntroLocatorResult", "REAL", res)
        atomic_write_json(ws.state_dir / "SIXTH_LOCATOR_STATUS.json", res)
        return res
    finally:
        st.close()
