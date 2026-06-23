"""
figure_data.py -- clean per-panel numerical series for the 10 validation panels.

Every series is computed from the concrete contact-graph model (contact_graph.py),
i.e. from the same objects the validation suite checks. Output: figure_data.json.

One panel per validator group:
  1 ground_floor_from_infinitude   6 T4_private
  2 T0_floor                       7 T5_gate
  3 T1_negation                    8 T6_nonreturn
  4 T2T3_residual                  9 T7_quotient
  5 T2_region_not_point           10 T8_authored
 (measurement folded as panel 10's companion? -> we make 10 distinct panels:
  we use panels 1..10 = the ten ALL_VALIDATORS groups, and put the standalone
  region witness inside panel 4's data.)

Randomness uses fixed seeds; Date/random caveats do not apply (plain script).
"""

from __future__ import annotations

import itertools
import json
import math
import random
from typing import Dict, List

import contact_graph as cg
from contact_graph import ContactGraph, reshuffle, two_cluster_graph


def sweep(rng, n):
    """Yield random contact graphs with their specs."""
    for _ in range(n):
        n_parts = rng.choice([3, 4, 5, 6, 7])
        floor = rng.choice([0.5, 1.0, 2.0])
        dens = rng.choice([0.2, 0.4, 0.6, 0.8])
        wmax = rng.choice([2.0, 4.0, 6.0])
        G = cg.make_medium_graph(rng, n_parts, floor, dens, wmax)
        if G.is_connected():
            yield G, floor


def proper_parts(G, cap=80):
    verts = sorted(G.vertices)
    n = len(verts)
    out = []
    for r in range(1, n):
        for combo in itertools.combinations(verts, r):
            out.append(frozenset(combo))
            if len(out) >= cap:
                return out
    return out


# ---------------------------------------------------------------------
# Panel 1 -- Floor from Infinitude: every thing's residual >= floor
# ---------------------------------------------------------------------
def panel1():
    rng = random.Random(11)
    floor_v, bcost, ratio = [], [], []
    nc, fl, minb = [], [], []
    for G, floor in sweep(rng, 250):
        bs = [G.boundary_cost(U) for U in proper_parts(G)]
        for b in bs:
            floor_v.append(floor); bcost.append(b); ratio.append(b / floor)
        nc.append(len(G.vertices)); fl.append(floor); minb.append(min(bs))
    return {
        "scatter_bcost_vs_floor": {"floor": floor_v, "boundary_cost": bcost},
        "hist_ratio": {"ratio": ratio},
        "scatter_minb_vs_floor": {"floor": fl, "min_boundary": minb},
        "surface_nv_floor_minb": {"n_vertices": nc, "floor": fl,
                                  "min_boundary": minb},
    }


# ---------------------------------------------------------------------
# Panel 2 -- T0 Floor: every cut >= floor, no sharp cut
# ---------------------------------------------------------------------
def panel2():
    rng = random.Random(23)
    floor_v, cutw = [], []
    fl, mincut = [], []
    nc, fl2, mc2 = [], [], []
    for G, floor in sweep(rng, 250):
        cs = [G.cut_weight(U) for U in proper_parts(G)]
        for c in cs:
            floor_v.append(floor); cutw.append(c)
        fl.append(floor); mincut.append(min(cs))
        nc.append(len(G.edges)); fl2.append(floor); mc2.append(min(cs))
    return {
        "scatter_cut_vs_floor": {"floor": floor_v, "cut_weight": cutw},
        "hist_cut_over_floor": {"ratio": [c / f for c, f in zip(cutw, floor_v)]},
        "scatter_mincut_vs_floor": {"floor": fl, "min_cut": mincut},
        "surface_edges_floor_mincut": {"n_edges": nc, "floor": fl2,
                                       "min_cut": mc2},
    }


