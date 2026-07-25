// =====================================================================
//  Agent Smith Sandbox — the runner.
//
//  The single place that knows the engine's call contract. It takes DSL
//  source, drives the REAL engine in web/src/lib/agent-smith (the same
//  TypeScript engine the Buhera OS imports — NOT a reimplementation), and
//  flattens the results into the flat record table + structure + attention
//  shapes the store and charts consume.
//
//  Offline & deterministic: we build a ctx with useModel:false, so the whole
//  sandbox runs with no API keys and no network — the deterministic residual
//  descent stands in for the model at the irreducible seam. (A live Buhera
//  deployment swaps in a real runHook; the sandbox never needs one.)
// =====================================================================

import {
  build,
  makeTown,
  defaultCtx,
  runTown,
  waterFill,
  characterInvariant,
  realisedFloor,
  logGain,
} from "@/lib/agent-smith";

const MAX_TICKS = 30;

// Compute the structure panel data for one compiled agent.
function structureFor(agent) {
  const parts = agent.self?.parts ?? [];
  const separations = (agent.self?.separations ?? []).map((s) => ({
    a: s.a,
    b: s.b,
    cost: s.cost,
  }));
  const { chi, side } = characterInvariant(parts, separations);
  const floor = realisedFloor(parts, separations);

  // enumerate a handful of bipartition costs for the "landscape" chart
  const allPartitions = enumeratePartitions(parts, separations).slice(0, 24);

  return {
    agent: agent.name,
    parts,
    separations,
    chi,
    side: [...side],
    nonLocal: side.size > 1,
    floor,
    declaredFloor: agent.floor ?? 0,
    allPartitions,
  };
}

// All nontrivial bipartition cut costs (small graphs only), sorted ascending.
function enumeratePartitions(parts, separations) {
  const n = parts.length;
  if (n < 2 || n > 16) return [];
  const adj = new Map(parts.map((p) => [p, new Map()]));
  for (const { a, b, cost } of separations) {
    adj.get(a).set(b, (adj.get(a).get(b) || 0) + cost);
    adj.get(b).set(a, (adj.get(b).get(a) || 0) + cost);
  }
  const rest = parts.slice(1);
  const out = [];
  for (let mask = 1; mask < (1 << rest.length); mask++) {
    const S = new Set([parts[0]]);
    for (let b = 0; b < rest.length; b++) if (mask & (1 << b)) S.add(rest[b]);
    if (S.size === n) continue;
    let w = 0;
    for (const v of S) for (const [u, c] of adj.get(v)) if (!S.has(u)) w += c;
    if (w > 0) out.push({ cost: w, size: S.size, block: [...S] });
  }
  return out.sort((x, y) => x.cost - y.cost);
}

// Water-filling panel for one compiled agent (default log-gain profiles).
function attentionFor(agent) {
  const scenes = agent.scenes.map((s) => {
    const gain = s.gain ?? logGain(s.gain?.g0 ?? 1.5);
    return { id: s.id ?? s.name, name: s.name, g0: gain.g0, invMarginal: gain.invMarginal, gain };
  });
  const { allocations, price } = waterFill(
    scenes.map((s) => ({ id: s.id, g0: s.g0, invMarginal: s.invMarginal })),
    agent.budget ?? 1.0
  );
  const rows = scenes.map((s) => ({
    scene: s.name,
    g0: s.g0,
    allocation: allocations.get(s.id) ?? 0,
    active: (allocations.get(s.id) ?? 0) > 1e-6,
  }));
  return { agent: agent.name, budget: agent.budget ?? 1.0, price, rows, scenes };
}

/**
 * Compile + run a source string. Returns everything the store needs, or an
 * error payload if the build failed. Never throws for user errors.
 */
export async function compileAndRun(source) {
  const log = [];
  const built = build(source);

  if (!built.ok) {
    for (const e of built.errors ?? []) {
      log.push(`✗ ${e.severity ?? "error"}: ${e.message}${e.line ? ` (line ${e.line})` : ""}`);
    }
    return { build: built, records: [], structure: null, attention: null, society: null, logLines: log };
  }

  const program = built.program;
  const agents = program.agents ?? [];
  log.push(`✓ compiled — ${agents.length} agent${agents.length === 1 ? "" : "s"}`);
  for (const a of agents) {
    log.push(`  ${a.name}: regime=${a.regime} χ=${a.chi} floor=${a.floor}`);
  }

  // structure + attention are computed on the FIRST agent (the panels show one
  // agent at a time; the explorer/legend lets the reader pick which).
  const structure = agents.length ? structureFor(agents[0]) : null;
  const attention = agents.length ? attentionFor(agents[0]) : null;

  // run the town offline
  const town = makeTown(program);
  const ctx = defaultCtx({ useModel: false });
  const history = await runTown(town, ctx, MAX_TICKS);

  // flatten history → one flat record row per (tick, agent)
  const records = [];
  for (const step of history) {
    for (const rec of step.records) {
      records.push({
        tick: step.tick,
        agent: rec.agent,
        regime: rec.regime,
        outcome: rec.outcome,
        limit: rec.limit ?? null,
        phase: rec.outcome === "commit" ? "commitment" : "construction",
        price: rec.price ?? 0,
        residual: rec.residual ?? 0,
        delta: rec.delta ?? 0,
        count: rec.count ?? 0,
        scene: rec.scene ?? null,
        reason: rec.reason ?? null,
      });
    }
  }
  log.push(`✓ ran ${history.length} tick${history.length === 1 ? "" : "s"} → ${records.length} records`);

  const society = town.society
    ? { chi: town.society.chi, side: town.society.side, couple: town.society.couple }
    : null;
  if (society) log.push(`  society χ = ${society.chi} (couple ${society.couple ?? "—"})`);

  return { build: built, records, structure, attention, society, logLines: log };
}
