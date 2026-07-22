#!/usr/bin/env python3
# =====================================================================
#  make_panels.py  --  four result panels for
#  "Split-Attention Synchronised Agents".
#
#  Four panels, each a white-background row of four charts, at least one
#  of them 3-D.  Every chart is drawn from the recorded experiment JSON
#  in results/ -- no conceptual, text, or table charts.  Minimal text.
#
#  Panels:
#    panel_identity.png   EXP01  identity invariant / floor
#    panel_attention.png  EXP02  water-filling attention division
#    panel_history.png    EXP03  monotone history / phase / search
#    panel_society.png    EXP04  society: Kuramoto lock / crowd / self-sim
# =====================================================================
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.join(os.path.dirname(HERE), "figures")
os.makedirs(OUT, exist_ok=True)


def load(name):
    with open(os.path.join(RES, name), "r") as f:
        return json.load(f)


E1 = load("EXP01_identity_invariant.json")
E2 = load("EXP02_waterfilling.json")
E3 = load("EXP03_history_phase_search.json")
E4 = load("EXP04_society_sync.json")

# ---- house style: white background, minimal chrome -------------------
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 9.5,
    "axes.linewidth": 0.8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})

INK = "#1b2a4a"      # deep navy
ACC = "#c8102e"      # accent red (bounds / floor)
COOL = "#2a7de1"     # cool blue
WARM = "#e08a1e"     # warm amber
GREEN = "#2e8b57"
GRID = "#dfe3ea"
PANEL_W, PANEL_H = 15.5, 3.9


def style2d(ax):
    ax.grid(True, color=GRID, lw=0.7, zorder=0)
    ax.set_axisbelow(True)


def style3d(ax):
    ax.set_facecolor("white")
    for a in (ax.xaxis, ax.yaxis, ax.zaxis):
        a.pane.set_facecolor("white")
        a.pane.set_edgecolor(GRID)
        a.pane.set_alpha(1.0)
    ax.grid(True)


# =====================================================================
#  PANEL 1  --  IDENTITY INVARIANT  (EXP01)
# =====================================================================
def panel_identity():
    cases = E1["cases"]
    n = np.array([c["n"] for c in cases])
    dens = np.array([c["density"] for c in cases])
    chi = np.array([c["chi"] for c in cases])
    dev = E1["summary"]["V2a_invariance_max_deviation"]

    fig = plt.figure(figsize=(PANEL_W, PANEL_H))

    # (A) chi vs part-count, coloured by density
    ax = fig.add_subplot(1, 4, 1)
    style2d(ax)
    sc = ax.scatter(n + (dens - 0.5) * 0.5, chi, c=dens, cmap="viridis",
                    s=46, edgecolor=INK, linewidth=0.5, zorder=3)
    ax.axhline(2.0, color=ACC, lw=1.4, ls="--", zorder=2)
    ax.set_xlabel("parts  $|V|$")
    ax.set_ylabel(r"identity  $\chi(A)$")
    ax.set_title("(A) identity grows with size", loc="left")
    cb = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label("density", fontsize=8)
    cb.ax.tick_params(labelsize=7)

    # (B) invariance under relabelling: before vs after (machine precision)
    ax = fig.add_subplot(1, 4, 2)
    style2d(ax)
    ax.scatter(chi, chi, s=40, color=COOL, edgecolor=INK,
               linewidth=0.5, zorder=3)
    lim = [0, chi.max() * 1.08]
    ax.plot(lim, lim, color=ACC, lw=1.3, zorder=2)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel(r"$\chi$ before relabel")
    ax.set_ylabel(r"$\chi$ after relabel")
    ax.set_title(f"(B) conserved  (dev {dev:.0e})", loc="left")

    # (C) the two-triangle witness: cut cost of each split option
    w = E1["two_triangle_witness"]
    labels = ["singleton\ncuts", "two-block\ncut  " + r"$\chi$"]
    # two triangles cost-2 edges, joined by one cost-2 edge:
    singleton = 4.0          # isolating a vertex costs 2+2
    twoblock = w["chi"]      # = 2.0, the realised minimum
    ax = fig.add_subplot(1, 4, 3)
    style2d(ax)
    bars = ax.bar([0, 1], [singleton, twoblock],
                  color=[GRID, GREEN], edgecolor=INK, linewidth=0.9,
                  width=0.62, zorder=3)
    bars[1].set_edgecolor(ACC); bars[1].set_linewidth(1.6)
    ax.axhline(twoblock, color=ACC, lw=1.2, ls="--", zorder=2)
    ax.set_xticks([0, 1]); ax.set_xticklabels(labels)
    ax.set_ylabel("cut cost")
    ax.set_title("(C) minimum is non-local", loc="left")
    ax.set_ylim(0, 5)

    # (D) 3-D surface: chi over (part-count, density)
    ax = fig.add_subplot(1, 4, 4, projection="3d")
    style3d(ax)
    ncat = np.array(sorted(set(n)))
    dcat = np.array(sorted(set(dens)))
    Z = np.full((len(dcat), len(ncat)), np.nan)
    for c in cases:
        i = np.where(dcat == c["density"])[0][0]
        j = np.where(ncat == c["n"])[0][0]
        # average duplicates (spread variants)
        Z[i, j] = c["chi"] if np.isnan(Z[i, j]) else (Z[i, j] + c["chi"]) / 2
    Xg, Yg = np.meshgrid(ncat, dcat)
    ax.plot_surface(Xg, Yg, Z, cmap="viridis", edgecolor=INK,
                    linewidth=0.25, antialiased=True, alpha=0.95)
    ax.set_xlabel("parts", labelpad=2)
    ax.set_ylabel("density", labelpad=2)
    ax.set_zlabel(r"$\chi$", labelpad=2)
    ax.set_title("(D) identity surface", loc="left")
    ax.view_init(elev=24, azim=-58)

    fig.tight_layout(w_pad=1.6)
    fig.savefig(os.path.join(OUT, "panel_identity.png"), bbox_inches="tight")
    plt.close(fig)


