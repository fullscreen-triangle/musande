"""
Publication panels for S-Entropy paper.

Generates five 1x4 panels with at least one 3D chart per panel,
white background, minimal text. Output: PNG files in ./figures/.
"""

import json
import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from matplotlib import cm

# ------------------------------------------------------------
# Setup
# ------------------------------------------------------------

ROOT = Path(__file__).parent
FIG_DIR = ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR = ROOT / "results"

# Global style
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.8,
    "xtick.color": "#333333",
    "ytick.color": "#333333",
    "axes.labelcolor": "#333333",
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.titlesize": 10,
    "legend.fontsize": 8,
    "legend.frameon": False,
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 100,
})

PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
           "#9467bd", "#17becf", "#8c564b", "#e377c2"]
COLOR_3D = cm.viridis


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def load_result(name: str) -> dict:
    with (RESULTS_DIR / f"{name}.json").open("r", encoding="utf-8") as fh:
        return json.load(fh)


def style_3d(ax):
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("#cccccc")
    ax.yaxis.pane.set_edgecolor("#cccccc")
    ax.zaxis.pane.set_edgecolor("#cccccc")
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=7)
    ax.xaxis.label.set_fontsize(8)
    ax.yaxis.label.set_fontsize(8)
    ax.zaxis.label.set_fontsize(8)


def make_figure(width: float = 16.0, height: float = 4.0):
    fig = plt.figure(figsize=(width, height))
    return fig


# ============================================================
# Panel 1: Floor Theorem and Bounded Cognition
# ============================================================

def panel_1_floor():
    floor_data = load_result("01_floor_theorem")["data"]
    info_data = load_result("14_floor_information")["data"]
    info_bound = load_result("11_information_bound")["data"]

    fig = make_figure()

    # A. Floor vs capacity (log-log)
    ax1 = fig.add_subplot(1, 4, 1)
    caps = np.array([d["capacity"] for d in floor_data])
    floors = np.array([d["floor"] for d in floor_data])
    ax1.loglog(caps, floors, "o-", color=PALETTE[0], lw=1.5, markersize=5)
    ax1.set_xlabel("Capacity |K|")
    ax1.set_ylabel(r"$S_\flat$")
    ax1.set_title("A. Floor vs capacity")
    ax1.grid(True, which="both", alpha=0.3)

    # B. Information divergence as floor → 0
    ax2 = fig.add_subplot(1, 4, 2)
    ifloors = np.array([d["floor"] for d in info_data])
    bits = np.array([d["information_bits"] for d in info_data])
    ax2.semilogx(ifloors, bits, "o-", color=PALETTE[1], lw=1.5, markersize=5)
    ax2.invert_xaxis()
    ax2.set_xlabel(r"$S_\flat$")
    ax2.set_ylabel("Information (bits)")
    ax2.set_title(r"B. $I \to \infty$ as $S_\flat \to 0$")
    ax2.grid(True, which="both", alpha=0.3)

    # C. 3D: Information surface over (floor, epsilon)
    ax3 = fig.add_subplot(1, 4, 3, projection="3d")
    floors_unique = sorted(set(d["floor"] for d in info_bound))
    epsilons_unique = sorted(set(d["epsilon"] for d in info_bound))
    F, E = np.meshgrid(np.array(floors_unique), np.array(epsilons_unique))
    info_grid = np.zeros_like(F)
    for d in info_bound:
        i = floors_unique.index(d["floor"])
        j = epsilons_unique.index(d["epsilon"])
        info_grid[j, i] = d["information_bits"]
    surf = ax3.plot_surface(np.log10(F), np.log10(E), info_grid,
                            cmap=COLOR_3D, alpha=0.85, edgecolor="none")
    ax3.set_xlabel(r"$\log_{10} S_\flat$")
    ax3.set_ylabel(r"$\log_{10} \epsilon$")
    ax3.set_zlabel("bits")
    ax3.set_title("C. Information surface")
    ax3.view_init(elev=22, azim=-50)
    style_3d(ax3)

    # D. S-distribution: candidates near truth
    ax4 = fig.add_subplot(1, 4, 4)
    np.random.seed(0)
    rng = np.random.default_rng(0)
    candidates = rng.normal(0, 1.0, 5000)
    floor_value = 1.5
    s_vals = np.maximum(np.abs(candidates) * 50.0 / 3.0, floor_value)
    ax4.hist(s_vals, bins=50, color=PALETTE[2], edgecolor="white",
             linewidth=0.5)
    ax4.axvline(floor_value, color=PALETTE[3], lw=1.5,
                linestyle="--", label=r"$S_\flat$")
    ax4.set_xlabel("S-value")
    ax4.set_ylabel("Count")
    ax4.set_title("D. S-distribution (floor)")
    ax4.legend(loc="upper right")
    ax4.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "panel_1_floor.png", dpi=200,
                bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  saved panel_1_floor.png")


