"""Vercel's internal preview entrypoint; never connects to the local demo stack.

SQLite is ephemeral on Vercel. This service is deliberately internal; the
public frontend uses its explicitly labeled, browser-local fixture simulation.
"""

import os

os.environ.setdefault("PP_DB_PATH", "/tmp/payrollpilot-preview.db")

from payrollpilot.app import app  # noqa: E402,F401
