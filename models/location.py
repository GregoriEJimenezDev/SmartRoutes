"""models/location.py
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto

class LocationState(Enum):
    """Possible logical states for a location."""
    ACTIVE = auto()
    INACTIVE = auto()

@dataclass(frozen=True)
class Location:
    """Immutable value object representing a delivery point.

    Attributes
    ----------
    id: int
        Unique, never‑reused identifier.
    name: str
        Human‑readable name (unique among active locations).
    state: LocationState
        Current logical state.
    """
    id: int
    name: str
    state: LocationState = LocationState.ACTIVE
