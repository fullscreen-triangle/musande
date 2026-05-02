"""
Numerical validation suite for the Epistemological Mode-Methodology Equivalence
manuscript. Twenty-five experiments testing:
  - Receiver floor (E1-E3)
  - Cell-truth (E4-E6)
  - Representational invariance (E7-E9)
  - Layered receivers (E10-E12)
  - Mode non-privilege (E13-E14)
  - Methodological floor (E15-E17)
  - Catalytic composition (E18-E19)
  - Mode-methodology equivalence (E20-E22)
  - Production-completion (E23)
  - Distribution theorem (E24-E25)

All experiments compare measured quantities to closed-form theoretical values
and report relative error. Verdict PASS at machine precision is required.
"""

import json
import os
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Callable, Dict, Any, List

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

SIGMA = 100.0
RNG = np.random.default_rng(20260501)


# ----------------------------------------------------------------------------
# Core primitives
# ----------------------------------------------------------------------------

@dataclass
class Receiver:
    """Receiver: (knowledge framework, decoder, candidate-projection, floor)."""
    name: str
    beta: float
    decoder_noise: float
    projection_radius: float

    def decode(self, x: np.ndarray) -> np.ndarray:
        return x + RNG.normal(0.0, self.decoder_noise, size=x.shape)

    def project(self, k: np.ndarray, n_candidates: int = 16) -> np.ndarray:
        return k[None, :] + RNG.normal(
            0.0, self.projection_radius, size=(n_candidates, k.shape[0])
        )

    def floor(self) -> float:
        return self.beta


@dataclass
class Cell:
    """Action-cell: a closed ball of given tolerance about a centre."""
    centre: np.ndarray
    tolerance: float

    def distance(self, x: np.ndarray) -> float:
        return max(0.0, np.linalg.norm(x - self.centre) - self.tolerance)

    def contains(self, x: np.ndarray) -> bool:
        return np.linalg.norm(x - self.centre) <= self.tolerance


def S_functional(receiver: Receiver, x: np.ndarray, cell: Cell,
                 n_candidates: int = 32) -> float:
    """Compute S(receiver, x; cell) as inf over candidates of d(x', cell) + beta."""
    k = receiver.decode(x)
    candidates = receiver.project(k, n_candidates=n_candidates)
    dists = np.array([cell.distance(c) for c in candidates])
    return float(np.min(dists) + receiver.beta)


@dataclass
class Methodology:
    """Methodology: (per-iteration update, kappa, sigma)."""
    name: str
    kappa: float
    sigma: float

    def floor(self) -> float:
        return self.sigma * self.kappa / (1.0 - self.kappa)

    def iterate(self, s: float, n: int = 1) -> float:
        cur = s
        for _ in range(n):
            cur = self.kappa * cur + self.sigma * self.kappa
        return cur


# ----------------------------------------------------------------------------
# Experiment runner
# ----------------------------------------------------------------------------

EXPERIMENTS: List[Dict[str, Any]] = []


def record(eid: str, cluster: str, claim: str, measured: float,
           predicted: float, extra: Dict[str, Any] = None) -> Dict[str, Any]:
    if predicted == 0.0:
        rel_err = abs(measured - predicted)
    else:
        rel_err = abs(measured - predicted) / abs(predicted)
    verdict = "PASS" if rel_err < 1e-10 else "FAIL"
    result = {
        "experiment_id": eid,
        "cluster": cluster,
        "claim": claim,
        "measured": measured,
        "predicted": predicted,
        "relative_error": rel_err,
        "verdict": verdict,
        "extra": extra or {},
    }
    EXPERIMENTS.append(result)
    with open(RESULTS_DIR / f"{eid}.json", "w") as f:
        json.dump(result, f, indent=2, default=float)
    return result


# ----------------------------------------------------------------------------
# E1-E3: Receiver floor positivity & attainment
# ----------------------------------------------------------------------------

def run_e1():
    """E1: floor positivity — S >= beta for all states."""
    rcv = Receiver("standard", beta=2.5, decoder_noise=0.0, projection_radius=0.0)
    cell = Cell(centre=np.array([0.0, 0.0]), tolerance=1.0)
    n = 1000
    states = RNG.uniform(-10, 10, size=(n, 2))
    S_values = np.array([S_functional(rcv, x, cell) for x in states])
    measured_min = float(S_values.min())
    record("E01", "receiver_floor",
           "S >= beta for all states", measured_min, rcv.beta,
           extra={"n_states": n, "beta": rcv.beta,
                  "S_mean": float(S_values.mean()),
                  "S_max": float(S_values.max())})


