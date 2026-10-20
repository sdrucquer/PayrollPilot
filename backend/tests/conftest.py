from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from payrollpilot.settings import load_settings

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def settings(tmp_path):
    base = load_settings()
    return dataclasses.replace(
        base,
        db_path=tmp_path / "pp.db",
        fixtures_dir=FIXTURES,
        private_snapshots_dir=tmp_path / "snapshots",
        test_recipient="+15550000012",
        allowlist=("+15550000012",),
        messaging_mode="fake",
        browser_use_key_present=False,
        policy_file=tmp_path / "policy.json",
    )
