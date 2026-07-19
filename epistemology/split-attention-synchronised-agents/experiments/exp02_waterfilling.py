"""
EXP02 -- Optimal attention division is water-filling (T2), and its corollaries
(present-but-preoccupied, token presence).

Claims tested:
  (V3a) The bisection water-filling allocation (Algorithm in the paper) matches
        an INDEPENDENT convex optimiser (scipy SLSQP) to tolerance.
  (V3b) On attended scenes, marginal gains equalise at a single price p*.
  (V3c) p* is nonincreasing in the budget alpha, nondecreasing in #scenes.
  (V4)  Token presence: as a scene's gamma_i'(0) -> p*+, its allocation -> 0+.

Gain profiles: gamma_i(a) = k_i * ln(1 + s_i * a), concave, increasing,
gamma_i(0)=0. Then gamma_i'(a) = k_i s_i / (1 + s_i a), and the inverse
(gamma_i')^{-1}(p) = (k_i s_i / p - 1)/s_i for p < k_i s_i, else 0.

Independence: the water-filling result is checked against scipy's general-
purpose constrained maximiser, which knows nothing of the water-filling
structure. Agreement is a genuine cross-method test.
"""
import json, os
import numpy as np
from scipy.optimize import minimize

RNG = np.random.default_rng(42)
HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")


def gamma(a, k, s):
    return k * np.log1p(s * a)


def gamma_prime(a, k, s):
    return k * s / (1.0 + s * a)


def gamma_prime_inv(p, k, s):
    # solve k s /(1+ s a) = p  ->  a = (k s / p - 1)/s ; clip at 0
    if p <= 0:
        return np.inf
    a = (k * s / p - 1.0) / s
    return max(a, 0.0)


def waterfill_bisection(ks, ss, alpha, eps=1e-12, iters=200):
    """Paper's Algorithm: bisection on price p*."""
    p_lo, p_hi = 0.0, max(k * s for k, s in zip(ks, ss))  # max gamma'(0)
    for _ in range(iters):
        if p_hi - p_lo <= eps:
            break
        p = 0.5 * (p_lo + p_hi)
        a = [gamma_prime_inv(p, k, s) for k, s in zip(ks, ss)]
        total = sum(a)
        if total > alpha:      # price too low -> too much demand
            p_lo = p
        else:
            p_hi = p
    p = 0.5 * (p_lo + p_hi)
    a = np.array([gamma_prime_inv(p, k, s) for k, s in zip(ks, ss)])
    return a, p


def waterfill_scipy(ks, ss, alpha):
    """Independent convex solve: maximise sum gamma_i(a_i) s.t. sum a<=alpha, a>=0."""
    n = len(ks)

    def neg_obj(a):
        return -sum(gamma(a[i], ks[i], ss[i]) for i in range(n))

    def neg_grad(a):
        return -np.array([gamma_prime(a[i], ks[i], ss[i]) for i in range(n)])

    cons = [{"type": "ineq", "fun": lambda a: alpha - np.sum(a)}]
    bounds = [(0.0, alpha) for _ in range(n)]
    x0 = np.full(n, alpha / n)
    res = minimize(neg_obj, x0, jac=neg_grad, bounds=bounds,
                   constraints=cons, method="SLSQP",
                   options={"ftol": 1e-12, "maxiter": 500})
    return res.x


