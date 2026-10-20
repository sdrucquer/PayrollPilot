"""PayrollPilot pure core: money, time, audit, calc, readiness, corrections, packet, workbook.

No IO (except workbook writing to a caller-supplied path), no LLM, no network.
Money is integer cents, time is integer minutes, unknown is None (never 0).
"""

CALC_VERSION = "calc_v1"
CONTRACT_VERSION = "1"
