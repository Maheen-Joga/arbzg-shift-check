"""arbzg-check: check shift rosters against the German Working Hours Act (ArbZG)."""

from .checker import check
from .model import Break, Finding, RosterError, Shift

__all__ = ["Break", "Finding", "RosterError", "Shift", "check"]
__version__ = "0.1.0"
