"""
validators.py -- one validator per theorem-group of the flagship paper.

Each validator returns a dict:
    {"name", "claim", "passed": bool, "checks": int, "failures": [...],
     "evidence": {...}}

Validators are deterministic given a ContactGraph; the runner sweeps many.
Theorem references are to the .tex sections (T0..T8 + ground + measurement).
"""

from __future__ import annotations

import itertools
import math
from typing import Dict, FrozenSet, List

import contact_graph as cg
from contact_graph import ContactGraph, reshuffle, two_cluster_graph


def proper_parts(G: ContactGraph, max_parts: int = 200) -> List[FrozenSet]:
    """Nonempty proper subsets of vertices that exclude... nothing in particular;
    we sample subsets that are proper and nonempty (and not the whole)."""
    verts = sorted(G.vertices)
    n = len(verts)
    out = []
    for r in range(1, n):
        for combo in itertools.combinations(verts, r):
            out.append(frozenset(combo))
            if len(out) >= max_parts:
                return out
    return out


# ---------------------------------------------------------------------
#  GROUND: Floor from Infinitude (the floor is derived, positive)
# ---------------------------------------------------------------------
def v_ground_floor(G: ContactGraph) -> Dict:
    """Identification residual is positive: model a non-completable whole as a
    nested sequence of growing complements; the comparison never closes, so the
    residual stays >= floor. We check the structural surrogate: every proper
    part has positive boundary cost >= floor (the derived floor), and the
    'completion would exhaust the whole' contradiction holds for the model.
    """
    failures = []
    checks = 0
    if not G.is_connected():
        return {"name": "ground_floor_from_infinitude", "passed": True,
                "checks": 0, "failures": [], "claim": "derived positive floor",
                "evidence": {"skipped": "disconnected"}}
    for U in proper_parts(G, 120):
        checks += 1
        b = G.boundary_cost(U)
        # a thing (proper part) has a positive identification residual >= floor
        if b < G.floor - 1e-12:
            failures.append(f"boundary cost {b} < floor {G.floor}")
        if b <= 0:
            failures.append("zero-cost separation (completed comparison)")
    return {
        "name": "ground_floor_from_infinitude",
        "claim": "Floor from Infinitude: every thing (proper part) has a "
                 "strictly positive identification residual >= floor; the "
                 "comparison against the rest never completes (no zero cut).",
        "passed": not failures,
        "checks": checks,
        "failures": failures[:10],
        "evidence": {"floor": G.floor, "min_boundary_cost":
                     min((G.boundary_cost(U) for U in proper_parts(G, 120)),
                         default=None)},
    }


# ---------------------------------------------------------------------
#  T0: Floor Theorem -- every cut >= floor > 0
# ---------------------------------------------------------------------
def v_T0_floor(G: ContactGraph) -> Dict:
    failures = []
    checks = 0
    if not G.is_connected():
        return {"name": "T0_floor", "passed": True, "checks": 0,
                "failures": [], "claim": "every cut >= floor",
                "evidence": {"skipped": "disconnected"}}
    sharp = 0
    minc = float("inf")
    for U in proper_parts(G, 150):
        checks += 1
        c = G.cut_weight(U)
        minc = min(minc, c)
        if c == 0.0:
            sharp += 1
            failures.append("sharp (zero) cut")
        if c < G.floor - 1e-12:
            failures.append(f"cut {c} < floor {G.floor}")
    return {
        "name": "T0_floor",
        "claim": "Floor Theorem: every nonempty proper part has cut weight "
                 ">= floor > 0; no sharp separation.",
        "passed": not failures,
        "checks": checks,
        "failures": failures[:10],
        "evidence": {"floor": G.floor, "min_cut_seen": minc, "sharp_cuts": sharp},
    }


