// =====================================================================
//  Agent Smith — instantiation (TypeScript).
//
//  The web-tool port of `crates/agent-smith/src/instantiate.rs`.
//
//  This framework generates agents. That is its whole job.
//
//  The rest of the engine (parse -> typecheck -> compile -> tick) is the path
//  a HUMAN takes: someone writes a `.smith` source declaring an agent, and
//  the engine builds and drives it. That path assumes the agents are known in
//  advance, which is true of a character and false of everything else.
//
//  This module is the other path. A module, mid-run, decomposes a problem
//  into subtasks and needs an agent per subtask — now, with no source text,
//  no declaration, and no pause. `instantiate` is that call. It lowers a
//  Subtask straight to a running Agent, skipping parse and typecheck because
//  there is no source to parse and no human error to catch.
//
//  Two properties of the resulting agent matter more than anything else here:
//
//   * IT HOLDS ONE SUBTASK AND NOTHING ELSE. It cannot ask what the wider
//     task is, what came before it, or what comes after, because those fields
//     do not exist on it. A module decides the decomposition and the
//     coordination; the agent just carries its piece. This is not a
//     restriction imposed on a capable object — it is the shape of the
//     object.
//
//   * IT IS NOT PRIVILEGED. The module that generates DSL code is itself
//     built out of agents, so whatever calls `instantiate` may well have been
//     produced by `instantiate`. There is no layer above this one. The
//     function is therefore free of any assumption that its caller is a
//     human, a top-level orchestrator, or a distinguished module.
//
//  What an instantiated agent does NOT get is a self-graph. A self-graph
//  supports chi, identity conserved across change — which presupposes
//  something persisting to be identical to. A ticket holds one subtask and
//  has no ordering, so there is nothing for identity to be conserved across.
//  Callers building a standing character supply a self-graph via the DSL
//  path; callers building a ticket do not, and `chi` is left at zero rather
//  than fabricated. Same agent shape either way — the difference is what is
//  populated, not what is possible.
//
//  The agents produced here are structurally identical to those `compileAgent`
//  produces, so they drop straight into `makeTown` / `stepTown` unchanged.
// =====================================================================

// @ts-ignore — identity.js is untyped JS; `logGain` returns the `Gain` shape
// declared below, which we state explicitly rather than infer.
import { logGain } from "./identity";
import type { Chunk, Graph, Raised, Subtask } from "./subtask";

// ---------------------------------------------------------------------
//  The agent shape (mirrors compile.js `compileAgent`)
// ---------------------------------------------------------------------

/**
 * A concave gain profile: what a scene returns for attention spent. Written
 * out rather than inferred from `logGain`, which is untyped JS and would
 * otherwise widen this field to `any`.
 */
export interface Gain {
  k: number;
  g0: number;
  gain: (a: number) => number;
  marginal: (a: number) => number;
  invMarginal: (p: number) => number;
}

/** A scene: one outward act available to the agent. */
export interface Scene {
  id: string;
  name: string;
  serves: string;
  /** Opaque routing key, resolved by the runtime's hook registry. */
  hook: string;
  gain: Gain;
}

/** A compiled agent instance — the object the tick-loop reads and writes. */
export interface Agent {
  id: string;
  name: string;
  regime: "character" | "task";
  self: { parts: string[]; separations: Array<{ a: string; b: string; cost: number }> };
  chi: number;
  chiSide: string[];
  chiNonLocal: boolean;
  floor: number;
  scenes: Scene[];
  budget: number;
  purpose: { mode: "minimise" | "reach"; target: string };
  coherenceKeep: Set<string>;
  disposition: number;
  count: number;
  phase: "construction" | "commitment";
  trajectory: string[];
  lastResidual: number;
  stallWindow: number[];
  state: "running" | "quiescent" | "observing";
}

let _uid = 0;
function ticketId(): string {
  return `ticket_${(_uid++).toString(36)}`;
}

/**
 * How much attention an instantiated agent may spend. Defaulted rather than
 * required, because the raising module usually has no basis for a number and
 * a made-up one is worse than a uniform one.
 */
const DEFAULT_BUDGET = 1.0;

// ---------------------------------------------------------------------
//  The ticket
// ---------------------------------------------------------------------

/**
 * An agent generated from a subtask.
 *
 * It bundles the runtime `Agent` (the object the tick machinery reads and
 * writes) with the `Subtask` it carries, so a hook at the seam can see both
 * the instruction and the chunks when the agent fires. Without this pairing
 * the hook would see a scene name and nothing else, and the DSL code would
 * have no route to the point of execution.
 */
export interface Ticket {
  /** The runtime object. Drop-in compatible with `makeTown`. */
  readonly agent: Agent;
  /** The subtask it carries: instruction plus realising chunks. */
  readonly subtask: Subtask;
  /**
   * Which module generated it. Provenance for the report; the agent itself
   * never reads this.
   */
  readonly by?: string;
}

