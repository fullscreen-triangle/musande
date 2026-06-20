"""
brs.py -- Concrete bounded resolvable spaces.

A computational model of Axiom (BRS) from
"The Irreducible Boundary of a Bounded Resolvable Space".

We realise a bounded resolvable space as a finite metric-measure space:
a grid of atoms (the underlying continuum sampled finely), a measure
(atom weights), and a *partition* into cells, each cell a set of atoms of
diameter >= delta. This is exactly the embedded-agent picture: the agent
can only ever name unions of cells, never sub-cell sets.

All theorem-validators in this suite operate on instances of `Space`.
No randomness lives here; randomized sweeps live in the runner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from math import sqrt
from typing import Dict, FrozenSet, Iterable, List, Sequence, Set, Tuple

Atom = Tuple[int, ...]  # integer lattice coordinate of a sampled point


# ---------------------------------------------------------------------
#  The space
# ---------------------------------------------------------------------
@dataclass
class Space:
    """A bounded resolvable space realised on a finite integer lattice.

    atoms       : the sampled points of the bounded continuum.
    weight      : measure of each atom (mu of a single atom).
    cells       : partition -> list of frozensets of atoms (the realisable
                  grain; an agent names only unions of these).
    delta       : the resolution (min cell diameter in lattice units).
    """

    atoms: FrozenSet[Atom]
    weight: float
    cells: List[FrozenSet[Atom]]
    delta: float

    # --- measure ---
    def mu(self, region: Iterable[Atom]) -> float:
        return self.weight * len(set(region))

    @property
    def total_measure(self) -> float:
        return self.mu(self.atoms)

    @property
    def mu_min(self) -> float:
        """Minimum cell measure -- the lower bound the floor must clear."""
        return min(self.mu(c) for c in self.cells)

    # --- adjacency (4/6/2n-neighbourhood on the lattice) ---
    def neighbours(self, a: Atom) -> List[Atom]:
        out = []
        for i in range(len(a)):
            for step in (-1, 1):
                b = list(a)
                b[i] += step
                b = tuple(b)
                if b in self.atoms:
                    out.append(b)
        return out

    def is_connected(self) -> bool:
        if not self.atoms:
            return True
        start = next(iter(self.atoms))
        seen = {start}
        stack = [start]
        while stack:
            x = stack.pop()
            for y in self.neighbours(x):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        return len(seen) == len(self.atoms)

    # --- cell lookup ---
    def cell_of(self, a: Atom) -> int:
        for idx, c in enumerate(self.cells):
            if a in c:
                return idx
        raise KeyError(a)


# ---------------------------------------------------------------------
#  Builders
# ---------------------------------------------------------------------
def make_box(shape: Sequence[int], cell_side: int, weight: float = 1.0) -> Space:
    """A box [0,shape_0) x ... sampled on the integer lattice, partitioned
    into axis-aligned cells of side `cell_side`. Each cell has diameter
    >= cell_side (delta), so BRS2 (finite resolution) holds by construction.
    """
    ranges = [range(s) for s in shape]
    atoms: Set[Atom] = set(product(*ranges))
    # group atoms into cells by integer division of each coordinate
    buckets: Dict[Atom, Set[Atom]] = {}
    for a in atoms:
        key = tuple(coord // cell_side for coord in a)
        buckets.setdefault(key, set()).add(a)
    cells = [frozenset(s) for s in buckets.values()]
    delta = float(cell_side)
    return Space(frozenset(atoms), weight, cells, delta)


# ---------------------------------------------------------------------
#  Regions, complements, separators  (Defs in Sec. 1)
# ---------------------------------------------------------------------
def complement(sp: Space, region: FrozenSet[Atom]) -> FrozenSet[Atom]:
    """Negation-sequence N(A) = Omega \\ A  (Def: negation-sequence)."""
    return frozenset(sp.atoms - set(region))


def realisable_region_from_cells(sp: Space, cell_idxs: Iterable[int]) -> FrozenSet[Atom]:
    """A Part-realisable region: a union of whole cells."""
    out: Set[Atom] = set()
    for i in cell_idxs:
        out |= set(sp.cells[i])
    return frozenset(out)


def separator_cells(sp: Space, region: FrozenSet[Atom]) -> List[int]:
    """Sigma_Part(A): indices of cells bordering BOTH A and its complement.

    A cell borders A if it contains, or is lattice-adjacent to, an atom of A.
    For a realisable A (union of cells), a cell is a separator cell iff it
    is adjacent to a cell on the other side of the A/complement divide.
    """
    comp = complement(sp, region)
    sep: List[int] = []
    for idx, c in enumerate(sp.cells):
        touches_A = any((a in region) or any(n in region for n in sp.neighbours(a))
                        for a in c)
        touches_C = any((a in comp) or any(n in comp for n in sp.neighbours(a))
                        for a in c)
        if touches_A and touches_C:
            sep.append(idx)
    return sep


def separator_atoms(sp: Space, region: FrozenSet[Atom]) -> FrozenSet[Atom]:
    out: Set[Atom] = set()
    for i in separator_cells(sp, region):
        out |= set(sp.cells[i])
    return frozenset(out)


def boundary_thickness(sp: Space, region: FrozenSet[Atom]) -> float:
    """beta_Part(A) = mu(Sigma_Part(A))  (Def: boundary thickness)."""
    return sp.mu(separator_atoms(sp, region))
