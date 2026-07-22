// =====================================================================
//  Agent Smith — the tick-loop.
//  What a compiled agent does each tick: observe → diagnose → commit.
//  The agent acts on the STATE OF THE SOLUTION, not on internal reasoning.
//
//  observe : read a slice of the shared solution-state Omega (tier 0 cheap
//            probe; escalate to a model read only on residue). Never stores
//            the task; re-reads Omega. → residual gap + a candidate act.
//  diagnose: read the residual descent → a typed limit
//            (converging | compute-limited | structure-limited/stall).
//  commit  : a RUNTIME-owned gate reading the OUTCOME of the candidate act.
//            Fires iff (sufficiency: outcome-gain clears the price) AND
//            (coherence: preserves the agent's coherence). Else the agent
//            stays a pure observer — valid, almost free, contributes 0.
//
//  The model (providers.think) is used only at the irreducible seam: the
//  domain judgment inside observe/commit. Everything else is deterministic.
// =====================================================================

import { waterFill } from "./identity";
import { think } from "./providers";

export const LIMIT = {
  CONVERGING: "converging",
  COMPUTE: "compute-limited",
  STRUCTURE: "structure-limited",
};

export const OUTCOME = {
  COMMIT: "commit",
  OBSERVE: "observe", // gate did not fire; pure observer this tick
  DECLINE: "decline", // off-purpose / incoherent for this interaction
  QUIESCENT: "quiescent", // task-agent reached its attainable outcome
};

/**
 * observe(agent, omega, ctx)
 * Tier-0 read is deterministic: measure the residual gap of THIS agent's
 * purpose against the current solution-state via ctx.probe. If the slice is
 * not enough to determine an act (gap ambiguous), escalate to a model read
 * (Tier 1). Returns { residual, candidate, tier, slice }.
 */
async function observe(agent, omega, ctx) {
  // Tier 0: cheap deterministic probe of the solution-state.
  const slice = ctx.probe(omega, agent); // { residual, hint }
  let residual = slice.residual;
  let tier = 0;
  let candidate = null;

  // The EFFECTIVE gain of a scene scales with the residual gap: acting pays
  // in proportion to how far the solution-state is from this agent's purpose.
  // At the floor the gap is ~0, so no scene clears the price → the agent
  // observes (and a task-agent quiesces). This is the single mechanism behind
  // both the pure observer and task halting: the gate reads the state, and
  // when the state does not call for the agent, it does not act.
  const price = waterFillPrice(agent);
  const gap = Math.max(0, residual - agent.floorNorm);
  const effGain = (s) => s.gain.g0 * gap;
  const active = agent.scenes.filter((s) => effGain(s) > price);
  if (active.length === 0) {
    // no scene clears the price for this state → nothing to do (observer)
    return { residual, candidate: null, tier, slice, price };
  }

  // Ambiguity test: escalate to a model read (Tier 1) only when the gap is in
  // the "unsure" band near the floor, where a judgment is genuinely needed;
  // otherwise form the candidate deterministically from the highest-gain scene.
  const unsureBand = gap > 0 && gap < 0.15;
  if (unsureBand && ctx.useModel) {
    tier = 1;
    const j = await judgeSufficiency(agent, slice, ctx);
    residual = j.residual ?? residual;
    candidate = j.act ? { ...j.act, expectedGain: effGain(agent.scenes[0]) } : null;
  } else {
    // deterministic candidate: the highest-gain active scene
    const scene = active.reduce((a, b) => (effGain(b) > effGain(a) ? b : a));
    candidate = { scene: scene.name, hook: scene.hook, expectedGain: effGain(scene) };
  }
  return { residual, candidate, tier, slice, price };
}

/**
 * diagnose(agent) — read the residual descent over recent ticks.
 * Uses agent.stallWindow (recent deltas). Returns a LIMIT.
 */
function diagnose(agent) {
  const win = agent.stallWindow;
  if (win.length === 0) return LIMIT.COMPUTE;
  const recent = win.slice(-3);
  const sum = recent.reduce((a, b) => a + b, 0);
  if (sum <= 1e-9) return LIMIT.STRUCTURE; // no descent over the window: stall
  const last = win[win.length - 1];
  if (last > 0.02) return LIMIT.CONVERGING;
  return LIMIT.COMPUTE;
}

/**
 * commit(agent, candidate, residual, omega, ctx) — the runtime sufficiency
 * gate. Reads the OUTCOME of the candidate act. Fires iff sufficiency AND
 * coherence. On fire: deposit act, increment count, extend trajectory, and
 * change omega. Returns { outcome, delta, act }.
 */