/** The instruction this agent carries. */
export function instruction(t: Ticket): string {
  return t.subtask.instruction;
}

/**
 * The realisations this agent carries. All of them are to be executed; there
 * is no accessor that selects one.
 */
export function chunks(t: Ticket): readonly Chunk[] {
  return t.subtask.chunks;
}

// ---------------------------------------------------------------------
//  Instantiation
// ---------------------------------------------------------------------

/**
 * Options for instantiation. Every field has a defensible default, so the
 * common call is `instantiate(sub)`.
 */
export interface Spawn {
  /** Which module is raising this. Recorded as provenance. */
  by?: string;
  /** Attention budget. Defaults to `DEFAULT_BUDGET`. */
  budget?: number;
  /**
   * The resolution floor for this agent: the smallest residual it can
   * distinguish from zero. A bounded reader cannot resolve below its own
   * floor, so an agent that drives residual to its floor is as done as it can
   * tell — which is what makes a ticket halt rather than grind.
   */
  floor?: number;
}

/** Deterministic hash -> [0,1). Bit-for-bit the same as compile.js. */
function hashUnit(str: string): number {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) % 1000 / 1000;
}

/**
 * Generate an agent from a subtask.
 *
 * The agent's purpose is `reach <tau>` — a task-agent, which halts at
 * quiescence, rather than a character with a standing purpose. Its scenes are
 * derived from the subtask's chunks: one scene per realisation, since running
 * a realisation is the outward act available to this agent. A subtask with no
 * chunks yet still yields a working agent with a single generic scene, so a
 * module can raise an unrealised subtask and let a code-generating module
 * converge a chunk onto it later.
 *
 * This does not touch a graph. Use `instantiateInto` to generate the agent
 * and publish its subtask as a node in one step.
 */
export function instantiate(sub: Subtask, spawn: Spawn = {}): Ticket {
  const target = sub.tau as string;
  const budget = spawn.budget ?? DEFAULT_BUDGET;
  const floor = spawn.floor ?? 0;

  // One scene per realisation. The scene's `hook` names the DSL, so a hook
  // implementation can route on it — this is the only place the DSL tag is
  // read by this module, and it is read as an opaque routing key, never
  // parsed.
  const scenes: Scene[] = sub.chunks.map((c, i) => {
    const name = `run_${c.dsl}_${i}`;
    return {
      id: `scene_${ticketId()}_${i}`,
      name,
      serves: target,
      hook: c.dsl,
      gain: logGain(1 + 0.5 * hashUnit(name)),
    };
  });

  // An unrealised subtask still gets an agent: it has been raised but not yet
  // translated into code. Its single scene is the act of obtaining a
  // realisation.
  if (scenes.length === 0) {
    const name = "realise";
    scenes.push({
      id: `scene_${ticketId()}_0`,
      name,
      serves: target,
      hook: "unrealised",
      gain: logGain(1 + 0.5 * hashUnit(name)),
    });
  }

  const agent: Agent = {
    id: ticketId(),
    name: target,
    regime: "task",
    // No self-graph: a ticket has no persistence for an identity to be
    // conserved across. Left empty rather than fabricated.
    self: { parts: [], separations: [] },
    chi: 0,
    chiSide: [],
    chiNonLocal: false,
    floor,
    scenes,
    budget,
    purpose: { mode: "reach", target },
    coherenceKeep: new Set<string>(),
    // runtime state
    disposition: 1.0,
    count: 0,
    phase: "construction",
    trajectory: [],
    lastResidual: 1.0,
    stallWindow: [],
    state: "running",
  };

  return spawn.by === undefined
    ? { agent, subtask: sub }
    : { agent, subtask: sub, by: spawn.by };
}

/**
 * Generate an agent and publish its subtask as a node in one step.
 *
 * Returns the ticket and whether the subtask created a new node or converged
 * onto an existing one. Convergence is the normal case and is not a collision
 * to be resolved: two agents arriving at the same subtask meet at one node,
 * and the node accretes both realisations.
 */
export function instantiateInto(
  sub: Subtask,
  graph: Graph,
  spawn: Spawn = {},
): { ticket: Ticket; raised: Raised } {
  const raised = graph.raise(sub);
  return { ticket: instantiate(sub, spawn), raised };
}

/**
 * Generate agents for a whole decomposition, publishing every subtask.
 *
 * The order of the returned tickets is the order given, but that ordering
 * carries no meaning to the agents — none of them can observe its own
 * position, and nothing in a ticket refers to another. A module that needs an
 * ordering enforces it itself, by deciding when to raise what.
 */
export function instantiateAll(
  subs: readonly Subtask[],
  graph: Graph,
  spawn: Spawn = {},
): Ticket[] {
  return subs.map((s) => instantiateInto(s, graph, spawn).ticket);
}
