# Source role confirmation report (human action required)

Generated 2026-11-14T23:57:35+00:00. Identity = SHA256 of the bytes on disk; files were not renamed, modified or re-indexed.

| File | SHA256 (12) | Resolution | Frames source | Current role | Basis | Confirmed by |
|---|---|---|---|---|---|---|
| A.I. ‐ Humanity's Final Invention_.mp4 | `d283e67b6e32` | 1280x720 | 60/1 fps | BASE_FILM | DEFAULT_NON_SIXTH | — |
| AI Just Crossed the Terrifying Line - Now What_.mp4 | `584dbc4c52ee` | 1280x720 | 60/1 fps | BASE_FILM | DEFAULT_NON_SIXTH | — |
| GERMANY IS OVER.mp4 | `027407606650` | 1280x720 | 60/1 fps | BASE_FILM | DEFAULT_NON_SIXTH | — |
| How to Make a Kurzgesagt Video in 1200 Hours.mp4 | `2a54f0de183c` | 1280x720 | 30/1 fps | SIXTH_SPECIAL | USER_CONFIRMED | USER (chat 2026-11-15) |
| The Most Insane Megaproject You Never Heard About.mp4 | `1fec93ec7fcf` | 1280x720 | 30/1 fps | BASE_FILM | DEFAULT_NON_SIXTH | — |
| You're More Stressed Than Ever - Let's Change That.mp4 | `a3e410bad3a5` | 1280x720 | 60/1 fps | BASE_FILM | DEFAULT_NON_SIXTH | — |

## Mismatch with the contract

01_IMPLEMENTATION_CONTRACT.md §0.3 names: A.I. – Humanity's Final Invention; How Are Memories Stored Inside Your Brain; Why Your Brain Blinds You; How Nuclear Flies Protect You; Why Humanity Will Never Leave Solar System.
Only the first title has a matching file here. The other four BASE_FILM files are different videos and are **UNCONFIRMED**:
they are quarantined from study until you confirm them (or supply the intended films).

## Resolution

All six local files are **1280×720**. Native-detail claims are limited to 720p pixels. If 1080p originals exist, supply them; they would be NEW sources (new SHA256, new index) — the existing 720p indexes stay as they are.

## Sixth clip

Role: confirmed by the user in chat on 2026-11-15 ("the sixth clip is the Kurzgesagt 1200 Hours video").
Volcano-start / Earth-logo boundaries: **UNCONFIRMED** (locator status `CANDIDATE_BOUNDARIES_AWAITING_HUMAN_REVIEW`). They must be chosen from actually viewed frames: open the local witness packet PNGs and run `vme selection sixth-lock --start N --end M --confirmed-by NAME --witness-sha 7af1fa12e067dcbdd15b293563dd59ef7c1e0c6cbbc5d1578e1971bc074333c8`.

## Commands to confirm

```bash
python -m vme sources confirm-role --sha <sha256> --role BASE_FILM --by "<your name>"
```