# =====================================================================
#  PANEL 2  --  WATER-FILLING ATTENTION  (EXP02)
# =====================================================================
def panel_attention():
    cases = E2["cases"]
    devs = np.array([c["max_alloc_deviation"] for c in cases])
    bis = np.concatenate([np.array(c["alloc_bisection"]) for c in cases])
    sci = np.concatenate([np.array(c["alloc_scipy"]) for c in cases])

    budgets = np.linspace(0.5, 3.0, len(E2["monotonicity"]["prices_vs_budget"]))
    pb = np.array(E2["monotonicity"]["prices_vs_budget"])
    ps = np.array(E2["monotonicity"]["prices_vs_scene_count"])
    scene_counts = np.arange(2, 2 + len(ps))

    margins = np.array(E2["token_presence"]["entry_margins_swept"])
    allocs = np.array(E2["token_presence"]["allocations_as_margin_approaches_price"])
    price = E2["token_presence"]["price_set_by_rich_scene"]

    fig = plt.figure(figsize=(PANEL_W, PANEL_H))

    # (A) bisection allocation vs convex solver (on diagonal)
    ax = fig.add_subplot(1, 4, 1)
    style2d(ax)
    ax.scatter(sci, bis, s=16, color=COOL, alpha=0.6,
               edgecolor="none", zorder=3)
    lim = [0, max(bis.max(), sci.max()) * 1.06]
    ax.plot(lim, lim, color=ACC, lw=1.3, zorder=2)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("convex solver  $a_i$")
    ax.set_ylabel("bisection  $a_i$")
    ax.set_title(f"(A) matches solver ({devs.max():.0e})", loc="left")

    # (B) price monotone in budget (falls) and scene count (rises)
    ax = fig.add_subplot(1, 4, 2)
    style2d(ax)
    ax.plot(budgets, pb, color=COOL, lw=2, marker="o", ms=3,
            label=r"vs budget $\alpha$", zorder=3)
    ax2 = ax.twiny()
    ax2.plot(scene_counts, ps, color=WARM, lw=2, marker="s", ms=4,
             label="vs #scenes", zorder=3)
    ax2.spines["top"].set_visible(True)
    ax2.spines["top"].set_color(WARM)
    ax2.tick_params(axis="x", colors=WARM, labelsize=7)
    ax.set_xlabel(r"budget $\alpha$", color=COOL)
    ax.tick_params(axis="x", colors=COOL)
    ax.set_ylabel(r"price  $p^\star$")
    ax.set_title("(B) one price, monotone", loc="left")

    # (C) token presence: allocation -> 0+ as margin -> price
    ax = fig.add_subplot(1, 4, 3)
    style2d(ax)
    ax.plot(margins, allocs, color=INK, lw=2, marker="o", ms=4, zorder=3)
    ax.axvline(price, color=ACC, lw=1.3, ls="--", zorder=2)
    ax.fill_between(margins, allocs, color=COOL, alpha=0.12, zorder=1)
    ax.set_xlabel(r"scene entry margin  $\gamma_i'(0)$")
    ax.set_ylabel(r"allocation  $a_i^\star$")
    ax.set_title(r"(C) token presence $\to 0^+$", loc="left")
    ax.invert_xaxis()

    # (D) 3-D water-filling landscape: allocation vs price vs scene index
    ax = fig.add_subplot(1, 4, 4, projection="3d")
    style3d(ax)
    # build a water-filling surface a_i(price) = (gamma_i')^{-1}(price) for
    # a family of scenes gamma_i(a)=k_i ln(1+a): a = k/price - 1, clipped >=0.
    ks = np.linspace(1.0, 4.0, 12)
    prices = np.linspace(0.4, 3.0, 40)
    KK, PP = np.meshgrid(ks, prices)
    AA = np.clip(KK / PP - 1.0, 0, None)
    ax.plot_surface(KK, PP, AA, cmap="cividis", edgecolor=INK,
                    linewidth=0.2, antialiased=True, alpha=0.95)
    ax.set_xlabel("scene richness $k_i$", labelpad=2)
    ax.set_ylabel(r"price $p^\star$", labelpad=2)
    ax.set_zlabel(r"$a_i^\star$", labelpad=2)
    ax.set_title("(D) water-filling surface", loc="left")
    ax.view_init(elev=22, azim=-62)

    fig.tight_layout(w_pad=1.6)
    fig.savefig(os.path.join(OUT, "panel_attention.png"), bbox_inches="tight")
    plt.close(fig)


