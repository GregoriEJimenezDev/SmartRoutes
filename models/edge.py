"""models/edge.py
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Edge:
    """Immutable representation of a weighted, undirected connection.

    Attributes
    ----------
    origin: int
        ID of the source location.
    destination: int
        ID of the destination location.
    weight: float
        Positive cost/distance.
    """
    origin: int
    destination: int
    weight: float
