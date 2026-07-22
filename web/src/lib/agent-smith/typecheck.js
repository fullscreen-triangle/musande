// =====================================================================
//  Agent Smith — type checker.
//  The four typing rules of the paper, made into a decidable front-end
//  check. A spec that types denotes a well-formed agent object; the
//  compiler instantiates all and only well-typed specs.
//
//  Rule (Self):   parts connected, simple, nonempty; every cost >= floor > 0.
//  Rule (Drive):  purpose is strongly convex (minimise <phi>) or reach <o>.
//  Rule (Scene):  every scene serves the ONE declared purpose; has a hook.
//  Rule (Agent):  all of the above, plus budget > 0 and floor > 0.
//
//  Returns { ok, errors, typed } where `typed` is the spec annotated with
//  derived quantities (chi, realised floor). Errors carry a line where
//  available so the editor can point at them.
// =====================================================================

import { isConnected, characterInvariant, realisedFloor } from "./identity";

// The strongly-convex potentials the standalone tool knows by name. A
// Buhera deployment can extend this registry; `reach <outcome>` always
// types (squared distance is 1-strongly convex), so a user can always
// specify a task-agent without registering a potential.
export const CONVEX_POTENTIALS = new Set([
  // residual-to-purpose style names; any of these denotes ||x - x*||^2 / 2
  "forge_residual",
  "verdict_confirmed",
  "bake_residual",
  "residual",
  "distance_to_goal",
]);

function err(errors, message, line) {
  errors.push({ message, line: line ?? null });
}

/** Rule (Self). */
function checkSelf(spec, errors) {
  const self = spec.self;
  if (!self) {
    err(errors, 'agent has no "self { ... }" block', spec.line);
    return false;
  }
  const { parts, separations } = self;
  if (!parts || parts.length === 0) {
    err(errors, "self has no parts", self.line);
    return false;
  }
  // simple: no self-loops, no duplicate part names
  const seen = new Set();
  for (const p of parts) {
    if (seen.has(p)) err(errors, `duplicate part "${p}"`, self.line);
    seen.add(p);
  }
  for (const s of separations) {
    if (s.a === s.b) err(errors, `self-loop on "${s.a}" is not allowed`, s.line);
    if (!seen.has(s.a)) err(errors, `separation references unknown part "${s.a}"`, s.line);
    if (!seen.has(s.b)) err(errors, `separation references unknown part "${s.b}"`, s.line);
  }
  // floor: every cost >= floor > 0
  const floor = spec.floor;
  if (floor == null) err(errors, 'agent has no "floor"', spec.line);
  else if (!(floor > 0)) err(errors, `floor must be > 0 (got ${floor})`, spec.line);
  if (floor != null) {
    for (const s of separations) {
      if (!(s.cost >= floor)) {
        err(
          errors,
          `separation (${s.a}, ${s.b}) cost ${s.cost} is below the floor ${floor}`,
          s.line
        );
      }
    }
  }
  // connected
  if (parts.length > 1 && !isConnected(parts, separations)) {
    err(errors, "self-graph is not connected (an agent must be one whole)", self.line);
    return false;
  }
  return errors.length === 0;
}

/** Rule (Drive). */
function checkDrive(spec, errors) {
  const p = spec.purpose;
  if (!p) {
    err(errors, 'agent has no "purpose"', spec.line);
    return false;
  }
  if (p.mode === "reach") {
    // squared distance to an outcome is always 1-strongly convex: types.
    return true;
  }
  if (p.mode === "minimise") {
    if (!CONVEX_POTENTIALS.has(p.potential)) {
      err(
        errors,
        `purpose "minimise ${p.potential}" is not a known strongly convex potential; ` +
          `register it or use "reach <outcome>" for a task-agent`,
        p.line
      );
      return false;
    }
    return true;
  }
  err(errors, "unknown purpose mode", p.line);
  return false;
}

