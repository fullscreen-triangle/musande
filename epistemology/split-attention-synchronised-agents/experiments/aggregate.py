"""
Aggregate the four validation experiments into one master JSON with a
per-prediction verdict table. Reports honestly: which checks are exact
(machine precision), which are cross-method (against an independent solver),
which are Monte-Carlo (statistical), and which rely on negative controls.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

FILES = {
    "EXP01": "EXP01_identity_invariant.json",
    "EXP02": "EXP02_waterfilling.json",
    "EXP03": "EXP03_history_phase_search.json",
    "EXP04": "EXP04_society_sync.json",
}

# prediction -> (theorem tag, experiment, summary-key, method-of-test)
TABLE = [
    ("V1  floor: no zero cut, realised floor>0",          "thm:floor",        "EXP01", "V1_floor_pass",                      "exact enumeration"),
    ("V2a identity invariant under relabelling",           "thm:identity(ii)", "EXP01", "V2a_invariance_pass",                "exact (random automorphism-domain perms)"),
    ("V2b identity positive (>= floor)",                   "thm:identity(i)",  "EXP01", "V2b_positivity_pass",                "exact enumeration"),
    ("V2c identity non-local (witness)",                   "thm:identity(iii)","EXP01", "V2c_nonlocal_witness_pass",          "exact witness"),
    ("V3a water-filling matches convex solver",            "thm:waterfill",    "EXP02", "V3a_bisection_matches_convex_pass",  "cross-method vs scipy SLSQP"),
    ("V3b marginal gains equalise at one price",           "cor:preoccupied",  "EXP02", "V3b_equalisation_pass",              "exact (KKT margins)"),
    ("V3c price monotone in budget",                       "thm:waterfill",    "EXP02", "V3c_budget_monotone_pass",           "monotone sweep"),
    ("V3c price monotone in #scenes",                      "thm:waterfill",    "EXP02", "V3c_scene_monotone_pass",            "monotone sweep"),
    ("V4  token presence (alloc -> 0+)",                   "cor:token",        "EXP02", "V4_token_pass",                      "limit sweep"),
    ("V5  construction/commitment alternation",            "thm:alternation",  "EXP03", "V5_alternation_pass",                "reference runtime + neg. control"),
    ("V6a committed count strictly increasing",            "thm:history(i)",   "EXP03", "V6a_monotone_count_pass",            "reference runtime"),
    ("V6b distinct copies at every step",                  "thm:history(iii)", "EXP03", "V6b_distinct_copies_pass",           "reference runtime + neg. control"),
    ("V7  recall is search (>=1 act/answer)",              "thm:recsearch",    "EXP03", "V7_recall_is_search_pass",           "reference runtime + neg. control"),
    ("V8a society carries own non-local identity",         "cor:society-id",   "EXP04", "V8a_society_identity_pass",          "exact witness"),
    ("V8b coord. cost C=lambda(1-R)>=0, =0 iff R=1",       "thm:phaselock",    "EXP04", "V8b_coordination_cost_pass",         "real Kuramoto integration"),
    ("V8c coordination without shared internals",          "thm:coord",        "EXP04", "V8c_disjoint_coordination_pass",     "disjoint-internal agents"),
    ("V8d crowd sharpening (prod q_i)",                    "thm:crowd",        "EXP04", "V8d_crowd_sharpening_pass",          "Monte-Carlo vs formula"),
    ("V9  society water-filling self-similar",             "thm:socwaterfill", "EXP04", "V9_self_similarity_pass",            "cross-method vs scipy SLSQP"),
]


def main():
    data = {}
    for k, fn in FILES.items():
        with open(os.path.join(RESULTS, fn)) as f:
            data[k] = json.load(f)

    rows, n_pass = [], 0
    for pred, thm, exp, key, method in TABLE:
        val = bool(data[exp]["summary"][key])
        n_pass += int(val)
        rows.append({
            "prediction": pred, "theorem": thm, "experiment": exp,
            "summary_key": key, "method": method,
            "pass": val,
        })

    master = {
        "paper": "Split-Attention Synchronised Agents",
        "seed": 42,
        "n_predictions": len(TABLE),
        "n_pass": n_pass,
        "all_pass": n_pass == len(TABLE),
        "experiment_verdicts": {k: data[k]["verdict"] for k in FILES},
        "key_quantities": {
            "identity_invariance_max_deviation": data["EXP01"]["summary"]["V2a_invariance_max_deviation"],
            "waterfilling_max_dev_vs_scipy": data["EXP02"]["summary"]["V3a_max_alloc_deviation_vs_scipy"],
            "waterfilling_margin_spread": data["EXP02"]["summary"]["V3b_max_margin_spread_on_support"],
            "kuramoto_max_R": data["EXP04"]["coordination_cost"]["max_R_reached"],
            "crowd_mc_vs_formula_max_error": data["EXP04"]["crowd_sharpening"]["max_abs_error_mc_vs_formula"],
            "society_selfsim_max_dev": data["EXP04"]["self_similarity"]["max_alloc_deviation_society_scale"],
        },
        "honesty_notes": [
            "V2a/V2b/V2c/V3b/V8a exact: brute-force enumeration or KKT, machine precision.",
            "V3a/V9 are CROSS-METHOD: bisection water-filling vs scipy SLSQP; agreement "
            "~6e-7 reflects SLSQP's own convergence tolerance, not a defect of either method.",
            "V8d is Monte-Carlo (2e5 trials); ~1e-3 error is sampling noise, consistent with 1/sqrt(N).",
            "V5/V6b/V7 pass includes NEGATIVE CONTROLS: purpose-built violating runtimes "
            "(fetch-cache, rollback, multitask) are each detected by the predicate, so a "
            "pass on the reference runtime is a meaningful test, not a tautology.",
            "V8b uses REAL Kuramoto ODE integration to drive R from dispersed to locked; "
            "C=lambda(1-R) is then evaluated on the achieved R, not assumed.",
            "These test internal mathematical consistency of the paper's claims. They are "
            "NOT external empirical validation against real-world attention/coordination data.",
        ],
        "verdict_table": rows,
    }

    with open(os.path.join(RESULTS, "MASTER_validation.json"), "w") as f:
        json.dump(master, f, indent=2)

    print(f"MASTER: {n_pass}/{len(TABLE)} predictions pass "
          f"({'ALL CONFIRMED' if master['all_pass'] else 'SOME FAILED'})")
    for r in rows:
        print(f"  [{'PASS' if r['pass'] else 'FAIL'}] {r['prediction']:<45} "
              f"({r['theorem']}, {r['method']})")


if __name__ == "__main__":
    main()
