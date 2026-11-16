"""Shared fixtures + a plugin that records which requirement IDs each test exercises and its REAL outcome.

`@pytest.mark.req("A01", "C01", phase="OFFLINE")` — phase PAID/ART marks tests that prove the system
correctly REFUSES/BLOCKS work which can only be positively demonstrated after authorization; the
requirement matrix reports those requirements as BLOCKED (with the refusal evidence), never PASS.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RESULTS: list[dict] = []


def pytest_configure(config):
    config.addinivalue_line("markers", "req(*ids, phase='OFFLINE'): requirement ids covered by the test")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    out = yield
    rep = out.get_result()
    if rep.when == "call" or (rep.when == "setup" and rep.outcome != "passed"):
        m = item.get_closest_marker("req")
        RESULTS.append({"nodeid": item.nodeid, "outcome": rep.outcome, "when": rep.when,
                        "req_ids": list(m.args) if m else [], "phase": (m.kwargs.get("phase", "OFFLINE") if m else "OFFLINE"),
                        "path": (m.kwargs.get("path", "ENGINEERING") if m else "ENGINEERING"),
                        "duration_s": round(rep.duration, 3),
                        "longrepr": (str(rep.longrepr)[-1500:] if rep.failed else None)})


def pytest_sessionfinish(session, exitstatus):
    out = Path(os.environ.get("VME_TEST_RESULTS", ROOT / "reports" / "test_results_raw.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"exitstatus": int(exitstatus), "results": RESULTS}, indent=1), encoding="utf-8")


@pytest.fixture
def ws(tmp_path):
    from vme.state.workspace import Workspace
    return Workspace(tmp_path / "ws").ensure()


@pytest.fixture
def store(ws):
    s = ws.store()
    yield s
    s.close()


@pytest.fixture
def skill(tmp_path):
    from vme.fixtures.synthetic import build_synthetic_skill
    folder = tmp_path / "skill"
    h = build_synthetic_skill(folder)
    return folder, h


@pytest.fixture
def caps():
    from vme.fixtures.synthetic import fixture_caps
    return fixture_caps()


@pytest.fixture
def brief():
    from vme.fixtures.synthetic import synthetic_brief
    return synthetic_brief()


@pytest.fixture(scope="session")
def clip24(tmp_path_factory):
    from vme.fixtures.synthetic import make_clip
    return make_clip(tmp_path_factory.mktemp("clip") / "c24.mp4", frames=24)


@pytest.fixture(scope="session")
def indexed24(clip24, tmp_path_factory):
    from vme.fixtures.loop_fixtures import index_and_loader
    idx, loader = index_and_loader(clip24, tmp_path_factory.mktemp("idx24"))
    return clip24, idx, loader


def compile_job(skill, brief, caps, node="n1_scene", **kw):
    from vme.compiler.compiler import StyleProgramCompiler
    folder, h = skill
    return StyleProgramCompiler().compile(brief, folder, pinned_skill_hash=h, recipe_id="character_world", node_id=node, caps=caps, **kw)


def offline_gateway(store, tmp_path, caps, mode="ok", queryable=True):
    from vme.providers.gateway import StyleImageGateway, OfflineRecordingTransport
    from vme.providers.runware import RunwareAdapter
    from vme.providers.authorization import AuthorizationRegistry
    t = OfflineRecordingTransport(tmp_path / f"rt_{mode}", mode=mode, queryable=queryable)
    return StyleImageGateway(store, tmp_path / "art", RunwareAdapter(caps, t, kind="OFFLINE_RECORDING"),
                             AuthorizationRegistry(tmp_path / "authz")), t