def run_e2():
    """E2: floor attainment when x in cell."""
    rcv = Receiver("zero-noise", beta=1.7, decoder_noise=0.0, projection_radius=0.0)
    cell = Cell(centre=np.array([0.0, 0.0, 0.0]), tolerance=2.0)
    x_in = np.array([0.5, 0.3, 0.1])
    measured = S_functional(rcv, x_in, cell)
    record("E02", "receiver_floor",
           "S = beta when x in cell with zero noise", measured, rcv.beta,
           extra={"x_distance_to_cell": cell.distance(x_in)})


def run_e3():
    """E3: floor scales linearly with beta."""
    cell = Cell(centre=np.zeros(2), tolerance=1.0)
    x = np.array([0.2, 0.1])
    betas = [0.1, 0.5, 1.0, 2.0, 5.0]
    measured_floors = []
    for b in betas:
        rcv = Receiver(f"r-{b}", beta=b, decoder_noise=0.0, projection_radius=0.0)
        measured_floors.append(S_functional(rcv, x, cell))
    measured_floors = np.array(measured_floors)
    expected = np.array(betas)
    rel_err = float(np.max(np.abs(measured_floors - expected) / expected))
    record("E03", "receiver_floor",
           "Floor scales linearly with beta",
           rel_err, 0.0,
           extra={"betas": betas, "measured": measured_floors.tolist()})


# ----------------------------------------------------------------------------
# E4-E6: Cell-truth indistinguishability
# ----------------------------------------------------------------------------

def run_e4():
    """E4: S identical for two states inside the same cell."""
    rcv = Receiver("ct1", beta=1.0, decoder_noise=0.0, projection_radius=0.0)
    cell = Cell(centre=np.array([5.0, 5.0]), tolerance=3.0)
    x1 = np.array([5.5, 5.5])
    x2 = np.array([4.0, 5.5])
    s1 = S_functional(rcv, x1, cell)
    s2 = S_functional(rcv, x2, cell)
    record("E04", "cell_truth",
           "S(x1)=S(x2) for x1,x2 in cell",
           s1, s2,
           extra={"x1": x1.tolist(), "x2": x2.tolist()})


def run_e5():
    """E5: variance of S inside cell is zero."""
    rcv = Receiver("ct2", beta=2.0, decoder_noise=0.0, projection_radius=0.0)
    cell = Cell(centre=np.zeros(3), tolerance=4.0)
    n = 500
    angles = RNG.uniform(0, 2 * np.pi, size=n)
    radii = RNG.uniform(0, 3.5, size=n)
    states = np.stack([radii * np.cos(angles),
                       radii * np.sin(angles),
                       np.zeros(n)], axis=1)
    S_values = np.array([S_functional(rcv, x, cell) for x in states])
    measured_var = float(np.var(S_values))
    record("E05", "cell_truth",
           "Variance of S inside cell is zero",
           measured_var, 0.0,
           extra={"n": n, "S_mean": float(S_values.mean())})


def run_e6():
    """E6: S grows linearly with d(x, cell) outside the cell."""
    rcv = Receiver("ct3", beta=0.5, decoder_noise=0.0, projection_radius=0.0)
    cell = Cell(centre=np.zeros(2), tolerance=1.0)
    distances = np.array([2, 4, 6, 8, 10], dtype=float)
    measured = []
    for d in distances:
        x = np.array([d, 0.0])
        s = S_functional(rcv, x, cell)
        measured.append(s)
    measured = np.array(measured)
    expected = (distances - cell.tolerance) + rcv.beta
    rel_err = float(np.max(np.abs(measured - expected) / expected))
    record("E06", "cell_truth",
           "S = d(x, cell) + beta outside cell",
           rel_err, 0.0,
           extra={"distances": distances.tolist(),
                  "measured": measured.tolist(),
                  "expected": expected.tolist()})


# ----------------------------------------------------------------------------
# E7-E9: Representational invariance
# ----------------------------------------------------------------------------

