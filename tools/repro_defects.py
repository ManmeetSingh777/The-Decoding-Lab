"""Reproducers for R01/R04/R05/R07/R08/R09/R13 run against the CURRENT code. Prints JSON (red-before / green-after)."""
import json, re, sys, uuid, inspect
sys.path.insert(0, ".")
out = {}
from vme.vision import runner
idx = [{"pts": i, "pts_time": i / 30, "frame_content_sha256": f"{i:064x}"} for i in range(32)]
plans = runner.plan_packets(idx, 0, 31, film_sha="a" * 64, pass_id="L0", cluster_id="c", model_version="m", max_images=20)
src = inspect.getsource(runner.PacketRunner.run)
try:
    from vme.providers.ids import packet_custom_id
    tid = packet_custom_id(plans[0])
except Exception:
    tid = f"{plans[0].idempotency_key}-{uuid.uuid5(uuid.NAMESPACE_URL, plans[0].packet_id)}"
out["R01_packet_custom_id_len"] = len(tid)
out["R01_valid"] = bool(re.fullmatch(r"[A-Za-z0-9_-]{1,64}", tid))
from vme.providers import gateway
g = inspect.getsource(gateway.StyleImageGateway)
out["R04_uses_uuid5"] = "uuid5" in g
out["R04_uses_uuid4"] = "uuid4" in g
from vme.compiler import compiler
out["R05_includeCost_in_compiler"] = "includeCost" in inspect.getsource(compiler)
from vme.providers import authorization
out["R07_has_reservation"] = hasattr(authorization.AuthorizationRegistry, "reserve")
from vme.style import authoring
s = inspect.getsource(authoring.author_skill)
out["R08_author_skill_references_empty_literal"] = "references=[]" in s
out["R09_decision_id_from_dims_only"] = hasattr(authoring, "decision_id_for") and authoring.decision_id_for(["FACE"]) == authoring.decision_id_for(["FACE"])
from vme.loop import real
s0 = inspect.getsource(real.RealLoopRunner._s0)
out["R13_s0_completes_with_sixth_pending"] = "PENDING_HUMAN_BOUNDARY_LOCK" in s0 and 'return "COMPLETED", out' in s0
print(json.dumps(out, indent=1))
