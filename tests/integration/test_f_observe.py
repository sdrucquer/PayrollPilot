"""Synthetic HTTP stand-ins: observation must never approve or mutate the live demo."""
import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def observed_server():
    events = [
        {"type": "handoff.accepted", "refs": {}},
        {"type": "approval.granted", "refs": {}},
        {"type": "message.sent", "refs": {"batch_id": "msg_batch_test", "messaging_mode": "bridge"}},
        {"type": "message.received", "refs": {"batch_id": "msg_batch_test", "inbound_id": "in_test"}},
        {"type": "reply.parsed", "refs": {"inbound_id": "in_test"}},
        {"type": "correction.applied", "refs": {}},
        {"type": "readiness.changed", "refs": {}},
        {"type": "memory.written", "refs": {}},
        {"type": "memory.recalled", "refs": {"memory_adapter": "cognee"}},
        {"type": "memory.applied", "refs": {"proposed": {"job_id": "job_02", "based_on_resolution_ids": ["res_test"]}}},
        {"type": "workbook.generated", "refs": {"workbook_id": "wb_test"}},
        {"type": "workbook.verified", "refs": {"workbook_id": "wb_test"}},
    ]
    responses = {
        "/api/health": {"ok": True, "private": "PRIVATE_TEST_MARKER"},
        "/api/comms/health": {"messaging": "bridge", "memory": "cognee", "band": "band_cli", "llm_key_present": True, "band_room_configured": True},
        "/health": {"ok": True, "mode": "real", "secret": "PRIVATE_TEST_MARKER"},
        "/api/cycles/cyc_synth_v1": {"id": "cyc_synth_v1"},
        "/api/cycles/cyc_synth_v1/exceptions": [{"evidence": ["PRIVATE_TEST_MARKER"]}],
        "/api/cycles/cyc_synth_v1/readiness": {"stage1": {"state": "blocked"}, "items": []},
        "/api/cycles/cyc_synth_v1/packet": {"draft_version": "v1", "destination": "internal_draft"},
        "/api/events": events,
    }
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append((self.command, self.path))
            path = urlsplit(self.path).path
            body = b"<title>PRIVATE_TEST_MARKER</title>" if path == "/" else json.dumps(responses.get(path, {})).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            requests.append((self.command, self.path))
            self.send_response(405)
            self.end_headers()

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}", responses, requests
    server.shutdown()
    server.server_close()
    thread.join()


def run_observation(server, tmp_path):
    base, _, _ = server
    out = tmp_path / "rehearsal.md"
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/f_smoke.sh"), "--observe", "--out", str(out)],
        env={**os.environ, "BASE": base, "BRIDGE": base, "WEB": base},
        capture_output=True, text=True, timeout=20,
    )
    return result, out.read_text()


def test_observation_is_get_only_and_does_not_publish_response_data(observed_server, tmp_path):
    result, transcript = run_observation(observed_server, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert observed_server[2] and all(method == "GET" for method, _ in observed_server[2])
    assert "PRIVATE_TEST_MARKER" not in result.stdout + result.stderr + transcript
    assert "GET-only observation" in transcript and "exact T15 comparison | SKIP" in transcript
    assert "readiness available | PASS" in transcript  # blocked remains a valid reported state


def test_http_success_without_memory_action_proof_fails(observed_server, tmp_path):
    observed_server[1]["/api/events"] = [e for e in observed_server[1]["/api/events"] if e["type"] != "memory.applied"]
    result, transcript = run_observation(observed_server, tmp_path)
    assert result.returncode != 0
    assert "memory action change log | FAIL" in transcript


def test_fake_or_uncorrelated_transport_cannot_pass_as_live(observed_server, tmp_path):
    observed_server[1]["/api/comms/health"]["messaging"] = "fake"
    next(e for e in observed_server[1]["/api/events"] if e["type"] == "message.received")["refs"]["batch_id"] = "msg_batch_other"
    result, transcript = run_observation(observed_server, tmp_path)
    assert result.returncode != 0
    assert "active real comms | FAIL" in transcript
    assert "recorded live round trip | FAIL" in transcript


def test_observe_refuses_send_before_any_network_request():
    result = subprocess.run(["bash", str(ROOT / "scripts/f_smoke.sh"), "--observe", "--send"], capture_output=True, text=True)
    assert result.returncode == 2
    assert "cannot be combined" in result.stdout