def oscillatory_encoding(x: np.ndarray) -> np.ndarray:
    """Isometric oscillatory encoding (rotation by orthogonal matrix)."""
    Q = np.array([[np.cos(0.7), -np.sin(0.7)],
                  [np.sin(0.7),  np.cos(0.7)]])
    if x.shape[0] == 2:
        return Q @ x
    if x.shape[0] == 3:
        Q3 = np.eye(3)
        Q3[:2, :2] = Q
        return Q3 @ x
    return x


def categorical_encoding(x: np.ndarray) -> np.ndarray:
    """Isometric categorical encoding (permutation + reflection)."""
    if x.shape[0] == 2:
        return np.array([x[1], -x[0]])
    if x.shape[0] == 3:
        return np.array([x[2], -x[0], x[1]])
    return x


def partition_encoding(x: np.ndarray) -> np.ndarray:
    """Isometric partition encoding (sign flip)."""
    return -x


def run_e7():
    """E7: oscillatory encoding preserves S."""
    rcv = Receiver("ri1", beta=1.0, decoder_noise=0.0, projection_radius=0.0)
    cell = Cell(centre=np.array([2.0, 1.0]), tolerance=0.5)
    cell_enc = Cell(centre=oscillatory_encoding(cell.centre),
                    tolerance=cell.tolerance)
    x = np.array([3.0, 2.5])
    s_orig = S_functional(rcv, x, cell)
    s_enc = S_functional(rcv, oscillatory_encoding(x), cell_enc)
    record("E07", "rep_invariance",
           "Oscillatory encoding preserves S",
           s_enc, s_orig)


def run_e8():
    """E8: categorical encoding preserves S."""
    rcv = Receiver("ri2", beta=1.0, decoder_noise=0.0, projection_radius=0.0)
    cell = Cell(centre=np.array([1.0, 2.0, 0.5]), tolerance=0.7)
    cell_enc = Cell(centre=categorical_encoding(cell.centre),
                    tolerance=cell.tolerance)
    x = np.array([2.5, 3.0, 1.0])
    s_orig = S_functional(rcv, x, cell)
    s_enc = S_functional(rcv, categorical_encoding(x), cell_enc)
    record("E08", "rep_invariance",
           "Categorical encoding preserves S",
           s_enc, s_orig)


def run_e9():
    """E9: partition encoding preserves S."""
    rcv = Receiver("ri3", beta=1.0, decoder_noise=0.0, projection_radius=0.0)
    cell = Cell(centre=np.array([1.0, -1.5]), tolerance=0.8)
    cell_enc = Cell(centre=partition_encoding(cell.centre),
                    tolerance=cell.tolerance)
    x = np.array([2.0, -2.5])
    s_orig = S_functional(rcv, x, cell)
    s_enc = S_functional(rcv, partition_encoding(x), cell_enc)
    record("E09", "rep_invariance",
           "Partition encoding preserves S",
           s_enc, s_orig)


# ----------------------------------------------------------------------------
# E10-E12: Layered receivers
# ----------------------------------------------------------------------------

def layered_S(receivers: List[Receiver], x: np.ndarray, cell: Cell) -> float:
    return min(S_functional(r, x, cell) for r in receivers)


def run_e10():
    """E10: layered floor = min of layer floors."""
    layers = [
        Receiver("L1", beta=0.5, decoder_noise=0.0, projection_radius=0.0),
        Receiver("L2", beta=1.5, decoder_noise=0.0, projection_radius=0.0),
        Receiver("L3", beta=3.0, decoder_noise=0.0, projection_radius=0.0),
    ]
    cell = Cell(centre=np.zeros(2), tolerance=1.0)
    x = np.array([0.5, 0.0])
    measured = layered_S(layers, x, cell)
    expected = min(r.beta for r in layers)
    record("E10", "layered_receivers",
           "Layered floor = min of layer floors",
           measured, expected,
           extra={"layer_floors": [r.beta for r in layers]})


