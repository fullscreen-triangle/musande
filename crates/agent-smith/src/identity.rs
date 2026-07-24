// =====================================================================
//  Agent Smith — identity invariant and water-filling.
//  The paper's core graph/convex computations the compiler and runtime
//  consume. Port of identity.js, with one deliberate simplification: the
//  chi invariant is computed by EXACT bipartition enumeration only (real
//  agents have < 12 parts; the JS Karger fallback for n > 20 never runs
//  in practice and is omitted).
//
//  - character_invariant(self-graph): chi = min over nontrivial bipartitions
//    of the inter-part cut weight (the paper's chi). Non-local by
//    construction: realised by a set of edges, not a single vertex label.
//  - water_fill(scenes, budget): the single-price attention division.
// =====================================================================

use std::collections::{HashMap, HashSet};

use crate::ast::Separation;

// ---- self-graph helpers ---------------------------------------------

/// Adjacency as part -> (part -> summed cost). Parallel edges are summed,
/// matching the JS `adjacency` (which accumulates `+ cost`).
fn adjacency(parts: &[String], seps: &[Separation]) -> HashMap<String, HashMap<String, f64>> {
    let mut adj: HashMap<String, HashMap<String, f64>> = HashMap::new();
    for p in parts {
        adj.entry(p.clone()).or_default();
    }
    for e in seps {
        adj.entry(e.a.clone()).or_default();
        adj.entry(e.b.clone()).or_default();
        *adj.get_mut(&e.a).unwrap().entry(e.b.clone()).or_insert(0.0) += e.cost;
        *adj.get_mut(&e.b).unwrap().entry(e.a.clone()).or_insert(0.0) += e.cost;
    }
    adj
}

/// Is the self-graph connected? (DFS from the first part.)
pub fn is_connected(parts: &[String], seps: &[Separation]) -> bool {
    if parts.is_empty() {
        return false;
    }
    let adj = adjacency(parts, seps);
    let mut seen: HashSet<&String> = HashSet::new();
    seen.insert(&parts[0]);
    let mut stack: Vec<&String> = vec![&parts[0]];
    while let Some(v) = stack.pop() {
        if let Some(nbrs) = adj.get(v) {
            for u in nbrs.keys() {
                // borrow the canonical String key from `parts` for lifetime
                if let Some(uref) = parts.iter().find(|p| *p == u) {
                    if !seen.contains(uref) {
                        seen.insert(uref);
                        stack.push(uref);
                    }
                }
            }
        }
    }
    seen.len() == parts.len()
}

/// Weight of the cut between block S and its complement (V \ S).
fn cut_weight(adj: &HashMap<String, HashMap<String, f64>>, s: &HashSet<String>) -> f64 {
    let mut w = 0.0;
    for v in s {
        if let Some(nbrs) = adj.get(v) {
            for (u, c) in nbrs {
                if !s.contains(u) {
                    w += c;
                }
            }
        }
    }
    w
}

/// The character invariant chi(A): the minimum inter-part boundary weight
/// over all nontrivial bipartitions of the self-graph. Computed exactly by
/// enumerating bipartitions with parts[0] fixed in S (halves the search and
/// avoids the empty/full trivial cuts).
///
/// Returns (chi, side) where `side` is the smaller block realising the
/// minimum — used to show the invariant is non-local (|side| may be > 1).
pub fn character_invariant(parts: &[String], seps: &[Separation]) -> (f64, HashSet<String>) {
    let n = parts.len();
    if n < 2 {
        return (0.0, parts.iter().cloned().collect());
    }
    let adj = adjacency(parts, seps);

    let mut best = f64::INFINITY;
    let mut best_side: Option<HashSet<String>> = None;
    let rest = &parts[1..];
    let total: u64 = 1u64 << rest.len();
    for mask in 0..total {
        let mut s: HashSet<String> = HashSet::new();
        s.insert(parts[0].clone());
        for (b, part) in rest.iter().enumerate() {
            if mask & (1u64 << b) != 0 {
                s.insert(part.clone());
            }
        }
        if s.len() == n {
            continue; // full set is trivial
        }
        let w = cut_weight(&adj, &s);
        if w > 0.0 && w < best {
            best = w;
            best_side = Some(s);
        }
    }

    match best_side {
        None => (0.0, parts.iter().cloned().collect()),
        Some(side) => {
            let complement_smaller = side.len() > n - side.len();
            let final_side = if complement_smaller {
                parts.iter().filter(|p| !side.contains(*p)).cloned().collect()
            } else {
                side
            };
            (best, final_side)
        }
    }
}

