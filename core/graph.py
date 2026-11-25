"""core/graph.py
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Set
from models.location import Location, LocationState
from models.edge import Edge
from exceptions import (
    InvalidLocationError,
    DuplicateEdgeError,
    InactiveNodeError,
    EdgeNotFoundError,
)

class Graph:
    """
    The sole source of truth for locations and routes.
    All modifications keep the adjacency list bidirectional.
    """

    def __init__(self) -> None:
        # location_id → Location (immutable)
        self._locations: Dict[int, Location] = {}
        # adjacency list: location_id → List[(neighbor_id, weight)]
        self._adjacency: Dict[int, List[Tuple[int, float]]] = {}

    # --------------------------------------------------------------------- #
    # Location management
    # --------------------------------------------------------------------- #
    def add_location(self, location: Location) -> None:
        """
        Register a new location.

        Time Complexity: O(1)
        """
        if location.id in self._locations:
            raise InvalidLocationError(f"Location ID {location.id} already exists.")
        self._locations[location.id] = location
        self._adjacency[location.id] = []

    def get_location(self, loc_id: int) -> Location:
        """Return the Location object, raising if missing. O(1)"""
        try:
            return self._locations[loc_id]
        except KeyError:
            raise InvalidLocationError(f"Location ID {loc_id} not found.")

    def list_locations(self, only_active: bool = False) -> List[Location]:
        """Return all locations, optionally filtering to ACTIVE only. O(V)"""
        return [
            loc for loc in self._locations.values()
            if not only_active or loc.state == LocationState.ACTIVE
        ]

    def inactivate_location(self, loc_id: int) -> None:
        """
        Logical inactivation. Disallowed while incident edges exist.

        Time Complexity: O(deg(v))
        """
        loc = self.get_location(loc_id)
        if loc.state == LocationState.INACTIVE:
            return
        if self._adjacency[loc_id]:
            raise InactiveNodeError(
                "Cannot inactivate location with existing routes. Remove them first."
            )
        self._locations[loc_id] = Location(loc.id, loc.name, LocationState.INACTIVE)

    def activate_location(self, loc_id: int) -> None:
        """
        Reactivate a location after confirming name uniqueness among actives.

        Time Complexity: O(V)
        """
        loc = self.get_location(loc_id)
        if loc.state == LocationState.ACTIVE:
            return
        for other in self._locations.values():
            if (
                other.id != loc_id
                and other.state == LocationState.ACTIVE
                and other.name.lower() == loc.name.lower()
            ):
                raise InvalidLocationError(
                    f"An active location with name '{loc.name}' already exists."
                )
        self._locations[loc_id] = Location(loc.id, loc.name, LocationState.ACTIVE)

    # --------------------------------------------------------------------- #
    # Edge management (undirected, always stored both ways)
    # --------------------------------------------------------------------- #
    def add_edge(self, edge: Edge) -> None:
        """
        Insert a new undirected edge. Duplicates and self‑loops are rejected.

        Time Complexity: O(deg(origin) + deg(destination))
        """
        if edge.origin == edge.destination:
            raise ValueError("Self‑loops are not allowed.")
        if edge.weight <= 0:
            raise ValueError("Weight must be positive.")
        self._ensure_active_nodes(edge.origin, edge.destination)

        if self.has_edge(edge.origin, edge.destination):
            raise DuplicateEdgeError(
                f"Edge {edge.origin} ↔ {edge.destination} already exists."
            )
        self._adjacency[edge.origin].append((edge.destination, edge.weight))
        self._adjacency[edge.destination].append((edge.origin, edge.weight))

    def update_edge(self, origin: int, destination: int, new_weight: float) -> None:
        """
        Change the weight of an existing undirected edge.

        Time Complexity: O(deg(origin) + deg(destination))
        """
        if new_weight <= 0:
            raise ValueError("Weight must be positive.")
        self._ensure_active_nodes(origin, destination)

        if not self.has_edge(origin, destination):
            raise EdgeNotFoundError(
                f"Edge {origin} ↔ {destination} does not exist."
            )
        self._replace_neighbor(origin, destination, new_weight)
        self._replace_neighbor(destination, origin, new_weight)

    def remove_edge(self, origin: int, destination: int) -> None:
        """
        Delete an undirected edge. No‑op if edge missing.

        Time Complexity: O(deg(origin) + deg(destination))
        """
        if self.has_edge(origin, destination):
            self._remove_neighbor(origin, destination)
            self._remove_neighbor(destination, origin)

    # --------------------------------------------------------------------- #
    # Read‑only helpers
    # --------------------------------------------------------------------- #
    def get_neighbors(self, loc_id: int) -> List[Tuple[int, float]]:
        """Return a copy of the neighbor list for a location. O(1)"""
        self._ensure_node_exists(loc_id)
        return list(self._adjacency[loc_id])

    def has_edge(self, origin: int, destination: int) -> bool:
        """Check existence of an undirected edge. O(deg(origin))"""
        self._ensure_node_exists(origin)
        return any(nbr == destination for nbr, _ in self._adjacency[origin])

    # --------------------------------------------------------------------- #
    # Internal utilities
    # --------------------------------------------------------------------- #
    def _ensure_node_exists(self, loc_id: int) -> None:
        if loc_id not in self._locations:
            raise InvalidLocationError(f"Location ID {loc_id} does not exist.")

    def _ensure_active_nodes(self, *ids: int) -> None:
        for loc_id in ids:
            self._ensure_node_exists(loc_id)
            if self._locations[loc_id].state != LocationState.ACTIVE:
                raise InactiveNodeError(f"Location ID {loc_id} is inactive.")

    def _replace_neighbor(
        self, src: int, dst: int, new_weight: float
    ) -> None:
        lst = self._adjacency[src]
        for i, (nbr, _) in enumerate(lst):
            if nbr == dst:
                lst[i] = (dst, new_weight)
                return

    def _remove_neighbor(self, src: int, dst: int) -> None:
        lst = self._adjacency[src]
        self._adjacency[src] = [(nbr, w) for nbr, w in lst if nbr != dst]