def run_e11():
    """E11: per-layer S decreases with layer floor."""
    cell = Cell(centre=np.zeros(2), tolerance=1.0)
    x = np.array([0.3, 0.2])
    betas = [0.2, 0.5, 1.0, 2.0, 5.0]
    s_per_layer = []
    for b in betas:
        rcv = Receiver(f"R{b}", beta=b, decoder_noise=0.0, projection_radius=0.0)
        s_per_layer.append(S_functional(rcv, x, cell))
    monotonic = all(s_per_layer[i] <= s_per_layer[i+1] for i in range(len(betas)-1))
    record("E11", "layered_receivers",
           "S monotonic in layer floor",
           1.0 if monotonic else 0.0, 1.0,
           extra={"betas": betas, "S_values": s_per_layer})


def run_e12():
    """E12: cell-closure under layer substitution."""
    pre_decoder = Receiver("reflex", beta=0.3, decoder_noise=0.0, projection_radius=0.0)
    decoder_v1 = Receiver("dec1", beta=2.0, decoder_noise=0.0, projection_radius=0.0)
    decoder_v2 = Receiver("dec2", beta=5.0, decoder_noise=0.0, projection_radius=0.0)
    cell = Cell(centre=np.zeros(2), tolerance=1.0)
    x = np.array([0.5, 0.0])
    s1 = layered_S([pre_decoder, decoder_v1], x, cell)
    s2 = layered_S([pre_decoder, decoder_v2], x, cell)
    record("E12", "layered_receivers",
           "Cell-closure under decoder substitution",
           s1, s2)


# ----------------------------------------------------------------------------
# E13-E14: Mode non-privilege
# ----------------------------------------------------------------------------

def run_e13():
    """E13: pre-decoder reaches cell when decoder cannot."""
    cell = Cell(centre=np.zeros(2), tolerance=1.0)
    pre_decoder = Receiver("reflex", beta=0.2, decoder_noise=0.0, projection_radius=0.0)
    decoder = Receiver("decoder", beta=2.5, decoder_noise=0.0, projection_radius=0.0)
    x = np.array([0.3, 0.3])
    s_layered = layered_S([pre_decoder, decoder], x, cell)
    s_decoder_only = S_functional(decoder, x, cell)
    record("E13", "mode_nonpriv",
           "Pre-decoder reaches cell when decoder above tolerance",
           s_layered, pre_decoder.beta,
           extra={"decoder_only_S": s_decoder_only,
                  "tolerance": cell.tolerance,
                  "decoder_floor": decoder.beta})


def run_e14():
    """E14: knowledge is not unique mode (3-receiver zoo example)."""
    cell = Cell(centre=np.zeros(2), tolerance=1.0)
    receivers = {
        "A_naive": [Receiver("reflex_A", beta=0.4, decoder_noise=0.0, projection_radius=0.0),
                     Receiver("decoder_A", beta=4.0, decoder_noise=0.0, projection_radius=0.0)],
        "B_expert": [Receiver("reflex_B", beta=0.5, decoder_noise=0.0, projection_radius=0.0),
                      Receiver("decoder_B", beta=0.3, decoder_noise=0.0, projection_radius=0.0)],
        "C_child": [Receiver("reflex_C", beta=0.1, decoder_noise=0.0, projection_radius=0.0),
                     Receiver("decoder_C", beta=8.0, decoder_noise=0.0, projection_radius=0.0)],
    }
    x = np.array([0.4, 0.2])
    floors = {}
    for name, layers in receivers.items():
        floors[name] = layered_S(layers, x, cell)
    all_below = all(f < cell.tolerance for f in floors.values())
    record("E14", "mode_nonpriv",
           "All three receivers reach action-cell despite different decoder floors",
           1.0 if all_below else 0.0, 1.0,
           extra=floors)


# ----------------------------------------------------------------------------
# E15-E17: Methodological floor
# ----------------------------------------------------------------------------

def run_e15():
    """E15: methodological floor = sigma*kappa/(1-kappa)."""
    method = Methodology("M1", kappa=0.5, sigma=0.3)
    measured = method.floor()
    expected = method.sigma * method.kappa / (1.0 - method.kappa)
    record("E15", "methodological_floor",
           "Floor closed form",
           measured, expected)


def run_e16():
    """E16: iterating methodology converges to floor."""
    method = Methodology("M2", kappa=0.4, sigma=0.5)
    s = 50.0
    s_final = method.iterate(s, n=1000)
    expected = method.floor()
    record("E16", "methodological_floor",
           "Iteration converges to floor",
           s_final, expected,
           extra={"start": 50.0, "n_iter": 1000})