# ============================================================
# Panel 2: Triple Equivalence
# ============================================================

def panel_2_triple_equivalence():
    eq_data = load_result("02_triple_equivalence")
    # Recompute the full 40 round-trips to plot densely
    omegas = np.exp(np.linspace(0.1, 5.0, 40))
    phis = np.linspace(0.0, 2 * math.pi, 40)

    # Mock the round trip (same logic as in s_entropy_validation)
    def osc_to_cat(omega, phi):
        if omega <= 0:
            return (0, 0, 0.0)
        n = int(math.floor(math.log2(max(omega, 1e-10))))
        residual = omega - 2 ** n
        if 2 ** n != 0:
            l = int(math.floor(residual / (2 ** max(n - 1, 0))))
        else:
            l = 0
        m = phi
        return (n, l, m)

    def cat_to_osc(label):
        n, l, m = label
        omega = 2 ** n + l * (2 ** max(n - 1, 0))
        return (omega, m)

    pairs_in = list(zip(omegas, phis))
    pairs_out = []
    errors = []
    for w, p in pairs_in:
        c = osc_to_cat(w, p)
        w2, p2 = cat_to_osc(c)
        pairs_out.append((w2, p2))
        errors.append(abs(w - w2) / max(w, 1e-10))

    fig = make_figure()

    # A. Round-trip omega error vs omega
    ax1 = fig.add_subplot(1, 4, 1)
    ax1.semilogx(omegas, errors, "o", color=PALETTE[0], markersize=5,
                 alpha=0.8)
    ax1.set_xlabel(r"$\omega_{in}$")
    ax1.set_ylabel("relative error")
    ax1.set_title("A. Round-trip error")
    ax1.grid(True, which="both", alpha=0.3)

    # B. omega_in vs omega_out (identity diagonal)
    ax2 = fig.add_subplot(1, 4, 2)
    out_w = np.array([p[0] for p in pairs_out])
    ax2.loglog(omegas, out_w, "o", color=PALETTE[1], markersize=5,
               alpha=0.8)
    diagonal = np.array([min(omegas), max(omegas)])
    ax2.plot(diagonal, diagonal, "--", color="#888888", lw=1.0)
    ax2.set_xlabel(r"$\omega_{in}$")
    ax2.set_ylabel(r"$\omega_{out}$")
    ax2.set_title("B. Round-trip identity")
    ax2.grid(True, which="both", alpha=0.3)

    # C. 3D: scatter of (omega_in, omega_out, error)
    ax3 = fig.add_subplot(1, 4, 3, projection="3d")
    ax3.scatter(np.log10(omegas), np.log10(out_w),
                np.array(errors), c=np.array(errors),
                cmap=COLOR_3D, s=30, alpha=0.9, edgecolor="black",
                linewidth=0.3)
    ax3.set_xlabel(r"$\log_{10}\omega_{in}$")
    ax3.set_ylabel(r"$\log_{10}\omega_{out}$")
    ax3.set_zlabel("error")
    ax3.set_title("C. (in, out, error)")
    ax3.view_init(elev=22, azim=-60)
    style_3d(ax3)

    # D. Phase recovery
    ax4 = fig.add_subplot(1, 4, 4)
    out_p = np.array([p[1] for p in pairs_out])
    ax4.plot(phis, out_p, "o", color=PALETTE[2], markersize=5,
             alpha=0.8)
    diagonal2 = np.array([0, 2 * math.pi])
    ax4.plot(diagonal2, diagonal2, "--", color="#888888", lw=1.0)
    ax4.set_xlabel(r"$\phi_{in}$")
    ax4.set_ylabel(r"$\phi_{out}$")
    ax4.set_title("D. Phase preservation")
    ax4.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "panel_2_triple_equivalence.png", dpi=200,
                bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  saved panel_2_triple_equivalence.png")


