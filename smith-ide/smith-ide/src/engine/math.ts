// =====================================================================
//  Core mathematics from the Split-Attention Synchronised Agents paper.
//  Every function here corresponds to a definition or theorem.
// =====================================================================

// --- Graph types ---

export interface WeightedGraph {
  parts: string[];
  separations: { from: string; to: string; cost: number }[];
}

export interface Partition {
  blocks: string[][];
  cost: number;
}

// --- Floor (Theorem 2.1) ---

/** Realised floor: min boundary cost over all nonempty proper subsets. */
export function realisedFloor(g: WeightedGraph): number {
  const n = g.parts.length;
  if (n <= 1) return Infinity;

  let minCost = Infinity;
  // Enumerate all nonempty proper subsets via bitmask
  const total = 1 << n;
  for (let mask = 1; mask < total - 1; mask++) {
    const subset = new Set<string>();
    for (let i = 0; i < n; i++) {
      if (mask & (1 << i)) subset.add(g.parts[i]);
    }
    const cost = boundaryCost(g, subset);
    if (cost < minCost) minCost = cost;
  }
  return minCost;
}

/** Boundary cost of a subset U: sum of weights crossing U and V\U. */
export function boundaryCost(g: WeightedGraph, subset: Set<string>): number {
  let cost = 0;
  for (const sep of g.separations) {
    const fromIn = subset.has(sep.from);
    const toIn = subset.has(sep.to);
    if (fromIn !== toIn) cost += sep.cost;
  }
  return cost;
}

// --- Character Invariant χ (Definition 4.2, Theorem 4.1) ---

/** 
 * Compute χ(A) = min over all partitions with r≥2 blocks of ρ(Q).
 * Returns { chi, partition } where partition is the minimising one.
 */
export function characterInvariant(g: WeightedGraph): { chi: number; partition: Partition } {
  const n = g.parts.length;
  if (n <= 1) return { chi: Infinity, partition: { blocks: [g.parts], cost: Infinity } };

  let bestChi = Infinity;
  let bestPartition: Partition = { blocks: [], cost: Infinity };

  // Enumerate all partitions into ≥2 blocks using restricted growth strings
  const rgs = new Array(n).fill(0);

  function enumerate(pos: number, maxSoFar: number): void {
    if (pos === n) {
      const numBlocks = maxSoFar + 1;
      if (numBlocks < 2) return;

      // Build blocks
      const blocks: string[][] = Array.from({ length: numBlocks }, () => []);
      for (let i = 0; i < n; i++) {
        blocks[rgs[i]].push(g.parts[i]);
      }
      // Skip if any block is empty
      if (blocks.some(b => b.length === 0)) return;

      // Compute ρ(Q) = sum of cut weights between all pairs of blocks
      const cost = partitionResidual(g, blocks);
      if (cost < bestChi) {
        bestChi = cost;
        bestPartition = { blocks: blocks.map(b => [...b]), cost };
      }
      return;
    }

    for (let val = 0; val <= maxSoFar + 1; val++) {
      rgs[pos] = val;
      enumerate(pos + 1, Math.max(maxSoFar, val));
    }
  }

  enumerate(0, -1);
  return { chi: bestChi, partition: bestPartition };
}

/** ρ(Q) = total cut weight between all pairs of blocks. */
export function partitionResidual(g: WeightedGraph, blocks: string[][]): number {
  // For each separation, if the endpoints are in different blocks, add the cost
  const partMap = new Map<string, number>();
  blocks.forEach((block, idx) => block.forEach(p => partMap.set(p, idx)));

  let cost = 0;
  for (const sep of g.separations) {
    const bi = partMap.get(sep.from);
    const bj = partMap.get(sep.to);
    if (bi !== undefined && bj !== undefined && bi !== bj) {
      cost += sep.cost;
    }
  }
  return cost;
}

/** 
 * Get all nontrivial partitions with their costs, sorted ascending. 
 * For the partition landscape chart.
 */