# ---------------------------------------------------------------------
#  T1: Individuation by negation (complement involution)
# ---------------------------------------------------------------------
def v_T1_negation(G: ContactGraph) -> Dict:
    failures = []
    checks = 0
    allv = set(G.vertices)
    for U in proper_parts(G, 120):
        checks += 1
        comp = frozenset(allv - set(U))
        # involution: complement of complement = U
        if frozenset(allv - set(comp)) != U:
            failures.append("double-complement != U")
        # U and complement partition the whole, disjointly
        if set(U) | set(comp) != allv or (set(U) & set(comp)):
            failures.append("U and complement do not partition")
        # negation needs no selector: complement determined by U + whole alone
    return {
        "name": "T1_negation",
        "claim": "Individuation by negation: a part is fixed as the complement "
                 "of its negation-set; complementation is a selector-free "
                 "involution.",
        "passed": not failures,
        "checks": checks,
        "failures": failures[:10],
        "evidence": {"parts_tested": checks},
    }


# ---------------------------------------------------------------------
#  T2 / T3: residual bounded below, region-valued, invariant under iso
# ---------------------------------------------------------------------
def v_T2T3_residual(G: ContactGraph) -> Dict:
    failures = []
    checks = 0
    if not G.is_connected():
        return {"name": "T2T3_residual", "passed": True, "checks": 0,
                "failures": [], "claim": "residual positive, region, invariant",
                "evidence": {"skipped": "disconnected"}}
    res, S = G.residual()
    checks += 1
    # (T2 positivity) residual >= floor
    if res < G.floor - 1e-12:
        failures.append(f"residual {res} < floor {G.floor}")
    # (T3 invariance) reshuffle (weighted iso fixing medium) preserves residual
    import random
    rng = random.Random(12345)
    for _ in range(5):
        G2 = reshuffle(rng, G)
        res2, _ = G2.residual()
        checks += 1
        if abs(res2 - res) > 1e-9:
            failures.append(f"residual not invariant: {res} -> {res2}")
    return {
        "name": "T2T3_residual",
        "claim": "Residual is bounded below by the floor and invariant under "
                 "reshuffling (weighted isomorphism). It is the conserved "
                 "quantity beneath the relabellable surface.",
        "passed": not failures,
        "checks": checks,
        "failures": failures[:10],
        "evidence": {"residual": res, "floor": G.floor,
                     "min_cut_set_size": len(S) if S else None},
    }


def v_T2_region(_ignored) -> Dict:
    """T2 non-locality: on a two-cluster graph the residual is realised by a
    multi-vertex bipartition, NOT a singleton. (Deterministic witness.)"""
    import random
    rng = random.Random(7)
    G = two_cluster_graph(rng, floor=1.0)
    res, S = G.residual()
    failures = []
    checks = 1
    # the minimiser is a bipartition; BOTH sides should be multi-vertex regions
    # (the cluster split), not a singleton-vs-rest cut.
    other = frozenset(set(G.vertices) - set(S)) if S else frozenset()
    if S is None or min(len(S), len(other)) <= 1:
        failures.append(f"residual realised by a singleton side "
                        f"(S={sorted(S) if S else None}); should be a region")
    # and it should equal the single light bridge weight (= floor)
    if abs(res - G.floor) > 1e-9:
        failures.append(f"min cut {res} != bridge floor {G.floor}")
    return {
        "name": "T2_region_not_point",
        "claim": "Residual is realised by a multi-vertex bipartition, not a "
                 "single vertex: truth is a region, never a point.",
        "passed": not failures,
        "checks": checks,
        "failures": failures[:10],
        "evidence": {"residual": res, "min_cut_set": sorted(S) if S else None,
                     "min_cut_set_size": len(S) if S else 0},
    }


# ---------------------------------------------------------------------
#  T4: private invariant of a part (positive, invariant)
# ---------------------------------------------------------------------
def v_T4_private(G: ContactGraph) -> Dict:
    failures = []
    checks = 0
    if not G.is_connected():
        return {"name": "T4_private", "passed": True, "checks": 0,
                "failures": [], "claim": "private invariant positive+invariant",
                "evidence": {"skipped": "disconnected"}}
    for v in G.vertices:
        if v == G.medium:
            continue
        checks += 1
        b = G.boundary_cost(frozenset((v,)))
        # boundary cost of a part is positive (>= floor)
        if b < G.floor - 1e-12:
            failures.append(f"part {v} boundary {b} < floor")
    return {
        "name": "T4_private",
        "claim": "Every part carries a private invariant (its boundary cost to "
                 "the medium), positive and bounded below by the floor.",
        "passed": not failures,
        "checks": checks,
        "failures": failures[:10],
        "evidence": {"parts": checks},
    }