# ============================================================
# Panel 3: Catalyst Convergence
# ============================================================

def panel_3_catalyst_convergence():
    conv_data = load_result("07_catalyst_convergence")
    series = conv_data["data"]

    # Recompute full data for plotting
    floor = 1.0
    initial_s = 100.0

    def apply_catalyst(s, kappa, fl):
        residual = s - fl
        return fl + residual * (1.0 - kappa)

    test_kappas = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]
    n_steps = 50
    full_series = {}
    for kappa in test_kappas:
        s_vals = [initial_s]
        s = initial_s
        for _ in range(n_steps):
            s = apply_catalyst(s, kappa, floor)
            s_vals.append(s)
        full_series[kappa] = s_vals

    fig = make_figure()

    # A. Geometric decay (semilog)
    ax1 = fig.add_subplot(1, 4, 1)
    for i, k in enumerate(test_kappas):
        residuals = np.array(full_series[k]) - floor
        residuals = np.maximum(residuals, 1e-20)
        ax1.semilogy(residuals, "-", color=PALETTE[i % len(PALETTE)],
                     lw=1.5, label=fr"$\kappa$={k}")
    ax1.set_xlabel("steps")
    ax1.set_ylabel(r"$S - S_\flat$")
    ax1.set_title("A. Geometric decay")
    ax1.legend(ncol=2, loc="upper right")
    ax1.grid(True, which="both", alpha=0.3)

    # B. Predicted vs measured residual (identity scatter)
    ax2 = fig.add_subplot(1, 4, 2)
    all_measured = []
    all_predicted = []
    for k in test_kappas:
        residuals = np.array(full_series[k]) - floor
        predicted = (initial_s - floor) * np.array(
            [(1 - k) ** i for i in range(len(residuals))])
        all_measured.extend(residuals)
        all_predicted.extend(predicted)
    measured = np.maximum(np.array(all_measured), 1e-25)
    predicted = np.maximum(np.array(all_predicted), 1e-25)
    ax2.loglog(predicted, measured, "o", color=PALETTE[1],
               markersize=4, alpha=0.5)
    diag = np.array([min(predicted), max(predicted)])
    ax2.loglog(diag, diag, "--", color="#888888", lw=1.0)
    ax2.set_xlabel("predicted residual")
    ax2.set_ylabel("measured residual")
    ax2.set_title("B. Identity (theory = experiment)")
    ax2.grid(True, which="both", alpha=0.3)

    # C. 3D: residual surface over (step, kappa)
    ax3 = fig.add_subplot(1, 4, 3, projection="3d")
    K, T = np.meshgrid(np.array(test_kappas), np.arange(n_steps + 1))
    Z = np.zeros_like(K, dtype=float)
    for j, k in enumerate(test_kappas):
        Z[:, j] = np.maximum(np.array(full_series[k]) - floor, 1e-20)
    Zlog = np.log10(Z)
    surf = ax3.plot_surface(K, T, Zlog, cmap=COLOR_3D,
                            alpha=0.85, edgecolor="none")
    ax3.set_xlabel(r"$\kappa$")
    ax3.set_ylabel("step")
    ax3.set_zlabel(r"$\log_{10}(S-S_\flat)$")
    ax3.set_title("C. Residual surface")
    ax3.view_init(elev=22, azim=-65)
    style_3d(ax3)

    # D. Half-life: steps to halve residual
    ax4 = fig.add_subplot(1, 4, 4)
    half_lives = [math.log(0.5) / math.log(1 - k) for k in test_kappas]
    ax4.plot(test_kappas, half_lives, "o-", color=PALETTE[3],
             lw=1.5, markersize=6)
    ax4.set_xlabel(r"$\kappa$")
    ax4.set_ylabel("steps to half")
    ax4.set_title("D. Half-life vs catalytic power")
    ax4.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "panel_3_convergence.png", dpi=200,
                bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  saved panel_3_convergence.png")