export function allPartitionCosts(g: WeightedGraph): Partition[] {
  const n = g.parts.length;
  if (n <= 1) return [];
  const results: Partition[] = [];
  const rgs = new Array(n).fill(0);

  function enumerate(pos: number, maxSoFar: number): void {
    if (pos === n) {
      const numBlocks = maxSoFar + 1;
      if (numBlocks < 2) return;
      const blocks: string[][] = Array.from({ length: numBlocks }, () => []);
      for (let i = 0; i < n; i++) blocks[rgs[i]].push(g.parts[i]);
      if (blocks.some(b => b.length === 0)) return;
      const cost = partitionResidual(g, blocks);
      results.push({ blocks: blocks.map(b => [...b]), cost });
      return;
    }
    for (let val = 0; val <= maxSoFar + 1; val++) {
      rgs[pos] = val;
      enumerate(pos + 1, Math.max(maxSoFar, val));
    }
  }

  enumerate(0, -1);
  results.sort((a, b) => a.cost - b.cost);
  return results;
}

// --- Water-filling (Theorem 5.1, Algorithm 1) ---

export interface GainProfile {
  name: string;
  /** Gain function γ(a) */
  gamma: (a: number) => number;
  /** Marginal gain γ'(a) */
  gammaPrime: (a: number) => number;
  /** Inverse of marginal: (γ')^{-1}(p) */
  gammaPrimeInverse: (p: number) => number;
  /** Entry margin γ'(0) */
  entryMargin: number;
}

/** Logarithmic gain profile: γ(a) = ln(1 + k*a), γ'(a) = k/(1+ka) */
export function logGainProfile(name: string, k: number): GainProfile {
  return {
    name,
    gamma: (a: number) => Math.log(1 + k * a),
    gammaPrime: (a: number) => k / (1 + k * a),
    gammaPrimeInverse: (p: number) => p > 0 ? (k / p - 1) / k : Infinity,
    entryMargin: k,
  };
}

export interface WaterFillResult {
  allocations: { scene: string; allocation: number; marginalGain: number }[];
  price: number;
  totalGain: number;
  budgetUsed: number;
}

/** 
 * Water-filling attention scheduler (Algorithm 1).
 * Bisection on the Lagrange multiplier p*.
 */
export function waterFill(
  scenes: GainProfile[],
  budget: number,
  tolerance: number = 1e-10
): WaterFillResult {
  if (scenes.length === 0) {
    return { allocations: [], price: 0, totalGain: 0, budgetUsed: 0 };
  }

  let pLo = 0;
  let pHi = Math.max(...scenes.map(s => s.entryMargin));

  // Check if budget is abundant (all scenes can be fully served)
  const totalAtZeroPrice = scenes.reduce((sum, s) => sum + s.gammaPrimeInverse(tolerance), 0);
  if (totalAtZeroPrice <= budget) {
    // Budget not binding
    const allocations = scenes.map(s => ({
      scene: s.name,
      allocation: s.gammaPrimeInverse(tolerance),
      marginalGain: tolerance,
    }));
    const totalGain = scenes.reduce((sum, s, i) => sum + s.gamma(allocations[i].allocation), 0);
    const budgetUsed = allocations.reduce((sum, a) => sum + a.allocation, 0);
    return { allocations, price: 0, totalGain, budgetUsed };
  }

  // Bisection
  let price = 0;
  for (let iter = 0; iter < 200; iter++) {
    price = (pLo + pHi) / 2;
    let totalAlloc = 0;
    for (const scene of scenes) {
      if (scene.entryMargin > price) {
        totalAlloc += scene.gammaPrimeInverse(price);
      }
    }
    if (totalAlloc > budget) {
      pLo = price;
    } else {
      pHi = price;
    }
    if (pHi - pLo < tolerance) break;
  }

  price = (pLo + pHi) / 2;
  const allocations = scenes.map(s => {
    const alloc = s.entryMargin > price ? s.gammaPrimeInverse(price) : 0;
    return {
      scene: s.name,
      allocation: alloc,
      marginalGain: alloc > 0 ? s.gammaPrime(alloc) : s.entryMargin,
    };
  });

  const totalGain = scenes.reduce((sum, s, i) => sum + s.gamma(allocations[i].allocation), 0);
  const budgetUsed = allocations.reduce((sum, a) => sum + a.allocation, 0);

  return { allocations, price, totalGain, budgetUsed };
}

// --- Kuramoto synchronisation (Definition 7.4, Theorem 7.3) ---

export interface KuramotoState {
  phases: number[];
  velocities: number[];
  R: number;
  psi: number;
  cost: number;
}

/** Compute order parameter R and mean phase ψ. */
export function orderParameter(phases: number[]): { R: number; psi: number } {
  if (phases.length === 0) return { R: 0, psi: 0 };
  const M = phases.length;
  let sumCos = 0, sumSin = 0;
  for (const phi of phases) {
    sumCos += Math.cos(phi);
    sumSin += Math.sin(phi);
  }
  sumCos /= M;
  sumSin /= M;
  const R = Math.sqrt(sumCos * sumCos + sumSin * sumSin);
  const psi = Math.atan2(sumSin, sumCos);
  return { R, psi };
}

