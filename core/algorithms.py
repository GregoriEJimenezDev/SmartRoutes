"""core/algorithms.py
"""
from __future__ import annotations
from collections import deque
import heapq
from typing import List, Tuple, Dict, Set, Optional
from core.graph import Graph
from models.location import LocationState

class GraphAlgorithms:
    """Pure‑algorithmic operations on a Graph.
    No I/O, no UI calls – only data transformations.
    """

    # --------------------------------------------------------------------- #
    # Traversals
    # --------------------------------------------------------------------- #
    @staticmethod
    def bfs(graph: Graph, start_id: int) -> List[int]:
        """Breadth‑first search returning the visit order (active nodes only).
        Time Complexity: O(V + E)
        """
        visited: Set[int] = set()
        order: List[int] = []
        queue: deque[int] = deque()

        try:
            start_loc = graph.get_location(start_id)
        except Exception:
            return order
        if start_loc.state != LocationState.ACTIVE:
            return order

        queue.append(start_id)
        visited.add(start_id)
        while queue:
            v = queue.popleft()
            order.append(v)
            for nbr, _ in graph.get_neighbors(v):
                if nbr not in visited:
                    if graph.get_location(nbr).state == LocationState.ACTIVE:
                        visited.add(nbr)
                        queue.append(nbr)
        return order

    @staticmethod
    def dfs(graph: Graph, start_id: int) -> List[int]:
        """Depth‑first search (stack‑based) returning the visit order.
        Time Complexity: O(V + E)
        """
        visited: Set[int] = set()
        order: List[int] = []
        stack: List[int] = []
        try:
            start_loc = graph.get_location(start_id)
        except Exception:
            return order
        if start_loc.state != LocationState.ACTIVE:
            return order

        stack.append(start_id)
        while stack:
            v = stack.pop()
            if v in visited:
                continue
            visited.add(v)
            order.append(v)
            # push neighbours in reverse to mimic recursion order
            for nbr, _ in reversed(graph.get_neighbors(v)):
                if nbr not in visited and graph.get_location(nbr).state == LocationState.ACTIVE:
                    stack.append(nbr)
        return order

    # --------------------------------------------------------------------- #
    # Dijkstra
    # --------------------------------------------------------------------- #
    @staticmethod
    def dijkstra(
        graph: Graph, origin: int, destination: int
    ) -> Tuple[Optional[List[int]], Optional[float]]:
        """Weighted shortest‑path using a min‑heap.
        Returns (path_ids, total_cost) or (None, None) if unreachable.
        Time Complexity: O((V + E) log V)
        """
        # Guard against missing or inactive nodes
        try:
            if (
                graph.get_location(origin).state != LocationState.ACTIVE
                or graph.get_location(destination).state != LocationState.ACTIVE
            ):
                return None, None
        except Exception:
            return None, None

        if origin == destination:
            return [origin], 0.0

        dist: Dict[int, float] = {origin: 0.0}
        prev: Dict[int, int] = {}
        heap: List[Tuple[float, int]] = [(0.0, origin)]
        visited: Set[int] = set()

        while heap:
            cur_dist, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)
            if u == destination:
                break
            for v, w in graph.get_neighbors(u):
                if graph.get_location(v).state != LocationState.ACTIVE:
                    continue
                alt = cur_dist + w
                if alt < dist.get(v, float('inf')):
                    dist[v] = alt
                    prev[v] = u
                    heapq.heappush(heap, (alt, v))

        if destination not in dist:
            return None, None
        # reconstruct path
        path: List[int] = []
        cur = destination
        while cur != origin:
            path.append(cur)
            cur = prev[cur]
        path.append(origin)
        path.reverse()
        return path, dist[destination]

    # --------------------------------------------------------------------- #
    # Connectivity & components
    # --------------------------------------------------------------------- #
    @staticmethod
    def are_connected(graph: Graph, a: int, b: int) -> bool:
        """True if an active path exists between a and b.
        Time Complexity: O(V + E) (BFS)
        """
        try:
            if (
                graph.get_location(a).state != LocationState.ACTIVE
                or graph.get_location(b).state != LocationState.ACTIVE
            ):
                return False
        except Exception:
            return False
        if a == b:
            return True
        visited: Set[int] = set([a])
        queue: deque[int] = deque([a])
        while queue:
            v = queue.popleft()
            for nbr, _ in graph.get_neighbors(v):
                if nbr == b:
                    return True
                if nbr not in visited and graph.get_location(nbr).state == LocationState.ACTIVE:
                    visited.add(nbr)
                    queue.append(nbr)
        return False

    @staticmethod
    def connected_components(graph: Graph) -> List[Set[int]]:
        """All connected components among ACTIVE locations.
        Time Complexity: O(V + E)
        """
        unvisited: Set[int] = {loc.id for loc in graph.list_locations(only_active=True)}
        components: List[Set[int]] = []
        while unvisited:
            start = unvisited.pop()
            comp: Set[int] = {start}
            queue: deque[int] = deque([start])
            while queue:
                v = queue.popleft()
                for nbr, _ in graph.get_neighbors(v):
                    if (
                        nbr not in comp
                        and graph.get_location(nbr).state == LocationState.ACTIVE
                    ):
                        comp.add(nbr)
                        unvisited.discard(nbr)
                        queue.append(nbr)
            components.append(comp)
        return components

    # --------------------------------------------------------------------- #
    # Metrics
    # --------------------------------------------------------------------- #
    @staticmethod
    def metrics(graph: Graph) -> Dict[str, float]:
        """Calculate required graph metrics.
        Returns keys: total_nodes, total_edges, components,
        max_degree_node, min_degree_node, avg_degree,
        isolated_nodes, active_nodes, inactive_nodes.
        """
        nodes = graph.list_locations()
        total_nodes = len(nodes)
        active_nodes = sum(1 for n in nodes if n.state == LocationState.ACTIVE)
        inactive_nodes = total_nodes - active_nodes

        seen: Set[Tuple[int, int]] = set()
        degree: Dict[int, int] = {loc.id: 0 for loc in nodes}
        total_edges = 0
        for loc in nodes:
            for nbr, _ in graph.get_neighbors(loc.id):
                edge = tuple(sorted((loc.id, nbr)))
                if edge not in seen:
                    seen.add(edge)
                    total_edges += 1
                degree[loc.id] += 1
        isolated_nodes = sum(1 for d in degree.values() if d == 0)
        max_deg_node = max(degree, key=degree.get) if degree else -1
        min_deg_node = min(degree, key=degree.get) if degree else -1
        avg_degree = (total_edges * 2) / total_nodes if total_nodes else 0.0
        components = len(GraphAlgorithms.connected_components(graph))
        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "components": components,
            "max_degree_node": max_deg_node,
            "min_degree_node": min_deg_node,
            "avg_degree": avg_degree,
            "isolated_nodes": isolated_nodes,
            "active_nodes": active_nodes,
            "inactive_nodes": inactive_nodes,
        }
"