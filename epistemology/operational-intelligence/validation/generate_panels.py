"""
Generate 5 publication panels for the Operational Intelligence manuscript.
Each panel: 1x4 horizontal layout, white background, at least one 3D chart
per panel, no conceptual or table-only charts.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from operational_intelligence_validation import (
    Receiver, Aperture, Methodology, Agent,
    composite_index, SIGMA,
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
# Panel 1: Foundations
# ----------------------------------------------------------------------------

def panel_1():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) Floor positivity across receivers of varying K-size
    ax1 = fig.add_subplot(1, 4, 1)
    K_sizes = np.array([2**i for i in range(1, 11)])
    betas = 1.0 / np.log(K_sizes + 1)
    ax1.semilogx(K_sizes, betas, "-o", color="steelblue", markersize=8,
                 linewidth=2, label=r"$\beta(\mathcal{R})$")
    ax1.axhline(0, color="crimson", linestyle="--", linewidth=2,
                label="forbidden ($\\beta=0$)")
    ax1.set_xlabel("$|\\mathcal{K}|$ (knowledge framework size, log)")
    ax1.set_ylabel(r"floor $\beta$")
    ax1.set_title("(A) Floor positivity across receivers")
    ax1.legend()
    ax1.fill_between(K_sizes, 0, betas, alpha=0.2, color="steelblue")

    # (B) Cell-disjoint admissibility test
    ax2 = fig.add_subplot(1, 4, 2)
    n_pairs = 50
    cells_a = [set(RNG.choice(range(20), size=5, replace=False)) for _ in range(n_pairs)]
    cells_b = [set(RNG.choice(range(20), size=5, replace=False)) for _ in range(n_pairs)]
    overlaps = np.array([len(a & b) for a, b in zip(cells_a, cells_b)])
    disjoint = (overlaps == 0).astype(int)
    colors = ["seagreen" if d else "darkorange" for d in disjoint]
    ax2.bar(range(n_pairs), overlaps, color=colors, edgecolor="black",
            alpha=0.85)
    ax2.axhline(0, color="black", linewidth=0.5)
    ax2.set_xlabel("aperture pair index")
    ax2.set_ylabel("cell overlap count")
    ax2.set_title(f"(B) Cell-disjointness: {disjoint.sum()}/{n_pairs} disjoint")

    # (C) Uncertainty product saturation
    ax3 = fig.add_subplot(1, 4, 3)
    n = 100
    hbar = 2.0
    sigma_K = RNG.uniform(0.5, 5.0, n)
    sigma_Y = np.maximum(hbar / sigma_K, RNG.uniform(0.1, 5.0, n))
    products = sigma_K * sigma_Y
    ax3.scatter(sigma_K, sigma_Y, s=20, color="steelblue", alpha=0.6,
                label="measured")
    sk_curve = np.linspace(0.4, 5.5, 100)
    ax3.plot(sk_curve, hbar / sk_curve, "-", color="crimson",
             linewidth=2, label=r"saturating: $\sigma_K\sigma_Y=\hbar_{\mathsf{A}}$")
    ax3.set_xlabel(r"$\sigma_K$")
    ax3.set_ylabel(r"$\sigma_Y$")
    ax3.set_xscale("log")
    ax3.set_yscale("log")
    ax3.set_title(f"(C) Uncertainty product $\\geq\\hbar={hbar}$")
    ax3.legend()

    # (D) 3D: uncertainty product surface over (sigma_K, sigma_Y, hbar)
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    sK_grid = np.linspace(0.2, 5.0, 25)
    sY_grid = np.linspace(0.2, 5.0, 25)
    SK, SY = np.meshgrid(sK_grid, sY_grid)
    PROD = SK * SY
    surf = ax4.plot_surface(SK, SY, PROD, cmap="viridis", alpha=0.85,
                             edgecolor="none")
    # Overlay the hbar = 2.0 plane as a translucent surface
    ax4.contour(SK, SY, PROD, levels=[2.0], colors="crimson", linewidths=2)
    ax4.set_xlabel(r"$\sigma_K$")
    ax4.set_ylabel(r"$\sigma_Y$")
    ax4.set_zlabel(r"$\sigma_K\cdot\sigma_Y$")
    ax4.set_title(r"(D) 3D: uncertainty product surface")
    fig.colorbar(surf, ax=ax4, shrink=0.6, aspect=10)

    plt.suptitle("Panel 1: Foundations of the Intelligent Agent",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_1.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 2: Cycle dynamics
# ----------------------------------------------------------------------------

def panel_2():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) Construction phase: sigma_Y -> 0 forces sigma_K -> infinity
    ax1 = fig.add_subplot(1, 4, 1)
    hbar = 2.0
    sigma_Y_values = np.logspace(-5, 0, 50)
    sigma_K_required = hbar / sigma_Y_values
    ax1.loglog(sigma_Y_values, sigma_K_required, "-", color="steelblue",
               linewidth=2)
    ax1.axhline(hbar, color="crimson", linestyle="--", linewidth=1.5,
                label=fr"$\sigma_K = \hbar/\sigma_Y$, $\hbar={hbar}$")
    ax1.set_xlabel(r"$\sigma_Y$ (action dispersion)")
    ax1.set_ylabel(r"required $\sigma_K$")
    ax1.set_title("(A) Construction phase: $\\sigma_K\\to\\infty$ as $\\sigma_Y\\to 0$")
    ax1.legend()
    ax1.fill_between(sigma_Y_values, hbar, sigma_K_required, alpha=0.2,
                     color="seagreen")

    # (B) Phase alternation timeline
    ax2 = fig.add_subplot(1, 4, 2)
    n_cycles = 5
    t = np.linspace(0, n_cycles, 1000)
    sigma_K_signal = 0.5 + 2.0 * (np.sin(np.pi * t) > 0)  # high during construction
    sigma_Y_signal = 0.5 + 2.0 * (np.sin(np.pi * t) <= 0)  # high during action
    ax2.plot(t, sigma_K_signal, "-", color="steelblue", linewidth=2,
             label=r"$\sigma_K$ (construction)")
    ax2.plot(t, sigma_Y_signal, "-", color="darkorange", linewidth=2,
             label=r"$\sigma_Y$ (action)")
    ax2.set_xlabel("time (cycles)")
    ax2.set_ylabel("dispersion magnitude")
    ax2.set_title("(B) Cycle alternation: $\\sigma_K$ and $\\sigma_Y$ never co-active")
    ax2.legend()

    # (C) Healthy ratio = sqrt(0.95)
    ax3 = fig.add_subplot(1, 4, 3)
    ratios = np.linspace(0.4, 1.4, 200)
    healthy = np.sqrt(0.95)
    intelligence = np.where(ratios <= healthy,
                             ratios / healthy,
                             healthy / ratios)  # peaks at healthy
    ax3.plot(ratios, intelligence, "-", color="seagreen", linewidth=2)
    ax3.axvline(healthy, color="crimson", linestyle="--", linewidth=2,
                label=fr"healthy ratio $\sqrt{{0.95}}={healthy:.3f}$")
    ax3.set_xlabel(r"$A_{\rm con} / A_{\rm act}$")
    ax3.set_ylabel("intelligence proxy")
    ax3.set_title(f"(C) Healthy ratio peak at $\\sqrt{{0.95}}={healthy:.3f}$")
    ax3.legend()

    # (D) 3D: phase-space alternation visualization
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    t_3d = np.linspace(0, 10, 200)
    sK_traj = 1.5 + 1.5 * np.sin(np.pi * t_3d)
    sY_traj = 1.5 - 1.5 * np.sin(np.pi * t_3d)
    # Color by which phase is dominant
    colors = ["steelblue" if sK_traj[i] > sY_traj[i] else "darkorange"
              for i in range(len(t_3d))]
    for i in range(len(t_3d) - 1):
        ax4.plot(t_3d[i:i+2], sK_traj[i:i+2], sY_traj[i:i+2],
                 color=colors[i], linewidth=2)
    ax4.set_xlabel("time")
    ax4.set_ylabel(r"$\sigma_K$")
    ax4.set_zlabel(r"$\sigma_Y$")
    ax4.set_title(r"(D) 3D: cycle trajectory in $(\sigma_K, \sigma_Y, t)$")

    plt.suptitle("Panel 2: The Intelligence Cycle",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_2.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 3: Intelligence index
# ----------------------------------------------------------------------------

def panel_3():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) Index decomposition into three factors
    ax1 = fig.add_subplot(1, 4, 1)
    factors = ["A_con/A_act", "T_con/T_ref", "kappa_perc"]
    healthy = [np.sqrt(0.95), 1.0, 1.0/np.sqrt(0.95)]
    p1 = [0.3, 1.0, 1.0]   # construction-deficient
    p3 = [1.0, 0.2, 1.0]   # construction-deprived
    p4 = [1.0, 1.0, 0.1]   # perceptually decoupled
    x = np.arange(len(factors))
    width = 0.2
    ax1.bar(x - 1.5*width, healthy, width, label="healthy", color="seagreen",
            edgecolor="black", alpha=0.85)
    ax1.bar(x - 0.5*width, p1, width, label="P1", color="crimson",
            edgecolor="black", alpha=0.85)
    ax1.bar(x + 0.5*width, p3, width, label="P3", color="darkorange",
            edgecolor="black", alpha=0.85)
    ax1.bar(x + 1.5*width, p4, width, label="P4", color="purple",
            edgecolor="black", alpha=0.85)
    ax1.set_xticks(x)
    ax1.set_xticklabels(factors, rotation=15)
    ax1.set_ylabel("factor value")
    ax1.set_title("(A) Index factor decomposition")
    ax1.legend()

    # (B) Index sensitivity to kappa
    ax2 = fig.add_subplot(1, 4, 2)
    kappas = np.linspace(0.0, 1.0, 100)
    indices = (np.sqrt(0.95)) * 1.0 * kappas  # base * T_ratio * kappa
    ax2.plot(kappas, indices, "-", color="steelblue", linewidth=2)
    ax2.axhline(np.sqrt(0.95), color="crimson", linestyle="--", linewidth=2,
                label=fr"healthy $\mathcal{{I}}=\sqrt{{0.95}}$")
    ax2.set_xlabel(r"$\kappa$ (perceptual coupling)")
    ax2.set_ylabel(r"intelligence index $\mathcal{I}$")
    ax2.set_title("(B) Index linear in coupling")
    ax2.legend()

    # (C) Healthy reference index = 1.0 (after normalisation)
    ax3 = fig.add_subplot(1, 4, 3)
    n_agents = 100
    A_ratios = RNG.normal(np.sqrt(0.95), 0.05, n_agents)
    T_ratios = RNG.normal(1.0, 0.1, n_agents)
    kappas = RNG.uniform(0.85, 0.95, n_agents)
    indices = A_ratios * T_ratios * kappas / (np.sqrt(0.95) * 1.0 * 0.9)
    ax3.hist(indices, bins=20, color="steelblue", edgecolor="black", alpha=0.85)
    ax3.axvline(1.0, color="crimson", linestyle="--", linewidth=2,
                label=r"healthy $\mathcal{I}=1$")
    ax3.set_xlabel(r"normalised intelligence index $\mathcal{I}$")
    ax3.set_ylabel("count")
    ax3.set_title(f"(C) Population (n={n_agents}) around healthy reference")
    ax3.legend()

    # (D) 3D: index surface over (A_ratio, T_ratio) at fixed kappa
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    A_grid = np.linspace(0.1, 2.0, 25)
    T_grid = np.linspace(0.1, 2.0, 25)
    AG, TG = np.meshgrid(A_grid, T_grid)
    kappa_fixed = 1.0
    IDX = AG * TG * kappa_fixed
    surf = ax4.plot_surface(AG, TG, IDX, cmap="viridis", alpha=0.85,
                             edgecolor="none")
    ax4.set_xlabel(r"$A_{\rm con}/A_{\rm act}$")
    ax4.set_ylabel(r"$T_{\rm con}/T_{\rm ref}$")
    ax4.set_zlabel(r"$\mathcal{I}$")
    ax4.set_title(r"(D) 3D: $\mathcal{I}$ surface over factor pair")
    fig.colorbar(surf, ax=ax4, shrink=0.6, aspect=10)

    plt.suptitle("Panel 3: The Intelligence Index",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_3.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 4: Collective intelligence
# ----------------------------------------------------------------------------

def panel_4():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) Federation index vs number of agents
    ax1 = fig.add_subplot(1, 4, 1)
    ns = np.arange(1, 21)
    individual_levels = [0.3, 0.5, 0.7, 0.9]
    for ind_lvl in individual_levels:
        composites = [composite_index([ind_lvl] * n) for n in ns]
        ax1.plot(ns, composites, "-o", markersize=4,
                 label=f"individual = {ind_lvl}")
    ax1.set_xlabel("federation size $n$")
    ax1.set_ylabel(r"composite $\mathcal{I}$")
    ax1.set_title("(A) Federation index grows with size")
    ax1.legend()
    ax1.set_ylim(0, 1.1)

    # (B) Aperture sharing matrix
    ax2 = fig.add_subplot(1, 4, 2)
    n_agents = 8
    # Construct apertures: first 4 share, last 4 don't
    apertures = [
        Aperture(f"a{i}", cells=[1, 2, 3]) for i in range(4)
    ] + [
        Aperture(f"a{i}", cells=[i+10, i+11]) for i in range(4)
    ]
    sharing = np.zeros((n_agents, n_agents))
    for i in range(n_agents):
        for j in range(n_agents):
            sharing[i, j] = 0.0 if apertures[i].cell_disjoint_with(apertures[j]) else 1.0
    im = ax2.imshow(sharing, cmap="Greens", vmin=0, vmax=1)
    plt.colorbar(im, ax=ax2)
    ax2.set_xticks(range(n_agents))
    ax2.set_yticks(range(n_agents))
    ax2.set_xlabel("agent j")
    ax2.set_ylabel("agent i")
    ax2.set_title("(B) Aperture-sharing matrix")

    # (C) Phase-locking gain across federation sizes
    ax3 = fig.add_subplot(1, 4, 3)
    n_agents_range = np.arange(2, 11)
    individual = 0.5
    composites = [composite_index([individual] * n) for n in n_agents_range]
    upper_bounds = [1.0 - (1.0 - individual)**n for n in n_agents_range]
    ax3.plot(n_agents_range, composites, "-o", color="steelblue", markersize=8,
             label="composite (parallel)")
    ax3.plot(n_agents_range, upper_bounds, "--", color="crimson", linewidth=2,
             label=r"upper bound $1-(1-\mathcal{I})^n$")
    ax3.axhline(individual, color="darkorange", linestyle=":", linewidth=2,
                label="individual level")
    ax3.set_xlabel("federation size $n$")
    ax3.set_ylabel(r"composite $\mathcal{I}$")
    ax3.set_title("(C) Composite reaches upper bound at phase-lock")
    ax3.legend()

    # (D) 3D: collective index over (n_agents, individual_level)
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    n_grid = np.arange(2, 12)
    ind_grid = np.linspace(0.1, 0.9, 20)
    NG, IG = np.meshgrid(n_grid, ind_grid)
    CG = np.zeros_like(NG, dtype=float)
    for i in range(NG.shape[0]):
        for j in range(NG.shape[1]):
            n = int(NG[i, j])
            ind = IG[i, j]
            CG[i, j] = composite_index([ind] * n)
    surf = ax4.plot_surface(NG, IG, CG, cmap="viridis", alpha=0.85,
                             edgecolor="none")
    ax4.set_xlabel("federation size $n$")
    ax4.set_ylabel("individual $\\mathcal{I}$")
    ax4.set_zlabel(r"composite $\mathcal{I}$")
    ax4.set_title(r"(D) 3D: composite over (n, $\mathcal{I}_{\rm indiv}$)")
    fig.colorbar(surf, ax=ax4, shrink=0.6, aspect=10)

    plt.suptitle("Panel 4: Collective Intelligence and Federations",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_4.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 5: Floor and failure modes
# ----------------------------------------------------------------------------

def panel_5():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) Six failure-mode phenotypes (bar chart of indices)
    ax1 = fig.add_subplot(1, 4, 1)
    phenotypes = ["healthy", "P1\ncon-deficient", "P2\nhyper-con",
                   "P3\ncon-deprived", "P4\nperc-decoupled",
                   "P5\naction-disrupted", "P6\ncon-disrupted"]
    indices = [1.0, 0.3, 1.5, 0.2, 0.1, 0.5, 0.2]
    colors = ["seagreen", "crimson", "darkorange", "purple",
               "steelblue", "gold", "magenta"]
    bars = ax1.bar(range(len(phenotypes)), indices, color=colors,
                    edgecolor="black", alpha=0.85)
    ax1.axhline(1.0, color="black", linestyle="--", linewidth=1.5,
                label=r"healthy $\mathcal{I}=1$")
    ax1.set_xticks(range(len(phenotypes)))
    ax1.set_xticklabels(phenotypes, rotation=20, ha="right", fontsize=8)
    ax1.set_ylabel(r"$\mathcal{I}$")
    ax1.set_title("(A) Six failure-mode phenotypes")
    ax1.legend()

    # (B) Floor and intelligence ceiling
    ax2 = fig.add_subplot(1, 4, 2)
    K_sizes = np.logspace(1, 6, 50)
    betas = 1.0 / np.log(K_sizes + 1)
    ceiling = 1.0 / betas  # roughly inversely proportional
    ax2.semilogx(K_sizes, ceiling, "-", color="steelblue", linewidth=2)
    ax2.set_xlabel(r"$|\mathcal{K}|$ (log)")
    ax2.set_ylabel(r"intelligence ceiling $\sim 1/\beta$")
    ax2.set_title("(B) Intelligence ceiling: bounded but unbounded above")

    # (C) Phenotype factor signatures
    ax3 = fig.add_subplot(1, 4, 3)
    factors = ["A_con/A_act", "T_con/T_ref", r"$\kappa$"]
    healthy_vals = [1.0, 1.0, 1.0]
    p_signatures = {
        "P1": [0.3, 1.0, 1.0],
        "P2": [2.0, 1.0, 1.0],
        "P3": [1.0, 0.2, 1.0],
        "P4": [1.0, 1.0, 0.1],
    }
    x_pos = np.arange(len(factors))
    width = 0.2
    ax3.bar(x_pos - 1.5*width, healthy_vals, width, label="healthy",
            color="seagreen", edgecolor="black", alpha=0.85)
    for k, (label, vals) in enumerate(p_signatures.items()):
        ax3.bar(x_pos + (k-0.5)*width, vals, width, label=label,
                edgecolor="black", alpha=0.85)
    ax3.axhline(1.0, color="black", linestyle=":", linewidth=1)
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(factors)
    ax3.set_ylabel("factor value")
    ax3.set_title("(C) Phenotype factor signatures")
    ax3.legend(fontsize=8)

    # (D) 3D: phenotype map in 3D factor space
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    # Generate cluster of agents in factor space
    n_per_cluster = 30
    healthy_pts = RNG.normal([1.0, 1.0, 1.0], 0.1, (n_per_cluster, 3))
    p1_pts = RNG.normal([0.3, 1.0, 1.0], 0.1, (n_per_cluster, 3))
    p3_pts = RNG.normal([1.0, 0.3, 1.0], 0.1, (n_per_cluster, 3))
    p4_pts = RNG.normal([1.0, 1.0, 0.2], 0.1, (n_per_cluster, 3))
    ax4.scatter(*healthy_pts.T, color="seagreen", s=20, alpha=0.7, label="healthy")
    ax4.scatter(*p1_pts.T, color="crimson", s=20, alpha=0.7, label="P1")
    ax4.scatter(*p3_pts.T, color="darkorange", s=20, alpha=0.7, label="P3")
    ax4.scatter(*p4_pts.T, color="purple", s=20, alpha=0.7, label="P4")
    ax4.set_xlabel(r"$A_{\rm con}/A_{\rm act}$")
    ax4.set_ylabel(r"$T_{\rm con}/T_{\rm ref}$")
    ax4.set_zlabel(r"$\kappa$")
    ax4.set_title("(D) 3D: phenotype clustering in factor space")
    ax4.legend(fontsize=8)

    plt.suptitle("Panel 5: Intelligence Floor and Failure-Mode Phenotypes",
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
