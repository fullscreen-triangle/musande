// =====================================================================
//  Agent Smith — identity invariant and water-filling.
//  Pure graph/convex computations the compiler and runtime consume.
//
//  - characterInvariant(selfGraph):  chi = min over 2-block partitions of
//    the inter-part cut weight (the paper's chi; here computed exactly by
//    minimum cut, which for a connected weighted graph equals the min
//    over all bipartitions of the crossing weight). Non-local by
//    construction: realised by a set of edges, not a vertex label.
//  - waterFill(scenes, budget):  the single-price attention division.
//    Returns { allocations, price } with marginal gains equalised at
//    price p* on attended scenes, per the water-filling theorem.
// =====================================================================

// ---- self-graph helpers ---------------------------------------------

/** Build adjacency (Map<part, Map<part, cost>>) from a self-graph spec. */
function adjacency(parts, separations) {
  const adj = new Map();
  for (const p of parts) adj.set(p, new Map());
  for (const { a, b, cost } of separations) {
    if (!adj.has(a)) adj.set(a, new Map());
    if (!adj.has(b)) adj.set(b, new Map());
    adj.get(a).set(b, (adj.get(a).get(b) || 0) + cost);
    adj.get(b).set(a, (adj.get(b).get(a) || 0) + cost);
  }
  return adj;
}

/** Is the self-graph connected? (BFS from the first part.) */
export function isConnected(parts, separations) {
  if (parts.length === 0) return false;
  const adj = adjacency(parts, separations);
  const seen = new Set([parts[0]]);
  const stack = [parts[0]];
  while (stack.length) {
    const v = stack.pop();
    for (const u of adj.get(v).keys()) {
      if (!seen.has(u)) {
        seen.add(u);
        stack.push(u);
      }
    }
  }
  return seen.size === parts.length;
}

/** Weight of the cut between block S and its complement (V \ S). */
function cutWeight(adj, S) {
  let w = 0;
  for (const v of S) {
    for (const [u, c] of adj.get(v)) {
      if (!S.has(u)) w += c;
    }
  }
  return w;
}

/**
 * The character invariant chi(A): the minimum inter-part boundary weight
 * over all nontrivial bipartitions of the self-graph.
 *
 * Agent Smith self-graphs are small (a handful of parts), so we compute the
 * global minimum cut exactly by enumerating bipartitions. To keep it O(2^n)
 * only up to a safe bound we cap exact enumeration at n <= 20 (1M subsets);
 * above that we fall back to a repeated randomised-contraction estimate.
 * In practice agents have < 12 parts and the exact path is instant.
 *
 * Returns { chi, side } where `side` is the smaller block realising the
 * minimum — used to show the invariant is non-local (|side| may be > 1).
 */
export function characterInvariant(parts, separations) {
  const n = parts.length;
  if (n < 2) return { chi: 0, side: new Set(parts) };
  const adj = adjacency(parts, separations);

  if (n <= 20) {
    let best = Infinity;
    let bestSide = null;
    // enumerate subsets S with part[0] in S (fix vertex 0 to halve, avoid
    // the empty/full trivial cuts). S ranges over 1..2^(n-1)-1 of the
    // remaining n-1 vertices, always including vertex 0.
    const rest = parts.slice(1);
    const total = 1 << rest.length;
    for (let mask = 0; mask < total; mask++) {
      const S = new Set([parts[0]]);
      for (let b = 0; b < rest.length; b++) if (mask & (1 << b)) S.add(rest[b]);
      if (S.size === n) continue; // full set is trivial
      const w = cutWeight(adj, S);
      if (w > 0 && w < best) {
        best = w;
        bestSide = S;
      }
    }
    if (bestSide === null) return { chi: 0, side: new Set(parts) };
    const side = bestSide.size <= n - bestSide.size
      ? bestSide
      : new Set(parts.filter((p) => !bestSide.has(p)));
    return { chi: best, side };
  }

  // large-graph fallback: randomised min-cut (Karger), several trials.
  let best = Infinity;
  let bestSide = null;
  const trials = 40;
  for (let t = 0; t < trials; t++) {
    const r = kargerOnce(parts, separations);
    if (r.chi > 0 && r.chi < best) {
      best = r.chi;
      bestSide = r.side;
    }
  }
  return { chi: best === Infinity ? 0 : best, side: bestSide || new Set([parts[0]]) };
}

