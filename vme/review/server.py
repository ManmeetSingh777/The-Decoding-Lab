"""Local review gallery wired to real persistence (04, 01 §10 Local review UX, A18, C36).

GET /            → review page for a run (actual images from artifacts; synthetic clearly labelled)
POST /feedback   → atomic VisualReview record (verdict enum) in the store
POST /art-verdict, /asset-verdict → GateKeeper verdicts (human name required)
"""
from __future__ import annotations

import html
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from ..util import Blocked
from .approvals import GateKeeper, save_user_review, REVIEW_VERDICTS


def build_review_page(store, run_id: str, *, images: list[dict], packet: dict) -> str:
    gate = GateKeeper(store).state(run_id)
    syn = gate.get("synthetic") or any(i.get("label", "").startswith("OFFLINE") for i in images)
    banner = ("<div class=warn>SYNTHETIC / OFFLINE FIXTURE — NOT LEARNED ART. Wiring only.</div>" if syn else "")
    cards = "".join(f"<figure><img src='/img?p={html.escape(i['path'])}' alt=''><figcaption>{html.escape(i.get('caption',''))}"
                    f"<br><code>{i['sha256'][:16]}</code> {html.escape(i.get('label',''))}</figcaption></figure>" for i in images)
    rows = "".join(f"<tr><td>{html.escape(str(k))}</td><td><pre>{html.escape(json.dumps(v, indent=1)[:1500])}</pre></td></tr>"
                   for k, v in packet.items())
    opts = "".join(f"<option>{v}</option>" for v in REVIEW_VERDICTS)
    return f"""<!doctype html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>
<title>Visual Mastery Review</title><style>
:root{{--bg:#fff;--fg:#111;--mut:#666;--warn:#a40}}@media(prefers-color-scheme:dark){{:root{{--bg:#111;--fg:#eee;--mut:#aaa;--warn:#f96}}}}
body{{background:var(--bg);color:var(--fg);font:15px system-ui;margin:16px;max-width:1200px}}figure{{display:inline-block;margin:8px;max-width:46%}}
img{{max-width:100%}}.warn{{color:var(--warn);font-weight:700;border:2px solid var(--warn);padding:8px}}td{{vertical-align:top}}pre{{white-space:pre-wrap}}
</style></head><body><h1>Visual Mastery — Run {html.escape(run_id)}</h1>{banner}
<p>Gate state: <b>{html.escape(gate['state'])}</b></p><section>{cards}</section>
<h2>Which important visual qualities are still missing or wrong?</h2>
<form method=post action=/feedback><input type=hidden name=run_id value='{html.escape(run_id)}'>
<label>Verdict <select name=verdict>{opts}</select></label><br><label>Biggest remaining issues (one per line)<br>
<textarea name=gaps rows=5 cols=80></textarea></label><br><label>Preferred next visual focus <input name=focus size=60></label><br>
<label>Your name <input name=by required></label><br><button>Save review</button></form>
<h2>Evidence packet</h2><table>{rows}</table></body></html>"""


def serve(store, run_id: str, *, images: list[dict], packet: dict, port: int = 8765, once: bool = False):
    page = build_review_page(store, run_id, images=images, packet=packet)
    allowed = {i["path"] for i in images}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path.startswith("/img?p="):
                p = parse_qs(self.path.split("?", 1)[1]).get("p", [""])[0]
                if p not in allowed:
                    self.send_error(403)
                    return
                b = Path(p).read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.end_headers()
                self.wfile.write(b)
                return
            b = page.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            form = {k: v[0] for k, v in parse_qs(self.rfile.read(n).decode()).items()}
            try:
                if self.path == "/feedback":
                    r = save_user_review(store, run_id=form["run_id"], verdict=form["verdict"],
                                         top_remaining_gaps=[g for g in form.get("gaps", "").splitlines() if g.strip()],
                                         preferred_next_focus=form.get("focus", ""), submitted_by=form.get("by", ""),
                                         linked_image_hashes=[i["sha256"] for i in images])
                    body = json.dumps({"saved": r["review_id"]}).encode()
                    code = 200
                else:
                    body, code = b'{"error":"unknown"}', 404
            except (Blocked, KeyError) as e:
                body, code = json.dumps({"error": str(e)}).encode(), 400
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    if once:
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        return srv
    srv.serve_forever()