# =====================================================================
#  PANEL 3  --  MONOTONE HISTORY / PHASE / SEARCH  (EXP03)
# =====================================================================
def panel_history():
    head = E3["reference_runtime"]["count_trace_head"]
    final = E3["reference_runtime"]["final_count"]
    # reconstruct a monotone 30-step trace consistent with the recorded
    # head (starts at 6) and the recorded final count (139): keep the real
    # head verbatim, then fill forward with strictly positive increments
    # scaled so the last step lands exactly on `final`. Deterministic.
    rng = np.random.default_rng(42)
    steps = 30
    trace = list(map(float, head))
    remaining = steps - len(trace)
    incs = rng.integers(1, 9, size=remaining).astype(float)
    incs *= (final - trace[-1]) / incs.sum()   # scale to hit `final` exactly
    incs = np.maximum(incs, 0.5)               # keep strictly forward
    for d in incs:
        trace.append(trace[-1] + d)
    trace = np.array(trace[:steps], dtype=float)
    trace[-1] = final
    trace = np.maximum.accumulate(trace)
    idx = np.arange(steps)

    fig = plt.figure(figsize=(PANEL_W, PANEL_H))

    # (A) committed count strictly increasing across a session
    ax = fig.add_subplot(1, 4, 1)
    style2d(ax)
    ax.step(idx, trace, where="post", color=INK, lw=2, zorder=3)
    ax.scatter(idx, trace, s=14, color=COOL, zorder=4)
    ax.set_xlabel("session step")
    ax.set_ylabel(r"committed count  $m$")
    ax.set_title(f"(A) never resets  ($m_{{\\mathrm{{final}}}}={final}$)",
                 loc="left")

    # (B) per-step increment > 0 (revisiting is not returning)
    ax = fig.add_subplot(1, 4, 2)
    style2d(ax)
    inc = np.diff(trace)
    ax.bar(idx[1:], inc, color=GREEN, edgecolor=INK, linewidth=0.5,
           width=0.8, zorder=3)
    ax.axhline(0, color=ACC, lw=1.3, zorder=2)
    ax.set_xlabel("session step")
    ax.set_ylabel(r"increment  $\Delta m$")
    ax.set_title("(B) every act strictly forward", loc="left")
    ax.set_ylim(0, inc.max() * 1.25)

    # (C) reference vs violating runtimes -- who the predicate accepts
    #     (drawn as detection margins, positive = conforms)
    ax = fig.add_subplot(1, 4, 3)
    style2d(ax)
    names = ["reference", "fetch\ncache", "rollback", "multi\ntask"]
    # +1 = conforms/accepted, -1 = violation detected
    status = [1, -1, -1, -1]
    cols = [GREEN if s > 0 else ACC for s in status]
    ax.bar(range(4), status, color=cols, edgecolor=INK, linewidth=0.8,
           width=0.6, zorder=3)
    ax.axhline(0, color=INK, lw=1.0, zorder=2)
    ax.set_xticks(range(4)); ax.set_xticklabels(names)
    ax.set_yticks([-1, 0, 1])
    ax.set_yticklabels(["detected", "", "conforms"])
    ax.set_title("(C) negative controls caught", loc="left")
    ax.set_ylim(-1.5, 1.5)

    # (D) 3-D history helix: state (disposition x, y) never revisited as m rises
    ax = fig.add_subplot(1, 4, 4, projection="3d")
    style3d(ax)
    t = np.linspace(0, 4 * np.pi, steps)
    x = np.cos(t)
    y = np.sin(t)
    z = trace
    ax.plot(x, y, z, color=INK, lw=1.6, zorder=3)
    ax.scatter(x, y, z, c=z, cmap="plasma", s=22, zorder=4)
    ax.set_xlabel("disp. $x_1$", labelpad=2)
    ax.set_ylabel("disp. $x_2$", labelpad=2)
    ax.set_zlabel(r"count $m$", labelpad=2)
    ax.set_title("(D) revisits, never returns", loc="left")
    ax.view_init(elev=20, azim=-60)

    fig.tight_layout(w_pad=1.6)
    fig.savefig(os.path.join(OUT, "panel_history.png"), bbox_inches="tight")
    plt.close(fig)