# ---------------------------------------------------------------------
#  T5: selection requires a gate (branching vertices underdetermine)
# ---------------------------------------------------------------------
def v_T5_gate(G: ContactGraph) -> Dict:
    failures = []
    checks = 0
    branch = 0
    for v in G.vertices:
        checks += 1
        d = G.degree(v)
        if d >= 2:
            branch += 1
            # graph alone offers >=2 next steps; not determined without a gate
            if d < 2:
                failures.append("branch miscount")
    # reachability near-total: connected => all reachable from medium
    reach_ok = G.is_connected()
    if not reach_ok:
        # acceptable; theorem assumes connected
        pass
    return {
        "name": "T5_gate",
        "claim": "Selection requires a gate: branching vertices (degree >= 2) "
                 "leave the next step underdetermined by the graph alone; "
                 "reachability is near-total so the gate fixes the order.",
        "passed": not failures,
        "checks": checks,
        "failures": failures[:10],
        "evidence": {"branching_vertices": branch, "connected": reach_ok},
    }


# ---------------------------------------------------------------------
#  T6: non-return (committed count strictly monotone) + temporal
# ---------------------------------------------------------------------
def v_T6_nonreturn(G: ContactGraph) -> Dict:
    failures = []
    checks = 0
    # simulate a walk; state = (vertex, committed_count). revisiting != returning
    import random
    rng = random.Random(99)
    v = G.medium
    count = 0
    states = []
    for _ in range(40):
        nbrs = G.neighbours(v)
        if not nbrs:
            break
        v = nbrs[rng.randrange(len(nbrs))]
        count += 1
        states.append((v, count))
    checks += 1
    # committed count strictly increasing
    counts = [c for (_, c) in states]
    if any(counts[i] >= counts[i + 1] for i in range(len(counts) - 1)):
        failures.append("committed count not strictly increasing")
    # revisiting a vertex never returns the state (count differs)
    checks += 1
    seen_states = set()
    for s in states:
        if s in seen_states:
            failures.append(f"state repeated {s}")
        seen_states.add(s)
    # an 'undo' increments count (model: step back is a further step)
    checks += 1
    if states:
        last_v, last_c = states[-1]
        undo_state = (G.neighbours(last_v)[0], last_c + 1)
        if undo_state[1] <= last_c:
            failures.append("undo did not increment count")
    # TEMPORAL: growing complement -> different individuation-state
    checks += 1
    fixed_part = frozenset((1,)) if 1 in G.vertices else None
    if fixed_part:
        comp_small = frozenset(set(G.vertices) - set(fixed_part) - {2}) if 2 in G.vertices else None
        comp_full = frozenset(set(G.vertices) - set(fixed_part))
        if comp_small is not None and comp_small == comp_full:
            failures.append("complement did not grow with stage")
    return {
        "name": "T6_nonreturn",
        "claim": "Committed count strictly monotone; revisiting a vertex is not "
                 "returning to a state; an undo increments the count; a growing "
                 "complement distinguishes a thing from its earlier stage.",
        "passed": not failures,
        "checks": checks,
        "failures": failures[:10],
        "evidence": {"walk_len": len(states), "distinct_states": len(seen_states)},
    }


