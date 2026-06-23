"""
make_panels.py -- render the 6 validation panels.

Each panel: one row of 4 charts, at least one 3D, white background, minimal
text (short axis labels only; no titles, legends-as-prose, tables, or
conceptual diagrams). Every chart is driven by figure_data.json, produced from
the concrete bounded-resolvable-space model.

Outputs panel_1.png ... panel_6.png (300 dpi).
"""

from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "font.size": 9,
    "axes.linewidth": 0.8,
    "axes.edgecolor": "#444444",
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "axes.labelcolor": "#222222",
})

INK = "#1f3b73"      # primary
INK2 = "#c0392b"     # contrast
INK3 = "#2e8b57"     # third
GRID = "#dddddd"

with open("figure_data.json", encoding="utf-8") as f:
    D = json.load(f)


def style(ax):
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def trisurf(ax, x, y, z, cmap="viridis"):
    x = np.asarray(x, float); y = np.asarray(y, float); z = np.asarray(z, float)
    ax.plot_trisurf(x, y, z, cmap=cmap, linewidth=0.1, antialiased=True,
                    edgecolor="none", alpha=0.95)
    ax.xaxis.pane.set_facecolor("white")
    ax.yaxis.pane.set_facecolor("white")
    ax.zaxis.pane.set_facecolor("white")
    ax.xaxis.pane.set_edgecolor("#cccccc")
    ax.yaxis.pane.set_edgecolor("#cccccc")
    ax.zaxis.pane.set_edgecolor("#cccccc")
    ax.grid(True)


def newrow():
    fig = plt.figure(figsize=(18, 4.5))
    return fig


