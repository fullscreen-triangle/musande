// =====================================================================
//  Agent Smith — the town (society) and the shared solution-state.
//  A town holds many agents and ONE solution-state Omega. Every tick,
//  each agent reads Omega, decides, and (if it commits) changes Omega —
//  which the others read next tick. This is outcome-space coordination:
//  no agent holds a model of any other; they meet in Omega.
//
//  The default ctx supplies:
//    - probe(omega, agent): the tier-0 deterministic read of Omega for an
//      agent's purpose → { residual, hint }. Empty-dictionary: it derives
//      the residual from Omega, stores nothing.
//    - coherent(agent, candidate): the coherence check.
//    - runHook(agent, candidate, obs, omega): the tier-1 domain work via a
//      model (the irreducible seam).
//    - applyToOmega(omega, agent, candidate, delta): commit's effect.
// =====================================================================

import { tick, initFloorNorm, OUTCOME } from "./tick";
import { characterInvariant } from "./identity";

/**
 * A solution-state Omega. Tracks, per purpose-target, a global residual in
 * [0,1] (1 = untouched, floor = as solved as a bounded reader can tell), and
 * a log of committed acts (the shared outcome record every agent reads).
 */
export function makeOmega(agents) {
  const residual = new Map();
  // A standalone agent (its target is the only one) always has work: start
  // far. In a mixed town, a task/reach agent that shares the town with
  // characters pursuing OTHER targets starts at its floor (already
  // satisfied) — it is a pure observer until another agent's act RAISES its
  // residual in outcome space (the penguin-watcher: safe until danger).
  const nTargets = new Set(agents.map((a) => a.purpose.target)).size;
  for (const a of agents) {
    const t = a.purpose.target;
    if (residual.has(t)) continue;
    const standalone = nTargets === 1;
    const hasWork = a.regime === "character" || standalone;
    residual.set(t, hasWork ? 1.0 : a.floorNorm);
  }
  return {
    residual, // Map<target, gap in [0,1]>
    log: [], // committed acts, newest last (the shared outcome-state)
    tickIndex: 0,
  };
}

/** Build a Town from a compiled program. */
export function makeTown(program) {
  const agents = program.agents.map((a) => initFloorNorm(a));
  const omega = makeOmega(agents);
  // society identity: chi over the agent quotient (ties as inter-agent edges)
  let society = null;
  if (program.kind === "society" && program.ties?.length) {
    const parts = agents.map((a) => a.name);
    const separations = program.ties.map((t) => ({ a: t.a, b: t.b, cost: t.cost }));
    const { chi, side } = characterInvariant(parts, separations);
    society = { chi, side: [...side], couple: program.couple ?? null };
  }
  return { name: program.name || "town", agents, omega, society, program };
}

/**
 * The default context. In Buhera OS, replace `probe` with `purpose ask` and
 * `runHook` with chatCascade; here they are self-contained so the tool runs
 * standalone (but still uses real models for the judgment, via ctx.useModel).
 */
export function defaultCtx(opts = {}) {
  return {
    useModel: opts.useModel !== false, // models are the point; on by default
    keys: opts.keys,
    crowd: !!opts.crowd,
    crowdSize: opts.crowdSize || 3,

    // tier-0 deterministic read of Omega for this agent's purpose.
    probe(omega, agent) {
      const residual = omega.residual.get(agent.purpose.target) ?? 1.0;
      // hint: the last few committed acts touching this target (what others
      // have already done toward it) — the shared outcome slice.
      const hint = omega.log
        .filter((e) => e.target === agent.purpose.target)
        .slice(-3)
        .map((e) => ({ by: e.by, scene: e.scene, delta: e.delta }));
      // the agent reads Omega's residual as its disposition (it does not
      // store the task; it re-reads the state each tick).
      agent.disposition = residual;
      return { residual, hint };
    },

    // coherence: the act must keep the agent's coherence-parts related.
    // (Standalone default: always coherent unless the hook says otherwise.)
    coherent(agent, candidate) {
      return true;
    },

    // tier-1 domain work via a model. Opaque to the runtime; we read only
    // its outcome (a residual reduction and some content). Provided by the
    // caller (page wires it to /api/agent-smith-think through providers).
    runHook: opts.runHook || null,

    // commit's effect on Omega: lower the shared residual for the target and
    // append the act to the shared log.
    applyToOmega(omega, agent, candidate, delta, hookResult) {
      const t = agent.purpose.target;
      const cur = omega.residual.get(t) ?? 1.0;
      omega.residual.set(t, Math.max(agent.floorNorm, cur - delta));
      omega.log.push({
        tick: omega.tickIndex,
        by: agent.name,
        target: t,
        scene: candidate.scene,
        delta: Number(delta.toFixed(3)),
        content: hookResult?.content ?? null,
      });
    },
  };
}

/**
 * Step the whole town once: every agent takes a tick against the shared
 * Omega. Returns { tick, records, omega } for the UI. Agents are stepped in
 * order but all read the SAME Omega snapshot for their observe; commits
 * apply immediately so later agents in the same tick can see earlier commits
 * (this is what makes the penguin-watcher run in the same wave).
 */
export async function stepTown(town, ctx) {
  town.omega.tickIndex += 1;
  const records = [];
  for (const agent of town.agents) {
    const rec = await tick(agent, town.omega, ctx);
    records.push(rec);
  }
  const anyLive = town.agents.some((a) => a.state !== "quiescent");
  const anyProgress = records.some((r) => r.outcome === OUTCOME.COMMIT);
  return {
    tick: town.omega.tickIndex,
    records,
    residuals: Object.fromEntries(town.omega.residual),
    quiescent: !anyProgress && town.agents.every((a) => a.state !== "running"),
    done: !anyLive,
  };
}

/** Run the town until quiescence or a max number of ticks. */
export async function runTown(town, ctx, maxTicks = 30) {
  const history = [];
  for (let i = 0; i < maxTicks; i++) {
    const step = await stepTown(town, ctx);
    history.push(step);
    if (step.done || step.quiescent) break;
  }
  return history;
}
