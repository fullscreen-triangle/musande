# Agent Smith — `smith` CLI + `agent-smith` crate

Agent Smith is the runnable core of the **split-attention synchronised-agents**
paper (`epistemology/split-attention-synchronised-agents/`): a small DSL for
bounded agents and societies, and a tick-loop that drives them. This crate is the
Rust port of the JavaScript engine in `web/src/lib/agent-smith/` — a **library**
other projects embed, plus an installable **`smith`** binary, in the same spirit as
`purpose`: drop-in, offline, deterministic.

The four invariants of the paper are honoured by construction:

- **I1 identity** — `χ(A)`, a conserved, non-local graph invariant (min inter-part cut).
- **I2 count** — a monotone committed count that never resets.
- **I3 search** — the agent stores no answers; it re-reads the shared state each tick.
- **I4 phase** — construction and commitment never share an instant.

The engine is deterministic everywhere except one seam — the domain judgment (a model
call). That seam is the `Hook` trait; the bundled `DeterministicHook` runs the whole
thing offline, so `smith` needs no network and no provider.

## The DSL (concrete surface)

```
agent smith {
  purpose minimise forge_residual        // character: standing purpose, runs on
  scenes {
    scene hammer serves forge_residual with forge_hook
  }
  self {
    parts { skill, stock, orders, reputation }
    separations { (skill, stock: 3), (stock, orders: 2),
                  (orders, reputation: 2), (reputation, skill: 2) }
  }
  budget 1.0
  floor  2.0
  coherence keeps { reputation, skill }
}
```

`purpose reach <outcome>` makes a **task-agent** that halts at quiescence instead of a
standing character. A `society <id> { agent … tie (a, b: cost) … couple <K> }` wraps
several agents that meet only in a shared outcome-space.

## CLI

```bash
smith check <file.smith>                 # parse + typecheck; print χ / floor / regime
smith run   <file.smith> [--ticks N] [--json]   # build + drive the tick-loop
smith show  [town|task]  [--ticks N] [--json]   # run a bundled example end-to-end
smith --version
```

- `check` reports, per agent, its `regime` (character | task), `χ`, realised `floor`,
  and whether `χ` is non-local — or the type errors with line numbers.
- `run` / `show` print a per-tick table (or `--json`): agent, outcome
  (commit | observe | decline | quiescent), attention price, residual, delta, count, scene.
- Exit codes: `0` OK, `1` build/type errors, `2` I/O error.

## Library

```rust
use agent_smith::{build, make_town, run_town, Ctx};

let built = build(source);                       // parse → typecheck → compile
let mut town = make_town(built.program.unwrap());
let ctx = Ctx::deterministic();                  // offline; or Ctx::with_hook(Box::new(MyHook))
let history = run_town(&mut town, &ctx, 30);     // Vec<StepResult>
```

Plug a model in by implementing `Hook` (`run` for the domain work, `judge_sufficiency`
for the tier-1 gate) and passing `Ctx::with_hook(...)` — exactly where the JS
`providers.think` sat. The crate itself ships no domain answers, only the seam.

## Build & test

The crate is a member of the musande Cargo workspace:

```bash
cargo build -p agent-smith               # library + smith binary
cargo test  -p agent-smith               # fidelity tests (χ witness, water-filling, runtime)
cargo install --path crates/agent-smith --bin smith   # put `smith` on PATH, like purpose
```

Fidelity tests cross-check the port against the JS engine and the paper's own witnesses:
the two-triangle `χ = 2` non-local identity, water-filling's single price, `hash_unit`
parity, monotone-history quiescence, and the pure-observer ("penguin-watcher") case.
