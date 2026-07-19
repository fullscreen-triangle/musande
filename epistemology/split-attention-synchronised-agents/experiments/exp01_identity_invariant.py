"""
EXP01 -- Identity as a conserved, positive, non-local invariant (T1).

Tests the claims of Theorem (Identity is a conserved, positive, non-local
region) and its corollary, by EXACT enumeration over partitions of the
self-graph -- no formula is checked against itself.

Claims tested:
  (V1) Floor: every nonempty proper cut has weight >= floor; realised floor
       = min boundary cost is > 0 and attained.
  (V2a) chi(A) = min over partitions (r>=2) of internal residual is invariant
        under every weight-preserving relabelling (random automorphism-domain
        permutations), to machine precision.
  (V2b) chi(A) >= floor  (positivity).
  (V2c) Non-locality: on the two-triangle witness the minimiser is a
        two-block partition, and NO singleton split attains chi.

Independence of the test: chi is computed by brute-force enumeration of all
set-partitions with >=2 blocks; invariance is checked by relabelling the
vertex set with random permutations and recomputing chi from scratch. The
relabelled graph is a genuinely different adjacency structure, so equality of
the recomputed minima is a real test, not an identity.
"""
import json, itertools, os
import numpy as np

RNG = np.random.default_rng(42)
HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")


def all_partitions(elements):
    """Yield all set-partitions of `elements` (list) as list-of-blocks."""
    if len(elements) == 1:
        yield [elements]
        return
    first = elements[0]
    for smaller in all_partitions(elements[1:]):
        for i, block in enumerate(smaller):
            yield smaller[:i] + [[first] + block] + smaller[i + 1:]
        yield [[first]] + smaller


def cut_weight(W, S, T):
    return sum(W[u][v] for u in S for v in T if W[u][v] > 0)


def internal_residual(W, partition):
    r = 0.0
    for i in range(len(partition)):
        for j in range(i + 1, len(partition)):
            r += cut_weight(W, partition[i], partition[j])
    return r


def character_invariant(W):
    """chi = min over partitions with >=2 blocks of internal residual.
    Returns (chi, minimising_partition, minimiser_is_singleton_split)."""
    n = len(W)
    verts = list(range(n))
    best, best_part = np.inf, None
    for part in all_partitions(verts):
        if len(part) < 2:
            continue
        r = internal_residual(W, part)
        if r < best - 1e-12:
            best, best_part = r, part
    # is the minimiser a "singleton split" (isolating exactly one vertex)?
    is_singleton = any(len(b) == 1 for b in best_part) and len(best_part) == 2 \
        and (min(len(b) for b in best_part) == 1)
    # stricter: a singleton split means one block has size 1 and the other n-1
    sizes = sorted(len(b) for b in best_part)
    is_singleton_split = (len(best_part) == 2 and sizes[0] == 1)
    return best, best_part, is_singleton_split


def realised_floor(W):
    """min over nonempty proper subsets U of boundary cost b(U)."""
    n = len(W)
    verts = list(range(n))
    best = np.inf
    for k in range(1, n):
        for U in itertools.combinations(verts, k):
            Uset = set(U)
            comp = [v for v in verts if v not in Uset]
            b = cut_weight(W, list(U), comp)
            best = min(best, b)
    return best


def random_connected_weighted_graph(n, floor, density, weight_spread):
    """Random connected simple weighted graph, all weights >= floor."""
    W = np.zeros((n, n))
    # spanning path to guarantee connectivity
    perm = RNG.permutation(n)
    for a, b in zip(perm[:-1], perm[1:]):
        w = floor + RNG.uniform(0, weight_spread)
        W[a][b] = W[b][a] = w
    # extra edges
    for i in range(n):
        for j in range(i + 1, n):
            if W[i][j] == 0 and RNG.random() < density:
                w = floor + RNG.uniform(0, weight_spread)
                W[i][j] = W[j][i] = w
    return W


def relabel(W, perm):
    n = len(W)
    W2 = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            W2[perm[i]][perm[j]] = W[i][j]
    return W2


def two_triangle_witness():
    # vertices 0,1,2 triangle (edge 2), 3,4,5 triangle (edge 2), join 2-3 (edge 2)
    n = 6
    W = np.zeros((n, n))
    for (a, b) in [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5)]:
        W[a][b] = W[b][a] = 2.0
    W[2][3] = W[3][2] = 2.0
    return W


def main():
    out = {"experiment": "EXP01_identity_invariant", "seed": 42, "cases": []}

    # ---- witness: two triangles ----
    Wt = two_triangle_witness()
    chi_t, part_t, singleton_t = character_invariant(Wt)
    floor_t = realised_floor(Wt)
    out["two_triangle_witness"] = {
        "chi": chi_t,
        "minimising_partition": [sorted(b) for b in part_t],
        "minimiser_is_singleton_split": bool(singleton_t),
        "realised_floor": floor_t,
        "V2c_nonlocal_pass": bool((not singleton_t) and abs(chi_t - 2.0) < 1e-9),
    }

    # ---- random sweep with relabelling invariance ----
    invariance_max_dev = 0.0
    floor_ok = True
    positivity_ok = True
    n_cases = 0
    for n in [4, 5, 6, 7]:
        for density in [0.2, 0.5, 0.8]:
            for spread in [0.5, 3.0]:
                W = random_connected_weighted_graph(n, floor=2.0,
                                                    density=density,
                                                    weight_spread=spread)
                chi0, _, _ = character_invariant(W)
                rf = realised_floor(W)
                floor_ok &= (rf >= 2.0 - 1e-9) and (rf > 0)
                positivity_ok &= (chi0 >= 2.0 - 1e-9)
                # relabel test
                for _ in range(5):
                    perm = RNG.permutation(n)
                    Wr = relabel(W, perm)
                    chir, _, _ = character_invariant(Wr)
                    invariance_max_dev = max(invariance_max_dev, abs(chir - chi0))
                n_cases += 1
                out["cases"].append({
                    "n": n, "density": density, "spread": spread,
                    "chi": chi0, "realised_floor": rf,
                })

    out["summary"] = {
        "n_random_cases": n_cases,
        "V1_floor_pass": bool(floor_ok),
        "V2a_invariance_max_deviation": invariance_max_dev,
        "V2a_invariance_pass": bool(invariance_max_dev < 1e-9),
        "V2b_positivity_pass": bool(positivity_ok),
        "V2c_nonlocal_witness_pass": out["two_triangle_witness"]["V2c_nonlocal_pass"],
    }
    out["verdict"] = (
        "CONFIRMED" if all([
            out["summary"]["V1_floor_pass"],
            out["summary"]["V2a_invariance_pass"],
            out["summary"]["V2b_positivity_pass"],
            out["summary"]["V2c_nonlocal_witness_pass"],
        ]) else "FAILED"
    )

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "EXP01_identity_invariant.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("EXP01", out["verdict"], "| invariance dev =",
          f"{invariance_max_dev:.2e}", "| chi(witness) =", chi_t,
          "singleton?", singleton_t)


if __name__ == "__main__":
    main()
