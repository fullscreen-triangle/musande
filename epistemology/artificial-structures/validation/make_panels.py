"""
make_panels.py -- render the 10 validation panels (one per validator).

Each panel: one row of 4 charts, at least one 3D, white background, minimal
text (short axis labels only; no titles, legends-as-prose, tables, or
conceptual diagrams). Every chart is driven by figure_data.json.

Outputs panel_1.png ... panel_10.png (300 dpi).
"""

from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "font.size": 9,
    "axes.linewidth": 0.8, "axes.edgecolor": "#444444",
    "xtick.color": "#444444", "ytick.color": "#444444",
    "axes.labelcolor": "#222222",
})

INK = "#1f3b73"; INK2 = "#c0392b"; INK3 = "#2e8b57"; INK4 = "#8e44ad"
GRID = "#dddddd"

with open("figure_data.json", encoding="utf-8") as f:
    D = json.load(f)


def style(ax):
    ax.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def trisurf(ax, x, y, z, cmap="viridis"):
    x = np.asarray(x, float); y = np.asarray(y, float); z = np.asarray(z, float)
    try:
        ax.plot_trisurf(x, y, z, cmap=cmap, linewidth=0.1, antialiased=True,
                        edgecolor="none", alpha=0.95)
    except Exception:
        ax.scatter(x, y, z, c=z, cmap=cmap, s=10)
    for pane in (ax.xaxis, ax.yaxis, ax.zaxis):
        pane.pane.set_facecolor("white"); pane.pane.set_edgecolor("#cccccc")
    ax.grid(True)


def row():
    return plt.figure(figsize=(18, 4.5))