/** One Kuramoto integration step. */
export function kuramotoStep(
  phases: number[],
  velocities: number[],
  K: number,
  dt: number
): number[] {
  const { R, psi } = orderParameter(phases);
  return phases.map((phi, j) => {
    const dphi = velocities[j] + K * R * Math.sin(psi - phi);
    return phi + dt * dphi;
  });
}

/** Run Kuramoto to convergence or maxSteps. */
export function kuramotoRun(
  initialPhases: number[],
  velocities: number[],
  K: number,
  dt: number = 0.05,
  maxSteps: number = 2000,
  convergenceThreshold: number = 0.999
): KuramotoState[] {
  const history: KuramotoState[] = [];
  let phases = [...initialPhases];

  for (let step = 0; step < maxSteps; step++) {
    const { R, psi } = orderParameter(phases);
    const cost = 1 - R; // λ_c = 1 for simplicity
    history.push({ phases: [...phases], velocities: [...velocities], R, psi, cost });
    if (R >= convergenceThreshold) break;
    phases = kuramotoStep(phases, velocities, K, dt);
  }
  return history;
}

/** Coordination cost C = λ_c * (1 - R). */
export function coordinationCost(R: number, lambdaC: number = 1): number {
  return lambdaC * (1 - R);
}

// --- Crowd sharpening (Theorem 7.6) ---

/** Collective failure probability = ∏ q_i. */
export function crowdFailure(individualFailures: number[]): number {
  return individualFailures.reduce((prod, q) => prod * q, 1);
}

/** Crowd failure curve: M → ∏_{i=1}^{M} q. */
export function crowdFailureCurve(q: number, maxM: number): { M: number; failure: number }[] {
  const curve: { M: number; failure: number }[] = [];
  let prod = 1;
  for (let m = 1; m <= maxM; m++) {
    prod *= q;
    curve.push({ M: m, failure: prod });
  }
  return curve;
}

// --- Methodology Banach floor (Theorem 7.1 of economics paper) ---

/** Methodology floor σκ/(1−κ). */
export function methodologyFloor(kappa: number, sigma: number): number {
  if (kappa >= 1) return Infinity;
  return (sigma * kappa) / (1 - kappa);
}

/** Convergence trajectory: s_t = S̄ + κ^t (s_0 − S̄). */
export function convergenceTrajectory(
  kappa: number,
  sigma: number,
  s0: number,
  maxT: number
): { t: number; s: number }[] {
  const floor = methodologyFloor(kappa, sigma);
  const trajectory: { t: number; s: number }[] = [];
  for (let t = 0; t <= maxT; t++) {
    const s = floor + Math.pow(kappa, t) * (s0 - floor);
    trajectory.push({ t, s });
  }
  return trajectory;
}

// --- S-functional (economics paper) ---

/** S(R, x; C) = max(β, d(x, C)). Simplified for 1D/2D. */
export function sFunctional(beta: number, distanceToCell: number): number {
  return Math.max(beta, distanceToCell) ;
}

// --- Template overlap (epidemiology paper) ---

export interface TemplateStructure {
  dimensions: { name: string; weight: number }[];
}

export interface AgentState {
  dimensions: { name: string; value: number }[];
}

/** Overlap integral: ∫ T(c) · ρ(c) dc, discretised. */
export function templateOverlap(template: TemplateStructure, state: AgentState): number {
  let overlap = 0;
  for (const td of template.dimensions) {
    const sd = state.dimensions.find(s => s.name === td.name);
    if (sd) {
      // Gaussian overlap centered on match
      overlap += td.weight * sd.value;
    }
  }
  return Math.max(0, overlap);
}

/** Coordination weighting f(R) from the epidemiology paper. */
export function coordinationWeighting(R: number): number {
  if (R < 0.3) return 0.2;
  if (R < 0.5) return 0.4;
  if (R < 0.8) return 0.6;
  if (R < 0.95) return 0.8;
  return 1.0;
}

/** Template convergence fraction: C = 1 − exp(−τ/τ_sat). */
export function templateConvergence(coevTime: number, satTime: number = 100000): number {
  return 1 - Math.exp(-coevTime / satTime);
}
