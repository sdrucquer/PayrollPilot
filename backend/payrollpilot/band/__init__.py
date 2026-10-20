"""Lane C: Band product-agent coordination (pp-audit, pp-resolution, pp-payroll) via the band CLI."""
from .cli import BandError, BandRequired, CliBand, NullBand, get_band, parse_decision
from .handoff import case_card, handoff_to_resolution, request_owner_decision, deliver_to_payroll

__all__ = ["BandError", "BandRequired", "CliBand", "NullBand", "get_band", "parse_decision",
           "case_card", "handoff_to_resolution", "request_owner_decision", "deliver_to_payroll"]