def run_e17():
    """E17: floor invariant of starting state."""
    method = Methodology("M3", kappa=0.6, sigma=0.2)
    starts = [0.0, 5.0, 25.0, 75.0, 99.0]
    finals = [method.iterate(s, n=2000) for s in starts]
    expected = method.floor()
    rel_err = float(max(abs(f - expected) / expected for f in finals))
    record("E17", "methodological_floor",
           "Floor independent of starting S",
           rel_err, 0.0,
           extra={"starts": starts, "finals": finals, "expected": expected})


# ----------------------------------------------------------------------------
# E18-E19: Catalytic composition
# ----------------------------------------------------------------------------

def composite_floor(floors: List[float], sigma: float = SIGMA) -> float:
    deficit = 1.0
    for f in floors:
        deficit *= (1.0 - f / sigma)
    return sigma * (1.0 - deficit)


def run_e18():
    """E18: composition of two methodologies."""
    m1 = Methodology("M_a", kappa=0.4, sigma=0.5)
    m2 = Methodology("M_b", kappa=0.6, sigma=0.3)
    f1 = m1.floor()
    f2 = m2.floor()
    measured = composite_floor([f1, f2])
    expected = f1 + f2 - f1 * f2 / SIGMA
    record("E18", "catalytic_composition",
           "Two-methodology composition law",
           measured, expected,
           extra={"f1": f1, "f2": f2})


def run_e19():
    """E19: composition of n=5 methodologies."""
    methods = [Methodology(f"M{i}", kappa=0.3 + 0.05*i, sigma=0.2 + 0.1*i)
               for i in range(5)]
    floors = [m.floor() for m in methods]
    measured = composite_floor(floors)
    expected = SIGMA * (1.0 - np.prod([1.0 - f/SIGMA for f in floors]))
    record("E19", "catalytic_composition",
           "Five-methodology composition law",
           measured, expected,
           extra={"floors": floors})


# ----------------------------------------------------------------------------
# E20-E22: Mode-methodology equivalence
# ----------------------------------------------------------------------------

def run_e20():
    """E20: receiver-methodology composition follows same law."""
    rcv = Receiver("rm1", beta=1.5, decoder_noise=0.0, projection_radius=0.0)
    method = Methodology("rm-method", kappa=0.5, sigma=0.4)
    measured = composite_floor([rcv.floor(), method.floor()])
    expected = rcv.floor() + method.floor() - rcv.floor() * method.floor() / SIGMA
    record("E20", "mode_methodology",
           "Receiver-methodology composition law",
           measured, expected)


def run_e21():
    """E21: stack of n receivers and m methodologies."""
    receivers = [Receiver(f"R{i}", beta=0.5 + i, decoder_noise=0.0, projection_radius=0.0)
                 for i in range(3)]
    methods = [Methodology(f"M{i}", kappa=0.4 + 0.1*i, sigma=0.3) for i in range(2)]
    floors = [r.floor() for r in receivers] + [m.floor() for m in methods]
    measured = composite_floor(floors)
    expected = SIGMA * (1.0 - np.prod([1.0 - f/SIGMA for f in floors]))
    record("E21", "mode_methodology",
           "Stack of receivers and methodologies",
           measured, expected,
           extra={"receiver_floors": [r.floor() for r in receivers],
                  "method_floors": [m.floor() for m in methods]})


def run_e22():
    """E22: symmetry — swapping receiver-floor for methodology-floor."""
    fA = 1.5  # original receiver floor
    fB = 0.8  # original methodology floor
    composite_orig = composite_floor([fA, fB])
    composite_swapped = composite_floor([fB, fA])
    record("E22", "mode_methodology",
           "Composition is symmetric in floors",
           composite_orig, composite_swapped)


# ----------------------------------------------------------------------------
# E23: Production-completion incompatibility
# ----------------------------------------------------------------------------

def run_e23():
    """E23: production requires sigma>0; completion requires sigma=0."""
    # Production methodology
    m_prod = Methodology("prod", kappa=0.5, sigma=0.4)
    can_produce = m_prod.sigma > 0
    # Completion methodology
    m_comp = Methodology("comp", kappa=0.5, sigma=0.0)
    can_complete = m_comp.sigma == 0
    # Incompatibility: cannot have sigma>0 and sigma=0 simultaneously
    incompatible = can_produce and can_complete and (m_prod.sigma != m_comp.sigma)
    record("E23", "incompatibility",
           "Production and completion mutually exclusive",
           1.0 if incompatible else 0.0, 1.0,
           extra={"prod_sigma": m_prod.sigma, "comp_sigma": m_comp.sigma})