def main():
    out = {"experiment": "EXP02_waterfilling", "seed": 42, "cases": []}
    max_alloc_dev = 0.0
    max_margin_spread = 0.0
    monotone_budget_ok = True
    monotone_scene_ok = True

    for trial in range(40):
        n = int(RNG.integers(2, 7))
        ks = RNG.uniform(0.5, 3.0, size=n)
        ss = RNG.uniform(0.5, 4.0, size=n)
        alpha = RNG.uniform(0.5, 3.0)

        a_bis, p_star = waterfill_bisection(ks, ss, alpha)
        a_sci = waterfill_scipy(ks, ss, alpha)
        dev = float(np.max(np.abs(a_bis - a_sci)))
        max_alloc_dev = max(max_alloc_dev, dev)

        # marginal-gain equalisation on the support
        active = a_bis > 1e-9
        if active.sum() >= 1:
            margins = np.array([gamma_prime(a_bis[i], ks[i], ss[i])
                                for i in range(n) if active[i]])
            spread = float(margins.max() - margins.min()) if len(margins) > 1 else 0.0
            max_margin_spread = max(max_margin_spread, spread)

        out["cases"].append({
            "trial": trial, "n": n, "alpha": float(alpha),
            "p_star": float(p_star),
            "alloc_bisection": a_bis.tolist(),
            "alloc_scipy": a_sci.tolist(),
            "max_alloc_deviation": dev,
        })

    # ---- V3c monotonicity of p* in budget ----
    ks = np.array([1.0, 2.0, 1.5, 0.8])
    ss = np.array([1.0, 2.0, 0.5, 3.0])
    prices_budget = []
    for alpha in np.linspace(0.2, 5.0, 25):
        _, p = waterfill_bisection(ks, ss, alpha)
        prices_budget.append(p)
    for i in range(1, len(prices_budget)):
        if prices_budget[i] > prices_budget[i - 1] + 1e-9:
            monotone_budget_ok = False

    # ---- V3c monotonicity of p* in #scenes (add scenes, fixed budget) ----
    prices_scenes = []
    alpha_fixed = 1.0
    base_k, base_s = [], []
    for m in range(1, 9):
        base_k.append(float(RNG.uniform(0.5, 3.0)))
        base_s.append(float(RNG.uniform(0.5, 4.0)))
        _, p = waterfill_bisection(base_k, base_s, alpha_fixed)
        prices_scenes.append(p)
    for i in range(1, len(prices_scenes)):
        if prices_scenes[i] < prices_scenes[i - 1] - 1e-9:
            monotone_scene_ok = False

    # ---- V4 token presence ----
    # Scene 1 is rich and fixed; scene 2 has marginal-at-zero gamma2'(0)=k2*s2.
    # We lower scene 2's k2*s2 toward the price the rich scene alone sets. As
    # scene 2's entry margin approaches that price from above, its allocation
    # must shrink to 0+ (it becomes a token/near-zero presence), while staying
    # positive until it drops below the price. We measure scene 2's own share.
    alpha2 = 1.0
    s2 = 1.0
    # price set by scene 1 alone spending the whole budget:
    k1, s1 = 2.0, 2.0
    p_rich = gamma_prime(alpha2, k1, s1)          # gamma1'(alpha) if scene1 took all
    token_allocs, entry_margins = [], []
    for k2 in np.linspace(3.0, p_rich * 1.0005 / s2, 15):
        a, p = waterfill_bisection([k1, float(k2)], [s1, s2], alpha2)
        token_allocs.append(float(a[1]))
        entry_margins.append(float(k2 * s2))
    # monotone shrink toward 0 as entry margin falls toward the price
    shrinking = all(token_allocs[i] >= token_allocs[i + 1] - 1e-9
                    for i in range(len(token_allocs) - 1))
    token_pass = bool(shrinking and token_allocs[-1] < 1e-2
                      and token_allocs[0] > token_allocs[-1])

    out["monotonicity"] = {
        "prices_vs_budget": prices_budget,
        "V3c_budget_monotone_pass": bool(monotone_budget_ok),
        "prices_vs_scene_count": prices_scenes,
        "V3c_scene_monotone_pass": bool(monotone_scene_ok),
    }
    out["token_presence"] = {
        "price_set_by_rich_scene": float(p_rich),
        "entry_margins_swept": entry_margins,
        "allocations_as_margin_approaches_price": token_allocs,
        "V4_token_pass": bool(token_pass),
    }
    out["summary"] = {
        "V3a_max_alloc_deviation_vs_scipy": max_alloc_dev,
        "V3a_bisection_matches_convex_pass": bool(max_alloc_dev < 1e-5),
        "V3b_max_margin_spread_on_support": max_margin_spread,
        "V3b_equalisation_pass": bool(max_margin_spread < 1e-6),
        "V3c_budget_monotone_pass": bool(monotone_budget_ok),
        "V3c_scene_monotone_pass": bool(monotone_scene_ok),
        "V4_token_pass": bool(token_pass),
    }
    out["verdict"] = "CONFIRMED" if all([
        out["summary"]["V3a_bisection_matches_convex_pass"],
        out["summary"]["V3b_equalisation_pass"],
        out["summary"]["V3c_budget_monotone_pass"],
        out["summary"]["V3c_scene_monotone_pass"],
        out["summary"]["V4_token_pass"],
    ]) else "FAILED"

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "EXP02_waterfilling.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("EXP02", out["verdict"],
          "| alloc dev vs scipy =", f"{max_alloc_dev:.2e}",
          "| margin spread =", f"{max_margin_spread:.2e}")


if __name__ == "__main__":
    main()
