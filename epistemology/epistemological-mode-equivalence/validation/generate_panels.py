"""
Generate 5 publication panels for the Epistemological Mode-Methodology
Equivalence manuscript. Each panel has 4 charts, white background, at least
one 3D chart per panel. No conceptual or table-only charts.
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from epistemological_validation import (
    Receiver, Cell, Methodology, S_functional, layered_S, composite_floor,
    SIGMA, oscillatory_encoding, categorical_encoding, partition_encoding,
)

FIG_DIR = Path(__file__).parent / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
})

RNG = np.random.default_rng(20260501)


# ----------------------------------------------------------------------------
# Panel 1: Receiver floor and cell-truth
# ----------------------------------------------------------------------------

def panel_1():
    fig = plt.figure(figsize=(22, 5.5))

    # (a) S distribution across random states
    ax1 = fig.add_subplot(1, 4, 1)
    rcv = Receiver("p1", beta=2.5, decoder_noise=0.0, projection_radius=0.0)
    cell = Cell(centre=np.zeros(2), tolerance=1.0)
    states = RNG.uniform(-10, 10, size=(2000, 2))
    S_vals = np.array([S_functional(rcv, x, cell) for x in states])
    ax1.hist(S_vals, bins=40, color="steelblue", edgecolor="black", alpha=0.85)
    ax1.axvline(rcv.beta, color="crimson", linestyle="--", linewidth=2,
                label=fr"floor $\beta={rcv.beta}$")
    ax1.set_xlabel("S(R, x; C)")
    ax1.set_ylabel("count")
    ax1.set_title("(a) S distribution: floor at beta")
    ax1.legend()

    # (b) S inside vs. outside cell
    ax2 = fig.add_subplot(1, 4, 2)
    cell_b = Cell(centre=np.zeros(2), tolerance=2.0)
    rcv_b = Receiver("p1b", beta=1.5, decoder_noise=0.0, projection_radius=0.0)
    n_in = 200
    angles = RNG.uniform(0, 2 * np.pi, n_in)
    radii_in = RNG.uniform(0, 1.8, n_in)
    inside = np.stack([radii_in * np.cos(angles), radii_in * np.sin(angles)], axis=1)
    radii_out = RNG.uniform(2.5, 8.0, n_in)
    angles2 = RNG.uniform(0, 2 * np.pi, n_in)
    outside = np.stack([radii_out * np.cos(angles2), radii_out * np.sin(angles2)], axis=1)
    S_in = np.array([S_functional(rcv_b, x, cell_b) for x in inside])
    S_out = np.array([S_functional(rcv_b, x, cell_b) for x in outside])
    ax2.scatter(np.linalg.norm(inside, axis=1), S_in, alpha=0.6, color="seagreen",
                label="x in cell", s=20)
    ax2.scatter(np.linalg.norm(outside, axis=1), S_out, alpha=0.6, color="darkorange",
                label="x outside cell", s=20)
    ax2.axhline(rcv_b.beta, color="crimson", linestyle="--",
                label=fr"floor $\beta={rcv_b.beta}$")
    ax2.set_xlabel("|x|")
    ax2.set_ylabel("S")
    ax2.set_title("(b) Cell-truth: S constant inside cell")
    ax2.legend()

    # (c) Floor scales linearly with beta
    ax3 = fig.add_subplot(1, 4, 3)
    betas = np.linspace(0.1, 5.0, 30)
    measured = []
    cell_c = Cell(centre=np.zeros(2), tolerance=1.0)
    for b in betas:
        rcv_c = Receiver(f"p1c-{b:.2f}", beta=b, decoder_noise=0.0, projection_radius=0.0)
        x_c = np.array([0.5, 0.0])
        measured.append(S_functional(rcv_c, x_c, cell_c))
    ax3.plot(betas, measured, "o", color="steelblue", markersize=6,
             label="measured")
    ax3.plot(betas, betas, "-", color="crimson", linewidth=2,
             label="theory: S = beta")
    ax3.set_xlabel("beta")
    ax3.set_ylabel("S(R, x in cell)")
    ax3.set_title("(c) Floor attainment: S = beta")
    ax3.legend()

    # (d) 3D: S over (x,y) and beta
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    xs = np.linspace(-3, 3, 25)
    ys = np.linspace(-3, 3, 25)
    X, Y = np.meshgrid(xs, ys)
    cell_d = Cell(centre=np.zeros(2), tolerance=1.0)
    for b in [0.5, 1.5, 2.5]:
        rcv_d = Receiver(f"p1d-{b}", beta=b, decoder_noise=0.0, projection_radius=0.0)
        Z = np.zeros_like(X)
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                Z[i, j] = S_functional(rcv_d, np.array([X[i, j], Y[i, j]]), cell_d)
        ax4.plot_surface(X, Y, Z, alpha=0.5,
                         cmap=plt.cm.viridis if b == 1.5 else None,
                         color="steelblue" if b == 0.5 else
                         ("crimson" if b == 2.5 else None),
                         label=fr"$\beta={b}$")
    ax4.set_xlabel("x")
    ax4.set_ylabel("y")
    ax4.set_zlabel("S")
    ax4.set_title("(d) 3D: S surface for varying beta")

    plt.suptitle("Panel 1: Receiver Floor and Cell-Truth", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_1.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 2: Representational invariance
# ----------------------------------------------------------------------------

def panel_2():
    fig = plt.figure(figsize=(22, 5.5))

    rcv = Receiver("p2", beta=1.0, decoder_noise=0.0, projection_radius=0.0)
    n = 100
    states = RNG.uniform(-3, 3, size=(n, 2))
    cell_orig = Cell(centre=np.array([1.0, 0.5]), tolerance=0.7)

    # (a) Oscillatory
    ax1 = fig.add_subplot(1, 4, 1)
    cell_osc = Cell(centre=oscillatory_encoding(cell_orig.centre),
                    tolerance=cell_orig.tolerance)
    s_orig = np.array([S_functional(rcv, x, cell_orig) for x in states])
    s_osc = np.array([S_functional(rcv, oscillatory_encoding(x), cell_osc)
                      for x in states])
    ax1.scatter(s_orig, s_osc, color="steelblue", alpha=0.7, s=30)
    lo, hi = min(s_orig.min(), s_osc.min()), max(s_orig.max(), s_osc.max())
    ax1.plot([lo, hi], [lo, hi], "--", color="crimson", linewidth=2,
             label="y=x (invariance)")
    ax1.set_xlabel("S in original")
    ax1.set_ylabel("S after oscillatory encoding")
    ax1.set_title("(a) Oscillatory invariance")
    ax1.legend()

    # (b) Categorical
    ax2 = fig.add_subplot(1, 4, 2)
    cell_cat = Cell(centre=categorical_encoding(cell_orig.centre),
                    tolerance=cell_orig.tolerance)
    s_cat = np.array([S_functional(rcv, categorical_encoding(x), cell_cat)
                      for x in states])
    ax2.scatter(s_orig, s_cat, color="seagreen", alpha=0.7, s=30)
    lo, hi = min(s_orig.min(), s_cat.min()), max(s_orig.max(), s_cat.max())
    ax2.plot([lo, hi], [lo, hi], "--", color="crimson", linewidth=2,
             label="y=x")
    ax2.set_xlabel("S in original")
    ax2.set_ylabel("S after categorical encoding")
    ax2.set_title("(b) Categorical invariance")
    ax2.legend()

    # (c) Partition
    ax3 = fig.add_subplot(1, 4, 3)
    cell_par = Cell(centre=partition_encoding(cell_orig.centre),
                    tolerance=cell_orig.tolerance)
    s_par = np.array([S_functional(rcv, partition_encoding(x), cell_par)
                      for x in states])
    ax3.scatter(s_orig, s_par, color="darkorange", alpha=0.7, s=30)
    lo, hi = min(s_orig.min(), s_par.min()), max(s_orig.max(), s_par.max())
    ax3.plot([lo, hi], [lo, hi], "--", color="crimson", linewidth=2, label="y=x")
    ax3.set_xlabel("S in original")
    ax3.set_ylabel("S after partition encoding")
    ax3.set_title("(c) Partition invariance")
    ax3.legend()

    # (d) 3D triple-equivalence manifold
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    ax4.scatter(s_orig, s_osc, s_cat, color="steelblue", alpha=0.7, s=30,
                label="(orig, osc, cat)")
    # diagonal
    diag = np.linspace(lo, hi, 50)
    ax4.plot(diag, diag, diag, "--", color="crimson", linewidth=2,
             label="triple equivalence diagonal")
    ax4.set_xlabel("S original")
    ax4.set_ylabel("S oscillatory")
    ax4.set_zlabel("S categorical")
    ax4.set_title("(d) 3D triple-equivalence manifold")
    ax4.legend()

    plt.suptitle("Panel 2: Representational Invariance",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_2.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 3: Layered receivers and mode non-privilege
# ----------------------------------------------------------------------------

def panel_3():
    fig = plt.figure(figsize=(22, 5.5))

    cell = Cell(centre=np.zeros(2), tolerance=1.0)

    # (a) Per-layer floors and aggregate
    ax1 = fig.add_subplot(1, 4, 1)
    layer_betas = [0.3, 0.8, 1.5, 3.0, 6.0]
    aggregate = min(layer_betas)
    bars = ax1.bar(range(len(layer_betas)), layer_betas, color="steelblue",
                   edgecolor="black", alpha=0.85)
    bars[layer_betas.index(aggregate)].set_color("seagreen")
    ax1.axhline(aggregate, color="crimson", linestyle="--", linewidth=2,
                label=f"aggregate floor = {aggregate}")
    ax1.set_xticks(range(len(layer_betas)))
    ax1.set_xticklabels([f"L{i+1}" for i in range(len(layer_betas))])
    ax1.set_ylabel("layer floor")
    ax1.set_title("(a) Layered floor = min layer floor")
    ax1.legend()

    # (b) Pre-decoder firing region
    ax2 = fig.add_subplot(1, 4, 2)
    pre_decoder = Receiver("reflex", beta=0.4, decoder_noise=0.0, projection_radius=0.0)
    decoder = Receiver("dec", beta=2.5, decoder_noise=0.0, projection_radius=0.0)
    grid = 60
    xs = np.linspace(-3, 3, grid)
    ys = np.linspace(-3, 3, grid)
    X, Y = np.meshgrid(xs, ys)
    Z = np.zeros_like(X)
    for i in range(grid):
        for j in range(grid):
            x = np.array([X[i, j], Y[i, j]])
            Z[i, j] = layered_S([pre_decoder, decoder], x, cell)
    cf = ax2.contourf(X, Y, Z, levels=20, cmap="viridis")
    plt.colorbar(cf, ax=ax2, label="S")
    circle = plt.Circle((0, 0), 1.0, fill=False, color="white", linewidth=2,
                         label="action-cell")
    ax2.add_patch(circle)
    ax2.set_xlabel("x")
    ax2.set_ylabel("y")
    ax2.set_title("(b) S map: pre-decoder dominates")

    # (c) Reachability: reflex-only vs decoder-only
    ax3 = fig.add_subplot(1, 4, 3)
    n = 500
    states = RNG.uniform(-3, 3, size=(n, 2))
    reflex_floors = [0.2, 0.5, 1.0, 2.0]
    decoder_floor = 2.5
    reflex_reach = []
    decoder_reach = []
    for rf in reflex_floors:
        pd = Receiver(f"r-{rf}", beta=rf, decoder_noise=0.0, projection_radius=0.0)
        dec = Receiver("d", beta=decoder_floor, decoder_noise=0.0, projection_radius=0.0)
        reach_reflex = sum(1 for x in states
                            if S_functional(pd, x, cell) < cell.tolerance)
        reach_decoder = sum(1 for x in states
                            if S_functional(dec, x, cell) < cell.tolerance)
        reflex_reach.append(reach_reflex / n)
        decoder_reach.append(reach_decoder / n)
    ax3.plot(reflex_floors, reflex_reach, "o-", color="seagreen",
             markersize=8, label="reflex layer reach")
    ax3.plot(reflex_floors, decoder_reach, "s-", color="darkorange",
             markersize=8, label=f"decoder layer reach (beta={decoder_floor})")
    ax3.set_xlabel("reflex floor")
    ax3.set_ylabel("fraction of states reaching cell")
    ax3.set_title("(c) Reflex vs decoder reach")
    ax3.legend()

    # (d) 3D heatmap of S over layer floor combinations
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    reflex_betas = np.linspace(0.1, 3.0, 20)
    decoder_betas = np.linspace(0.1, 5.0, 20)
    R, D = np.meshgrid(reflex_betas, decoder_betas)
    F = np.minimum(R, D)
    surf = ax4.plot_surface(R, D, F, cmap="viridis", alpha=0.85,
                             edgecolor="none")
    ax4.set_xlabel("reflex floor")
    ax4.set_ylabel("decoder floor")
    ax4.set_zlabel("aggregate floor")
    ax4.set_title("(d) 3D: aggregate floor surface")
    fig.colorbar(surf, ax=ax4, shrink=0.6, aspect=10)

    plt.suptitle("Panel 3: Layered Receivers and Mode Non-Privilege",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_3.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 4: Methodological floor
# ----------------------------------------------------------------------------

def panel_4():
    fig = plt.figure(figsize=(22, 5.5))

    # (a) S trajectory across iterations
    ax1 = fig.add_subplot(1, 4, 1)
    methods = [
        Methodology("M_a", kappa=0.3, sigma=0.5),
        Methodology("M_b", kappa=0.5, sigma=0.5),
        Methodology("M_c", kappa=0.7, sigma=0.5),
    ]
    n_iter = 50
    s0 = 50.0
    for m in methods:
        traj = [s0]
        s = s0
        for _ in range(n_iter):
            s = m.kappa * s + m.sigma * m.kappa
            traj.append(s)
        ax1.plot(range(n_iter + 1), traj, "-o", markersize=3,
                 label=fr"$\kappa={m.kappa}$, floor={m.floor():.3f}")
    ax1.set_xlabel("iteration")
    ax1.set_ylabel("S")
    ax1.set_yscale("log")
    ax1.set_title("(a) S trajectory: convergence to methodological floor")
    ax1.legend()

    # (b) Floor vs kappa
    ax2 = fig.add_subplot(1, 4, 2)
    kappas = np.linspace(0.05, 0.95, 30)
    sigma_fixed = 0.5
    floors = sigma_fixed * kappas / (1 - kappas)
    ax2.plot(kappas, floors, "-", color="steelblue", linewidth=2,
             label=fr"sigma = {sigma_fixed}")
    ax2.set_xlabel("kappa")
    ax2.set_ylabel("methodological floor")
    ax2.set_title("(b) Floor diverges as kappa -> 1")
    ax2.legend()

    # (c) Floor vs sigma
    ax3 = fig.add_subplot(1, 4, 3)
    sigmas = np.linspace(0.0, 2.0, 30)
    for k in [0.3, 0.5, 0.7]:
        floors_s = sigmas * k / (1 - k)
        ax3.plot(sigmas, floors_s, "-", linewidth=2,
                 label=fr"$\kappa={k}$")
    ax3.set_xlabel("sigma")
    ax3.set_ylabel("methodological floor")
    ax3.set_title("(c) Floor linear in sigma")
    ax3.legend()

    # (d) 3D surface of floor over (kappa, sigma)
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    K = np.linspace(0.05, 0.9, 30)
    S = np.linspace(0.05, 1.5, 30)
    KK, SS = np.meshgrid(K, S)
    FF = SS * KK / (1 - KK)
    surf = ax4.plot_surface(KK, SS, FF, cmap="viridis", alpha=0.85,
                             edgecolor="none")
    ax4.set_xlabel("kappa")
    ax4.set_ylabel("sigma")
    ax4.set_zlabel("floor")
    ax4.set_title("(d) 3D: floor over (kappa, sigma)")
    fig.colorbar(surf, ax=ax4, shrink=0.6, aspect=10)

    plt.suptitle("Panel 4: Methodological Floor",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_4.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 5: Mode-methodology equivalence and distribution
# ----------------------------------------------------------------------------

def panel_5():
    fig = plt.figure(figsize=(22, 5.5))

    # (a) Composite floor: measured vs predicted
    ax1 = fig.add_subplot(1, 4, 1)
    measured = []
    predicted = []
    for _ in range(40):
        f1 = RNG.uniform(0.1, 5.0)
        f2 = RNG.uniform(0.1, 5.0)
        m = composite_floor([f1, f2])
        p = f1 + f2 - f1 * f2 / SIGMA
        measured.append(m)
        predicted.append(p)
    ax1.scatter(predicted, measured, color="steelblue", alpha=0.7, s=40)
    lo, hi = min(predicted), max(predicted)
    ax1.plot([lo, hi], [lo, hi], "--", color="crimson", linewidth=2,
             label="y=x")
    ax1.set_xlabel("predicted composite floor")
    ax1.set_ylabel("measured composite floor")
    ax1.set_title("(a) Composite floor: measured vs predicted")
    ax1.legend()

    # (b) Multiplicative composition with n stacked methodologies
    ax2 = fig.add_subplot(1, 4, 2)
    base_floors = [0.5, 1.0, 1.5, 2.0]
    for bf in base_floors:
        ns = list(range(1, 11))
        composite = [composite_floor([bf] * n) for n in ns]
        ax2.plot(ns, composite, "-o", markersize=6,
                 label=fr"per-stack floor = {bf}")
    ax2.set_xlabel("n (number of stacked methodologies)")
    ax2.set_ylabel("composite floor")
    ax2.set_title("(b) Stacked methodologies: composite reduction")
    ax2.legend()

    # (c) Anti-monopoly: max knowledge vs receiver floor
    ax3 = fig.add_subplot(1, 4, 3)
    rcv_floors = np.linspace(0.1, 10.0, 30)
    max_knowledge = SIGMA - rcv_floors
    ax3.plot(rcv_floors, max_knowledge, "-", color="steelblue", linewidth=2,
             label="upper bound = Sigma - floor")
    measured_max = []
    for fl in rcv_floors:
        rcv = Receiver(f"d-{fl:.2f}", beta=fl, decoder_noise=0.0,
                        projection_radius=0.0)
        n_sample = 100
        states = RNG.uniform(-5, 5, size=(n_sample, 2))
        cells = [Cell(centre=x, tolerance=2.5) for x in states]
        knowledges = [SIGMA - S_functional(rcv, x, c)
                       for x, c in zip(states, cells)]
        measured_max.append(max(knowledges))
    ax3.plot(rcv_floors, measured_max, "o", color="darkorange",
             markersize=6, label="measured max")
    ax3.set_xlabel("receiver floor")
    ax3.set_ylabel("max knowledge")
    ax3.set_title("(c) Anti-monopoly: knowledge bounded by Sigma - floor")
    ax3.legend()

    # (d) 3D: composite floor over (receiver floor, methodology floor)
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    rcv_F = np.linspace(0.1, 10.0, 25)
    method_F = np.linspace(0.1, 10.0, 25)
    Rg, Mg = np.meshgrid(rcv_F, method_F)
    Cg = Rg + Mg - Rg * Mg / SIGMA
    surf = ax4.plot_surface(Rg, Mg, Cg, cmap="viridis", alpha=0.85,
                             edgecolor="none")
    ax4.set_xlabel("receiver floor")
    ax4.set_ylabel("methodology floor")
    ax4.set_zlabel("composite floor")
    ax4.set_title("(d) 3D: mode-methodology equivalence surface")
    fig.colorbar(surf, ax=ax4, shrink=0.6, aspect=10)

    plt.suptitle("Panel 5: Mode-Methodology Equivalence and Distribution",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_5.png", dpi=150, bbox_inches="tight")
    plt.close()


def main():
    print("Generating Panel 1...")
    panel_1()
    print("Generating Panel 2...")
    panel_2()
    print("Generating Panel 3...")
    panel_3()
    print("Generating Panel 4...")
    panel_4()
    print("Generating Panel 5...")
    panel_5()
    print(f"All panels saved to {FIG_DIR}")


if __name__ == "__main__":
    main()
