// =====================================================================
//  Agent Smith — subtasks and nodes (TypeScript).
//
//  The web-tool port of `crates/agent-smith/src/subtask.rs`. Same object,
//  same guarantees; this is the half of the system a browser can hold.
//
//  A NODE is the convergence of a subtask with the executable code that
//  realises it, and it is the durable object of the system:
//
//      node = ( tau, chunks, values )
//
//  Three properties are load-bearing and are enforced here by construction:
//
//   * IDENTITY IS TAU. Nodes are individuated by subtask identity. Two
//     agents — from the same module or different ones — that decompose their
//     problems and arrive at the same subtask CONVERGE on one node.
//     `Graph.raise` is therefore idempotent under tau: raising an existing
//     subtask accretes chunks and values onto the existing node rather than
//     minting a second one. A node is a meeting point, not a possession.
//
//   * CHUNKS ARE A BAG, AND ALL OF THEM RUN. A subtask can be realised more
//     than one way — say one chunk in one module's DSL and another in a
//     different module's. These are NOT competing candidates to be selected
//     among. There is deliberately no "best chunk" accessor anywhere in this
//     file, because the runtime executes every chunk on a node.
//
//   * VALUES ARE THE ONLY SHARED SURFACE. A module can identify a node, read
//     its values, transform internally, and emit new values. There is no
//     fifth verb. In particular there is no way to ask whether a value is
//     correct, because correctness is not a property the graph represents —
//     the graph stores what WAS emitted, not what should have been. That
//     closure is what keeps adjudication out of this layer and in the
//     consumer where it belongs.
//
//  What this module does NOT do, and must not grow into: it does not execute
//  chunks (that is the OS), it does not judge a value against an expectation
//  (nothing here can), it does not order the graph, and it does not read the
//  content of a chunk. Chunk bodies are opaque strings with a DSL tag.
//  Nothing in this file understands any DSL, and nothing needs to.
// =====================================================================

// ---------------------------------------------------------------------
//  Subtask identity
// ---------------------------------------------------------------------

/**
 * The identity `tau` of a subtask. Nodes are individuated by this and by
 * nothing else: two realisations converge exactly when their `Tau` is equal.
 *
 * It is an opaque string chosen by the raising module. This module never
 * parses it, and deliberately imposes no scheme — the address discipline of
 * the runtime paper is a module-side convention, not a constraint here.
 *
 * Branded so a bare string cannot be passed where a tau is meant.
 */
export type Tau = string & { readonly __tau: unique symbol };

/** Make a `Tau` from a string. */
export function tau(s: string): Tau {
  return s as Tau;
}

// ---------------------------------------------------------------------
//  Chunks
// ---------------------------------------------------------------------

/**
 * One executable realisation of a subtask: a body of DSL source, tagged with
 * which DSL it is written in.
 *
 * The body is opaque. This module does not parse it, validate it, or compare
 * two chunks for preference — it carries it to whoever executes it.
 */
export interface Chunk {
  /**
   * Which DSL the body is written in (e.g. "turbulance", "purpose",
   * "vahera"). Uninterpreted here; meaningful only to a consumer.
   */
  readonly dsl: string;
  /** The source text. Opaque as far as this module is concerned. */
  readonly body: string;
  /**
   * Which module generated this realisation. Provenance, not ownership — a
   * node is not owned by anyone (see `Graph.raise`).
   */
  readonly by?: string;
}

/** Build a chunk. */
export function chunk(dsl: string, body: string, by?: string): Chunk {
  return by === undefined ? { dsl, body } : { dsl, body, by };
}

/** Structural equality, so re-raising an identical realisation is idempotent. */
function sameChunk(a: Chunk, b: Chunk): boolean {
  return a.dsl === b.dsl && a.body === b.body && a.by === b.by;
}

// ---------------------------------------------------------------------
//  Values
// ---------------------------------------------------------------------

/**
 * A value carried on a node: the medium of exchange between modules.
 *
 * A value is whatever a module cares to attach — a measurement, a derived
 * record, a finding, a partial result, or an anomaly. Anomalies are values
 * like any other: a chunk that throws produces an error record which is
 * emitted onto the graph exactly as a numeric result would be. Nothing in
 * this module branches on a value's content, which is what makes
 * run-to-completion structural rather than a policy.
 */
export interface Value {
  /** Which module emitted it. */
  readonly by: string;
  /** A module-chosen key. Uninterpreted here. */
  readonly key: string;
  /** The payload, serialised by the emitter. Opaque. */
  readonly payload: string;
}

/** Build a value. */
export function value(by: string, key: string, payload: string): Value {
  return { by, key, payload };
}

// ---------------------------------------------------------------------
//  The subtask an agent carries
// ---------------------------------------------------------------------

/**
 * A subtask: the instruction, plus the code chunks that are a translation of
 * that instruction into DSL.
 *
 * Both halves travel together. The instruction is the information — what is
 * to be done, in whatever terms the raising module thinks in. The chunks are
 * its realisation. An agent carries this and nothing else about the wider
 * problem: it holds no task identity beyond its own subtask, no position in
 * an ordering, and no knowledge of what came before or comes next, because
 * those fields do not exist on it.
 */
export interface Subtask {
  /** The identity under which this subtask converges with others. */
  readonly tau: Tau;
  /** The instruction — the information half of the subtask. */
  readonly instruction: string;
  /**
   * The realisations — the code half. A bag: order carries no meaning and
   * every chunk is to be executed, none selected over another.
   */
  readonly chunks: readonly Chunk[];
}

/**
 * Build a subtask. A subtask may legitimately have no chunks — it has been
 * raised but not yet realised (a code-generating module converges a chunk
 * onto the same tau later).
 */
