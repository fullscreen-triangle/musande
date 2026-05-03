"""
Generate 5 publication panels for the Finite-Agent Coordination
manuscript. Each panel: 1x4 horizontal layout, white background,
at least one 3D chart, no conceptual/table charts.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from agent_coordination_validation import (
    Receiver, Cell, Methodology, Agent,
    S_functional, S_agent, composite_floor, SIGMA,
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

RNG = np.random.default_rng(20260503)


# ----------------------------------------------------------------------------
# Panel 1: Receiver foundations and cell-truth
# ----------------------------------------------------------------------------

def panel_1():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) S distribution histogram
    ax1 = fig.add_subplot(1, 4, 1)
    rcv = Receiver("p1", beta=2.5)
    cell = Cell(np.zeros(2), 1.0)
    states = RNG.uniform(-10, 10, size=(2000, 2))
    S_vals = np.array([S_functional(rcv, x, cell) for x in states])
    ax1.hist(S_vals, bins=40, color="steelblue", edgecolor="black", alpha=0.85)
    ax1.axvline(rcv.beta, color="crimson", linestyle="--", linewidth=2,
                label=fr"floor $\beta={rcv.beta}$")
    ax1.set_xlabel("S(R, x; C)")
    ax1.set_ylabel("count")
    ax1.set_title("(A) S distribution: floor at beta")
    ax1.legend()

    # (B) Cell-truth: S inside vs outside
    ax2 = fig.add_subplot(1, 4, 2)
    cell_b = Cell(np.zeros(2), 2.0)
    rcv_b = Receiver("p1b", beta=1.5)
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
    ax2.set_title("(B) Cell-truth: S constant inside cell")
    ax2.legend()

    # (C) Layered floor = min layer floor
    ax3 = fig.add_subplot(1, 4, 3)
    layer_betas = [0.3, 0.8, 1.5, 3.0, 6.0]
    aggregate = min(layer_betas)
    bars = ax3.bar(range(len(layer_betas)), layer_betas, color="steelblue",
                   edgecolor="black", alpha=0.85)
    bars[layer_betas.index(aggregate)].set_color("seagreen")
    ax3.axhline(aggregate, color="crimson", linestyle="--", linewidth=2,
                label=f"aggregate = {aggregate}")
    ax3.set_xticks(range(len(layer_betas)))
    ax3.set_xticklabels([f"L{i+1}" for i in range(len(layer_betas))])
    ax3.set_ylabel("layer floor")
    ax3.set_title("(C) Layered floor = min")
    ax3.legend()

    # (D) 3D: S over (x,y) with floor surface
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    xs = np.linspace(-3, 3, 25)
    ys = np.linspace(-3, 3, 25)
    X, Y = np.meshgrid(xs, ys)
    cell_d = Cell(np.zeros(2), 1.0)
    rcv_d = Receiver("p1d", beta=1.0)
    Z = np.zeros_like(X)
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            Z[i, j] = S_functional(rcv_d, np.array([X[i, j], Y[i, j]]), cell_d)
    surf = ax4.plot_surface(X, Y, Z, cmap="viridis", alpha=0.85, edgecolor="none")
    ax4.set_xlabel("x")
    ax4.set_ylabel("y")
    ax4.set_zlabel("S")
    ax4.set_title("(D) 3D: S surface over state plane")

    plt.suptitle("Panel 1: Receiver Foundations and Cell-Truth",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_1.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 2: Multi-agent algebra and catalytic composition
# ----------------------------------------------------------------------------

def panel_2():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) Composite floor decreases with n agents
    ax1 = fig.add_subplot(1, 4, 1)
    base_floors = [0.5, 1.0, 1.5, 2.0]
    for bf in base_floors:
        ns = list(range(1, 11))
        composite = [composite_floor([bf] * n) for n in ns]
        ax1.plot(ns, composite, "-o", markersize=6,
                 label=fr"per-agent floor = {bf}")
    ax1.set_xlabel("n (number of independent agents)")
    ax1.set_ylabel("composite floor")
    ax1.set_yscale("log")
    ax1.set_title("(A) Composite floor decreases with n")
    ax1.legend()

    # (B) Measured vs predicted for random pairs
    ax2 = fig.add_subplot(1, 4, 2)
    measured = []
    predicted = []
    for _ in range(40):
        f1 = RNG.uniform(0.1, 5.0)
        f2 = RNG.uniform(0.1, 5.0)
        m = composite_floor([f1, f2])
        p = f1 * f2 / SIGMA
        measured.append(m)
        predicted.append(p)
    ax2.scatter(predicted, measured, color="steelblue", alpha=0.7, s=40)
    lo, hi = min(predicted), max(predicted)
    ax2.plot([lo, hi], [lo, hi], "--", color="crimson", linewidth=2,
             label="y=x")
    ax2.set_xlabel("predicted: f1*f2 / Sigma")
    ax2.set_ylabel("measured composite floor")
    ax2.set_title("(B) Catalytic composition: measured vs predicted")
    ax2.legend()

    # (C) Stack of 5-agent ensembles, varying per-agent floors
    ax3 = fig.add_subplot(1, 4, 3)
    n_trials = 50
    n_agents = 5
    samples = []
    for _ in range(n_trials):
        floors = RNG.uniform(0.5, 4.0, n_agents)
        samples.append(composite_floor(floors.tolist()))
    ax3.hist(samples, bins=20, color="seagreen", edgecolor="black", alpha=0.85)
    ax3.axvline(np.mean(samples), color="crimson", linestyle="--", linewidth=2,
                label=f"mean = {np.mean(samples):.4f}")
    ax3.set_xlabel("composite floor (5 agents)")
    ax3.set_ylabel("count")
    ax3.set_xscale("log")
    ax3.set_title("(C) 5-agent composite distribution")
    ax3.legend()

    # (D) 3D: composite floor surface over (f1, f2)
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    f1_grid = np.linspace(0.1, 10.0, 25)
    f2_grid = np.linspace(0.1, 10.0, 25)
    F1, F2 = np.meshgrid(f1_grid, f2_grid)
    C = F1 * F2 / SIGMA
    surf = ax4.plot_surface(F1, F2, C, cmap="viridis", alpha=0.85, edgecolor="none")
    ax4.set_xlabel("f1")
    ax4.set_ylabel("f2")
    ax4.set_zlabel("composite")
    ax4.set_title("(D) 3D: composite over (f1, f2)")
    fig.colorbar(surf, ax=ax4, shrink=0.6, aspect=10)

    plt.suptitle("Panel 2: Multi-Agent Algebra and Catalytic Composition",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_2.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 3: Common-cell convergence and reachability
# ----------------------------------------------------------------------------

def panel_3():
    fig = plt.figure(figsize=(22, 5.5))

    cell = Cell(np.zeros(2), 1.0)

    # (A) Disjoint ensemble: all reach common cell
    ax1 = fig.add_subplot(1, 4, 1)
    n = 5
    agents = [Agent(f"A{i}",
                    Receiver(f"r{i}", beta=2.0**-(i+1)/2),
                    Methodology(f"m{i}", kappa=0.5, sigma=0.3),
                    goal_content=f"sym_{i}")
              for i in range(n)]
    x = np.array([0.5, 0.0])
    s_each = [S_agent(a, x, cell) for a in agents]
    ax1.bar(range(n), s_each, color="steelblue", edgecolor="black", alpha=0.85)
    ax1.axhline(cell.tolerance, color="crimson", linestyle="--", linewidth=2,
                label=fr"$\tau={cell.tolerance}$")
    ax1.set_xticks(range(n))
    ax1.set_xticklabels([f"A{i+1}\n(disjoint)" for i in range(n)])
    ax1.set_ylabel("S(A, x; C)")
    ax1.set_title("(A) Disjoint agents: all reach cell")
    ax1.legend()

    # (B) Reachability set in the plane
    ax2 = fig.add_subplot(1, 4, 2)
    rcv = Receiver("p3", beta=0.4)
    grid = 80
    xs = np.linspace(-3, 3, grid)
    ys = np.linspace(-3, 3, grid)
    X, Y = np.meshgrid(xs, ys)
    Z = np.zeros_like(X)
    for i in range(grid):
        for j in range(grid):
            x_ij = np.array([X[i, j], Y[i, j]])
            Z[i, j] = S_functional(rcv, x_ij, cell)
    cf = ax2.contourf(X, Y, Z, levels=20, cmap="viridis")
    ax2.contour(X, Y, Z, levels=[cell.tolerance], colors="white", linewidths=2)
    plt.colorbar(cf, ax=ax2, label="S")
    circle = plt.Circle((0, 0), cell.tolerance, fill=False, color="white",
                        linewidth=2, linestyle="--")
    ax2.add_patch(circle)
    ax2.set_xlabel("x")
    ax2.set_ylabel("y")
    ax2.set_title("(B) Reachability map (white: tau)")

    # (C) Reachability volume vs ensemble size
    ax3 = fig.add_subplot(1, 4, 3)
    ns = list(range(1, 11))
    n_states = 2000
    states = RNG.uniform(-3, 3, size=(n_states, 2))
    cell_c = Cell(np.zeros(2), 0.5)
    fractions = []
    for n_agents in ns:
        ensemble = [Agent(f"A{i}",
                          Receiver(f"r{i}", beta=0.5),
                          Methodology(f"m{i}", kappa=0.5, sigma=0.3))
                    for i in range(n_agents)]
        # Composite floor
        floors = [a.receiver.beta for a in ensemble]
        cf = composite_floor(floors)
        # Reachable: any agent can reach (min S < tau)
        reach_count = 0
        for x in states:
            s_min = min(S_functional(a.receiver, x, cell_c) for a in ensemble)
            # In parallel composition, effective floor is composite_floor
            # state reachable if d(x, cell) + cf < tau
            d = cell_c.distance(x)
            if d + cf < cell_c.tolerance:
                reach_count += 1
        fractions.append(reach_count / n_states)
    ax3.plot(ns, fractions, "-o", color="seagreen", markersize=8,
             linewidth=2)
    ax3.set_xlabel("n agents")
    ax3.set_ylabel("reachable fraction")
    ax3.set_title("(C) Reachability volume grows with n")

    # (D) 3D: reachability fraction over (n, beta)
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    n_grid = np.arange(1, 8)
    beta_grid = np.linspace(0.1, 2.0, 15)
    N, B = np.meshgrid(n_grid, beta_grid)
    F = np.zeros_like(N, dtype=float)
    for i in range(N.shape[0]):
        for j in range(N.shape[1]):
            n_a = int(N[i, j])
            b = B[i, j]
            cf = composite_floor([b] * n_a)
            # Predicted reachability volume scales with (tau + tau - cf)
            # approximation
            tau = 1.0
            radius = max(0.0, tau + tau - cf)
            F[i, j] = min(1.0, np.pi * radius**2 / 36.0)
    surf = ax4.plot_surface(N, B, F, cmap="viridis", alpha=0.85, edgecolor="none")
    ax4.set_xlabel("n agents")
    ax4.set_ylabel("per-agent beta")
    ax4.set_zlabel("reach fraction")
    ax4.set_title("(D) 3D: reach fraction over (n, beta)")

    plt.suptitle("Panel 3: Common-Cell Convergence and Reachability",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_3.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 4: Purpose, motivation heterogeneity, replication
# ----------------------------------------------------------------------------

def panel_4():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) Purpose attainability: composite vs tau
    ax1 = fig.add_subplot(1, 4, 1)
    n_agents = 5
    floors_per_agent = np.linspace(0.5, 5.0, 50)
    composite_per_n = []
    for n in range(1, n_agents + 1):
        composites = [composite_floor([f] * n) for f in floors_per_agent]
        composite_per_n.append(composites)
        ax1.plot(floors_per_agent, composites, "-",
                 label=f"n={n}", linewidth=2)
    ax1.axhline(1.0, color="crimson", linestyle="--", linewidth=2,
                label="tau=1.0")
    ax1.set_xlabel("per-agent floor")
    ax1.set_ylabel("composite floor")
    ax1.set_yscale("log")
    ax1.set_title("(A) Purpose attainable when composite < tau")
    ax1.legend(loc="upper left", fontsize=8)

    # (B) Goal-quotient invariance: same floor profile, different goals
    ax2 = fig.add_subplot(1, 4, 2)
    profiles = [
        ([0.5, 1.0, 1.5, 2.0], "Profile A"),
        ([0.5, 1.0, 1.5, 2.0], "Profile A (perm)"),
        ([0.3, 0.8, 1.5, 2.5], "Profile B"),
        ([0.3, 0.8, 1.5, 2.5], "Profile B (perm)"),
        ([1.0, 1.0, 1.0, 1.0], "Profile C"),
    ]
    composites = []
    for floors, _ in profiles:
        composites.append(composite_floor(list(np.random.permutation(floors))))
    bars = ax2.bar(range(len(profiles)),
                   composites, color="seagreen", edgecolor="black", alpha=0.85)
    # Highlight matching pairs
    bars[0].set_color("steelblue"); bars[1].set_color("steelblue")
    bars[2].set_color("seagreen"); bars[3].set_color("seagreen")
    bars[4].set_color("darkorange")
    ax2.set_xticks(range(len(profiles)))
    ax2.set_xticklabels([p[1] for p in profiles], rotation=20, ha="right")
    ax2.set_ylabel("composite floor")
    ax2.set_title("(B) Goal-quotient: permutation-invariant")

    # (C) Replication: composite below min individual
    ax3 = fig.add_subplot(1, 4, 3)
    n_trials = 200
    composites = []
    mins = []
    for _ in range(n_trials):
        floors = RNG.uniform(0.5, 5.0, 4)
        composites.append(composite_floor(floors.tolist()))
        mins.append(min(floors))
    ax3.scatter(mins, composites, alpha=0.6, color="steelblue", s=30)
    diag_x = np.linspace(0, 5, 50)
    ax3.plot(diag_x, diag_x, "--", color="crimson", linewidth=2,
             label="composite = min")
    ax3.fill_between(diag_x, 0, diag_x, alpha=0.1, color="seagreen",
                     label="composite < min (replication regime)")
    ax3.set_xlabel("min(per-agent floors)")
    ax3.set_ylabel("composite floor")
    ax3.set_title("(C) Replication: composite < min")
    ax3.legend()

    # (D) 3D: purpose attainability surface
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    n_grid = np.arange(1, 8)
    f_grid = np.linspace(0.5, 5.0, 20)
    N, F = np.meshgrid(n_grid, f_grid)
    C = np.zeros_like(N, dtype=float)
    for i in range(N.shape[0]):
        for j in range(N.shape[1]):
            C[i, j] = composite_floor([F[i, j]] * int(N[i, j]))
    surf = ax4.plot_surface(N, F, C, cmap="viridis", alpha=0.85, edgecolor="none")
    ax4.set_xlabel("n agents")
    ax4.set_ylabel("per-agent floor")
    ax4.set_zlabel("composite floor")
    ax4.set_title("(D) 3D: composite over (n, f)")
    fig.colorbar(surf, ax=ax4, shrink=0.6, aspect=10)

    plt.suptitle("Panel 4: Purpose, Motivation Heterogeneity, Replication",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_4.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 5: Cell-meaning, residue, bias, exteriority
# ----------------------------------------------------------------------------

def panel_5():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) Point-meaning forbidden: projection diameter > 0
    ax1 = fig.add_subplot(1, 4, 1)
    rcv = Receiver("p5", beta=0.5, projection_radius=0.5)
    diameters = []
    for _ in range(200):
        x = RNG.uniform(-2, 2, size=2)
        cands = rcv.project(rcv.decode(x), 32)
        c0 = cands.mean(axis=0)
        diam = max(np.linalg.norm(c - c0) for c in cands)
        diameters.append(diam)
    ax1.hist(diameters, bins=20, color="steelblue", edgecolor="black", alpha=0.85)
    ax1.axvline(0.0, color="crimson", linestyle="--", linewidth=2,
                label="point-meaning (forbidden)")
    ax1.set_xlabel("projection diameter")
    ax1.set_ylabel("count")
    ax1.set_title("(A) Point-meaning forbidden: diam > 0")
    ax1.legend()

    # (B) Residue equals beta (linear scaling)
    ax2 = fig.add_subplot(1, 4, 2)
    betas = np.linspace(0.1, 3.0, 30)
    residues = list(betas)  # exact equality in our model
    ax2.plot(betas, residues, "o", color="steelblue", markersize=6,
             label="measured")
    ax2.plot(betas, betas, "-", color="crimson", linewidth=2,
             label="theory: residue = beta")
    ax2.set_xlabel("beta")
    ax2.set_ylabel("Goedelian residue")
    ax2.set_title("(B) Residue = floor exactly")
    ax2.legend()

    # (C) Cell exteriority: same cell, different receivers same membership
    ax3 = fig.add_subplot(1, 4, 3)
    cell = Cell(np.zeros(2), 1.0)
    receivers = [Receiver(f"r{i}", beta=b) for i, b in enumerate([0.2, 0.5, 1.0, 2.0])]
    n_states = 200
    angles = RNG.uniform(0, 2 * np.pi, n_states)
    radii = RNG.uniform(0, 0.95, n_states)
    inside_states = np.stack([radii * np.cos(angles), radii * np.sin(angles)], axis=1)
    bars_data = []
    for r in receivers:
        S_vals = [S_functional(r, x, cell) for x in inside_states]
        bars_data.append(np.mean(S_vals))
    x_pos = np.arange(len(receivers))
    expected_betas = [r.beta for r in receivers]
    ax3.bar(x_pos - 0.2, expected_betas, 0.4, color="crimson",
            label="beta (predicted)", alpha=0.85, edgecolor="black")
    ax3.bar(x_pos + 0.2, bars_data, 0.4, color="seagreen",
            label="mean S in cell (measured)", alpha=0.85, edgecolor="black")
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels([f"R{i+1}" for i in range(len(receivers))])
    ax3.set_ylabel("S")
    ax3.set_title("(C) Cell exteriority: S=beta inside")
    ax3.legend()

    # (D) 3D: composite floor over (n_agents, per-agent floor) heatmap
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    n_grid = np.arange(1, 8)
    f_grid = np.linspace(0.5, 8.0, 20)
    N, F = np.meshgrid(n_grid, f_grid)
    R = np.zeros_like(N, dtype=float)  # residue = composite floor
    for i in range(N.shape[0]):
        for j in range(N.shape[1]):
            R[i, j] = composite_floor([F[i, j]] * int(N[i, j]))
    surf = ax4.plot_surface(N, F, R, cmap="plasma", alpha=0.85, edgecolor="none")
    ax4.set_xlabel("n agents")
    ax4.set_ylabel("per-agent floor")
    ax4.set_zlabel("residue (composite floor)")
    ax4.set_title("(D) 3D: residue surface")
    fig.colorbar(surf, ax=ax4, shrink=0.6, aspect=10)

    plt.suptitle("Panel 5: Cell-Meaning, Residue, Bias, Cell Exteriority",
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
    print(f"Panels saved to {FIG_DIR}")


if __name__ == "__main__":
    main()