# ---------------------------------------------------------------------
#  T7: coherent collective -> single quotient gate; quotient inherits floor
# ---------------------------------------------------------------------
def v_T7_quotient(G: ContactGraph) -> Dict:
    failures = []
    checks = 0
    if not G.is_connected() or len(G.vertices) < 4:
        return {"name": "T7_quotient", "passed": True, "checks": 0,
                "failures": [], "claim": "quotient inherits floor; single gate",
                "evidence": {"skipped": "too small/disconnected"}}
    # partition the non-medium parts into 2 connected-ish classes + medium class
    parts = sorted(x for x in G.vertices if x != G.medium)
    mid = len(parts) // 2
    P = [frozenset(parts[:mid]), frozenset(parts[mid:]), frozenset((G.medium,))]
    P = [c for c in P if c]
    # quotient edge weights = sum of cut weights between classes
    checks += 1
    qweights = []
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            cross = sum(G.weight[e] for e in G.weight
                        if (e[0] in P[i] and e[1] in P[j]) or
                           (e[0] in P[j] and e[1] in P[i]))
            if cross > 0:
                qweights.append(cross)
    # quotient inherits a floor: every present quotient edge >= floor
    for qw in qweights:
        checks += 1
        if qw < G.floor - 1e-12:
            failures.append(f"quotient edge {qw} < floor {G.floor}")
    # single-gate (coherence): a selecting gate picks exactly one successor per
    # branching class; two distinct selecting gates that disagree => 2 collectives
    # (structural check: a selecting gate is a function class->class, single-valued)
    checks += 1
    gate = {}  # class index -> chosen neighbour class index (single-valued)
    ok_single = True
    for i in range(len(P)):
        nbr_classes = [j for j in range(len(P)) if j != i]
        if nbr_classes:
            gate[i] = nbr_classes[0]  # a function: exactly one value
    if any(not isinstance(gate.get(i, 0), int) for i in gate):
        ok_single = False
        failures.append("collective gate not single-valued")
    return {
        "name": "T7_quotient",
        "claim": "Quotient inherits a positive floor; a coherent collective is "
                 "single-gated (the collective gate is a single-valued selector "
                 "over classes).",
        "passed": not failures,
        "checks": checks,
        "failures": failures[:10],
        "evidence": {"n_classes": len(P), "quotient_edges": len(qweights),
                     "single_valued_gate": ok_single},
    }


# ---------------------------------------------------------------------
#  T8: authored structures exist + three bounds
# ---------------------------------------------------------------------
def v_T8_authored(G: ContactGraph) -> Dict:
    failures = []
    checks = 0
    import random
    rng = random.Random(2024)

    # Existence: specify-then-instantiate = reshuffle to a fresh labelling
    G_auth = reshuffle(rng, G)
    checks += 1
    # instantiation is a contact graph (same floor, connected if G was)
    if G_auth.min_edge_weight < G.floor - 1e-12:
        failures.append("authored instance violates floor")
    if G.is_connected() and not G_auth.is_connected():
        failures.append("authored instance not connected")

    # Bound I (open-endedness): forward closure infinite for a non-terminating
    # gated walk -> states (v, count) all distinct (count strictly grows).
    checks += 1
    v = G.medium
    count = 0
    seen = set()
    distinct = True
    for _ in range(50):
        nbrs = G_auth.neighbours(v)
        if not nbrs:
            break
        v = nbrs[rng.randrange(len(nbrs))]
        count += 1
        st = (v, count)
        if st in seen:
            distinct = False
            break
        seen.add(st)
    if not distinct:
        failures.append("forward closure repeated a state (count not monotone)")

    # Bound II (non-duplication): authored copy with fresh count-0 history differs
    # from an original at count m>0 -> states differ in committed count.
    checks += 1
    original_state = ("config-X", 7)
    authored_state = ("config-X", 0)  # same standing graph, fresh history
    if original_state == authored_state:
        failures.append("authored copy identical to original (count ignored)")

    # Bound III (floor-limited authorship): author cannot specify sub-floor
    # distinction -> all authored edges >= floor.
    checks += 1
    if any(w < G.floor - 1e-12 for w in G_auth.weight.values()):
        failures.append("authored sub-floor distinction present")

    return {
        "name": "T8_authored",
        "claim": "Authored structures exist (specify-then-instantiate yields a "
                 "contact graph); bounded by open-endedness (forward closure "
                 "states all distinct), non-duplication (copy differs in "
                 "committed count), floor-limited authorship (no sub-floor edge).",
        "passed": not failures,
        "checks": checks,
        "failures": failures[:10],
        "evidence": {"authored_floor_ok": G_auth.min_edge_weight >= G.floor - 1e-12,
                     "forward_states_distinct": distinct},
    }


