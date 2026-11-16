"""Bounded real-source calibration — LOCAL preparation of one contiguous interval (nothing is viewed, uploaded or sent).

Writes, under workspace/calibration/<film12>_<start>_<end>/ (git-ignored, never committed or zipped):
  frames/                       every NATIVE frame of the interval (exact presentation index + PTS in the filename)
  FRAME_MANIFEST.json           per frame: frame_id, index, pts, raw-frame SHA (index identity), PNG SHA, native=true
  CONTACT_SHEET_NAVIGATION_ONLY.png   downscaled mosaic for navigation — never evidence
  AUDIO_LOCAL.json              local envelope onsets mapped to frames by native PTS (meaning NOT inferred)
  CALIBRATION_STATE.json        status AWAITING_AUTHORIZED_SOURCE_TRANSFER until a human authorises viewing by a named model

    python tools/calibration_prepare.py --film <sha256> --start <pts> --end <pts> [--every 1]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vme.reference.audio import study_interval  # noqa: E402
from vme.reference.frame_index import read_index  # noqa: E402
from vme.reference.frames import FrameCache  # noqa: E402
from vme.reference.navigator import inspect_range  # noqa: E402
from vme.state.workspace import Workspace  # noqa: E402
from vme.util import now_iso, sha256_file  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", required=True)
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--every", type=int, default=1, help="1 = every native frame")
    ap.add_argument("--workspace", default=str(ROOT / "workspace"))
    a = ap.parse_args()
    if not 7.5 <= a.end - a.start <= 12.5:
        raise SystemExit("CALIBRATION_INTERVAL_OUT_OF_BOUNDS: the bounded calibration is ~8-12 s")
    ws = Workspace(Path(a.workspace))
    lock = json.loads((ws.state_dir / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
    s = next((x for x in lock["sources"] if x["sha256"] == a.film), None)
    if s is None:
        raise SystemExit("SOURCE_ASSET_MISSING: film sha not in SOURCE_LOCK")
    folder = next((p for p in [(b / lock["folder"]).resolve() for b in (ROOT, ws.root, ROOT.parent)] if (p / s["relative_path"]).exists()), None)
    if folder is None or sha256_file(folder / s["relative_path"]) != s["sha256"]:
        raise SystemExit("SOURCE_ASSET_MISSING_OR_CHANGED")
    video = folder / s["relative_path"]
    idx = read_index(ws.frames_dir / s["sha256"] / "index.jsonl.gz")
    out = ws.root / "calibration" / f"{s['sha256'][:12]}_{a.start:.2f}_{a.end:.2f}"
    r = inspect_range(film_sha=s["sha256"], index=idx, cache=FrameCache(video, idx), start_pts=a.start, end_pts=a.end,
                      purpose="bounded real-source calibration interval (local preparation only)",
                      granularity="every_frame" if a.every == 1 else "every_nth", nth=a.every,
                      contact_sheet_to=out / "CONTACT_SHEET_NAVIGATION_ONLY.png", write_frames_to=out / "frames")
    (out / "FRAME_MANIFEST.json").write_text(json.dumps({**r, "video_file": s["file_name"]}, indent=1), encoding="utf-8")
    ks = [f["frame_index"] for f in r["frames"]]
    d = sorted(idx[k + 1]["pts_time"] - idx[k]["pts_time"] for k in ks[:-1]) or [1 / 30]
    au = study_interval(video, start_pts=idx[ks[0]]["pts_time"], end_pts=idx[ks[-1]]["pts_time"], fps=1.0 / d[len(d) // 2],
                        film_sha256=s["sha256"], sequence_id="CALIBRATION")
    t0 = idx[ks[0]]["pts_time"]
    au["onset_frame_indices"] = sorted({min(ks, key=lambda k: abs(idx[k]["pts_time"] - (t0 + t))) for t in au.get("onset_times_s", [])})
    (out / "AUDIO_LOCAL.json").write_text(json.dumps(au, indent=1, default=str), encoding="utf-8")
    state = {"status": "AWAITING_AUTHORIZED_SOURCE_TRANSFER", "film": s["file_name"], "film_sha256": s["sha256"],
             "interval_pts": [a.start, a.end], "frames": [ks[0], ks[-1]], "frame_count": len(ks), "prepared_at": now_iso(),
             "transferred": [], "note": "no frame of this interval has been shown to any model; viewing requires explicit human authorisation "
                                        "naming the model/session and this exact interval"}
    (out / "CALIBRATION_STATE.json").write_text(json.dumps(state, indent=1), encoding="utf-8")
    print(json.dumps({"folder": str(out), "frames": len(ks), "first": r["frames"][0]["frame_id"], "last": r["frames"][-1]["frame_id"],
                      "audio_onsets": len(au.get("onset_frame_indices", [])), "status": state["status"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