def save(fig, n):
    fig.tight_layout()
    fig.savefig(f"panel_{n}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


# =====================================================================
def panel1():
    d = D["panel1_ground_floor"]; fig = row()
    ax = fig.add_subplot(1, 4, 1)
    s = d["scatter_bcost_vs_floor"]
    fl = np.array(s["floor"]); bc = np.array(s["boundary_cost"])
    ax.scatter(fl, bc, s=7, c=INK, alpha=0.3, edgecolors="none")
    lo, hi = fl.min(), fl.max(); ax.plot([lo, hi], [lo, hi], color=INK2, lw=1.6)
    style(ax); ax.set_xlabel(r"floor $\beta$"); ax.set_ylabel("residual of a thing")

    ax = fig.add_subplot(1, 4, 2)
    r = np.array(d["hist_ratio"]["ratio"])
    ax.hist(r, bins=40, color=INK, alpha=0.85); ax.axvline(1.0, color=INK2, lw=1.6)
    style(ax); ax.set_xlabel(r"residual $/\,\beta$"); ax.set_ylabel("count")

    ax = fig.add_subplot(1, 4, 3)
    s = d["scatter_minb_vs_floor"]
    ax.scatter(s["floor"], s["min_boundary"], s=12, c=INK3, alpha=0.5,
               edgecolors="none")
    lo, hi = min(s["floor"]), max(s["floor"]); ax.plot([lo, hi], [lo, hi],
                                                        color=INK2, lw=1.4)
    style(ax); ax.set_xlabel(r"floor $\beta$"); ax.set_ylabel("min residual / graph")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_nv_floor_minb"]
    trisurf(ax, s["n_vertices"], s["floor"], s["min_boundary"], "viridis")
    ax.set_xlabel("verts"); ax.set_ylabel(r"$\beta$"); ax.set_zlabel("min res")
    ax.view_init(elev=22, azim=-60)
    save(fig, 1)


def panel2():
    d = D["panel2_T0_floor"]; fig = row()
    ax = fig.add_subplot(1, 4, 1)
    s = d["scatter_cut_vs_floor"]
    fl = np.array(s["floor"]); cw = np.array(s["cut_weight"])
    ax.scatter(fl, cw, s=6, c=INK, alpha=0.25, edgecolors="none")
    lo, hi = fl.min(), fl.max(); ax.plot([lo, hi], [lo, hi], color=INK2, lw=1.6)
    style(ax); ax.set_xlabel(r"floor $\beta$"); ax.set_ylabel("cut weight")

    ax = fig.add_subplot(1, 4, 2)
    r = np.array(d["hist_cut_over_floor"]["ratio"])
    ax.hist(r, bins=50, color=INK, alpha=0.85); ax.axvline(1.0, color=INK2, lw=1.6)
    style(ax); ax.set_xlabel(r"cut $/\,\beta$"); ax.set_ylabel("count")

    ax = fig.add_subplot(1, 4, 3)
    s = d["scatter_mincut_vs_floor"]
    ax.scatter(s["floor"], s["min_cut"], s=12, c=INK3, alpha=0.5, edgecolors="none")
    lo, hi = min(s["floor"]), max(s["floor"]); ax.plot([lo, hi], [lo, hi],
                                                        color=INK2, lw=1.4)
    style(ax); ax.set_xlabel(r"floor $\beta$"); ax.set_ylabel("min cut / graph")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_edges_floor_mincut"]
    trisurf(ax, s["n_edges"], s["floor"], s["min_cut"], "plasma")
    ax.set_xlabel("edges"); ax.set_ylabel(r"$\beta$"); ax.set_zlabel("min cut")
    ax.view_init(elev=20, azim=-55)
    save(fig, 2)


def panel3():
    d = D["panel3_T1_negation"]; fig = row()
    ax = fig.add_subplot(1, 4, 1)
    s = d["scatter_sizes"]
    ax.scatter(s["size_U"], s["size_complement"], s=8, c=INK, alpha=0.3,
               edgecolors="none")
    style(ax); ax.set_xlabel(r"$|U|$"); ax.set_ylabel(r"$|\,$complement$\,|$")

    ax = fig.add_subplot(1, 4, 2)
    e = np.array(d["hist_involution_err"]["err"])
    ax.hist(e, bins=[-0.5, 0.5, 1.5], color=INK3, alpha=0.85)
    ax.axvline(0.0, color=INK2, lw=1.6)
    style(ax); ax.set_xlabel("involution error"); ax.set_ylabel("count")
    ax.set_xticks([0, 1])

    ax = fig.add_subplot(1, 4, 3)
    s = d["partition_sum"]
    ax.scatter(s["total"], s["u_plus_comp"], s=10, c=INK, alpha=0.4,
               edgecolors="none")
    lo, hi = min(s["total"]), max(s["total"]); ax.plot([lo, hi], [lo, hi],
                                                       color=INK2, lw=1.4)
    style(ax); ax.set_xlabel(r"$|V|$"); ax.set_ylabel(r"$|U|+|$comp$|$")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_U_comp_total"]
    trisurf(ax, s["size_U"], s["size_complement"], s["total"], "cividis")
    ax.set_xlabel(r"$|U|$"); ax.set_ylabel("comp"); ax.set_zlabel(r"$|V|$")
    ax.view_init(elev=24, azim=-58)
    save(fig, 3)


def panel4():
    d = D["panel4_T2T3_residual"]; fig = row()
    ax = fig.add_subplot(1, 4, 1)
    s = d["scatter_res_vs_floor"]
    ax.scatter(s["floor"], s["residual"], s=10, c=INK, alpha=0.4, edgecolors="none")
    lo, hi = min(s["floor"]), max(s["floor"]); ax.plot([lo, hi], [lo, hi],
                                                       color=INK2, lw=1.4)
    style(ax); ax.set_xlabel(r"floor $\beta$"); ax.set_ylabel("residual")

    ax = fig.add_subplot(1, 4, 2)
    s = d["invariance"]
    rb = np.array(s["res_before"]); ra = np.array(s["res_after"])
    ax.scatter(rb, ra, s=12, c=INK3, alpha=0.5, edgecolors="none")
    m = max(rb.max(), ra.max()); ax.plot([0, m], [0, m], color=INK2, lw=1.4)
    style(ax); ax.set_xlabel("residual before"); ax.set_ylabel("after reshuffle")

    ax = fig.add_subplot(1, 4, 3)
    ss = np.array(d["hist_mincut_side_size"]["side_size"])
    ax.hist(ss, bins=range(0, int(ss.max()) + 2), color=INK, alpha=0.85)
    ax.axvline(1.5, color=INK2, lw=1.6)
    style(ax); ax.set_xlabel("smaller min-cut side size"); ax.set_ylabel("count")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_res_floor_side"]
    trisurf(ax, s["floor"], s["residual"], s["side_size"], "viridis")
    ax.set_xlabel(r"$\beta$"); ax.set_ylabel("residual"); ax.set_zlabel("side")
    ax.view_init(elev=22, azim=-60)
    save(fig, 4)


def panel5():
    d = D["panel5_T4_private"]; fig = row()
    ax = fig.add_subplot(1, 4, 1)
    s = d["scatter_part_vs_floor"]
    fl = np.array(s["floor"]); pb = np.array(s["part_boundary"])
    ax.scatter(fl, pb, s=8, c=INK, alpha=0.3, edgecolors="none")
    lo, hi = fl.min(), fl.max(); ax.plot([lo, hi], [lo, hi], color=INK2, lw=1.6)
    style(ax); ax.set_xlabel(r"floor $\beta$"); ax.set_ylabel("part invariant")

    ax = fig.add_subplot(1, 4, 2)
    s = d["scatter_b_vs_degree"]
    ax.scatter(s["degree"], s["part_boundary"], s=8, c=INK3, alpha=0.35,
               edgecolors="none")
    style(ax); ax.set_xlabel("part degree"); ax.set_ylabel("part invariant")

    ax = fig.add_subplot(1, 4, 3)
    r = np.array(d["hist_part_over_floor"]["ratio"])
    ax.hist(r, bins=40, color=INK, alpha=0.85); ax.axvline(1.0, color=INK2, lw=1.6)
    style(ax); ax.set_xlabel(r"invariant $/\,\beta$"); ax.set_ylabel("count")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_nv_floor_minpart"]
    trisurf(ax, s["n_vertices"], s["floor"], s["min_part_boundary"], "magma")
    ax.set_xlabel("verts"); ax.set_ylabel(r"$\beta$"); ax.set_zlabel("min inv")
    ax.view_init(elev=22, azim=-58)
    save(fig, 5)


def panel6():
    d = D["panel6_T5_gate"]; fig = row()
    ax = fig.add_subplot(1, 4, 1)
    deg = np.array(d["hist_degree"]["degree"])
    ax.hist(deg, bins=range(0, int(deg.max()) + 2), color=INK, alpha=0.85)
    ax.axvline(1.5, color=INK2, lw=1.4)
    style(ax); ax.set_xlabel("vertex degree"); ax.set_ylabel("count")

    ax = fig.add_subplot(1, 4, 2)
    s = d["scatter_branchfrac_vs_nv"]
    ax.scatter(s["n_vertices"], s["branching_fraction"], s=14, c=INK3, alpha=0.5,
               edgecolors="none")
    style(ax); ax.set_xlabel("verts"); ax.set_ylabel("branching fraction")
    ax.set_ylim(0, 1.05)

    ax = fig.add_subplot(1, 4, 3)
    bc = np.array(d["hist_branch_count"]["branching_vertices"])
    ax.hist(bc, bins=range(0, int(bc.max()) + 2), color=INK, alpha=0.85)
    style(ax); ax.set_xlabel("branching vertices / graph"); ax.set_ylabel("count")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_nv_ne_branch"]
    trisurf(ax, s["n_vertices"], s["n_edges"], s["branching_vertices"], "viridis")
    ax.set_xlabel("verts"); ax.set_ylabel("edges"); ax.set_zlabel("branch")
    ax.view_init(elev=22, azim=-62)
    save(fig, 6)


def panel7():
    d = D["panel7_T6_nonreturn"]; fig = row()
    ax = fig.add_subplot(1, 4, 1)
    s = d["count_vs_step"]
    ax.plot(s["step"], s["count"], color=INK, lw=2)
    style(ax); ax.set_xlabel("step"); ax.set_ylabel("committed count")

    ax = fig.add_subplot(1, 4, 2)
    s = d["revisit_gap"]
    if s["step"]:
        ax.scatter(s["step"], s["count_gap"], s=20, c=INK2, edgecolors="none")
    ax.axhline(0.0, color="#222222", lw=1.0)
    style(ax); ax.set_xlabel("revisit step"); ax.set_ylabel("count gap (>0)")

    ax = fig.add_subplot(1, 4, 3)
    s = d["temporal_complement"]
    ax.step(s["stage"], s["complement_size"], color=INK3, lw=2, where="post")
    style(ax); ax.set_xlabel("stage"); ax.set_ylabel("complement size")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    cs = d["surface_walks"]
    cols = [INK, INK2, INK3]
    for i, (k, c) in enumerate(zip(sorted(cs), cols)):
        st = np.array(cs[k]["step"]); ct = np.array(cs[k]["count"])
        ax.plot(st, np.full_like(st, i, dtype=float), ct, color=c, lw=1.6)
    ax.set_xlabel("step"); ax.set_ylabel("walk"); ax.set_zlabel("count")
    ax.set_yticks([0, 1, 2]); ax.view_init(elev=20, azim=-60)
    save(fig, 7)


def panel8():
    d = D["panel8_T7_quotient"]; fig = row()
    ax = fig.add_subplot(1, 4, 1)
    s = d["scatter_qweight_vs_floor"]
    fl = np.array(s["floor"]); qw = np.array(s["quotient_weight"])
    ax.scatter(fl, qw, s=9, c=INK, alpha=0.35, edgecolors="none")
    lo, hi = fl.min(), fl.max(); ax.plot([lo, hi], [lo, hi], color=INK2, lw=1.6)
    style(ax); ax.set_xlabel(r"floor $\beta$"); ax.set_ylabel("quotient edge weight")

    ax = fig.add_subplot(1, 4, 2)
    r = np.array(d["hist_q_over_floor"]["ratio"])
    ax.hist(r, bins=40, color=INK, alpha=0.85); ax.axvline(1.0, color=INK2, lw=1.6)
    style(ax); ax.set_xlabel(r"quotient edge $/\,\beta$"); ax.set_ylabel("count")

    ax = fig.add_subplot(1, 4, 3)
    s = d["scatter_minq_vs_floor"]
    ax.scatter(s["floor"], s["min_quotient_edge"], s=12, c=INK3, alpha=0.5,
               edgecolors="none")
    lo, hi = min(s["floor"]), max(s["floor"]); ax.plot([lo, hi], [lo, hi],
                                                       color=INK2, lw=1.4)
    style(ax); ax.set_xlabel(r"floor $\beta$"); ax.set_ylabel("min quotient edge")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_ncl_nq_minq"]
    trisurf(ax, s["n_classes"], s["n_quotient_edges"], s["min_quotient_edge"],
            "plasma")
    ax.set_xlabel("classes"); ax.set_ylabel("q-edges"); ax.set_zlabel("min q")
    ax.view_init(elev=22, azim=-58)
    save(fig, 8)


def panel9():
    d = D["panel9_T8_authored"]; fig = row()
    ax = fig.add_subplot(1, 4, 1)
    s = d["scatter_orig_vs_auth_floor"]
    of = np.array(s["orig_floor"]); af = np.array(s["authored_floor"])
    ax.scatter(of, af, s=12, c=INK, alpha=0.4, edgecolors="none")
    m = max(of.max(), af.max()); ax.plot([0, m], [0, m], color=INK2, lw=1.4)
    style(ax); ax.set_xlabel("original min edge"); ax.set_ylabel("authored min edge")

    ax = fig.add_subplot(1, 4, 2)
    s = d["forward_closure"]
    ax.plot(s["step"], s["distinct_states"], color=INK, lw=2)
    lo, hi = min(s["step"]), max(s["step"]); ax.plot([lo, hi], [lo + 1, hi + 1],
                                                     color=INK2, lw=1.0, ls="--")
    style(ax); ax.set_xlabel("step"); ax.set_ylabel("distinct states")

    ax = fig.add_subplot(1, 4, 3)
    af = np.array(d["hist_auth_floor"]["authored_floor"])
    ax.hist(af, bins=30, color=INK3, alpha=0.85)
    style(ax); ax.set_xlabel("authored min edge weight"); ax.set_ylabel("count")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_nv_floor_authmin"]
    trisurf(ax, s["n_vertices"], s["floor"], s["authored_min_edge"], "viridis")
    ax.set_xlabel("verts"); ax.set_ylabel(r"$\beta$"); ax.set_zlabel("auth min")
    ax.view_init(elev=22, azim=-60)
    save(fig, 9)


def panel10():
    d = D["panel10_measurement"]; fig = row()
    ax = fig.add_subplot(1, 4, 1)
    s = d["residual_conserved"]
    ax.plot(s["measurement"], s["residual"], color=INK, lw=2, marker="o", ms=3)
    ax.axhline(s["residual"][0], color=INK2, lw=1.0, ls="--")
    style(ax); ax.set_xlabel("measurement"); ax.set_ylabel("residual (conserved)")

    ax = fig.add_subplot(1, 4, 2)
    s = d["self_defeat_separation"]
    ax.plot(s["measurement"], s["separation"], color=INK3, lw=2, marker="o", ms=3)
    ax.axhline(s["floor"], color=INK2, lw=1.4)
    ax.set_ylim(0, max(s["separation"]) * 1.1)
    style(ax); ax.set_xlabel("measurement"); ax.set_ylabel("separation (never 0)")

    ax = fig.add_subplot(1, 4, 3)
    s = d["resolution"]
    ax.plot(s["edges_added"], s["separation"], color=INK, lw=2, marker="s", ms=3)
    ax.axhline(s["floor"], color=INK2, lw=1.4)
    style(ax); ax.set_xlabel("boundary edges added"); ax.set_ylabel("separation")

    ax = fig.add_subplot(1, 4, 4, projection="3d")
    s = d["surface_residual_seed"]
    trisurf(ax, s["measurement"], s["seed"], s["residual"], "viridis")
    ax.set_xlabel("measmt"); ax.set_ylabel("seed"); ax.set_zlabel("residual")
    ax.view_init(elev=20, azim=-62)
    save(fig, 10)


if __name__ == "__main__":
    panel1(); panel2(); panel3(); panel4(); panel5()
    panel6(); panel7(); panel8(); panel9(); panel10()
    print("wrote panel_1.png .. panel_10.png")