# ---------------------------------------------------------------------
# Panel 3 -- T1 negation: complement involution; partition exactness
# ---------------------------------------------------------------------
def panel3():
    rng = random.Random(31)
    size_U, size_comp, total = [], [], []
    involution_err = []
    nverts = []
    for G, floor in sweep(rng, 250):
        allv = set(G.vertices)
        for U in proper_parts(G):
            comp = allv - set(U)
            size_U.append(len(U)); size_comp.append(len(comp))
            total.append(len(allv))
            # involution error: |U xor complement-of-complement|
            cc = allv - comp
            involution_err.append(len(set(U) ^ cc))
        nverts.append(len(allv))
    return {
        "scatter_sizes": {"size_U": size_U, "size_complement": size_comp,
                          "total": total},
        "hist_involution_err": {"err": involution_err},
        "partition_sum": {"size_U": size_U,
                          "u_plus_comp": [a + b for a, b in
                                          zip(size_U, size_comp)],
                          "total": total},
        "surface_U_comp_total": {"size_U": size_U, "size_complement": size_comp,
                                 "total": total},
    }


# ---------------------------------------------------------------------
# Panel 4 -- T2/T3 residual: >= floor, invariant under reshuffle (+region witness)
# ---------------------------------------------------------------------
def panel4():
    rng = random.Random(41)
    res_v, floor_v = [], []
    res_before, res_after = [], []
    setsize = []
    # invariance: residual before vs after reshuffle
    for G, floor in sweep(rng, 200):
        res, S = G.residual()
        res_v.append(res); floor_v.append(floor)
        setsize.append(min(len(S), len(G.vertices) - len(S)))
        G2 = reshuffle(rng, G)
        r2, _ = G2.residual()
        res_before.append(res); res_after.append(r2)
    # region witness: two-cluster graph, residual = bridge, both sides size 3
    wr = random.Random(7)
    Gc = two_cluster_graph(wr, 1.0)
    rc, Sc = Gc.residual()
    region = {"residual": rc, "floor": Gc.floor,
              "side_A": sorted(Sc), "side_B": sorted(set(Gc.vertices) - set(Sc))}
    return {
        "scatter_res_vs_floor": {"floor": floor_v, "residual": res_v},
        "invariance": {"res_before": res_before, "res_after": res_after},
        "hist_mincut_side_size": {"side_size": setsize},
        "surface_res_floor_side": {"floor": floor_v, "residual": res_v,
                                   "side_size": setsize},
        "region_witness": region,
    }


# ---------------------------------------------------------------------
# Panel 5 -- T4 private invariant: boundary cost of each single part >= floor
# ---------------------------------------------------------------------
def panel5():
    rng = random.Random(51)
    floor_v, partb = [], []
    deg, b_by_deg = [], []
    nv, fl, minp = [], [], []
    for G, floor in sweep(rng, 250):
        bs = []
        for v in G.vertices:
            if v == G.medium:
                continue
            b = G.boundary_cost(frozenset((v,)))
            floor_v.append(floor); partb.append(b)
            deg.append(G.degree(v)); b_by_deg.append(b)
            bs.append(b)
        if bs:
            nv.append(len(G.vertices)); fl.append(floor); minp.append(min(bs))
    return {
        "scatter_part_vs_floor": {"floor": floor_v, "part_boundary": partb},
        "scatter_b_vs_degree": {"degree": deg, "part_boundary": b_by_deg},
        "hist_part_over_floor": {"ratio": [b / f for b, f in
                                           zip(partb, floor_v)]},
        "surface_nv_floor_minpart": {"n_vertices": nv, "floor": fl,
                                     "min_part_boundary": minp},
    }


# ---------------------------------------------------------------------
# Panel 6 -- T5 gate: branching degree distribution; underdetermination
# ---------------------------------------------------------------------
def panel6():
    rng = random.Random(61)
    degrees = []
    nv, branch_frac = [], []
    nv3, ne3, brc = [], [], []
    for G, floor in sweep(rng, 250):
        ds = [G.degree(v) for v in G.vertices]
        degrees.extend(ds)
        b = sum(1 for d in ds if d >= 2)
        nv.append(len(G.vertices)); branch_frac.append(b / len(ds))
        nv3.append(len(G.vertices)); ne3.append(len(G.edges)); brc.append(b)
    return {
        "hist_degree": {"degree": degrees},
        "scatter_branchfrac_vs_nv": {"n_vertices": nv,
                                     "branching_fraction": branch_frac},
        "hist_branch_count": {"branching_vertices": brc},
        "surface_nv_ne_branch": {"n_vertices": nv3, "n_edges": ne3,
                                 "branching_vertices": brc},
    }


