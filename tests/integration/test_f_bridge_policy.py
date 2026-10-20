"""F-02: the bridge refuses non-allowlisted recipients independently of the backend (FR-10, FR-26)."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).parent
BUN = shutil.which("bun") or str(Path.home() / ".bun" / "bin" / "bun")


@pytest.mark.skipif(not Path(BUN).exists(), reason="bun not installed")
def test_bridge_checksend_enforces_allowlist_token_and_hash():
    out = subprocess.run([BUN, str(HERE / "f_bridge_policy_check.ts")], capture_output=True, text=True, timeout=60,
                         cwd=HERE.parents[1])
    assert out.returncode == 0, out.stderr
    r = json.loads(out.stdout.strip().splitlines()[-1])
    assert r["ok"] == {"ok": True}
    assert r["formatted_same_recipient"] == {"ok": True}
    assert r["other_recipient"] == {"ok": False, "status": 403, "error": "recipient_not_allowlisted"}
    assert r["empty_allowlist"]["ok"] is False and r["empty_allowlist"]["status"] == 403
    assert r["bad_token"] == {"ok": False, "status": 401, "error": "bad_bridge_token"}
    assert r["edited_text"] == {"ok": False, "status": 409, "error": "text_hash_mismatch"}
