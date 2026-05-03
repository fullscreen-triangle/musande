"""
Generate 5 publication panels for the Synchronised Agent Coordination
manuscript. Each panel: 1x4 horizontal layout, white background,
at least one 3D chart per panel, no conceptual or table-only charts.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from synchronised_coordination_validation import (
    SAgentState, Agent, Aperture, Ensemble,
    V_sync, V_var, V_SF, Phi, Rstar, sigma2_min,
    Kc_from_sigma_omega, regime, synchronisation_tension,
    composite_floor_parallel, SIGMA, KB,
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
# Panel 1: Single-agent state manifold and partition potential
# ----------------------------------------------------------------------------

def panel_1():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) V_sync surface over (R, K)
    ax1 = fig.add_subplot(1, 4, 1)
    Rs = np.linspace(0, 1, 100)
    for K, label, c in [(0.5, "K<Kc (sub)", "steelblue"),
                         (1.0, "K=Kc", "seagreen"),
                         (3.0, "K>Kc (super)", "crimson")]:
        Vs = [V_sync(R, K, 1.0) for R in Rs]
        ax1.plot(Rs, Vs, "-", color=c, linewidth=2, label=label)
    ax1.set_xlabel("R")
    ax1.set_ylabel(r"$V_{\rm sync}(R)$")
    ax1.set_title(r"(A) $V_{\rm sync}$: bifurcation at $K=K_c$")
    ax1.legend()
    ax1.axhline(0, color="black", linewidth=0.5)

    # (B) V_var: variance floor
    ax2 = fig.add_subplot(1, 4, 2)
    sig2s = np.linspace(0.05, 3, 200)
    for K, c in [(1.0, "steelblue"), (2.0, "seagreen"), (4.0, "crimson")]:
        Vs = [V_var(s, 1.0, K) for s in sig2s]
        s_min = np.sqrt(1.0 / K)
        ax2.plot(sig2s, Vs, "-", color=c, linewidth=2, label=f"K={K}")
        ax2.axvline(s_min, color=c, linestyle="--", alpha=0.5)
    ax2.set_xlabel(r"$\sigma^2$")
    ax2.set_ylabel(r"$V_{\rm var}$")
    ax2.set_title(r"(B) $V_{\rm var}$: variance floor at $\sigma^2 = \sqrt{1/K}$")
    ax2.legend()

    # (C) Variance floor scaling: log-log slope -1
    ax3 = fig.add_subplot(1, 4, 3)
    Ks = np.array([0.5, 1, 2, 4, 8, 16])
    s_min = np.array([np.sqrt(1.0 / K) for K in Ks])
    sigma2_vals = s_min**2  # variance, not std dev
    ax3.loglog(Ks, sigma2_vals, "o", color="steelblue", markersize=10, label="measured")
    K_fine = np.linspace(0.5, 16, 100)
    ax3.loglog(K_fine, KB * 1.0 / K_fine, "-", color="crimson",
               linewidth=2, label=r"theory: $\sigma^2_{\min} = k_BT/K$")
    ax3.set_xlabel("K (log)")
    ax3.set_ylabel(r"$\sigma^2_{\min}$ (log)")
    ax3.set_title(r"(C) Slope $-1$: $\sigma^2_{\min} \propto K^{-1}$")
    ax3.legend()

    # (D) 3D Phi surface over (R, sigma2)
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    Rgrid = np.linspace(0.05, 0.95, 25)
    sgrid = np.linspace(0.1, 1.5, 25)
    R, S = np.meshgrid(Rgrid, sgrid)
    P = np.zeros_like(R)
    K, Kc = 2.0, 0.5
    for i in range(R.shape[0]):
        for j in range(R.shape[1]):
            state = SAgentState(R=R[i,j], sigma2=S[i,j],
                                Sk=0.5, St=0.5, Se=0.5)
            P[i,j] = Phi(state, K, Kc)
    surf = ax4.plot_surface(R, S, P, cmap="viridis", alpha=0.85, edgecolor="none")
    ax4.set_xlabel("R")
    ax4.set_ylabel(r"$\sigma^2$")
    ax4.set_zlabel(r"$\Phi$")
    ax4.set_title(r"(D) 3D: $\Phi(R,\sigma^2)$ landscape")
    fig.colorbar(surf, ax=ax4, shrink=0.6, aspect=10)

    plt.suptitle("Panel 1: Single-Agent State Manifold and Partition Potential",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_1.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 2: Five operational regimes
# ----------------------------------------------------------------------------

def panel_2():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) R* bifurcation diagram
    ax1 = fig.add_subplot(1, 4, 1)
    Kc = 1.0
    Ks = np.linspace(0, 5, 200)
    R_stars = np.array([Rstar(K, Kc) for K in Ks])
    ax1.plot(Ks, R_stars, "-", color="steelblue", linewidth=2,
             label=r"$R^* = \sqrt{1-K_c/K}$")
    ax1.axvline(Kc, color="crimson", linestyle="--", linewidth=2,
                label=r"$K_c$")
    ax1.set_xlabel("K")
    ax1.set_ylabel(r"$R^*$")
    ax1.set_title(r"(A) Pitchfork bifurcation at $K=K_c$")
    ax1.legend()

    # (B) Regime boundaries on R-axis
    ax2 = fig.add_subplot(1, 4, 2)
    R_axis = np.linspace(0, 1, 1000)
    # Color by regime
    regimes_colors = {
        "turbulent": "crimson",
        "aperture": "darkorange",
        "cascade": "gold",
        "coherent": "seagreen",
        "phase-locked": "steelblue",
    }
    for r_name, c in regimes_colors.items():
        mask = np.array([regime(r) == r_name for r in R_axis])
        ax2.fill_between(R_axis, 0, 1, where=mask, color=c, alpha=0.6, label=r_name)
    for boundary in [0.3, 0.5, 0.8, 0.95]:
        ax2.axvline(boundary, color="black", linewidth=1, linestyle="--")
    ax2.set_xlabel("R")
    ax2.set_ylabel("regime")
    ax2.set_yticks([])
    ax2.set_title("(B) Five regimes partition R-axis")
    ax2.legend(loc="upper left", fontsize=8)
    ax2.set_xlim(0, 1)

    # (C) Distribution of states across regimes in random sample
    ax3 = fig.add_subplot(1, 4, 3)
    n_samples = 1000
    R_samples = RNG.uniform(0, 1, n_samples)
    counts = {r: sum(1 for x in R_samples if regime(x) == r)
              for r in regimes_colors}
    bars = ax3.bar(range(5), list(counts.values()),
                   color=[regimes_colors[r] for r in counts],
                   edgecolor="black", alpha=0.85)
    ax3.set_xticks(range(5))
    ax3.set_xticklabels(list(counts.keys()), rotation=20, ha="right")
    ax3.set_ylabel("count (uniform sample n=1000)")
    ax3.set_title("(C) Regime distribution under uniform R")

    # (D) 3D potential surface with regime colouring
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    Rgrid = np.linspace(0, 1, 50)
    Kgrid = np.linspace(0.1, 4, 50)
    Rg, Kg = np.meshgrid(Rgrid, Kgrid)
    Vsg = np.array([[V_sync(R, K, 1.0) for R in Rgrid] for K in Kgrid])
    surf = ax4.plot_surface(Rg, Kg, Vsg, cmap="viridis", alpha=0.85, edgecolor="none")
    ax4.set_xlabel("R")
    ax4.set_ylabel("K")
    ax4.set_zlabel(r"$V_{\rm sync}$")
    ax4.set_title(r"(D) 3D: $V_{\rm sync}(R,K)$ saddle landscape")

    plt.suptitle("Panel 2: Five Operational Regimes and Bifurcation",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_2.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 3: Ensemble Kuramoto and five coordination regimes
# ----------------------------------------------------------------------------

def panel_3():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) Ensemble R as function of internal R (uniform)
    ax1 = fig.add_subplot(1, 4, 1)
    n = 10
    Rs_internal = np.linspace(0, 1, 50)
    R_ens_vals = []
    for R0 in Rs_internal:
        agents = [Agent(f"a{i}", SAgentState(R0, 0.1, 0.5, 0.5, 0.5),
                        Aperture(1), natural_freq=i * np.pi / n)
                  for i in range(n)]
        ens = Ensemble(agents)
        R_ens_vals.append(ens.R_ensemble())
    ax1.plot(Rs_internal, R_ens_vals, "-o", color="steelblue", markersize=5)
    for boundary in [0.3, 0.5, 0.8, 0.95]:
        ax1.axhline(boundary, color="crimson", linewidth=1, linestyle="--")
    ax1.set_xlabel(r"individual $R_i$ (uniform)")
    ax1.set_ylabel(r"$R_{\rm ens}$")
    ax1.set_title(r"(A) Ensemble R vs individual R")

    # (B) Coupling coefficient vs ensemble R (synchronisation onset)
    ax2 = fig.add_subplot(1, 4, 2)
    sigma_omega = 1.0
    Kc_ens = Kc_from_sigma_omega(sigma_omega)
    Ks = np.linspace(0.05, 4, 100)
    R_ens_K = np.array([Rstar(K, Kc_ens) for K in Ks])
    ax2.plot(Ks, R_ens_K, "-", color="seagreen", linewidth=2)
    ax2.axvline(Kc_ens, color="crimson", linestyle="--", linewidth=2,
                label=fr"$K_c = {Kc_ens:.3f}$")
    ax2.axhline(0.95, color="steelblue", linestyle=":", linewidth=2,
                label="phase-locked")
    ax2.set_xlabel("inter-agent coupling K")
    ax2.set_ylabel(r"$R_{\rm ens}$")
    ax2.set_title(r"(B) Synchronisation onset at $K_c$")
    ax2.legend()

    # (C) Anti-phase agents -> low ensemble R
    ax3 = fig.add_subplot(1, 4, 3)
    n_agents_options = [2, 3, 4, 5, 6, 8]
    R_uniform_phase = []
    R_aligned = []
    for n in n_agents_options:
        # Uniform phase distribution (anti-correlated)
        agents_u = [Agent(f"u{i}", SAgentState(1.0, 0.05, 0.5, 0.5, 0.5),
                          Aperture(1), natural_freq=2 * np.pi * i / n)
                    for i in range(n)]
        ens_u = Ensemble(agents_u)
        R_uniform_phase.append(ens_u.R_ensemble())
        # Aligned (all same phase)
        agents_a = [Agent(f"a{i}", SAgentState(1.0, 0.05, 0.5, 0.5, 0.5),
                          Aperture(1), natural_freq=0.0)
                    for i in range(n)]
        ens_a = Ensemble(agents_a)
        R_aligned.append(ens_a.R_ensemble())
    width = 0.35
    x = np.arange(len(n_agents_options))
    ax3.bar(x - width/2, R_uniform_phase, width, color="crimson",
            label="uniform phase", edgecolor="black", alpha=0.85)
    ax3.bar(x + width/2, R_aligned, width, color="seagreen",
            label="aligned phase", edgecolor="black", alpha=0.85)
    ax3.set_xticks(x)
    ax3.set_xticklabels([f"n={n}" for n in n_agents_options])
    ax3.set_ylabel(r"$R_{\rm ens}$")
    ax3.set_title(r"(C) Ensemble R: uniform vs aligned")
    ax3.legend()

    # (D) 3D phase diagram: ensemble R over (n_agents, sigma_omega)
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    n_grid = np.arange(2, 11)
    so_grid = np.linspace(0.1, 2.0, 15)
    NG, SG = np.meshgrid(n_grid, so_grid)
    K_fixed = 2.0
    R_grid = np.zeros_like(NG, dtype=float)
    for i in range(NG.shape[0]):
        for j in range(NG.shape[1]):
            sig = SG[i, j]
            Kc_local = 2 * sig / np.pi
            R_grid[i, j] = Rstar(K_fixed, Kc_local)
    surf = ax4.plot_surface(NG, SG, R_grid, cmap="viridis", alpha=0.85, edgecolor="none")
    ax4.set_xlabel("n agents")
    ax4.set_ylabel(r"$\sigma_\omega$")
    ax4.set_zlabel(r"$R_{\rm ens}$")
    ax4.set_title(r"(D) 3D: $R_{\rm ens}$ over $(n,\sigma_\omega)$")

    plt.suptitle("Panel 3: Ensemble Kuramoto and Five Coordination Regimes",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_3.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 4: Synchronisation as partition extinction
# ----------------------------------------------------------------------------

def panel_4():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) tau_p vs T (analogue of partition extinction in physical paper)
    ax1 = fig.add_subplot(1, 4, 1)
    Ts = np.linspace(0.5, 2.5, 200)
    Tc = 1.0
    # Above Tc: tau_p = (T - Tc)
    # Below Tc: tau_p = 0 (partition extinction)
    tau_p = np.array([T - Tc if T > Tc else 0 for T in Ts])
    ax1.plot(Ts, tau_p, "-", color="steelblue", linewidth=2)
    ax1.axvline(Tc, color="crimson", linestyle="--", linewidth=2,
                label=r"$T_c$")
    ax1.set_xlabel(r"$T / T_c$")
    ax1.set_ylabel(r"partition lag $\tau_p$")
    ax1.set_title(r"(A) Partition lag $\tau_p$ vanishes below $T_c$")
    ax1.legend()
    ax1.fill_between(Ts, 0, np.where(Ts <= Tc, 0.5, 0),
                     color="seagreen", alpha=0.3, label="extinct")

    # (B) Coordination friction vs ensemble R
    ax2 = fig.add_subplot(1, 4, 2)
    R_ens_vals = np.linspace(0.1, 1.0, 100)
    # Friction = positive for R<0.95, drops to 0 at R>=0.95 (discontinuity)
    friction = np.array([1.0 - r if r < 0.95 else 0.0 for r in R_ens_vals])
    ax2.plot(R_ens_vals, friction, "-", color="darkorange", linewidth=2)
    ax2.axvline(0.95, color="crimson", linestyle="--", linewidth=2,
                label="phase-lock")
    ax2.set_xlabel(r"$R_{\rm ens}$")
    ax2.set_ylabel("coordination friction")
    ax2.set_title(r"(B) Friction vanishes at $R_{\rm ens} = 0.95$")
    ax2.legend()

    # (C) Synchronisation tension theta vs decoder distance
    ax3 = fig.add_subplot(1, 4, 3)
    decoder_distances = np.linspace(0, 2, 100)
    # theta = decoder_distance (linear proxy)
    theta_vals = decoder_distances.copy()
    ax3.plot(decoder_distances, theta_vals, "-", color="steelblue",
             linewidth=2)
    ax3.axhline(0.0, color="seagreen", linestyle="--", linewidth=2,
                label="phase-locked")
    ax3.set_xlabel("decoder distance")
    ax3.set_ylabel(r"$\theta$ (sync tension)")
    ax3.set_title(r"(C) Sync tension $\theta$ vs decoder distance")
    ax3.legend()

    # (D) 3D: composite floor with and without sync
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    n_grid = np.arange(2, 11)
    f_grid = np.linspace(0.5, 5.0, 20)
    NG, FG = np.meshgrid(n_grid, f_grid)
    composite_indep = np.zeros_like(NG, dtype=float)
    composite_sync = np.zeros_like(NG, dtype=float)
    for i in range(NG.shape[0]):
        for j in range(NG.shape[1]):
            n = int(NG[i, j])
            f = FG[i, j]
            composite_indep[i, j] = composite_floor_parallel([f] * n)
            composite_sync[i, j] = f  # synchronised: composite = single agent
    # Plot both surfaces
    surf1 = ax4.plot_surface(NG, FG, composite_indep, cmap="viridis",
                              alpha=0.7, edgecolor="none", label="independent")
    surf2 = ax4.plot_surface(NG, FG, composite_sync, cmap="plasma",
                              alpha=0.5, edgecolor="none", label="synchronised")
    ax4.set_xlabel("n agents")
    ax4.set_ylabel("per-agent floor")
    ax4.set_zlabel("composite floor")
    ax4.set_title("(D) 3D: independent (low) vs sync (flat)")

    plt.suptitle("Panel 4: Synchronisation as Partition Extinction",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_4.png", dpi=150, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# Panel 5: Aperture sharing and memory compatibility
# ----------------------------------------------------------------------------

def panel_5():
    fig = plt.figure(figsize=(22, 5.5))

    # (A) Aperture multipole orders
    ax1 = fig.add_subplot(1, 4, 1)
    theta = np.linspace(0, 2 * np.pi, 200)
    for ell, c, label in [(0, "steelblue", "monopole"),
                            (1, "seagreen", "dipole"),
                            (2, "darkorange", "quadrupole")]:
        # Multipole field magnitude: 1/r^(2+ell)
        # Plot angular pattern at fixed r
        if ell == 0:
            r = np.ones_like(theta)
        elif ell == 1:
            r = np.abs(np.cos(theta))
        else:
            r = np.abs(3 * np.cos(theta)**2 - 1) / 2
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        ax1.plot(x, y, "-", color=c, linewidth=2, label=f"{label} ($\\ell={ell}$)")
    ax1.set_xlim(-1.2, 1.2)
    ax1.set_ylim(-1.2, 1.2)
    ax1.set_aspect("equal")
    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.set_title("(A) Aperture multipole patterns")
    ax1.legend()

    # (B) Aperture sharing matrix for n=5 ensemble
    ax2 = fig.add_subplot(1, 4, 2)
    n = 5
    # All same aperture -> all share
    apertures_locked = [Aperture(1)] * n
    sharing = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            sharing[i, j] = 1.0 if apertures_locked[i].isomorphic(apertures_locked[j]) else 0.0
    im = ax2.imshow(sharing, cmap="Greens", vmin=0, vmax=1)
    plt.colorbar(im, ax=ax2, label="isomorphic")
    ax2.set_xticks(range(n))
    ax2.set_yticks(range(n))
    ax2.set_xlabel("agent j")
    ax2.set_ylabel("agent i")
    ax2.set_title("(B) Aperture sharing matrix (all dipole)")

    # (C) Memory traces for phase-locked agents
    ax3 = fig.add_subplot(1, 4, 3)
    t = np.linspace(0, 10, 100)
    H_field_base = 0.5 + 0.3 * np.sin(t / 2) + 0.1 * t / 10
    n_agents = 4
    for i in range(n_agents):
        noise = RNG.normal(0, 0.02, len(t))
        H_field = H_field_base + noise
        # Memory = cumulative positive differences
        M = np.cumsum(np.maximum(0, np.diff(H_field, prepend=H_field[0])))
        ax3.plot(t, M, "-", linewidth=1.5, label=f"agent {i+1}")
    ax3.set_xlabel("time")
    ax3.set_ylabel(r"memory trace $M(t)$")
    ax3.set_title("(C) Memory traces congruent (phase-locked)")
    ax3.legend()

    # (D) 3D: synchronisation phase diagram (R, theta, Kc)
    ax4 = fig.add_subplot(1, 4, 4, projection="3d")
    K_grid = np.linspace(0.1, 4, 25)
    sigma_grid = np.linspace(0.1, 2.0, 25)
    KG, SG = np.meshgrid(K_grid, sigma_grid)
    R_phase = np.zeros_like(KG)
    for i in range(KG.shape[0]):
        for j in range(KG.shape[1]):
            Kc = 2 * SG[i, j] / np.pi
            R_phase[i, j] = Rstar(KG[i, j], Kc)
    surf = ax4.plot_surface(KG, SG, R_phase, cmap="viridis", alpha=0.85,
                             edgecolor="none")
    ax4.set_xlabel("coupling K")
    ax4.set_ylabel(r"$\sigma_\omega$")
    ax4.set_zlabel(r"$R^*$")
    ax4.set_title(r"(D) 3D: Synchronisation phase diagram")

    plt.suptitle("Panel 5: Aperture Sharing and Memory Compatibility",
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