/** One Karger random-contraction pass (fallback for large self-graphs). */
function kargerOnce(parts, separations) {
  const supernode = new Map(parts.map((p) => [p, new Set([p])]));
  let edges = separations.map((e) => ({ ...e }));
  const alive = new Set(parts);
  while (alive.size > 2) {
    const e = edges[Math.floor(pseudoRandom() * edges.length)];
    if (!e || e.a === e.b) {
      edges = edges.filter((x) => x.a !== x.b);
      continue;
    }
    // contract e.b into e.a
    const merged = supernode.get(e.a);
    for (const x of supernode.get(e.b)) merged.add(x);
    alive.delete(e.b);
    supernode.delete(e.b);
    edges = edges
      .map((x) => ({ a: x.a === e.b ? e.a : x.a, b: x.b === e.b ? e.a : x.b, cost: x.cost }))
      .filter((x) => x.a !== x.b);
  }
  const [g1] = [...alive];
  const side = supernode.get(g1);
  const adj = adjacency(parts, separations);
  return { chi: cutWeight(adj, side), side };
}

// deterministic PRNG so identity is reproducible across runs
let _seed = 0x2545f491;
function pseudoRandom() {
  _seed ^= _seed << 13;
  _seed ^= _seed >>> 17;
  _seed ^= _seed << 5;
  return ((_seed >>> 0) % 1e6) / 1e6;
}

/** Realised floor: least boundary cost of any single part (singleton cut). */
export function realisedFloor(parts, separations) {
  const adj = adjacency(parts, separations);
  let min = Infinity;
  for (const p of parts) {
    let w = 0;
    for (const c of adj.get(p).values()) w += c;
    if (w > 0 && w < min) min = w;
  }
  return min === Infinity ? 0 : min;
}

// ---- water-filling ---------------------------------------------------

/**
 * Water-filling attention division over concurrent scenes under a budget.
 * Each scene supplies a concave gain profile via its marginal-gain-at-zero
 * `g0` and an inverse-marginal function invMarginal(price) -> allocation.
 * We solve for the single price p* by bisection so that sum(alloc) = budget
 * (or p*=0 if the budget is not binding).
 *
 * scenes: [{ id, g0, invMarginal }]  (invMarginal is nonincreasing in price)
 * returns { allocations: Map<id, a>, price }
 */
export function waterFill(scenes, budget, eps = 1e-7) {
  if (scenes.length === 0) return { allocations: new Map(), price: 0 };
  const g0max = Math.max(...scenes.map((s) => s.g0));
  // total demand at price p
  const demand = (p) =>
    scenes.reduce((sum, s) => sum + (s.g0 > p ? Math.max(0, s.invMarginal(p)) : 0), 0);

  // if even at price ~0 the demand fits the budget, price is 0
  if (demand(1e-9) <= budget) {
    const allocations = new Map();
    for (const s of scenes) allocations.set(s.id, s.g0 > 1e-9 ? Math.max(0, s.invMarginal(1e-9)) : 0);
    return { allocations, price: 0 };
  }

  let lo = 0;
  let hi = g0max;
  while (hi - lo > eps) {
    const p = (lo + hi) / 2;
    if (demand(p) > budget) lo = p;
    else hi = p;
  }
  const price = (lo + hi) / 2;
  const allocations = new Map();
  for (const s of scenes) {
    allocations.set(s.id, s.g0 > price ? Math.max(0, s.invMarginal(price)) : 0);
  }
  return { allocations, price };
}

/**
 * A standard concave gain profile gamma(a) = k * ln(1 + a).
 * marginal gamma'(a) = k/(1+a); at zero: k. inverse: a = k/p - 1.
 * Used as the default scene profile when a script does not supply one.
 */
export function logGain(k) {
  return {
    k,
    g0: k,
    gain: (a) => k * Math.log(1 + a),
    marginal: (a) => k / (1 + a),
    invMarginal: (p) => k / p - 1,
  };
}