/// Realised floor: least boundary cost of any single part (singleton cut).
pub fn realised_floor(parts: &[String], seps: &[Separation]) -> f64 {
    let adj = adjacency(parts, seps);
    let mut min = f64::INFINITY;
    for p in parts {
        let mut w = 0.0;
        if let Some(nbrs) = adj.get(p) {
            for c in nbrs.values() {
                w += c;
            }
        }
        if w > 0.0 && w < min {
            min = w;
        }
    }
    if min.is_infinite() {
        0.0
    } else {
        min
    }
}

// ---- water-filling ---------------------------------------------------

/// A standard concave gain profile gamma(a) = k * ln(1 + a).
/// marginal gamma'(a) = k/(1+a); at zero: k; inverse: a = k/p - 1.
/// The default scene profile when a script does not supply one.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct LogGain {
    pub k: f64,
}

impl LogGain {
    pub fn new(k: f64) -> Self {
        LogGain { k }
    }
    /// Marginal gain at zero attention: gamma'(0) = k.
    pub fn g0(&self) -> f64 {
        self.k
    }
    /// gamma(a) = k * ln(1 + a).
    pub fn gain(&self, a: f64) -> f64 {
        self.k * (1.0 + a).ln()
    }
    /// gamma'(a) = k / (1 + a).
    pub fn marginal(&self, a: f64) -> f64 {
        self.k / (1.0 + a)
    }
    /// inverse marginal: a such that gamma'(a) = p, i.e. a = k/p - 1.
    pub fn inv_marginal(&self, p: f64) -> f64 {
        self.k / p - 1.0
    }
}

/// A scene reduced to what water-filling needs: an id, its marginal-at-zero,
/// and its gain profile (for the inverse-marginal).
#[derive(Debug, Clone)]
pub struct SceneCost {
    pub id: String,
    pub gain: LogGain,
}

/// Water-filling attention division over concurrent scenes under a budget.
/// Solves for the single price p* by bisection so sum(alloc) = budget (or
/// p* = 0 if the budget is not binding). Returns (allocations, price).
///
/// `invMarginal` is nonincreasing in price, so total demand is nonincreasing
/// in price and the bisection has a unique root.
pub fn water_fill(scenes: &[SceneCost], budget: f64) -> (Vec<(String, f64)>, f64) {
    let eps = 1e-7;
    if scenes.is_empty() {
        return (Vec::new(), 0.0);
    }
    let g0max = scenes.iter().map(|s| s.gain.g0()).fold(f64::NEG_INFINITY, f64::max);

    // total demand at price p: sum over scenes whose g0 > p of max(0, invMarginal(p))
    let demand = |p: f64| -> f64 {
        scenes
            .iter()
            .map(|s| {
                if s.gain.g0() > p {
                    s.gain.inv_marginal(p).max(0.0)
                } else {
                    0.0
                }
            })
            .sum()
    };

    // if even at price ~0 the demand fits the budget, price is 0
    if demand(1e-9) <= budget {
        let allocations = scenes
            .iter()
            .map(|s| {
                let a = if s.gain.g0() > 1e-9 {
                    s.gain.inv_marginal(1e-9).max(0.0)
                } else {
                    0.0
                };
                (s.id.clone(), a)
            })
            .collect();
        return (allocations, 0.0);
    }

    let mut lo = 0.0;
    let mut hi = g0max;
    while hi - lo > eps {
        let p = (lo + hi) / 2.0;
        if demand(p) > budget {
            lo = p;
        } else {
            hi = p;
        }
    }
    let price = (lo + hi) / 2.0;
    let allocations = scenes
        .iter()
        .map(|s| {
            let a = if s.gain.g0() > price {
                s.gain.inv_marginal(price).max(0.0)
            } else {
                0.0
            };
            (s.id.clone(), a)
        })
        .collect();
    (allocations, price)
}

/// Convenience: the water-filling price alone, for an agent's scenes/budget.
pub fn water_fill_price(scenes: &[SceneCost], budget: f64) -> f64 {
    water_fill(scenes, budget).1
}
