# Musande Integration

**Status:** long-grass-side contract for the `musande` agent runtime.
**Depends on:** `docs/sources/split-attention-synchronised-agents.tex`
(the theoretical spec musande implements), and its three companion papers
(`non-playing-character-purpose.tex`, `non-playing-character-physiology.tex`,
`embedded-agent-mechanics.tex`).

This document is the specification of what long-grass expects `musande` to
be, how long-grass will consume it, and — critically — what long-grass
promises to preserve on its side so that musande's four runtime invariants
(§7 of the paper) actually hold. It is a two-way contract, not a
one-sided ask.

Every design choice in what follows is grounded in a numbered theorem or
invariant from the paper; each is cited at the point it lands.

---

## 0. What musande is, in one line

Musande is the runtime that instantiates the split-attention synchronised
agents of the paper — persistent, conserved-identity, purpose-directed,
attention-dividing, phase-alternating, coordination-capable characters —
as a first-class part of Buhera OS.

It is not a chatbot library, a task-planner, or an "agent framework" in
the RAG-plus-tools sense. It is the implementation of the four runtime
invariants (I1 conserved identity, I2 never-resetting count, I3
search-not-fetch, I4 phase exclusion) plus the water-filling attention
scheduler and the Kuramoto phase-lock loop, exposed as a package
long-grass can consume.

