// =====================================================================
//  Agent Smith — compiler (lowering).
//  Lowers a well-typed spec into a running Agent object. The compiler
//  installs the objects (self, drive, scenes) and seats the fixed runtime
//  (the tick-loop lives in tick.js; the Agent just holds state). The four
//  invariants are honoured by construction:
//    I1 identity   — chi computed from the self-graph, label-independent
//    I2 count      — m starts at 0, only ever incremented (by tick.commit)
//    I3 search     — the agent stores no answers; it re-reads Omega
//    I4 phase      — phase field flips construction <-> commitment
// =====================================================================

import { logGain } from "./identity";
import { typecheck } from "./typecheck";
import { parse } from "./parse";

let _uid = 0;
function uid(prefix) {
  return `${prefix}_${(_uid++).toString(36)}`;
}

/**
 * An Agent object (the compiled instance).
 * Fields the runtime reads/writes:
 *   name, regime ("character" | "task"),
 *   self { parts, separations }, chi, floor,
 *   scenes [{ id, name, serves, hook, gain }],
 *   budget, purpose { mode, target },
 *   disposition (number in [0,1]: distance-to-purpose proxy, 1 = far, 0 = at),
 *   count m, phase, coherenceKeep (Set),
 *   trajectory [] (the monotone address: how it got here — not the task),
 *   state ("running" | "quiescent" | "observing")
 */
export function compileAgent(typed) {
  const { name, self, budget, purpose, coherence, derived } = typed;

  const scenes = (typed.scenes || []).map((s) => ({
    id: uid("scene"),
    name: s.name,
    serves: s.serves,
    hook: s.hook, // opaque name; resolved by the runtime's hook registry
    // default concave gain profile; a Buhera deployment can override per hook.
    // richness varies a little by scene so water-filling has something to do.
    gain: logGain(1 + 0.5 * hashUnit(s.name)),
  }));

  const agent = {
    id: uid("agent"),
    name,
    regime: derived.regime,
    self: { parts: [...self.parts], separations: self.separations.map((e) => ({ ...e })) },
    chi: derived.chi,
    chiSide: derived.chiSide,
    chiNonLocal: derived.chiNonLocal,
    floor: derived.realisedFloor,
    scenes,
    budget,
    purpose: {
      mode: purpose.mode,
      // for reach: the outcome name; for minimise: the potential name.
      target: purpose.mode === "reach" ? purpose.outcome : purpose.potential,
    },
    coherenceKeep: new Set(coherence ? coherence.keeps : []),
    // runtime state
    disposition: 1.0, // starts far from purpose (residual = 1)
    count: 0, // m: monotone committed count (I2)
    phase: "construction", // I4
    trajectory: [], // the address: sequence of committed step-labels
    lastResidual: 1.0,
    stallWindow: [], // recent residual deltas, for the diagnosis
    state: "running",
  };
  return agent;
}

/**
 * Compile a whole program (agent or society) from a typed spec.
 * Returns { agents: [Agent], ties, couple } for a society, or
 * { agents: [Agent] } for a single agent.
 */
export function compileProgram(typed) {
  if (typed.kind === "society") {
    const agents = typed.members
      .filter((m) => m.kind !== "ref")
      .map((m) => compileAgent(m));
    return { kind: "society", name: typed.name, agents, ties: typed.ties, couple: typed.couple };
  }
  return { kind: "agent", agents: [compileAgent(typed)] };
}

/**
 * Full pipeline: source -> parse -> typecheck -> compile.
 * Returns { ok, errors, program } where program is the compiled result.
 */
export function build(source) {
  let spec;
  try {
    spec = parse(source);
  } catch (e) {
    return { ok: false, errors: [{ message: e.message, line: e.line ?? null }], program: null };
  }
  const tc = typecheck(spec);
  if (!tc.ok) return { ok: false, errors: tc.errors, program: null, spec };
  const program = compileProgram(tc.typed);
  return { ok: true, errors: [], program, typed: tc.typed, spec };
}

// deterministic hash -> [0,1), so scene richness is stable across runs
function hashUnit(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 1000) / 1000;
}