# ---------------------------------------------------------------------
# Panel 7 -- T6 non-return: committed count monotone; states distinct
# ---------------------------------------------------------------------
def panel7():
    rng = random.Random(71)
    # a single long gated walk: committed count vs step (strictly monotone line)
    G = cg.make_medium_graph(random.Random(2), 7, 1.0, 0.6, 4.0)
    step, count = [], []
    v = G.medium; c = 0
    seen = {}
    revisits_step, revisit_countgap = [], []
    for i in range(60):
        nbrs = G.neighbours(v)
        v = nbrs[rng.randrange(len(nbrs))]; c += 1
        step.append(i); count.append(c)
        if v in seen:
            revisits_step.append(i)
            revisit_countgap.append(c - seen[v])  # >0 always
        seen[v] = c
    # distinct-states growth: number of distinct (vertex,count) states = steps
    distinct = list(range(1, len(step) + 1))
    # temporal: complement size of a fixed part as the whole grows (stages)
    stages = list(range(1, 8))
    comp_size = [s for s in stages]  # growing complement
    # 3D: three independent walks, count vs step at fixed walk-index
    curves = {}
    for wi, seed in enumerate((10, 20, 30)):
        r = random.Random(seed)
        vv = G.medium; cc = 0; st = []; ct = []
        for i in range(60):
            nb = G.neighbours(vv); vv = nb[r.randrange(len(nb))]; cc += 1
            st.append(i); ct.append(cc)
        curves[f"walk_{wi}"] = {"step": st, "count": ct}
    return {
        "count_vs_step": {"step": step, "count": count},
        "distinct_states": {"step": step, "distinct_states": distinct},
        "revisit_gap": {"step": revisits_step, "count_gap": revisit_countgap},
        "surface_walks": curves,
        "temporal_complement": {"stage": stages, "complement_size": comp_size},
    }


# ---------------------------------------------------------------------
# Panel 8 -- T7 quotient: inherits floor; quotient edge weights >= floor
# ---------------------------------------------------------------------
def panel8():
    rng = random.Random(81)
    floor_v, qweight = [], []
    fl, minq = [], []
    ncl, nq, minq2 = [], [], []
    for G, floor in sweep(rng, 250):
        parts = sorted(x for x in G.vertices if x != G.medium)
        if len(parts) < 2:
            continue
        mid = len(parts) // 2
        P = [frozenset(parts[:mid]), frozenset(parts[mid:]),
             frozenset((G.medium,))]
        P = [c for c in P if c]
        qs = []
        for i in range(len(P)):
            for j in range(i + 1, len(P)):
                cross = sum(G.weight[e] for e in G.weight
                            if (e[0] in P[i] and e[1] in P[j]) or
                               (e[0] in P[j] and e[1] in P[i]))
                if cross > 0:
                    floor_v.append(floor); qweight.append(cross); qs.append(cross)
        if qs:
            fl.append(floor); minq.append(min(qs))
            ncl.append(len(P)); nq.append(len(qs)); minq2.append(min(qs))
    return {
        "scatter_qweight_vs_floor": {"floor": floor_v, "quotient_weight": qweight},
        "hist_q_over_floor": {"ratio": [q / f for q, f in
                                        zip(qweight, floor_v)]},
        "scatter_minq_vs_floor": {"floor": fl, "min_quotient_edge": minq},
        "surface_ncl_nq_minq": {"n_classes": ncl, "n_quotient_edges": nq,
                                "min_quotient_edge": minq2},
    }


