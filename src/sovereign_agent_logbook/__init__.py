"""Sovereign Agent Logbook — a tamper-evident, model-agnostic logbook for AI agents.

Public API:
    Logbook        append-only, hash-chained event store (JSON Lines on local disk)
    Event          one logged action
    verify_file    walk a logbook file and prove its chain is intact
"""

from .chain import GENESIS_HASH, compute_hash, verify_file
from .store import Event, Logbook, VerificationResult

__version__ = "0.1.0"
SPEC_VERSION = "0.1"

__all__ = [
    "Event",
    "Logbook",
    "VerificationResult",
    "GENESIS_HASH",
    "compute_hash",
    "verify_file",
    "SPEC_VERSION",
    "__version__",
]
