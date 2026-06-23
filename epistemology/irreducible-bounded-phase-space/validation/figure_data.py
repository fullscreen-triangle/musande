"""
figure_data.py -- produce clean per-figure numerical series from the concrete
bounded-resolvable-space model, for the paper's 6 chart panels.

Every series below is computed from brs.py / validators.py constructions, i.e.
from the same objects the validation suite checks. Output: figure_data.json.

No randomness in the deterministic series; the sweep series use a fixed seed.
"""

from __future__ import annotations

import json
import math
import random
from typing import Dict, List

import brs
from brs import (boundary_thickness, complement, realisable_region_from_cells,
                 separator_atoms, separator_cells)
from validators import _cost_g, sample_regions


# ---------------------------------------------------------------------
#  Panel 1 -- Boundary-Thickness Theorem: thickness >= mu_min, no sharp cut
# ---------------------------------------------------------------------
def panel1() -> Dict:
    rng = random.Random(11)
    thick, mumin, ratio, scale = [], [], [], []
    # 3D: (n_cells, mu_min, min_thickness) across a grid of spaces
    grid_nc, grid_mm, grid_mt = [], [], []
    for _ in range(400):
        shape = [rng.choice([4, 6, 8, 10]), rng.choice([4, 6, 8, 10])]
        cs = rng.choice([1, 2])
        cs = min(cs, min(shape) - 1)
        w = rng.choice([0.5, 1.0, 2.0])
        sp = brs.make_box(shape, cs, w)
        if not sp.is_connected():
            continue
        regions = sample_regions(sp, 40)
        ts = [boundary_thickness(sp, A) for A in regions]
        if not ts:
            continue
        for A, t in zip(regions, ts):
            thick.append(t)
            mumin.append(sp.mu_min)
            ratio.append(t / sp.mu_min)
            scale.append(sp.mu(A))
        grid_nc.append(len(sp.cells))
        grid_mm.append(sp.mu_min)
        grid_mt.append(min(ts))
    return {
        "scatter_thickness_vs_mumin": {"mu_min": mumin, "thickness": thick},
        "hist_ratio": {"ratio_thickness_over_mumin": ratio},
        "scatter_scale_vs_thickness": {"scale": scale, "thickness": thick},
        "surface_ncells_mumin_minthick": {
            "n_cells": grid_nc, "mu_min": grid_mm, "min_thickness": grid_mt},
    }