An agent (from long-grass's point of view) is:

- a **conserved identity** (`Char(A)`, the character invariant of §3)
- a **purpose** (the attractor of a strongly convex drive, §4)
- an **attention budget** (`α`, divided across scenes by water-filling
  under a single price `p★`, §4)
- a **monotone committed count** (`m`, never decremented, §6)
- a **self-graph** searched fresh on every response (§6)
- a **phase** (either constructing or committing, never both, §5)
- optionally, a **coupling** to other agents via Kuramoto (§8)

The user sees townspeople; the runtime sees these six fields.

---

## 1. Package identity

- **Name:** `@buhera/musande`
- **Language:** TypeScript, published with `.d.ts` types
- **Distribution:** vendored under `long-grass/vendor/musande/` (the same
  path pattern we use for `@buhera/purpose`, `@lavoisier/shapeshifter`,
  `scope-lang`). Not published to npm at v0. Consumed via `file:`
  specifier in `package.json`.
- **Runtime targets:** browser (Next.js client bundle) primarily; Node
  (for the `/api/musande` server route) as a subpath export if any
  server-only helpers are needed.
- **Dependencies:** should be minimal. The paper's numerics need only
  strongly-convex optimisation, KKT bisection, and Kuramoto ODE
  integration — all writable in ~200 lines each with no external deps.
  If musande takes a dep on an LLM SDK, that dep MUST be optional and
  loadable only server-side.
- **License:** whatever the rest of the Buhera stack uses.

---

## 2. Versioning contract

Same as purpose:

- Semver. long-grass pins to `^0.x` pre-1.0.
- **Before 1.0:** minor bumps may break shapes; CHANGELOG expected.
- **At 1.0.0:** the API surface in §4 is locked. Additions are minor
  bumps. Shape changes are major bumps.

---

## 3. Non-negotiable design principles

These follow directly from the paper's four invariants and its
interpretation firewall (§7.4). If musande violates any of them, the
guarantees the paper's theorems certify no longer hold on this
deployment.

1. **Musande is an agent-runtime library, not a chat framework.** It has
   no notion of "conversation," "prompt template," "system message," or
   "tool calling." Those are caller policy. Musande operates on
   `Interaction`, `Scene`, `Response`, `SelfGraph`, `Drive`, and
   `Phase` — the paper's vocabulary.

2. **Musande owns the four invariants.** Every operation musande exposes
   preserves them by construction. A caller cannot lower `m`, cannot
   fetch a cached answer, cannot violate phase exclusion, cannot mutate
   the identity invariant. Musande enforces this; long-grass does not
   need to police it.

3. **The self-graph is content-agnostic.** Just as `@buhera/purpose`
   accepts `terms: Set<string>` without caring what they mean, musande
   accepts `parts: Set<PartId>` and `separations: [PartId, PartId, cost]`
   without caring what a part represents. Long-grass supplies parts
   (from vahera state, audit-log entries, LLM-extracted concepts —
   long-grass's choice); musande maintains the graph and computes
   `Char`.

4. **Search is caller-implementable.** The recognition-search identity
   (§6, Theorem 6.3) says every response is a fresh walk on the
   self-graph. Musande provides the walk primitives; the actual
   "search step" — what happens when the walk touches a part — is a
   callback musande invokes with the current partial context. Long-grass
   plugs the LLM in there via the shared cascade
   (`src/lib/server/llm-cascade.js`).

5. **The interpretation firewall (§7.4) is preserved.** Every musande
   method has a predicate name from the paper: `commit()`, `carry()`,
   `alternate()`, `waterFill()`, `phaseCouple()`. No method is named
   after an interpretive category (`lie`, `gossip`, `ask`, `distract`,
   `remember`). Those behaviours arise from the invariants; they are
   not implemented as such.

6. **Errors are typed, never thrown from the core.** An agent asked to
   commit while in the construction phase returns
   `{ok: false, error: 'phase-exclusion-violation'}` rather than
   throwing. Same discipline as purpose. Programmer errors (wrong
   argument shape) may throw.

7. **LLM calls happen through a caller-supplied hook, not inside the
   library.** Musande NEVER contains a `fetch` to `openai.com` or
   `googleapis.com`. It calls the caller's `think(prompt, options)`
   function. Long-grass implements that hook by routing through
   `chatCascade`. This keeps musande browser-safe by default, keeps
   provider selection centralized, and — most importantly — lets us swap
   the LLM backend without musande knowing.

---

## 4. The public API (locked at 1.0)

### 4.1 Types

```typescript
/** Opaque caller-chosen identifiers. */
export type AgentId = string;
export type PartId = string;
export type SceneId = string;
export type ActId = number;             // monotone within an agent

/** A single distinction the agent draws within itself (§2). */
export interface Part {
  id: PartId;
  /** Opaque caller data. Musande never inspects. */
  payload?: unknown;
}

/** A cost of holding two parts apart. Must be > 0 (Ax. costly). */
export type Separation = { a: PartId; b: PartId; cost: number };

/** The self-graph Γ. */
export interface SelfGraph {
  parts: ReadonlyArray<Part>;
  separations: ReadonlyArray<Separation>;
}

/** The disposition space B is R^n; a point is a coordinate vector. */
export type Disposition = ReadonlyArray<number>;

/**
 * A drive potential Φ. Strongly convex, C^1 (§4). The caller
 * supplies Φ(x) and ∇Φ(x); musande handles the descent.
 */
export interface Drive {
  /** Strong-convexity constant λ > 0. */
  lambda: number;
  potential: (x: Disposition) => number;
  gradient: (x: Disposition) => Disposition;
}

/** An outward context the agent may act in (§2). */
export interface Scene {
  id: SceneId;
  /**
   * Gain profile γ(a): purpose residual removed per unit attention a.
   * Nondecreasing; if concave (Ax. concave, §2), water-filling is
   * optimal; otherwise the scheduler is heuristic (§7.2).
   */
  gain: (a: number) => number;
  /** ∂γ/∂a, needed by the water-filling bisection. */
  marginalGain: (a: number) => number;
  /** γ'(0), the marginal gain at zero attention. */
  marginalGainAtZero: number;
}

/** An interaction addressed to the agent (§4 of physiology paper). */
export interface Interaction {
  id: string;
  scene: SceneId;
  /** Opaque content the caller extracted terms/concepts from. */
  payload: unknown;
  /** Terms drawn from the interaction; feeds the self-graph. */
  parts: ReadonlyArray<PartId>;
}

/** The result of a committed act (§4 of physiology paper). */
export type Response =
  | {
      ok: true;
      scene: SceneId;
      /** The disposition after the act. */
      disposition: Disposition;
      /** The new committed count (m + 1). */
      count: ActId;
      /** Purpose gain g removed by this response. */
      gain: number;
      /** Content the caller supplied via `think()`. */
      content: unknown;
    }
  | {
      ok: false;
      error:
        | { kind: 'phase-exclusion-violation' }
        | { kind: 'irrelevant'; reason: string }
        | { kind: 'incoherent'; margin: number }
        | { kind: 'budget-exhausted'; price: number }
        | { kind: 'no-admissible-response' };
    };

/** Phase (§5). */
export type Phase = 'construction' | 'commitment';

/**
 * The caller-supplied "search step". Musande calls this while walking
 * the self-graph to produce a response. Long-grass plugs the LLM here.
 */
export interface ThinkHook {
  (input: {
    interaction: Interaction;
    walk: ReadonlyArray<PartId>;
    disposition: Disposition;
    purpose: Disposition;
  }): Promise<{ content: unknown; nextDisposition: Disposition }>;
}

/** Config for constructing an Agent. */
export interface AgentConfig {
  id: AgentId;
  vocation: string;                     // free-form label, for UI only
  selfGraph: SelfGraph;
  drive: Drive;
  attentionBudget: number;              // α > 0
  actFloor: number;                     // β_a > 0
  distinctionFloor: number;             // β > 0
  /** Initial phase; construction is the honest default (§5). */
  phase?: Phase;
  /** Kuramoto intrinsic velocity ω_j (§8). Defaults to 0. */
  phaseVelocity?: number;
  /** Persisted snapshot for hot reload. */
  snapshot?: AgentSnapshot;
}

/** Result of a carry (§4 of purpose paper analogue): what context to
 * apply for a scene. */
export interface Carry {
  scene: SceneId;
  keep: ReadonlyArray<PartId>;
  dropped: ReadonlyArray<PartId>;
  allocation: number;                   // a_i at this scene
  price: number;                        // p★
}

/** A snapshot of the whole runtime state, for persistence. */
export interface AgentSnapshot {
  version: 1;
  config: Omit<AgentConfig, 'snapshot' | 'drive'>;
  count: ActId;
  disposition: Disposition;
  phase: Phase;
  /** Musande-internal; caller treats as opaque. */
  internal: unknown;
}
```

### 4.2 The Agent class

```typescript
export class Agent {
  constructor(config: AgentConfig, think: ThinkHook);

  /** Read-only inspectors (§7.1 invariants). */
  readonly id: AgentId;
  readonly vocation: string;
  count(): ActId;                       // I2: monotone
  characterInvariant(): number;          // I1: Char(A), conserved
  phase(): Phase;                       // I4: exactly one at each instant
  purpose(): Disposition;               // §4: attractor of the drive
  disposition(): Disposition;
  attentionPrice(): number;             // p★, latest water-filling result

  /** Present an incoming interaction. Musande decides:
   *   (a) is it relevant (two-factor test, §4 of physiology paper)?
   *   (b) if yes, does the current phase allow a commit (§5)?
   *   (c) if yes, run the search (§6) via the think hook, produce a
   *       Response, increment the count, return it.
   * Never throws for graph reasons; returns typed errors on Response. */
  present(interaction: Interaction): Promise<Response>;

  /** Compute the carry for a specific scene under the current budget
   *  (§4 water-filling + §3 identity). Called by long-grass before
   *  present() to know which parts of the self-graph to hand the
   *  think hook. */
  carry(scene: SceneId, budget?: number): Carry;

  /** Divide attention across all currently-attended scenes (§4). */
  waterFill(scenes: ReadonlyArray<Scene>): {
    allocations: Map<SceneId, number>;
    price: number;
  };

  /** Advance one phase-alternation step (§5). Musande decides
   *  internally whether to construct or commit next; caller may hint. */
  alternate(hint?: Phase): void;

  /** Feed a new distinction into the self-graph. Only allowed in the
   *  construction phase (I4); returns false and does not mutate
   *  otherwise. */
  learn(parts: ReadonlyArray<Part>, separations: ReadonlyArray<Separation>):
    boolean;

  /** Kuramoto step for coordination (§8). Called by a Town when
   *  agents share a scene. */
  couple(meanPhase: number, orderParameter: number, K: number, dt: number):
    void;

  /** Serialize for persistence. Round-trip preserves count and identity. */
  snapshot(): AgentSnapshot;

  /** Reconstruct from a snapshot. Static factory. */
  static fromSnapshot(snapshot: AgentSnapshot, think: ThinkHook): Agent;
}
```

### 4.3 The Town class (society, §7)

```typescript
export interface TownConfig {
  id: string;
  agents: ReadonlyArray<Agent>;
  /** Inter-agent separations (§7): what holds agents apart, and at
   *  what cost. Optional; defaults to none. */
  ties?: ReadonlyArray<{ a: AgentId; b: AgentId; cost: number }>;
  /** Kuramoto coupling K for phase-locking (§8). */
  coupling: number;
  /** Society drive Φ_Σ (§7.4). Optional; if absent, the society has
   *  identity but no attractor of its own. */
  drive?: Drive;
}

export class Town {
  constructor(config: TownConfig);

  addAgent(agent: Agent): void;
  removeAgent(id: AgentId): boolean;
  agents(): ReadonlyArray<Agent>;
  agent(id: AgentId): Agent | null;

  /** Character of the society (§7 Cor. 7.2), conserved under relabel. */
  characterInvariant(): number;

  /** Kuramoto order parameter (§8). */
  orderParameter(): { R: number; psi: number };

  /** Cost of a shared act under current phases (§8, Thm 8.2). */
  coordinationCost(): number;

  /** Run the Kuramoto coupling one step (Alg. Sync in the paper). */
  synchronise(dt: number): void;

  /** Optimal division of collective attention across shared purposes
   *  (§7.4, Thm 7.7). */
  waterFillSociety(
    scenes: ReadonlyArray<Scene>,
    budget: number,
  ): { allocations: Map<SceneId, number>; price: number };

  snapshot(): TownSnapshot;
  static fromSnapshot(snap: TownSnapshot, think: ThinkHook): Town;
}
```

### 4.4 Pure operators (exported for tests, for lightweight callers)

```typescript
export function characterInvariant(graph: SelfGraph): number;
export function orderParameter(phases: ReadonlyArray<number>):
  { R: number; psi: number };
export function coordinationCost(R: number, lambda: number): number;
export function waterFill(
  scenes: ReadonlyArray<Scene>,
  budget: number,
  epsilon?: number,
): { allocations: Map<SceneId, number>; price: number };
export function kuramotoStep(
  phases: ReadonlyArray<number>,
  velocities: ReadonlyArray<number>,
  K: number,
  dt: number,
): { phases: number[]; R: number; psi: number };
```

### 4.5 Exports summary

The package's root `index.ts` exports exactly:

- **Types:** `AgentId`, `PartId`, `SceneId`, `ActId`, `Part`,
  `Separation`, `SelfGraph`, `Disposition`, `Drive`, `Scene`,
  `Interaction`, `Response`, `Phase`, `ThinkHook`, `AgentConfig`,
  `Carry`, `AgentSnapshot`, `TownConfig`, `TownSnapshot`.
- **Classes:** `Agent`, `Town`.
- **Pure operators:** `characterInvariant`, `orderParameter`,
  `coordinationCost`, `waterFill`, `kuramotoStep`.

Nothing else is public. Internal graph structures, integrators, and KKT
solvers are not part of the public surface.

---

## 5. Behavioural guarantees (what long-grass tests against)

Every claim below cites the theorem in the paper that makes it true.
Long-grass will maintain integration tests that assert each on real
runtime instances.

1. **Character conserved (I1, Thm 3.2).** For any Agent `A`, applying a
   weight-preserving relabelling of `A.selfGraph.parts` leaves
   `A.characterInvariant()` unchanged to floating-point precision.
2. **Count monotone (I2, Thm 6.2).** `A.count()` is nondecreasing across
   any sequence of `present()` calls. No API path lowers it.
3. **Distinct copies (Thm 6.2(iii)).** For agents `A`, `A'` with
   identical config but `A.count() > 0`, `A.snapshot()` and
   `A'.snapshot()` are unequal in the count field regardless of
   disposition.
4. **Search-not-fetch (I3, Thm 6.3).** Every `present()` call whose
   response has `ok: true` invokes `think()` exactly once, against the
   agent's current self-graph. There is no code path that returns a
   Response with `ok: true` without invoking `think()`.
5. **Phase exclusion (I4, Thm 5.1).** For any Agent `A`, at any instant
   `A.phase()` returns exactly one of `'construction' | 'commitment'`,
   and `A.learn(...)` returns `false` while in commitment;
   `A.present(...)` returns `{ok: false, error: 'phase-exclusion-violation'}`
   while in construction.
6. **Floor holds (Thm 2.1).** For every Agent `A`, every nonempty proper
   subset `U` of parts has boundary cost `≥ A.distinctionFloor`.
7. **Water-fill KKT (Thm 4.2).** For any set of concave-profile Scenes
   under a finite budget, `waterFill()` returns allocations whose
   marginal gains at attended scenes are equal to a single price `p★`,
   to floating-point precision.
8. **Kuramoto locks above threshold (Thm 8.3).** For a Town with
   coupling `K > K_c = O(Δω)`, iterating `synchronise(dt)` drives
   `orderParameter().R → 1` and `coordinationCost() → 0`. Below `K_c`,
   `R` stays near 0.
9. **Snapshot round-trip.** For any Agent `A`,
   `Agent.fromSnapshot(A.snapshot(), think)` produces an agent whose
   future `present()` results are identical to `A`'s.

---

## 6. What's deferred (deliberately)

Long-grass does NOT depend on any of the following in v1. Musande is
free to add them as minor releases.

- **Multi-basin drives** (agents torn between competing purposes).
  Strong convexity is the paper's assumption; single-basin is enough.
- **Drives that change over time** as history accumulates.
- **A search algorithm richer than a shortest-path walk** on the
  self-graph. The `think` hook is where richness lives; the walk is a
  scaffold.
- **Exact minimum-cut via max-flow** for identity computation. A
  near-linear heuristic is acceptable if it agrees with the exact
  value on the test suite.
- **A default LLM binding.** The think hook is required; no default
  provided by musande.
- **Multi-agent negotiation protocols** beyond Kuramoto sync.
- **A UI.** Rendering is long-grass's job.

---

## 7. Non-goals

Explicitly outside the scope of musande, even as future work:

- LLM SDK dependencies of any kind (all LLM work goes through the
  caller-supplied `think` hook).
- Content storage (musande operates on `PartId`s and opaque payloads).
- A prompt template library.
- Vector search or embedding infrastructure.
- Anything the interpretation firewall (§7.4) prohibits: named methods
  for "lying", "gossip", "questioning", "distraction", etc.

If any of these appear in the package, long-grass refuses the upgrade.

---

## 8. Integration surface in long-grass

Once musande ships, long-grass will add these files. All are
long-grass's own; the package's public surface stays untouched.

### 8.1 `src/lib/agents/registry.js`

An agent registry parallel to the module registry. Same trait:

```js
export const _agents = new Map();      // AgentId → Agent
export function registerAgent(agent);
export function unregisterAgent(id);
export function listAgents();
export function getAgent(id);
```

Agents can be born (via `registerAgent`), die (via `unregisterAgent`),
persist across sessions (via `Agent.snapshot()` → localStorage), and be
reconstructed on page load.

### 8.2 `src/lib/agents/town.js`

A single global `Town` singleton per page. Every registered agent joins
it. Users see the town via `:town` in the terminal or a dedicated
`/town` page (§10).

### 8.3 `src/lib/agents/think-hook.js`

The `ThinkHook` implementation that plugs musande into the LLM cascade.

```js
export const longGrassThinkHook = async ({ interaction, walk, disposition, purpose }) => {
  // Compose a prompt from the walk over the self-graph and the
  // interaction payload. Send through the shared cascade.
  const res = await fetch('/api/musande-think', {
    method: 'POST',
    body: JSON.stringify({ interaction, walk }),
  });
  const body = await res.json();
  return { content: body.content, nextDisposition: /* projected */ };
};
```

### 8.4 `src/pages/api/musande-think.js`

The server route the think hook calls. Wraps `chatCascade`, keeps API
keys server-side, respects the same cascade order as the rest of
long-grass (Ollama → Gemini → HF → OpenAI).

### 8.5 `src/lib/agents/scenes.js`

Long-grass's mapping from **modules to scenes**. Each module in the
federation is presented to agents as a scene with a gain profile.
Concretely: `shapeshifter` becomes a "workshop" scene the smith-agent
attends; `vahera` becomes an "archive" scene the scribe-agent attends;
etc. The gain profile is caller policy — long-grass picks concave
profiles by default (Ax. concave holds).

### 8.6 `src/lib/agents/audit-feeder.js`

A post-dispatch hook, same shape as the purpose feeder. Every dispatch
in the federation becomes an `Interaction` presented to every agent
whose scene set includes the dispatched module. Agents decide
individually whether the interaction is relevant to them (§4 of
physiology paper). Most decline; some commit.

### 8.7 `src/pages/town/index.js` and `src/pages/town/[agent].js`

New public routes:

- `/town` — lists every registered agent with vocation, phase, current
  attention price `p★`, and a "last committed act" summary. This is
  the "townspeople" panel from the pitch.
- `/town/[agent-slug]` — a page for one agent. Shows their self-graph
  (rendered), their purpose, their recent history, and a form to
  directly address them with an interaction.

Both are client-side (`ssr: false`), because agents live in browser
memory (with snapshot persistence).

### 8.8 Terminal integration

- `:town` meta command opens `/town` in a new tab.
- A small "townspeople: N" indicator in the terminal chrome, showing
  how many agents are currently instantiated.
- No changes to the existing dispatch / registry / audit-log surfaces.

---

## 9. The rerun primitive: how it interacts with agents

Long-grass has added (or will add) a `rerun(actId)` primitive to the
module registry (see the running conversation). This composes with
musande naturally:

- Rerunning act #47 (which was originally dispatched by user or by
  agent X) creates a new act #248.
- **If #47 was authored by an agent**, the rerun goes back to that
  agent's `present()` — with a fresh interaction that references the
  original one. The agent may respond differently because its
  self-graph has grown (§6 Thm 6.3). This is the paper's
  "same query, different act" prediction on real data.
- **Standing intents** (per the pitch: the archivist audits daily) are
  implemented as agents subscribing to a cron and repeatedly running
  their own `present(interaction)` on a scheduled interaction. Each
  produces a new act; each is honest about being a rerun (its
  `interaction.id` references the standing intent).

Musande needs no special support for this. Long-grass wires it.

---

## 10. Long-grass smoke test (the "sufficient test")

The passing criterion for musande integration is:

```
:town
```

opens a page showing at least three agents (say: "smith", "scribe",
"crier"), each with a vocation, a phase, and a purpose summary.

Then in the terminal:

```
memory store "iron-order" = "I need three horseshoes by Friday"
```

The vahera dispatch fires; the audit-feeder converts it to an
`Interaction`; every agent's `present()` is called; the smith responds
(it's in scene "workshop" for shapeshifter-style tasks; the
`iron-order` interaction is relevant to its purpose); the scribe and
crier decline (not relevant to their purposes). The smith's response
appears in the terminal AS AN AGENT-INITIATED ACT, tagged with the
smith's id, at a new committed count.

Then:

```
memory store "iron-order-2" = "another two horseshoes for the same customer"
```

Same flow; the smith commits again. `A.count()` for the smith is now 2.

Then, some time later or after the smith has learned more:

```
:rerun <act-id-of-first-iron-order>
```

The smith's `present()` fires against the same interaction. Its
self-graph has grown (two orders now instead of one). The response
differs — perhaps the smith quotes a bulk discount, or notes it's
already committed for Friday. Two responses, both correct, at different
`count`s. That is the paper's Thm 6.3 running end-to-end.

If that flow works, the integration is done.

---

## 11. Open questions musande owns

These are decisions long-grass explicitly hands to musande. Any choice
is fine; long-grass consumes whatever musande picks.

- The internal graph representation (adjacency list vs. matrix vs.
  incidence).
- The specific max-flow / min-cut algorithm used for the character
  invariant (or a near-linear heuristic).
- The ODE integrator for Kuramoto (explicit Euler is fine; RK4 is
  fine).
- The bisection tolerance ε for water-fill (10^-6 is fine).
- Whether snapshots are JSON or MessagePack (as long as `fromSnapshot`
  accepts what `snapshot()` produces).
- Whether the `think` hook is called with the whole walk or just the
  current-part context (either works; long-grass will adapt).

---

## 12. Change management

- Changes to §4 (public API) or §5 (behavioural guarantees) are
  coordination points. Musande posts a proposal; long-grass reviews and
  either accepts (with a version bump and migration note) or rejects.
- Changes to §6 (deferred) or §11 (musande-owned) are musande's call
  alone.
- If musande needs a new caller-side capability long-grass doesn't
  currently supply (a new hook, a new API route, access to some
  runtime state), musande adds an issue in the long-grass repo; the
  addition happens in a shim under `src/lib/agents/` so the musande
  package stays clean.

---

## 13. What lands unconditionally, and what depends on the environment

Per §7.2 of the paper, three of musande's four invariants
(I1 identity, I2 count, I3 search, I4 phase) are unconditional — they
hold in any environment long-grass can present. The fourth guarantee,
optimal water-filling attention division, is conditional on the scenes
being concave (Ax. concave).

Long-grass commits to configuring scenes with concave gain profiles by
default (`src/lib/agents/scenes.js`). Users authoring their own scenes
via advanced APIs (a future capability, not v0) may violate concavity;
in that case musande's scheduler becomes a heuristic rather than
optimal, and long-grass will flag this in the scene registration path.
Musande has no obligation to detect or enforce concavity.

---

## 14. What this integration UNBLOCKS

Once musande lands:

- **The town becomes a first-class OS surface.** Users see, not modules
  and dispatches, but townspeople doing their work.
- **The four papers stop being theory in `docs/sources/` and become the
  runtime.** Every phenomenon predicted — gossip drift, forced
  questioning, in-character replies, present-but-preoccupied
  attention, phase-locked crowd sharpening — is a testable property of
  the deployed system.
- **The rerun primitive earns its keep.** Rerunning an agent-authored
  act genuinely returns a different answer because the agent's
  self-graph has grown, not because the model got warmer.
- **The Uni Greifswald pitch has a concrete demo.** "This is my
  workshop; the mass-spec smith spent the morning preparing runs
  against the corpus you sent yesterday. Watch what happens when I
  commission a fresh analysis." That story exists only once musande is
  in.
- **Modules stop being the thing users address.** They become the
  workshops townspeople use to do their work. Users address
  townspeople. This is the "operating system" claim finally earning
  itself: an inhabited town, not a toolshop.

---

## 15. Timeline expectations (informational, not contractual)

- Long-grass will do zero prep work until the first musande release
  is available. Everything in §8 will happen in one focused session
  when the package lands, same pattern as `@buhera/purpose`.
- When musande's v0.1 is ready, long-grass ships the vendor,
  registration, hooks, and pages together, and reports back.

The current OS state (twelve modules registered, purpose-carry live,
tutorials with runnable cells, Vercel deployment green) is a coherent
stopping point until musande arrives.