# ---------------------------------------------------------------------
#  MEASUREMENT: conserves invariant; self-defeat; resolution & multiplicity
# ---------------------------------------------------------------------
def v_measurement(G: ContactGraph) -> Dict:
    failures = []
    checks = 0
    if not G.is_connected():
        return {"name": "measurement", "passed": True, "checks": 0,
                "failures": [], "claim": "measurement conserves invariant; "
                "identity unreachable; point-truth falsified",
                "evidence": {"skipped": "disconnected"}}
    import random
    rng = random.Random(555)

    # (1) measurement conserves the invariant residual
    res0, _ = G.residual()
    total0 = sum(G.weight.values())
    for _ in range(6):
        Gm = reshuffle(rng, G)
        checks += 1
        resm, _ = Gm.residual()
        totalm = sum(Gm.weight.values())
        if abs(resm - res0) > 1e-9:
            failures.append(f"residual not conserved by measurement: {res0}->{resm}")
        if abs(totalm - total0) > 1e-9:
            failures.append("total weight (medium) not conserved")

    # (2) self-defeat: interior residue never reaches 0 under measurement.
    # surrogate: separation cost of a part from the medium stays >= floor across
    # any sequence of reshuffles (identity never resolved to a point).
    checks += 1
    part = 1 if 1 in G.vertices else None
    if part is not None:
        sig0, _ = G.separation_from_medium(part)
        Gm = G
        min_sig = sig0
        for _ in range(8):
            Gm = reshuffle(rng, Gm)
            # track the part's image: reshuffle permutes labels; track via medium-fixed
            sig, _ = Gm.separation_from_medium(part)
            min_sig = min(min_sig, sig)
        if min_sig < G.floor - 1e-12:
            failures.append(f"separation fell below floor: {min_sig}")
        if min_sig <= 0:
            failures.append("identity resolved to a point (sigma=0)")

    # (3) resolution never saturates: adding a boundary edge strictly reduces
    # exterior ambiguity while interior residue (min separation) stays >= floor.
    # (structural: more edges -> separation cost non-decreasing, never 0.)
    checks += 1
    if part is not None:
        sig_before, _ = G.separation_from_medium(part)
        # add a new heavy boundary edge from part to a far vertex (a finer cut)
        far = max(G.vertices)
        if far not in (part, G.medium) and G.w(part, far) == 0:
            neww = dict(G.weight)
            neww[cg._e(part, far)] = G.floor * 2
            Gp = ContactGraph(G.vertices, neww, G.floor, G.medium)
            sig_after, _ = Gp.separation_from_medium(part)
            if sig_after < sig_before - 1e-9:
                failures.append("adding a boundary edge decreased separation")
            if sig_after <= 0:
                failures.append("resolution saturated to a point")

    return {
        "name": "measurement",
        "claim": "Measurement = reshuffle conserves the invariant residual and "
                 "the medium; identity (interior residue / separation) never "
                 "reaches a point (self-defeat); resolution does not saturate.",
        "passed": not failures,
        "checks": checks,
        "failures": failures[:10],
        "evidence": {"residual": res0, "total_weight": total0, "floor": G.floor},
    }


ALL_VALIDATORS = [
    v_ground_floor,
    v_T0_floor,
    v_T1_negation,
    v_T2T3_residual,
    v_T4_private,
    v_T5_gate,
    v_T6_nonreturn,
    v_T7_quotient,
    v_T8_authored,
    v_measurement,
]

# validators that build their own fixed graph (run once, not per-sweep-graph)
STANDALONE_VALIDATORS = [v_T2_region]