# ============================================================
# Panel 4: Compositional Multiplicity & Recursion
# ============================================================

def panel_4_multiplicity():
    comp_data = load_result("03_compositional_multiplicity")["data"]
    rec_data = load_result("08_recursive_multiplicity")["data"]

    fig = make_figure()

    # A. Composition count vs n
    ax1 = fig.add_subplot(1, 4, 1)
    ns = np.array([d["n"] for d in comp_data])
    actuals = np.array([d["actual"] for d in comp_data])
    predicted = np.array([d["predicted"] for d in comp_data])
    ax1.semilogy(ns, predicted, "-", color=PALETTE[0], lw=1.5,
                 label=r"$2^{n-1}$")
    ax1.semilogy(ns, actuals, "o", color=PALETTE[1], markersize=6,
                 label="enumerated")
    ax1.set_xlabel("n")
    ax1.set_ylabel("compositions")
    ax1.set_title(r"A. $|\mathrm{Comp}(n)| = 2^{n-1}$")
    ax1.legend(loc="upper left")
    ax1.grid(True, which="both", alpha=0.3)

    # B. Recursive multiplicity vs depth
    ax2 = fig.add_subplot(1, 4, 2)
    depths = np.array([d["depth"] for d in rec_data])
    leaf_count = np.array([d["leaf_count"] for d in rec_data])
    labelled = np.array([d["labelled_count"] for d in rec_data])
    ax2.semilogy(depths, leaf_count, "o-", color=PALETTE[2],
                 lw=1.5, markersize=6, label=r"$3^d$ leaves")
    ax2.semilogy(depths, labelled, "s-", color=PALETTE[3],
                 lw=1.5, markersize=6, label=r"$3 \cdot 4^{d-1}$")
    ax2.set_xlabel("depth d")
    ax2.set_ylabel("count")
    ax2.set_title("B. Recursive growth")
    ax2.legend(loc="upper left")
    ax2.grid(True, which="both", alpha=0.3)

    # C. 3D: T(n,d) surface
    ax3 = fig.add_subplot(1, 4, 3, projection="3d")
    n_grid = np.arange(1, 20)
    d_grid = np.arange(1, 8)
    N, D = np.meshgrid(n_grid, d_grid)
    T = D * (D + 1) ** (N - 1)
    Z = np.log10(T.astype(float))
    surf = ax3.plot_surface(N, D, Z, cmap=COLOR_3D,
                            alpha=0.85, edgecolor="none")
    ax3.set_xlabel("n")
    ax3.set_ylabel("d")
    ax3.set_zlabel(r"$\log_{10} T(n,d)$")
    ax3.set_title(r"C. $T(n,d)$ surface")
    ax3.view_init(elev=24, azim=-60)
    style_3d(ax3)

    # D. Bits to specify a composition
    ax4 = fig.add_subplot(1, 4, 4)
    bits_per_n = np.log2(actuals.astype(float))
    ax4.plot(ns, bits_per_n, "o-", color=PALETTE[4], lw=1.5, markersize=6)
    ax4.plot(ns, ns - 1, "--", color="#888888", lw=1.0,
             label=r"$n-1$")
    ax4.set_xlabel("n")
    ax4.set_ylabel("bits")
    ax4.set_title("D. Information per composition")
    ax4.legend(loc="upper left")
    ax4.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "panel_4_multiplicity.png", dpi=200,
                bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  saved panel_4_multiplicity.png")


# ============================================================
# Panel 5: Catalytic Power Composition
# ============================================================