/** Rule (Scene): every scene serves the one declared purpose and has a hook. */
function checkScenes(spec, errors) {
  const scenes = spec.scenes || [];
  if (scenes.length === 0) {
    err(errors, "agent has no scenes (an agent must have at least one activity)", spec.line);
    return false;
  }
  const declared =
    spec.purpose?.mode === "minimise" ? spec.purpose.potential : spec.purpose?.outcome;
  let ok = true;
  const names = new Set();
  for (const s of scenes) {
    if (names.has(s.name)) {
      err(errors, `duplicate scene "${s.name}"`, s.line);
      ok = false;
    }
    names.add(s.name);
    if (s.serves !== declared) {
      err(
        errors,
        `scene "${s.name}" serves "${s.serves}" but the agent's purpose is "${declared}" ` +
          `(no dead scenes: every scene must serve the one purpose)`,
        s.line
      );
      ok = false;
    }
    if (!s.hook) {
      err(errors, `scene "${s.name}" has no hook`, s.line);
      ok = false;
    }
  }
  return ok;
}

/** Rule (Agent): budget and act floor positive. */
function checkAgentExtras(spec, errors) {
  let ok = true;
  if (spec.budget == null) {
    err(errors, 'agent has no "budget"', spec.line);
    ok = false;
  } else if (!(spec.budget > 0)) {
    err(errors, `budget must be > 0 (got ${spec.budget})`, spec.line);
    ok = false;
  }
  // coherence is optional; if present, its parts must exist
  if (spec.coherence) {
    const parts = new Set(spec.self?.parts || []);
    for (const k of spec.coherence.keeps) {
      if (!parts.has(k))
        err(errors, `coherence keeps unknown part "${k}"`, spec.coherence.line);
    }
  }
  return ok;
}

/**
 * Type-check a single agent spec.
 * @returns {{ ok: boolean, errors: Array, typed: object|null }}
 */
export function typecheckAgent(spec) {
  const errors = [];
  const sOk = checkSelf(spec, errors);
  const dOk = checkDrive(spec, errors);
  const scOk = checkScenes(spec, errors);
  const aOk = checkAgentExtras(spec, errors);
  const ok = sOk && dOk && scOk && aOk && errors.length === 0;

  let typed = null;
  if (ok) {
    const { parts, separations } = spec.self;
    const { chi, side } = characterInvariant(parts, separations);
    const floor = realisedFloor(parts, separations);
    const regime = spec.purpose.mode === "reach" ? "task" : "character";
    typed = {
      ...spec,
      derived: {
        chi,
        chiSide: [...side],
        chiNonLocal: side.size > 1,
        realisedFloor: floor,
        regime, // "character" (standing) | "task" (attainable → halts)
      },
    };
  }
  return { ok, errors, typed };
}

/**
 * Type-check a program (agent or society).
 * @returns {{ ok, errors, typed }}
 */
export function typecheck(spec) {
  if (spec.kind === "agent") return typecheckAgent(spec);

  if (spec.kind === "society") {
    const errors = [];
    const typedMembers = [];
    for (const m of spec.members) {
      if (m.kind === "ref") {
        // references are resolved by the caller against a registry; here we
        // simply carry them through.
        typedMembers.push({ kind: "ref", name: m.name });
        continue;
      }
      const r = typecheckAgent(m);
      if (!r.ok) {
        for (const e of r.errors)
          errors.push({ ...e, message: `member "${m.name}": ${e.message}` });
      } else {
        typedMembers.push(r.typed);
      }
    }
    // ties: floor on inter-agent separations
    for (const t of spec.ties) {
      if (!(t.cost > 0)) errors.push({ message: `tie (${t.a}, ${t.b}) must have cost > 0`, line: spec.line });
    }
    const ok = errors.length === 0;
    return {
      ok,
      errors,
      typed: ok ? { ...spec, members: typedMembers } : null,
    };
  }

  return { ok: false, errors: [{ message: `unknown program kind "${spec.kind}"`, line: null }], typed: null };
}
