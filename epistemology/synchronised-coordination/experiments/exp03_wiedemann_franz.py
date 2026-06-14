"""
Experiment 03 — Wiedemann-Franz universality against real metals.

The partition-extinction framework predicts that the Lorenz ratio
L = kappa / (sigma * T) is a UNIVERSAL constant (the same combinatorial
partition structure underlies both electrical and thermal transport, so
their ratio is geometry-independent). Standard physics gives the
Sommerfeld value L0 = (pi^2/3)(k_B/e)^2 = 2.44e-8 W.Ohm.K^-2.

EXTERNAL test: compare the predicted universal L0 to *measured* Lorenz
numbers for real metals (Kittel, Introduction to Solid State Physics,
Table on Wiedemann-Franz law; values widely reproduced). If L clusters
tightly around L0 across chemically diverse metals, the universality claim
is supported; the spread quantifies where it breaks (inelastic/phonon-drag
scattering at intermediate T). Honest reporting of the spread is the point.
"""
import json
import numpy as np
from pathlib import Path

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)

# Sommerfeld (theoretical) Lorenz number, W.Ohm.K^-2
L0 = (np.pi ** 2 / 3.0) * (1.380649e-23 / 1.602176634e-19) ** 2

# Measured Lorenz numbers L (10^-8 W.Ohm.K^-2), Kittel ISSP Table (WF law).
# Two columns: 0 C and 100 C. (Standard textbook values; Cu 0C = 2.23 and
# W 100C = 3.2 cross-checked against Wikipedia's WF-law article.)
measured = {
    "Ag": (2.31, 2.37),
    "Au": (2.35, 2.40),
    "Cd": (2.42, 2.43),
    "Cu": (2.23, 2.33),
    "Ir": (2.49, 2.49),
    "Mo": (2.61, 2.79),
    "Pb": (2.47, 2.56),
    "Pt": (2.51, 2.60),
    "Sn": (2.52, 2.49),
    "W":  (3.04, 3.20),
    "Zn": (2.31, 2.33),
}

L0_e8 = L0 * 1e8   # in units of 10^-8

vals_0C = np.array([v[0] for v in measured.values()])
vals_100C = np.array([v[1] for v in measured.values()])
allvals = np.concatenate([vals_0C, vals_100C])

def stats(a):
    return {"mean": float(np.mean(a)), "std": float(np.std(a)),
            "min": float(np.min(a)), "max": float(np.max(a))}

# Fractional deviation of each measurement from the universal prediction
dev_0C = (vals_0C - L0_e8) / L0_e8
dev_100C = (vals_100C - L0_e8) / L0_e8

results = {
    "experiment_id": "EXT03",
    "title": "Wiedemann-Franz universality: predicted L0 vs measured metals",
    "L0_sommerfeld_W_Ohm_K2": L0,
    "L0_in_1e-8_units": L0_e8,
    "n_metals": len(measured),
    "metals": list(measured.keys()),
    "measured_0C_1e-8": vals_0C.tolist(),
    "measured_100C_1e-8": vals_100C.tolist(),
    "stats_0C": stats(vals_0C),
    "stats_100C": stats(vals_100C),
    "stats_all": stats(allvals),
    "mean_frac_dev_0C": float(np.mean(np.abs(dev_0C))),
    "mean_frac_dev_100C": float(np.mean(np.abs(dev_100C))),
    "max_frac_dev": float(np.max(np.abs(np.concatenate([dev_0C, dev_100C])))),
    "within_15pct_of_L0": int(np.sum(np.abs(np.concatenate([dev_0C, dev_100C])) < 0.15)),
    "n_measurements": int(allvals.size),
}

results["interpretation"] = (
    f"Predicted universal Lorenz number L0 = {L0_e8:.3f}e-8 W.Ohm.K^-2. "
    f"Across {len(measured)} chemically diverse metals, measured L at 0C/100C "
    f"has mean {results['stats_all']['mean']:.3f}e-8 (std "
    f"{results['stats_all']['std']:.3f}e-8). "
    f"{results['within_15pct_of_L0']}/{results['n_measurements']} measurements "
    f"lie within 15% of L0. The clustering supports the universality claim "
    f"(electrical and thermal transport share one partition structure, so "
    f"their ratio is material-independent). The positive outliers (W, Mo) are "
    f"the known transition-metal deviation from elastic-scattering WF and mark "
    f"the regime where the universal ratio is only approximate -- reported, "
    f"not hidden. Note: WF universality is standard physics; the framework "
    f"REPRODUCES it, it does not predict a new value. Claim defensible only as "
    f"'the partition picture is consistent with WF', NOT as novel.")

out = RESULTS / "EXT03_wiedemann_franz.json"
out.write_text(json.dumps(results, indent=2))
print(json.dumps({k: results[k] for k in
                  ["L0_in_1e-8_units", "stats_all", "mean_frac_dev_0C",
                   "mean_frac_dev_100C", "within_15pct_of_L0",
                   "n_measurements"]}, indent=2))
print("\n" + results["interpretation"])
print(f"\nwritten -> {out}")