def panel_5_catalytic_composition():
    cascade_data = load_result("12_cascade_composition")["data"]
    mult_data = load_result("06_multiplicative_catalytic_power")

    fig = make_figure()

    # A. Composite kappa vs k1 for various k2
    ax1 = fig.add_subplot(1, 4, 1)
    k_grid = np.linspace(0, 0.99, 100)
    for i, k2 in enumerate([0.0, 0.2, 0.5, 0.8, 0.95]):
        composite = 1 - (1 - k_grid) * (1 - k2)
        ax1.plot(k_grid, composite, "-",
                 color=PALETTE[i % len(PALETTE)], lw=1.5,
                 label=fr"$\kappa_2$={k2}")
    ax1.set_xlabel(r"$\kappa_1$")
    ax1.set_ylabel(r"$\kappa_{12}$")
    ax1.set_title("A. Composite catalytic power")
    ax1.legend(loc="lower right")
    ax1.grid(True, alpha=0.3)

    # B. Cascade convergence
    ax2 = fig.add_subplot(1, 4, 2)
    for i, base_k in enumerate([0.1, 0.3, 0.5, 0.7]):
        ns = np.arange(1, 21)
        composite = 1 - (1 - base_k) ** ns
        ax2.plot(ns, composite, "o-",
                 color=PALETTE[i % len(PALETTE)],
                 lw=1.5, markersize=4,
                 label=fr"$\kappa$={base_k}")
    ax2.axhline(1.0, linestyle="--", color="#888888", lw=1.0)
    ax2.set_xlabel("cascade length n")
    ax2.set_ylabel(r"$\kappa_{cascade}$")
    ax2.set_title("B. Cascade convergence")
    ax2.legend(loc="lower right")
    ax2.set_ylim(0, 1.05)
    ax2.grid(True, alpha=0.3)

    # C. 3D: Composite kappa surface over (k1, k2)
    ax3 = fig.add_subplot(1, 4, 3, projection="3d")
    K1 = np.linspace(0, 1, 50)
    K2 = np.linspace(0, 1, 50)
    K1g, K2g = np.meshgrid(K1, K2)
    composite_grid = 1 - (1 - K1g) * (1 - K2g)
    surf = ax3.plot_surface(K1g, K2g, composite_grid, cmap=COLOR_3D,
                            alpha=0.85, edgecolor="none")
    ax3.set_xlabel(r"$\kappa_1$")
    ax3.set_ylabel(r"$\kappa_2$")
    ax3.set_zlabel(r"$\kappa_{12}$")
    ax3.set_title(r"C. $1 - (1-\kappa_1)(1-\kappa_2)$")
    ax3.view_init(elev=24, azim=-55)
    style_3d(ax3)

    # D. Borel-Cantelli: cumulative kappa vs final residual
    ax4 = fig.add_subplot(1, 4, 4)
    n_terms = 100
    kappa_constant = 0.1
    cum_kappas_const = np.cumsum([kappa_constant] * n_terms)
    res_const = (1 - kappa_constant) ** np.arange(1, n_terms + 1) * 99.0
    cum_kappas_div = np.cumsum([1.0 / k for k in range(1, n_terms + 1)])
    res_div = []
    s = 99.0
    for k in range(1, n_terms + 1):
        s = s * (1 - 1.0 / k)
        res_div.append(max(s, 1e-20))
    cum_kappas_conv = np.cumsum([0.5 ** k for k in range(1, n_terms + 1)])
    res_conv = []
    s = 99.0
    for k in range(1, n_terms + 1):
        s = s * (1 - 0.5 ** k)
        res_conv.append(max(s, 1e-20))

    ax4.semilogy(cum_kappas_const, res_const, "-",
                 color=PALETTE[0], lw=1.5,
                 label=r"$\kappa_i = 0.1$ (div)")
    ax4.semilogy(cum_kappas_div, res_div, "-",
                 color=PALETTE[1], lw=1.5,
                 label=r"$\kappa_i = 1/i$ (div)")
    ax4.semilogy(cum_kappas_conv, res_conv, "-",
                 color=PALETTE[2], lw=1.5,
                 label=r"$\kappa_i = 2^{-i}$ (conv)")
    ax4.set_xlabel(r"$\sum \kappa_i$")
    ax4.set_ylabel(r"residual $S - S_\flat$")
    ax4.set_title("D. Borel-Cantelli analogue")
    ax4.legend(loc="upper right")
    ax4.grid(True, which="both", alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "panel_5_cascade.png", dpi=200,
                bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  saved panel_5_cascade.png")


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    print(f"Generating panels in {FIG_DIR}...")
    panel_1_floor()
    panel_2_triple_equivalence()
    panel_3_catalyst_convergence()
    panel_4_multiplicity()
    panel_5_catalytic_composition()
    print("Done.")