async function commit(agent, obs, omega, ctx) {
  const { candidate, residual, price } = obs;

  // task-agent that has reached its attainable outcome → quiescent, halts —
  // but only if it actually did work to get there (committed ≥ 1 act). A
  // task-agent that starts already at its floor never had work: it is a pure
  // OBSERVER (ready to act if the shared state raises its residual), not done.
  if (agent.regime === "task" && residual <= agent.floorNorm + 1e-6) {
    if (agent.count > 0) {
      agent.state = "quiescent";
      return { outcome: OUTCOME.QUIESCENT, delta: 0, act: null };
    }
    agent.state = "observing";
    return { outcome: OUTCOME.OBSERVE, delta: 0, act: null };
  }

  // no candidate cleared the price → pure observer (floor case). Free.
  if (!candidate) {
    agent.state = "observing";
    return { outcome: OUTCOME.OBSERVE, delta: 0, act: null };
  }

  // sufficiency: does the candidate's OUTCOME-gain clear the attention price?
  // (release at sufficiency for the parent, not at the agent's own floor.)
  const gain = candidate.expectedGain;
  const sufficient = gain > price;

  // coherence: would the act break the agent's coherence condition?
  const coherent = ctx.coherent ? ctx.coherent(agent, candidate) : true;

  if (!sufficient || !coherent) {
    agent.state = coherent ? "observing" : "running";
    return {
      outcome: coherent ? OUTCOME.OBSERVE : OUTCOME.DECLINE,
      delta: 0,
      act: null,
      reason: !sufficient ? "below price" : "incoherent",
    };
  }

  // FIRE. Perform the domain work via the hook (model at the irreducible
  // seam) and read its outcome. The hook is opaque; we read only its effect.
  let hookResult = null;
  if (ctx.useModel && ctx.runHook) {
    hookResult = await ctx.runHook(agent, candidate, obs, omega);
  }
  // outcome effect on the residual (deterministic descent scaled by gain,
  // or the model-reported reduction if the hook returned one)
  const reduction =
    hookResult && typeof hookResult.reduction === "number"
      ? hookResult.reduction
      : Math.min(residual - agent.floorNorm, 0.15 + 0.1 * (gain / (price + 1e-9) - 1));
  const before = agent.disposition;
  agent.disposition = Math.max(agent.floorNorm, before - Math.max(0, reduction));

  // I2: increment the monotone committed count; extend the trajectory.
  agent.count += 1;
  agent.trajectory.push(labelStep(candidate, agent.count));
  agent.lastResidual = agent.disposition;
  agent.state = "running";

  const delta = before - agent.disposition;
  // update omega: the committed act changes the shared solution-state that
  // every other agent will read next tick (outcome-space coordination).
  ctx.applyToOmega?.(omega, agent, candidate, delta, hookResult);

  return {
    outcome: OUTCOME.COMMIT,
    delta,
    act: {
      scene: candidate.scene,
      hook: candidate.hook,
      count: agent.count,
      content: hookResult?.content ?? null,
      model: hookResult?.model ?? null,
    },
  };
}

/**
 * tick(agent, omega, ctx) — one full observe → diagnose → commit cycle,
 * respecting phase exclusion (observe/diagnose in construction; commit in
 * commitment). Returns a record for the UI.
 */
export async function tick(agent, omega, ctx) {
  if (agent.state === "quiescent") {
    return { agent: agent.name, outcome: OUTCOME.QUIESCENT, count: agent.count };
  }

  // construction phase: observe + diagnose (no act)
  agent.phase = "construction";
  const obs = await observe(agent, omega, ctx);
  const limit = diagnose(agent);

  // commitment phase: the gate
  agent.phase = "commitment";
  const res = await commit(agent, obs, omega, ctx);

  // record the residual delta for the next diagnosis
  agent.stallWindow.push(res.delta || 0);
  if (agent.stallWindow.length > 8) agent.stallWindow.shift();

  return {
    agent: agent.name,
    regime: agent.regime,
    outcome: res.outcome,
    limit,
    tier: obs.tier,
    price: Number(obs.price?.toFixed?.(3) ?? obs.price ?? 0),
    residual: Number(agent.disposition.toFixed(3)),
    delta: Number((res.delta || 0).toFixed(3)),
    count: agent.count,
    scene: res.act?.scene ?? obs.candidate?.scene ?? null,
    content: res.act?.content ?? null,
    model: res.act?.model ?? null,
    reason: res.reason ?? null,
  };
}

// ---- helpers --------------------------------------------------------

/** Normalised floor: the residual level the agent treats as "at purpose". */
export function initFloorNorm(agent) {
  // scale the graph floor into the [0,1] residual space; a small positive
  // number so the gap never closes to zero (the floor theorem).
  agent.floorNorm = Math.min(0.08, 0.02 + 0.01 * (agent.floor || 1));
  agent.disposition = 1.0;
  agent.lastResidual = 1.0;
  return agent;
}

function waterFillPrice(agent) {
  const scenes = agent.scenes.map((s) => ({ id: s.id, g0: s.gain.g0, invMarginal: s.gain.invMarginal }));
  const { price } = waterFill(scenes, agent.budget);
  return price;
}

function labelStep(candidate, count) {
  // the trajectory ADDRESS: how we got here (scene + count), not the content.
  return `${candidate.scene}#${count}`;
}

// Tier-1 model judgment of sufficiency: ask a model whether the current
// slice is enough to act, and how much residual an act would remove.
async function judgeSufficiency(agent, slice, ctx) {
  const prompt =
    `You are the sufficiency gate for an agent whose purpose is "${agent.purpose.target}".\n` +
    `Current solution-state slice: ${JSON.stringify(slice.hint ?? {})}.\n` +
    `Residual gap to purpose: ${slice.residual.toFixed(3)} (floor ${agent.floorNorm.toFixed(3)}).\n` +
    `Answer with ONE word: ACT if committing an act now would advance the purpose, ` +
    `or WAIT if the state does not yet call for this agent.`;
  try {
    const r = await think(prompt, { keys: ctx.keys, crowd: ctx.crowd, crowdSize: ctx.crowdSize });
    const act = /\bACT\b/i.test(r.text);
    return {
      act: act ? { scene: agent.scenes[0].name, hook: agent.scenes[0].hook, expectedGain: agent.scenes[0].gain.g0, model: r.model } : null,
      residual: slice.residual,
    };
  } catch {
    // model unavailable → fall back to deterministic candidate
    return { act: { scene: agent.scenes[0].name, hook: agent.scenes[0].hook, expectedGain: agent.scenes[0].gain.g0 }, residual: slice.residual };
  }
}
