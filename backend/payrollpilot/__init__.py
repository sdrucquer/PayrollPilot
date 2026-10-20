"""PayrollPilot backend package (lane A: platform and data).

Business logic lives in ``payrollpilot_core`` (lane B). This package owns
persistence, the deterministic coordinator, permissions, and thin API routes.
"""

CONTRACT_VERSION = "1"
