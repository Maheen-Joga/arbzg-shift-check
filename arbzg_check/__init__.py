"""arbzg-check: check shift rosters against the German Working Hours Act (ArbZG)."""

from .checker import Options, check
from .loader import RosterFormatError, load, loads
from .model import Break, Finding, RosterError, Shift

__all__ = ["Break", "Finding", "Options", "RosterError", "RosterFormatError", "Shift", "check", "load", "loads"]
__version__ = "0.1.0"