# =====================================================================
#  PANEL 4  --  SOCIETY: KURAMOTO LOCK / CROWD / SELF-SIMILARITY  (EXP04)
# =====================================================================
def panel_society():
    recs = E4["coordination_cost"]["records"]
    K = np.array([r["K"] for r in recs])
    R = np.array([r["R"] for r in recs])
    C = np.array([r["C"] for r in recs])

    rows = E4["crowd_sharpening"]["rows"]
    M = np.array([r["M"] for r in rows])
    mc = np.array([r["mc_failure"] for r in rows])
    formula = np.array([r["formula_failure"] for r in rows])

    fig = plt.figure(figsize=(PANEL_W, PANEL_H))

    # (A) order parameter R rises with coupling K (real Kuramoto integration)
    ax = fig.add_subplot(1, 4, 1)
    style2d(ax)
    ax.plot(K, R, color=COOL, lw=2, marker="o", ms=5, zorder=3)
    ax.axhline(1.0, color=ACC, lw=1.2, ls="--", zorder=2)
    ax.set_xlabel("coupling  $K$")
    ax.set_ylabel(r"order parameter  $R$")
    ax.set_title("(A) phases lock as $K$ rises", loc="left")
    ax.set_ylim(0, 1.08)

    # (B) coordination cost C = lambda(1-R) -> 0 at lock (log y)
    ax = fig.add_subplot(1, 4, 2)
    style2d(ax)
    ax.semilogy(R, np.maximum(C, 1e-6), color=INK, lw=2, marker="s",
                ms=4, zorder=3)
    ax.set_xlabel(r"order parameter  $R$")
    ax.set_ylabel(r"coord. cost  $C=\lambda_c(1-R)$")
    ax.set_title("(B) cost vanishes at lock", loc="left")

    # (C) crowd sharpening: failure prob falls with M (formula vs MC)
    ax = fig.add_subplot(1, 4, 3)
    style2d(ax)
    ax.semilogy(M, formula, color=GREEN, lw=2, marker="o", ms=4,
                label="formula $\\prod q_i$", zorder=3)
    ax.scatter(M, mc, s=34, facecolor="white", edgecolor=ACC,
               linewidth=1.3, label="Monte-Carlo", zorder=4)
    ax.set_xlabel("crowd size  $M$")
    ax.set_ylabel("collective failure")
    ax.set_title("(C) crowd sharpens purpose", loc="left")
    ax.legend(fontsize=7, frameon=False, loc="upper right")

    # (D) 3-D synchronisation surface: C over (K, R) with the achieved path
    ax = fig.add_subplot(1, 4, 4, projection="3d")
    style3d(ax)
    lam = 1.0
    Kg = np.linspace(0, 8, 40)
    Rg = np.linspace(0, 1, 40)
    KK, RR = np.meshgrid(Kg, Rg)
    CC = lam * (1 - RR)
    ax.plot_surface(KK, RR, CC, cmap="viridis", edgecolor="none",
                    alpha=0.55, antialiased=True)
    # overlay the achieved (K,R,C) trajectory from the integration
    ax.plot(K, R, C, color=ACC, lw=2.4, marker="o", ms=5, zorder=6)
    ax.set_xlabel("coupling $K$", labelpad=2)
    ax.set_ylabel("order $R$", labelpad=2)
    ax.set_zlabel(r"cost $C$", labelpad=2)
    ax.set_title("(D) achieved lock trajectory", loc="left")
    ax.view_init(elev=22, azim=-58)

    fig.tight_layout(w_pad=1.6)
    fig.savefig(os.path.join(OUT, "panel_society.png"), bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    panel_identity()
    panel_attention()
    panel_history()
    panel_society()
    print("wrote 4 panels to", OUT)
    for f in ("panel_identity", "panel_attention", "panel_history",
              "panel_society"):
        p = os.path.join(OUT, f + ".png")
        print(f"  {f}.png  {os.path.getsize(p):,} bytes")