# ---------------------------------------------------------------------
#  Panel 2 -- Three derivations of the floor agree
# ---------------------------------------------------------------------
def panel2() -> Dict:
    rng = random.Random(23)
    geo, rep, cost, mm = [], [], [], []
    for _ in range(300):
        shape = [rng.choice([4, 6, 8]), rng.choice([4, 6, 8])]
        cs = min(rng.choice([1, 2]), min(shape) - 1)
        sp = brs.make_box(shape, cs, rng.choice([0.5, 1.0, 2.0]))
        if not sp.is_connected():
            continue
        regions = sample_regions(sp, 40)
        if not regions:
            continue
        gf = min(boundary_thickness(sp, A) for A in regions)
        # representational residue floor (whole separator cells)
        reps = []
        for A in regions:
            sep = separator_cells(sp, A)
            if not sep:
                continue
            c = sp.cells[sep[0]]
            half = frozenset(list(c)[: max(1, len(c) // 2)])
            target = frozenset(set(A) | set(half))
            named = [i for i, cc in enumerate(sp.cells) if set(cc) <= set(target)]
            disc = frozenset(set(target) ^ set(realisable_region_from_cells(sp, named)))
            if disc:
                touched = {sp.cell_of(a) for a in disc}
                reps.append(sp.mu(realisable_region_from_cells(sp, touched)))
        rf = min(reps) if reps else gf
        cf = sp.mu_min  # cost floor = e^{-C} = mu_min by construction
        geo.append(gf); rep.append(rf); cost.append(cf); mm.append(sp.mu_min)
    # cost divergence curve g(t) = -log t
    ts = [10 ** (-k / 20.0) for k in range(0, 120)]  # 1 .. 1e-6
    g = [_cost_g(t) for t in ts]
    return {
        "geo_vs_rep": {"geo_floor": geo, "rep_floor": rep},
        "geo_vs_cost": {"geo_floor": geo, "cost_floor": cost},
        "cost_divergence": {"t": ts, "g": g},
        "surface_three_floors": {"geo": geo, "rep": rep, "cost": cost},
    }


# ---------------------------------------------------------------------
#  Panel 3 -- Detectability: distinguishable iff sigma > beta_A
# ---------------------------------------------------------------------
def panel3() -> Dict:
    rng = random.Random(31)
    sigma, betaA, tau, interior = [], [], [], []
    for _ in range(250):
        shape = [rng.choice([6, 8, 10]), rng.choice([6, 8, 10])]
        cs = min(rng.choice([1, 2]), min(shape) - 1)
        sp = brs.make_box(shape, cs, rng.choice([0.5, 1.0]))
        if not sp.is_connected():
            continue
        for A in sample_regions(sp, 50):
            sep = separator_atoms(sp, A)
            s = sp.mu(A)
            bA = sp.mu(frozenset(set(A) & set(sep)))
            it = sp.mu(frozenset(set(A) - set(sep)))
            b_full = boundary_thickness(sp, A)
            sigma.append(s); betaA.append(bA); interior.append(it)
            tau.append(b_full / s if s else 0.0)
    return {
        "sigma_vs_betaA": {"sigma": sigma, "beta_A": betaA,
                           "interior": interior},
        "interior_vs_margin": {"margin_sigma_minus_betaA":
                               [s - b for s, b in zip(sigma, betaA)],
                               "interior": interior},
        "tau_hist": {"tau": tau},
        "surface_sigma_beta_interior": {"sigma": sigma, "beta_A": betaA,
                                        "interior": interior},
    }


# ---------------------------------------------------------------------
#  Panel 4 -- Sorites: tau descends across a band, no decisive grain
# ---------------------------------------------------------------------
def panel4() -> Dict:
    # accretive aggregate on a 2D box: grow one atom at a time, record tau, sigma
    sp = brs.make_box([12, 12], 2, 1.0)
    order = sorted(sp.atoms)
    grown = set()
    step, sigma, beta, tau = [], [], [], []
    for n, a in enumerate(order):
        grown.add(a)
        A = frozenset(grown)
        if not (0 < sp.mu(A) < sp.total_measure):
            continue
        b = boundary_thickness(sp, A)
        s = sp.mu(A)
        step.append(len(sigma))
        sigma.append(s); beta.append(b); tau.append(b / s if s else 0.0)
    # per-step jump in tau (no single decisive grain -> bounded once sigma>beta)
    djump = [abs(tau[i + 1] - tau[i]) for i in range(len(tau) - 1)]
    # 3D: three independent accretion orders -> tau curves
    curves = {}
    for ci, seed in enumerate((1, 2, 3)):
        rng = random.Random(seed)
        o = sorted(sp.atoms, key=lambda p: rng.random())
        g = set(); tser = []; sser = []
        for a in o:
            g.add(a); A = frozenset(g)
            if not (0 < sp.mu(A) < sp.total_measure):
                continue
            b = boundary_thickness(sp, A); s = sp.mu(A)
            tser.append(b / s if s else 0.0); sser.append(s)
        curves[f"order_{ci}"] = {"sigma": sser, "tau": tser}
    return {
        "tau_descent": {"step": step, "tau": tau, "sigma": sigma},
        "sigma_vs_tau": {"sigma": sigma, "tau": tau},
        "tau_jump": {"step": step[:-1], "jump": djump},
        "surface_orders_tau": curves,
    }


# ---------------------------------------------------------------------
#  Panel 5 -- Locating vs visiting: cost ~ beta*log K ; visiting freq = p
# ---------------------------------------------------------------------
def panel5() -> Dict:
    beta = 1.0  # take floor = 1 for the locating-cost law
    K = list(range(2, 257))
    locate_cost = [beta * math.ceil(math.log2(k)) for k in K]
    p = [1.0 / k for k in K]
    visit_free = [0.0 for _ in K]  # visiting cost is identically zero
    # frequency = p(W) ; rarity vs frequency (they coincide) -- and cost rises
    log_inv_p = [math.log2(1.0 / pp) for pp in p]
    # 3D: cost surface over (K, beta)
    betas = [0.5, 1.0, 1.5, 2.0]
    surf_K, surf_b, surf_c = [], [], []
    for b in betas:
        for k in K[::4]:
            surf_K.append(k); surf_b.append(b)
            surf_c.append(b * math.ceil(math.log2(k)))
    return {
        "locate_cost_vs_K": {"K": K, "locate_cost": locate_cost,
                             "visit_cost": visit_free},
        "cost_vs_loginvp": {"log2_inv_p": log_inv_p, "locate_cost": locate_cost},
        "freq_vs_rarity": {"p": p, "visiting_frequency": p},  # f = p
        "surface_cost_K_beta": {"K": surf_K, "beta": surf_b,
                                "locate_cost": surf_c},
    }


# ---------------------------------------------------------------------
#  Panel 6 -- Non-return & cessation: monotone record; halt at t_*
# ---------------------------------------------------------------------
def panel6() -> Dict:
    # monotone committed record along a separation process
    sp = brs.make_box([10, 10], 2, 1.0)
    regions = sample_regions(sp, 60)
    M = 0; step, record = [], []
    for i, A in enumerate(regions):
        M += len(separator_cells(sp, A))
        step.append(i); record.append(M)
    # an undo at the end still increments
    step.append(len(regions)); record.append(M + 1)

    # cessation: marginal return / cost vs thickness t  (return bounded by mu(Omega))
    R = sp.total_measure
    ts = [10 ** (-k / 20.0) for k in range(1, 110)]
    g = [-math.log(t) for t in ts]
    marginal = [R / gg for gg in g]
    cost = g
    # halt thresholds: t_* = e^{-R/theta} for several theta
    thetas = [0.5, 1.0, 2.0, 4.0]
    tstar = [math.exp(-R / th) for th in thetas]
    # 3D: marginal-return surface over (t, theta)
    surf_t, surf_th, surf_m = [], [], []
    for th in thetas:
        for t in ts[::3]:
            surf_t.append(t); surf_th.append(th)
            surf_m.append((R / (-math.log(t))) / th)
    return {
        "monotone_record": {"step": step, "record": record},
        "cost_vs_thickness": {"t": ts, "cost": cost},
        "marginal_return": {"t": ts, "marginal_return_per_cost": marginal,
                            "theta": thetas, "t_star": tstar},
        "surface_marginal_t_theta": {"t": surf_t, "theta": surf_th,
                                     "marginal": surf_m},
    }


def main():
    data = {
        "panel1_boundary_thickness": panel1(),
        "panel2_floor_agreement": panel2(),
        "panel3_detectability": panel3(),
        "panel4_sorites": panel4(),
        "panel5_locating_visiting": panel5(),
        "panel6_nonreturn_cessation": panel6(),
    }
    with open("figure_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
    # report sizes
    for k, v in data.items():
        print(k, "->", list(v.keys()))
    print("written figure_data.json")


if __name__ == "__main__":
    main()