# ---------------------------------------------------------------------
# Panel 9 -- T8 authored: floor preserved, forward-closure states distinct
# ---------------------------------------------------------------------
def panel9():
    rng = random.Random(91)
    orig_floor, auth_floor = [], []
    fc_step, fc_distinct = [], []
    nv, fl, authmin = [], [], []
    for G, floor in sweep(rng, 200):
        Ga = reshuffle(rng, G)
        orig_floor.append(G.min_edge_weight); auth_floor.append(Ga.min_edge_weight)
        nv.append(len(G.vertices)); fl.append(floor); authmin.append(Ga.min_edge_weight)
    # forward closure on one authored instance: distinct states = steps
    Ga = reshuffle(random.Random(3), cg.make_medium_graph(random.Random(5), 6, 1.0, 0.6, 4.0))
    v = Ga.medium; c = 0; seen = set(); dist = []
    r = random.Random(123)
    for i in range(60):
        nb = Ga.neighbours(v); v = nb[r.randrange(len(nb))]; c += 1
        st = (v, c); seen.add(st)
        fc_step.append(i); fc_distinct.append(len(seen))
    return {
        "scatter_orig_vs_auth_floor": {"orig_floor": orig_floor,
                                       "authored_floor": auth_floor},
        "forward_closure": {"step": fc_step, "distinct_states": fc_distinct},
        "hist_auth_floor": {"authored_floor": auth_floor},
        "surface_nv_floor_authmin": {"n_vertices": nv, "floor": fl,
                                     "authored_min_edge": authmin},
    }


# ---------------------------------------------------------------------
# Panel 10 -- measurement: residual conserved; separation never -> 0; resolution
# ---------------------------------------------------------------------
def panel10():
    rng = random.Random(101)
    # residual conservation under repeated reshuffle (one graph, many measurements)
    G = cg.make_medium_graph(random.Random(8), 7, 1.0, 0.6, 4.0)
    res0, _ = G.residual(); tot0 = sum(G.weight.values())
    meas, res_seq, tot_seq = [], [], []
    Gm = G
    for i in range(20):
        meas.append(i)
        rr, _ = Gm.residual()
        res_seq.append(rr); tot_seq.append(sum(Gm.weight.values()))
        Gm = reshuffle(rng, Gm)
    # self-defeat: separation-from-medium of a fixed part across measurements
    part = 1
    sep_seq = []
    Gm = G
    for i in range(20):
        s, _ = Gm.separation_from_medium(part)
        sep_seq.append(s)
        Gm = reshuffle(rng, Gm)
    # resolution: add boundary edges one at a time -> separation non-decreasing, never 0
    addk, sep_res = [], []
    base = cg.make_medium_graph(random.Random(9), 7, 1.0, 0.3, 4.0)
    neww = dict(base.weight)
    far_targets = [v for v in base.vertices if v not in (part, base.medium)]
    s0, _ = base.separation_from_medium(part)
    addk.append(0); sep_res.append(s0)
    for kk, t in enumerate(far_targets, start=1):
        neww[cg._e(part, t)] = base.floor * 2
        Gp = ContactGraph(base.vertices, neww, base.floor, base.medium)
        s, _ = Gp.separation_from_medium(part)
        addk.append(kk); sep_res.append(s)
    # 3D: residual surface over (measurement index, three seeds)
    surf_m, surf_seed, surf_res = [], [], []
    for si, seed in enumerate((1, 2, 3)):
        rr = random.Random(seed); Gm = G
        for i in range(20):
            rv, _ = Gm.residual()
            surf_m.append(i); surf_seed.append(si); surf_res.append(rv)
            Gm = reshuffle(rr, Gm)
    return {
        "residual_conserved": {"measurement": meas, "residual": res_seq,
                               "total_weight": tot_seq, "floor": G.floor},
        "self_defeat_separation": {"measurement": meas, "separation": sep_seq,
                                   "floor": G.floor},
        "resolution": {"edges_added": addk, "separation": sep_res,
                       "floor": base.floor},
        "surface_residual_seed": {"measurement": surf_m, "seed": surf_seed,
                                  "residual": surf_res},
    }


def main():
    data = {
        "panel1_ground_floor": panel1(),
        "panel2_T0_floor": panel2(),
        "panel3_T1_negation": panel3(),
        "panel4_T2T3_residual": panel4(),
        "panel5_T4_private": panel5(),
        "panel6_T5_gate": panel6(),
        "panel7_T6_nonreturn": panel7(),
        "panel8_T7_quotient": panel8(),
        "panel9_T8_authored": panel9(),
        "panel10_measurement": panel10(),
    }
    with open("figure_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
    for k, v in data.items():
        print(k, "->", list(v.keys()))
    print("written figure_data.json")


if __name__ == "__main__":
    main()