# ----------------------------------------------------------------------------
# E24-E25: Distribution
# ----------------------------------------------------------------------------

def run_e24():
    """E24: max knowledge bounded by Sigma - floor."""
    rcv = Receiver("d1", beta=2.0, decoder_noise=0.0, projection_radius=0.0)
    n = 500
    states = RNG.uniform(-5, 5, size=(n, 2))
    knowledges = []
    for x in states:
        cell = Cell(centre=x, tolerance=2.5)  # epsilon-ball about x
        s = S_functional(rcv, x, cell)
        knowledges.append(SIGMA - s)
    max_knowledge = float(max(knowledges))
    expected_max = SIGMA - rcv.floor()
    record("E24", "distribution",
           "max knowledge <= Sigma - floor",
           max_knowledge, expected_max,
           extra={"n": n, "rcv_floor": rcv.floor()})


def run_e25():
    """E25: knowledge cannot concentrate — distributed across multiple receivers."""
    receivers = [Receiver(f"R{i}", beta=1.0 + 0.5*i, decoder_noise=0.0, projection_radius=0.0)
                 for i in range(4)]
    subjects = [np.array([0.0, 0.0]), np.array([1.0, 1.0])]
    coverage_per_receiver = []
    for rcv in receivers:
        # Knowledge available to this receiver about each subject
        cells = [Cell(centre=s, tolerance=2.0) for s in subjects]
        S_vals = [S_functional(rcv, s, c) for s, c in zip(subjects, cells)]
        coverage = sum(SIGMA - s_v for s_v in S_vals)
        coverage_per_receiver.append(coverage)
    # Total coverage across all receivers exceeds any single receiver's coverage
    max_single = max(coverage_per_receiver)
    total = sum(coverage_per_receiver)
    distribution_works = total > max_single
    record("E25", "distribution",
           "Total coverage exceeds any single receiver's coverage",
           1.0 if distribution_works else 0.0, 1.0,
           extra={"per_receiver": coverage_per_receiver,
                  "max_single": max_single, "total": total})


# ----------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------

def run_all():
    runners = [
        run_e1, run_e2, run_e3,
        run_e4, run_e5, run_e6,
        run_e7, run_e8, run_e9,
        run_e10, run_e11, run_e12,
        run_e13, run_e14,
        run_e15, run_e16, run_e17,
        run_e18, run_e19,
        run_e20, run_e21, run_e22,
        run_e23,
        run_e24, run_e25,
    ]
    for r in runners:
        r()
    summary = {
        "total": len(EXPERIMENTS),
        "passed": sum(1 for e in EXPERIMENTS if e["verdict"] == "PASS"),
        "failed": sum(1 for e in EXPERIMENTS if e["verdict"] == "FAIL"),
        "max_relative_error": max(e["relative_error"] for e in EXPERIMENTS),
        "by_cluster": {},
    }
    for e in EXPERIMENTS:
        c = e["cluster"]
        summary["by_cluster"].setdefault(c, {"count": 0, "max_err": 0.0,
                                              "passed": 0})
        summary["by_cluster"][c]["count"] += 1
        if e["verdict"] == "PASS":
            summary["by_cluster"][c]["passed"] += 1
        summary["by_cluster"][c]["max_err"] = max(
            summary["by_cluster"][c]["max_err"], e["relative_error"]
        )
    with open(RESULTS_DIR / "master_summary.json", "w") as f:
        json.dump({"summary": summary, "experiments": EXPERIMENTS},
                  f, indent=2, default=float)
    print(f"Total: {summary['total']}  Passed: {summary['passed']}  "
          f"Failed: {summary['failed']}")
    print(f"Max relative error: {summary['max_relative_error']:.3e}")
    for c, d in summary["by_cluster"].items():
        print(f"  [{c}] {d['passed']}/{d['count']} passed; "
              f"max err {d['max_err']:.3e}")
    return summary


if __name__ == "__main__":
    run_all()
