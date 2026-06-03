"""Shared test harness.

- Isolates every test from the real data/store.json (temp store via OSFL_STORE_PATH).
- Forces the deterministic OFFLINE path (empty OPENAI_API_KEY) so the committed suite never
  hits the network; live-LLM behaviour is exercised separately. load_dotenv(override=False)
  respects the value we set here, so .env cannot re-enable the key during tests.
- Provides `client` (in-process FastAPI TestClient) and `base_url` (a real uvicorn subprocess
  for Playwright E2E).
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

import pytest

# MUST run before any `osfl` import so the module-level Store + LLM pick these up.
os.environ["OPENAI_API_KEY"] = ""  # force offline for the deterministic suite
# per-process store so concurrent `pytest` invocations (parallel agents) never share a file
_HARNESS_STORE = os.path.join(tempfile.gettempdir(), f"osfl_harness_{os.getpid()}.json")
os.environ["OSFL_STORE_PATH"] = _HARNESS_STORE


def pytest_configure(config):
    config.addinivalue_line("markers", "llm: hits the real OpenAI API; skipped unless --run-llm")


def pytest_addoption(parser):
    parser.addoption(
        "--run-llm",
        action="store_true",
        default=False,
        help="run @pytest.mark.llm tests against the real OpenAI API (uses the key in .env)",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-llm"):
        return
    skip_llm = pytest.mark.skip(reason="live OpenAI test; pass --run-llm to enable")
    for item in items:
        if "llm" in item.keywords:
            item.add_marker(skip_llm)


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="session", autouse=True)
def _clean_harness_store():
    for p in (_HARNESS_STORE, _HARNESS_STORE + ".tmp"):
        if os.path.exists(p):
            os.remove(p)
    yield
    for p in (_HARNESS_STORE, _HARNESS_STORE + ".tmp"):
        if os.path.exists(p):
            os.remove(p)


@pytest.fixture
def client():
    """In-process FastAPI TestClient against the isolated, offline store."""
    from fastapi.testclient import TestClient

    from osfl.app import app

    return TestClient(app)


@pytest.fixture(scope="session")
def base_url(tmp_path_factory):
    """A real uvicorn subprocess (own temp store, no key) for Playwright E2E."""
    store_path = tmp_path_factory.mktemp("osfl_e2e") / "store.json"
    env = {**os.environ, "OSFL_STORE_PATH": str(store_path), "OPENAI_API_KEY": ""}
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "osfl.app:app", "--port", str(port), "--log-level", "warning"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    try:
        ready = False
        for _ in range(80):
            if proc.poll() is not None:
                raise RuntimeError("uvicorn exited during startup")
            try:
                with urllib.request.urlopen(url + "/api/state", timeout=1) as r:
                    if r.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(0.5)
        if not ready:
            raise RuntimeError("server did not become ready")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