export function subtask(
  id: Tau | string,
  instruction: string,
  chunks: readonly Chunk[] = [],
): Subtask {
  return { tau: id as Tau, instruction, chunks: [...chunks] };
}

/** A copy of `s` with `c` appended to its chunk bag. */
export function withChunk(s: Subtask, c: Chunk): Subtask {
  return { ...s, chunks: [...s.chunks, c] };
}

/** A copy of `s` with several realisations appended. */
export function withChunks(s: Subtask, cs: readonly Chunk[]): Subtask {
  return { ...s, chunks: [...s.chunks, ...cs] };
}

/** Whether any realisation exists yet. */
export function isRealised(s: Subtask): boolean {
  return s.chunks.length > 0;
}

// ---------------------------------------------------------------------
//  The node
// ---------------------------------------------------------------------

/**
 * A node of the causal knowledge graph: `(tau, chunks, values)`.
 *
 * The node is the durable object. It is not owned by the agent or module
 * that first raised it: because the subtask individuates it and many agents
 * converge on the same subtask, a node accretes chunks and values from every
 * agent that reaches it.
 */
export class Node {
  readonly tau: Tau;
  /**
   * The instructions raised against this tau, in raise order. Usually one,
   * but two modules may phrase the same subtask differently and still
   * converge — both phrasings are kept, since neither is authoritative.
   */
  readonly instructions: string[] = [];
  /** The chunk bag. Every chunk is a co-resident realisation; all run. */
  readonly chunks: Chunk[] = [];
  /** The values carried, in emit order. */
  readonly values: Value[] = [];

  constructor(id: Tau) {
    this.tau = id;
  }

  /**
   * Read the values on this node. One of the four verbs.
   *
   * There is deliberately no companion that reports whether a value is
   * correct or expected: the graph stores what was emitted, not what should
   * have been.
   */
  read(): readonly Value[] {
    return this.values;
  }

  /** Read only the values emitted by a given module. */
  readBy(module: string): Value[] {
    return this.values.filter((v) => v.by === module);
  }

  /** Read only the values under a given key. */
  readKey(key: string): Value[] {
    return this.values.filter((v) => v.key === key);
  }

  /** Emit a value onto this node. One of the four verbs. */
  emit(v: Value): void {
    this.values.push(v);
  }

  /**
   * The chunks written in a given DSL. A filter for a consumer that can only
   * run one DSL — still not a selection among competing candidates.
   */
  chunksIn(dsl: string): Chunk[] {
    return this.chunks.filter((c) => c.dsl === dsl);
  }

  /** The distinct DSLs realised on this node. */
  dsls(): string[] {
    const out: string[] = [];
    for (const c of this.chunks) if (!out.includes(c.dsl)) out.push(c.dsl);
    return out;
  }
}

// ---------------------------------------------------------------------
//  The graph
// ---------------------------------------------------------------------

/** What `raise` did: minted a new node, or converged onto an existing one. */
export type Raised = "created" | "converged";

/**
 * The shared node medium: the set of distinct subtasks that agents have
 * raised, each carrying its chunk bag and its values.
 *
 * Note what is absent: there is no edge set. A causal edge — "a value
 * emitted at u was read at v" — exists only once the reading has happened,
 * so it is a product of a run, not an input to it. Storing edges here would
 * be storing a schedule, and the trajectory is not storable as a plan.
 */
export class Graph {
  /** Insertion-ordered by construction, so iteration is stable across runs. */
  private readonly byTau = new Map<Tau, Node>();

  /**
   * Publish a subtask as a node.
   *
   * Idempotent under tau: raising a subtask that already exists merges its
   * chunks and instruction onto the existing node rather than creating a
   * second. This is convergence, and it is the norm rather than the
   * exception, because different problems share sub-structure.
   *
   * Duplicate chunks (same DSL, same body, same author) are not appended
   * twice — re-raising an identical realisation is not a second realisation.
   * Distinct realisations always co-reside.
   */
  raise(s: Subtask): Raised {
    let node = this.byTau.get(s.tau);
    const existed = node !== undefined;
    if (!node) {
      node = new Node(s.tau);
      this.byTau.set(s.tau, node);
    }
    if (!node.instructions.includes(s.instruction)) {
      node.instructions.push(s.instruction);
    }
    for (const c of s.chunks) {
      if (!node.chunks.some((existing) => sameChunk(existing, c))) {
        node.chunks.push(c);
      }
    }
    return existed ? "converged" : "created";
  }

  /** Identify a node by subtask identity. One of the four verbs. */
  identify(id: Tau | string): Node | undefined {
    return this.byTau.get(id as Tau);
  }

  /**
   * Emit a value onto the node bearing `tau`. Returns false if no such node
   * has been raised.
   */
  emit(id: Tau | string, v: Value): boolean {
    const node = this.byTau.get(id as Tau);
    if (!node) return false;
    node.emit(v);
    return true;
  }

  /** All nodes, in raise order. */
  nodes(): Node[] {
    const out: Node[] = [];
    this.byTau.forEach((n) => out.push(n));
    return out;
  }

  /** How many distinct subtasks have been raised. */
  get size(): number {
    return this.byTau.size;
  }

  /**
   * A plain snapshot, for rendering or for handing to the OS. A projection,
   * not a second representation: nothing is computed here that the nodes do
   * not already carry, and no ordering is imposed beyond raise order.
   */
  snapshot(): Array<{
    tau: string;
    instructions: string[];
    chunks: Chunk[];
    values: Value[];
    dsls: string[];
  }> {
    return this.nodes().map((n) => ({
      tau: n.tau as string,
      instructions: [...n.instructions],
      chunks: [...n.chunks],
      values: [...n.values],
      dsls: n.dsls(),
    }));
  }
}
