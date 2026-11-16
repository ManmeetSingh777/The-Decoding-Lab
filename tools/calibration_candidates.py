"""Bounded real-source calibration — LOCAL candidate shortlist (no frame is viewed, uploaded or sent anywhere).

Ranks ~10-second contiguous windows of the BASE films (the locked sixth special interval is excluded) using only local signals:
the shot-cut candidates of the local FilmSurvey (a world/camera transition must exist but the window must not be a montage) and the
local audio envelope (continuous narration over the window, onsets). Writes workspace/calibration/CANDIDATES.json. Choosing the
interval to inspect, and authorising its frames to be viewed by a vision model, remain human decisions.

    python tools/calibration_candidates.py [--seconds 10] [--top 6]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vme.reference.audio import SR, _pcm, envelope, onsets  # noqa: E402
from vme.reference.frame_index import read_index  # noqa: E402
from vme.state.workspace import Workspace  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--workspace", default=str(ROOT / "workspace"))
    a = ap.parse_args()
    ws = Workspace(Path(a.workspace))
    st = ws.store()
    lock = json.loads((ws.state_dir / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
    folder = next((p for p in [Path(lock["folder"])] + [(b / lock["folder"]).resolve() for b in (ROOT, ws.root, ROOT.parent)]
                   if p.is_dir() and (p / lock["sources"][0]["relative_path"]).exists()), None)
    if folder is None:
        raise SystemExit(f"SOURCE_ASSET_MISSING: cannot find {lock['folder']}")
    from vme.util import sha256_file
    for s in lock["sources"]:
        if s["sha256"] != sha256_file(folder / s["relative_path"]):
            raise SystemExit(f"SOURCE_IDENTITY_CHANGED: {s['file_name']}")
    roles = {r["sha256"]: r.get("role") for r in st.list("SourceLock")}
    out = []
    for s in lock["sources"]:
        if roles.get(s["sha256"]) == "SIXTH_SPECIAL" or "1200 Hours" in s["file_name"]:
            continue
        sv = st.get("FilmSurvey", s["sha256"]) or {}
        idx = read_index(ws.frames_dir / s["sha256"] / "index.jsonl.gz")
        dur = idx[-1]["pts_time"]
        cuts = [(int(x["start_frame_index"]), float(x["start_pts_time"]), float(x.get("entry_change_score", 0))) for x in sv.get("shots", [])[1:]]
        video = folder / s["relative_path"]
        for k, t, score in cuts:
            t0, t1 = t - 0.4 * a.seconds, t + 0.6 * a.seconds
            if t0 < 30 or t1 > dur - 30:                                   # skip intros / end cards
                continue
            inside = [c for c in cuts if t0 <= c[1] <= t1]
            if not 1 <= len(inside) <= 3:                                  # a transition, but not a montage
                continue
            pcm = _pcm(video, t0, t1 - t0)
            env = envelope(pcm, 30.0) if pcm is not None else None
            if env is None or env.size == 0:
                continue
            voiced = float((env > 0.02).mean())
            ons = onsets(env)
            longest_static = max((b[1] - a_[1] for a_, b in zip([(0, t0)] + [(0, c[1]) for c in inside], [(0, c[1]) for c in inside] + [(0, t1)])), default=0)
            score_ = round(voiced * 2 + min(len(ons), 12) / 12 + (1 if longest_static >= 4 else 0), 3)
            fr = [i for i, r in enumerate(idx) if t0 <= r["pts_time"] <= t1]
            out.append({"film": s["file_name"], "film_sha256": s["sha256"], "start_pts": round(t0, 6), "end_pts": round(t1, 6),
                        "frames": [fr[0], fr[-1]], "frame_count": len(fr), "shot_cuts_inside": [{"frame": c[0], "pts": c[1], "change": c[2]} for c in inside],
                        "narration_voiced_fraction": round(voiced, 3), "audio_onsets": len(ons), "longest_single_shot_s": round(longest_static, 2),
                        "local_score": score_, "what_this_does_NOT_know": "the artistic content: nobody has looked at these frames yet"})
    out.sort(key=lambda x: -x["local_score"])
    seen, top = set(), []
    for c in out:
        key = (c["film_sha256"], int(c["start_pts"] // 30))
        if key in seen:
            continue
        seen.add(key)
        top.append(c)
        if len(top) >= a.top:
            break
    dst = ws.root / "calibration" / "CANDIDATES.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps({"seconds": a.seconds, "sample_rate": SR, "candidates": top, "excluded": "the locked sixth special interval",
                               "privacy": "local signals only; no frame viewed or transmitted"}, indent=1), encoding="utf-8")
    for c in top:
        print(f"{c['local_score']:5.2f}  {c['film'][:46]:46s} {c['start_pts']:8.2f}-{c['end_pts']:8.2f}s frames {c['frames']} "
              f"cuts={len(c['shot_cuts_inside'])} voiced={c['narration_voiced_fraction']} onsets={c['audio_onsets']} shot={c['longest_single_shot_s']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
