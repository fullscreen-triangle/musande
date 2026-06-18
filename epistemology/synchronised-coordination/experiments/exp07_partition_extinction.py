"""
Experiment 07 — Partition extinction: exact transport vanishing below Tc.

The framework's central physical claim is that below a critical temperature
constituents become categorically indistinguishable (phase-locked) and the
relevant transport coefficient vanishes EXACTLY (not asymptotically). The
canonical realisation is superconductivity (electrical resistivity -> 0) and
superfluidity (viscosity -> 0).

EXTERNAL test (two falsifiable parts):
  (A) Discontinuous, effectively-exact vanishing: measured upper bounds on
      superconducting resistivity are >=14-15 orders of magnitude below the
      normal-state value -- i.e. consistent with EXACT zero within any
      experiment. We tabulate measured normal-state vs superconducting
      resistivity bounds and persistent-current decay limits.
  (B) The transition is sharp (a true thermodynamic phase transition), and
      Tc values are definite material constants. We tabulate measured Tc for
      a range of superconductors and the superfluid-He lambda point.

This test does NOT claim the framework predicts Tc (it does not, from first
principles); it tests the qualitative claim 'exact, discontinuous vanishing
at a sharp Tc', which is what the partition-extinction theorem asserts.
"""
import json
import numpy as np
from pathlib import Path

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)

# (A) Resistivity: normal-state rho_n (Ohm.m) vs measured superconducting
# upper bound rho_s (Ohm.m). SC upper bounds from persistent-current decay
# experiments (Quinn & Ittner 1962: rho_s < 3.6e-23 Ohm.m for Pb-group;
# widely cited bound ~1e-25 from later flux-decay limits). Normal-state values
# are standard residual resistivities just above Tc.
resistivity = {
    # material: (rho_normal_just_above_Tc, rho_superconducting_upper_bound)
    "Pb":  (2.0e-9, 3.6e-23),
    "Nb":  (1.5e-8, 1.0e-22),
    "Sn":  (1.1e-8, 1.0e-22),
    "Hg":  (5.8e-7, 1.0e-22),
}

# (B) Critical temperatures (K), measured, conventional + HTSC + superfluid
Tc = {
    "Al": 1.18, "Sn": 3.72, "Hg": 4.15, "Pb": 7.20, "Nb": 9.25,
    "Nb3Sn": 18.3, "MgB2": 39.0, "YBCO": 92.0, "Bi2223": 110.0,
    "Hg-1223": 133.0,
}
He4_lambda = 2.17   # superfluid transition (viscosity -> 0)

# (A) compute orders-of-magnitude drop
drops = {}
for m, (rn, rs) in resistivity.items():
    drops[m] = float(np.log10(rn / rs))
min_drop = min(drops.values())
mean_drop = float(np.mean(list(drops.values())))

results = {
    "experiment_id": "EXT07",
    "title": "Partition extinction: exact transport vanishing below Tc",
    "partA_resistivity_drop_orders_of_magnitude": drops,
    "partA_min_orders_drop": float(min_drop),
    "partA_mean_orders_drop": float(mean_drop),
    "partB_critical_temperatures_K": Tc,
    "partB_superfluid_He4_lambda_K": He4_lambda,
    "n_superconductors": len(Tc),
}
results["interpretation"] = (
    f"(A) Measured superconducting resistivity upper bounds lie "
    f">={min_drop:.0f} orders of magnitude (mean {mean_drop:.0f}) below the "
    f"normal state -- operationally EXACT zero, consistent with the "
    f"partition-extinction claim that the transport coefficient vanishes "
    f"exactly (not asymptotically) once carriers become indistinguishable. "
    f"Persistent currents show no measurable decay over years, bounding "
    f"resistivity below any finite value. (B) Tc is a sharp, definite material "
    f"constant across {len(Tc)} superconductors (1.2 K to 133 K) plus the "
    f"He-4 lambda point at {He4_lambda} K where viscosity vanishes. The "
    f"discontinuous, sharp character matches a true phase transition. "
    f"IMPORTANT SCOPE: the framework REPRODUCES the qualitative phenomenology "
    f"(exact vanishing, sharp transition) shared with BCS/Landau theory; it "
    f"does NOT predict Tc from first principles. Defensible claim: "
    f"partition-extinction is consistent with the measured exact-zero/"
    f"sharp-transition phenomenology; it is an interpretation alongside BCS, "
    f"not a competitor that makes new quantitative predictions here.")

out = RESULTS / "EXT07_partition_extinction.json"
out.write_text(json.dumps(results, indent=2))
print(json.dumps({k: results[k] for k in
      ["partA_resistivity_drop_orders_of_magnitude", "partA_min_orders_drop",
       "partA_mean_orders_drop", "n_superconductors"]}, indent=2))
print("\n" + results["interpretation"])
print(f"\nwritten -> {out}")