# =====================================================================
# Panel 1 -- Boundary-Thickness Theorem
# =====================================================================
def panel1():
    d = D["panel1_boundary_thickness"]
    fig = newrow()

    ax = fig.add_subplot(1, 4, 1)
    s = d["scatter_thickness_vs_mumin"]
    mm = np.array(s["mu_min"]); th = np.array(s["thickness"])
    ax.scatter(mm, th, s=8, c=INK, alpha=0.35, edgecolors="none")
    lo, hi = mm.min(), mm.max()
    ax.plot([lo, hi], [lo, hi], color=INK2, lw=1.6)  # thickness = mu_min line
    style(ax); ax.set_xlabel(r"$\mu_{\min}$"); ax.set_ylabel(r"$\beta_\mathscr{P}(A)$")

    ax = fig.add_subplot(1, 4, 2)
    r = np.array(d["hist_ratio"]["ratio_thickness_over_mumin"])
    ax.hist(r, bins=40, color=INK, alpha=0.85)
    ax.axvline(1.0, color=INK2, lw=1.6)
    style(ax); ax.set_xlabel(r"$\beta / \mu_{\min}$"); ax.set_ylabel("count")

    ax = fig.add_subplot(1, 4, 3)
    s = d["scatter_scale_vs_thickness"]
    ax.scatter(s["scale"], s["thickness"], s=8, c=INK3, alpha=0.35,
               edgecolors="none")
    style(ax); ax.set_xlabel(r"$\sigma(A)$"); ax.set_ylabel(r"$\beta_\mathscr{P}(A)$")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_ncells_mumin_minthick"]
    trisurf(ax, s["n_cells"], s["mu_min"], s["min_thickness"], "viridis")
    ax.set_xlabel("cells"); ax.set_ylabel(r"$\mu_{\min}$"); ax.set_zlabel(r"$\min\beta$")
    ax.view_init(elev=22, azim=-60)

    fig.tight_layout()
    fig.savefig("panel_1.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


# =====================================================================
# Panel 2 -- Three derivations of the floor agree
# =====================================================================
def panel2():
    d = D["panel2_floor_agreement"]
    fig = newrow()

    ax = fig.add_subplot(1, 4, 1)
    s = d["geo_vs_rep"]
    g = np.array(s["geo_floor"]); r = np.array(s["rep_floor"])
    ax.scatter(g, r, s=12, c=INK, alpha=0.45, edgecolors="none")
    m = max(g.max(), r.max())
    ax.plot([0, m], [0, m], color=INK2, lw=1.4)
    style(ax); ax.set_xlabel("geometric floor"); ax.set_ylabel("representational")

    ax = fig.add_subplot(1, 4, 2)
    s = d["geo_vs_cost"]
    g = np.array(s["geo_floor"]); c = np.array(s["cost_floor"])
    ax.scatter(g, c, s=12, c=INK3, alpha=0.45, edgecolors="none")
    m = max(g.max(), c.max())
    ax.plot([0, m], [0, m], color=INK2, lw=1.4)
    style(ax); ax.set_xlabel("geometric floor"); ax.set_ylabel("cost floor")

    ax = fig.add_subplot(1, 4, 3)
    s = d["cost_divergence"]
    ax.plot(s["t"], s["g"], color=INK, lw=2)
    ax.set_xscale("log")
    style(ax); ax.set_xlabel(r"$t$"); ax.set_ylabel(r"$g(t)=-\log t$")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_three_floors"]
    trisurf(ax, s["geo"], s["rep"], s["cost"], "plasma")
    ax.set_xlabel("geo"); ax.set_ylabel("rep"); ax.set_zlabel("cost")
    ax.view_init(elev=20, azim=-50)

    fig.tight_layout()
    fig.savefig("panel_2.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


# =====================================================================
# Panel 3 -- Detectability: distinguishable iff sigma > beta_A
# =====================================================================
def panel3():
    d = D["panel3_detectability"]
    fig = newrow()

    ax = fig.add_subplot(1, 4, 1)
    s = d["sigma_vs_betaA"]
    sig = np.array(s["sigma"]); bA = np.array(s["beta_A"])
    it = np.array(s["interior"])
    disting = it > 1e-12
    ax.scatter(sig[~disting], bA[~disting], s=10, c=INK2, alpha=0.5,
               edgecolors="none")
    ax.scatter(sig[disting], bA[disting], s=10, c=INK, alpha=0.4,
               edgecolors="none")
    m = max(sig.max(), bA.max())
    ax.plot([0, m], [0, m], color="#222222", lw=1.4)  # sigma = beta_A boundary
    style(ax); ax.set_xlabel(r"$\sigma(A)$"); ax.set_ylabel(r"$\beta_A$")

    ax = fig.add_subplot(1, 4, 2)
    s = d["interior_vs_margin"]
    ax.scatter(s["margin_sigma_minus_betaA"], s["interior"], s=10, c=INK3,
               alpha=0.4, edgecolors="none")
    ax.axvline(0, color=INK2, lw=1.4)
    style(ax); ax.set_xlabel(r"$\sigma-\beta_A$"); ax.set_ylabel("interior")

    ax = fig.add_subplot(1, 4, 3)
    t = np.array(d["tau_hist"]["tau"])
    ax.hist(t, bins=45, color=INK, alpha=0.85)
    ax.axvline(1.0, color=INK2, lw=1.6)
    style(ax); ax.set_xlabel(r"$\tau=\beta/\sigma$"); ax.set_ylabel("count")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_sigma_beta_interior"]
    trisurf(ax, s["sigma"], s["beta_A"], s["interior"], "cividis")
    ax.set_xlabel(r"$\sigma$"); ax.set_ylabel(r"$\beta_A$"); ax.set_zlabel("int.")
    ax.view_init(elev=24, azim=-58)

    fig.tight_layout()
    fig.savefig("panel_3.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


# =====================================================================
# Panel 4 -- Sorites: tau descends across a band, no decisive grain
# =====================================================================
def panel4():
    d = D["panel4_sorites"]
    fig = newrow()

    ax = fig.add_subplot(1, 4, 1)
    s = d["tau_descent"]
    ax.plot(s["step"], s["tau"], color=INK, lw=1.8)
    ax.axhline(1.0, color=INK2, lw=1.4)
    style(ax); ax.set_xlabel("grains added"); ax.set_ylabel(r"$\tau$")

    ax = fig.add_subplot(1, 4, 2)
    s = d["sigma_vs_tau"]
    ax.plot(s["sigma"], s["tau"], color=INK3, lw=1.8)
    ax.axhline(1.0, color=INK2, lw=1.4)
    style(ax); ax.set_xlabel(r"$\sigma(A_n)$"); ax.set_ylabel(r"$\tau$")

    ax = fig.add_subplot(1, 4, 3)
    s = d["tau_jump"]
    ax.plot(s["step"], s["jump"], color=INK, lw=1.2)
    style(ax); ax.set_xlabel("grains added"); ax.set_ylabel(r"$|\Delta\tau|$")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    cs = d["surface_orders_tau"]
    cmaps = [INK, INK2, INK3]
    for i, (k, c) in enumerate(zip(sorted(cs), cmaps)):
        sig = np.array(cs[k]["sigma"]); tau = np.array(cs[k]["tau"])
        zs = np.full_like(sig, i, dtype=float)
        ax.plot(sig, zs, tau, color=c, lw=1.6)
    ax.set_xlabel(r"$\sigma$"); ax.set_ylabel("order"); ax.set_zlabel(r"$\tau$")
    ax.set_yticks([0, 1, 2])
    ax.view_init(elev=20, azim=-62)

    fig.tight_layout()
    fig.savefig("panel_4.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


# =====================================================================
# Panel 5 -- Locating vs visiting
# =====================================================================
def panel5():
    d = D["panel5_locating_visiting"]
    fig = newrow()

    ax = fig.add_subplot(1, 4, 1)
    s = d["locate_cost_vs_K"]
    ax.step(s["K"], s["locate_cost"], color=INK, lw=1.8, where="post")
    ax.plot(s["K"], s["visit_cost"], color=INK2, lw=2)  # zero line = free
    ax.set_xscale("log")
    style(ax); ax.set_xlabel(r"$K$"); ax.set_ylabel("cost")

    ax = fig.add_subplot(1, 4, 2)
    s = d["cost_vs_loginvp"]
    ax.scatter(s["log2_inv_p"], s["locate_cost"], s=10, c=INK3,
               edgecolors="none")
    style(ax); ax.set_xlabel(r"$\log_2(1/p)$"); ax.set_ylabel("locate cost")

    ax = fig.add_subplot(1, 4, 3)
    s = d["freq_vs_rarity"]
    ax.plot(s["p"], s["visiting_frequency"], color=INK, lw=2)
    ax.set_xscale("log"); ax.set_yscale("log")
    style(ax); ax.set_xlabel(r"$p(W)$"); ax.set_ylabel(r"$\bar f_W$")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_cost_K_beta"]
    trisurf(ax, np.log2(s["K"]), s["beta"], s["locate_cost"], "magma")
    ax.set_xlabel(r"$\log_2 K$"); ax.set_ylabel(r"$\beta$"); ax.set_zlabel("cost")
    ax.view_init(elev=22, azim=-55)

    fig.tight_layout()
    fig.savefig("panel_5.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


# =====================================================================
# Panel 6 -- Non-return & cessation
# =====================================================================
def panel6():
    d = D["panel6_nonreturn_cessation"]
    fig = newrow()

    ax = fig.add_subplot(1, 4, 1)
    s = d["monotone_record"]
    ax.step(s["step"], s["record"], color=INK, lw=1.8, where="post")
    ax.scatter(s["step"][-1], s["record"][-1], s=40, c=INK2, zorder=5)  # undo
    style(ax); ax.set_xlabel("step"); ax.set_ylabel(r"$M$")

    ax = fig.add_subplot(1, 4, 2)
    s = d["cost_vs_thickness"]
    ax.plot(s["t"], s["cost"], color=INK, lw=2)
    ax.set_xscale("log")
    style(ax); ax.set_xlabel(r"$t$"); ax.set_ylabel(r"$g(t)$")

    ax = fig.add_subplot(1, 4, 3)
    s = d["marginal_return"]
    ax.plot(s["t"], s["marginal_return_per_cost"], color=INK3, lw=2)
    for ts in s["t_star"]:
        ax.axvline(ts, color=INK2, lw=1.0, alpha=0.7)
    ax.set_xscale("log")
    style(ax); ax.set_xlabel(r"$t$"); ax.set_ylabel("return / cost")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_marginal_t_theta"]
    trisurf(ax, np.log10(s["t"]), s["theta"], s["marginal"], "viridis")
    ax.set_xlabel(r"$\log_{10}t$"); ax.set_ylabel(r"$\theta$")
    ax.set_zlabel("ret/cost")
    ax.view_init(elev=24, azim=-58)

    fig.tight_layout()
    fig.savefig("panel_6.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    panel1(); panel2(); panel3(); panel4(); panel5(); panel6()
    print("wrote panel_1.png .. panel_6.png")
