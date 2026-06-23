"""
contact_graph.py -- concrete finite contact graphs.

A computational model of the objects in
"On the Necessary Substructures of Finite Contact Graphs".

A contact graph is a finite, connected, weighted graph with a positive
edge-weight floor (Axiom: Finiteness Premise). One distinguished vertex (or
vertex set) is the MEDIUM -- the reference against which parts are individuated.

All theorem-validators in the suite operate on instances of `ContactGraph`.
No randomness here; randomized sweeps live in the runner.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

Vertex = int
Edge = Tuple[Vertex, Vertex]  # always stored as (min, max)


def _e(u: Vertex, v: Vertex) -> Edge:
    return (u, v) if u < v else (v, u)


@dataclass
class ContactGraph:
    """A finite weighted graph with a positive floor and a medium vertex.

    vertices : the parts (the medium is one of them).
    weight   : edge -> weight (all >= floor).
    floor    : the positive edge-weight floor (beta).
    medium   : the distinguished reference vertex.
    """

    vertices: FrozenSet[Vertex]
    weight: Dict[Edge, float]
    floor: float
    medium: Vertex

    # --- basic accessors ---
    @property
    def edges(self) -> List[Edge]:
        return list(self.weight.keys())

    def w(self, u: Vertex, v: Vertex) -> float:
        return self.weight.get(_e(u, v), 0.0)

    def neighbours(self, v: Vertex) -> List[Vertex]:
        out = []
        for (a, b) in self.weight:
            if a == v:
                out.append(b)
            elif b == v:
                out.append(a)
        return out

    def degree(self, v: Vertex) -> int:
        return len(self.neighbours(v))

    @property
    def min_edge_weight(self) -> float:
        return min(self.weight.values()) if self.weight else float("inf")

    # --- connectivity ---
    def is_connected(self) -> bool:
        if not self.vertices:
            return True
        start = next(iter(self.vertices))
        seen = {start}
        stack = [start]
        while stack:
            x = stack.pop()
            for y in self.neighbours(x):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        return seen == set(self.vertices)

    # --- cuts ---
    def cut_edges(self, S: FrozenSet[Vertex]) -> List[Edge]:
        """Edges with exactly one endpoint in S."""
        out = []
        for (a, b) in self.weight:
            if (a in S) != (b in S):
                out.append((a, b))
        return out

    def cut_weight(self, S: FrozenSet[Vertex]) -> float:
        return sum(self.weight[e] for e in self.cut_edges(S))

    def boundary_cost(self, U: FrozenSet[Vertex]) -> float:
        """b(U) = weight of the cut separating U from the rest."""
        return self.cut_weight(U)

    # --- separation cost from the medium (min cut with U on one side, medium on other) ---
    def separation_from_medium(self, v: Vertex) -> float:
        """sigma(v): min over S with v in S, medium not in S, of cut_weight(S).
        Brute force over subsets containing v and excluding medium (small graphs).
        """
        others = [x for x in self.vertices if x not in (v, self.medium)]
        best = float("inf")
        best_S = None
        # S must contain v, must not contain medium; may contain any subset of others
        for r in range(len(others) + 1):
            for combo in itertools.combinations(others, r):
                S = frozenset((v,) + combo)
                cw = self.cut_weight(S)
                if cw < best:
                    best = cw
                    best_S = S
        return best, best_S

    # --- residual: min cut weight over all nontrivial bipartitions ---
    def residual(self) -> Tuple[float, FrozenSet[Vertex]]:
        """rho(G) = min over nonempty proper S of cut_weight(S) (global min cut)."""
        verts = sorted(self.vertices)
        n = len(verts)
        best = float("inf")
        best_S = None
        # iterate proper nonempty subsets (fix verts[0] in S to halve symmetry)
        for r in range(1, n):
            for combo in itertools.combinations(verts[1:], r):
                S = frozenset((verts[0],) + combo)
                if len(S) == n:
                    continue
                cw = self.cut_weight(S)
                if cw < best:
                    best = cw
                    best_S = S
        # also singletons not containing verts[0]
        for v in verts[1:]:
            S = frozenset((v,))
            cw = self.cut_weight(S)
            if cw < best:
                best = cw
                best_S = S
        return best, best_S


# ---------------------------------------------------------------------
#  Builders
# ---------------------------------------------------------------------
def make_medium_graph(rng, n_parts: int, floor: float,
                      extra_edge_prob: float = 0.4,
                      wmax_mult: float = 4.0) -> ContactGraph:
    """Build a connected contact graph on n_parts parts + 1 medium vertex.

    The medium (vertex 0) is adjacent to every part (so the graph is connected
    and the medium is a universal reference). Additional part-part edges are
    added with probability extra_edge_prob. All weights in [floor, floor*wmax].
    """
    medium = 0
    parts = list(range(1, n_parts + 1))
    vertices = frozenset([medium] + parts)
    weight: Dict[Edge, float] = {}

    def rw() -> float:
        return floor + rng.random() * floor * (wmax_mult - 1.0)

    # medium adjacent to every part
    for p in parts:
        weight[_e(medium, p)] = rw()
    # random part-part edges
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            if rng.random() < extra_edge_prob:
                weight[_e(parts[i], parts[j])] = rw()

    return ContactGraph(vertices, weight, floor, medium)


def two_cluster_graph(rng, floor: float) -> ContactGraph:
    """Two heavy clusters joined by a single light bridge; the medium is one of
    the cluster vertices (the reference is part of the whole, not a hub over it).

    Witness for T2 non-locality: the global minimum cut is the cluster
    bipartition (cutting the single bridge), a MULTI-vertex region, and every
    *singleton* cut is strictly heavier (each vertex sits inside a heavy clique).
    So the residual is realised by a region, never a single vertex.
    """
    A = [0, 1, 2]      # medium = 0 lives inside cluster A
    B = [3, 4, 5]
    medium = 0
    vertices = frozenset(A + B)
    weight: Dict[Edge, float] = {}

    def heavy() -> float:
        return floor * (5.0 + rng.random())

    # dense, heavy within each cluster (every singleton cut crosses >=2 heavy edges)
    for cl in (A, B):
        for i in range(len(cl)):
            for j in range(i + 1, len(cl)):
                weight[_e(cl[i], cl[j])] = heavy()
    # single light bridge between the clusters (the unique cheap cut)
    weight[_e(2, 3)] = floor
    return ContactGraph(vertices, weight, floor, medium)


def reshuffle(rng, G: ContactGraph) -> ContactGraph:
    """A measurement = weight-preserving reshuffle fixing the medium.

    We permute the NON-medium vertex labels (a graph automorphism of the label
    set), which preserves the multiset of edge weights and the medium's incident
    structure setwise. This models 'reshuffling the marbles in the water':
    the total weight and the medium are conserved; the labelling changes.
    """
    parts = [v for v in G.vertices if v != G.medium]
    perm_targets = parts[:]
    rng.shuffle(perm_targets)
    relabel = {G.medium: G.medium}
    for src, dst in zip(parts, perm_targets):
        relabel[src] = dst
    new_weight: Dict[Edge, float] = {}
    for (a, b), wv in G.weight.items():
        na, nb = relabel[a], relabel[b]
        new_weight[_e(na, nb)] = wv
    return ContactGraph(G.vertices, new_weight, G.floor, G.medium)
