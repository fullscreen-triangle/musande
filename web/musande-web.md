# Installing the Musande Web Tool into Buhera OS

How to link the **Agent Smith** engine and its **sandbox** (this `web/` project) into
the Buhera operating system as a vendored TypeScript/JavaScript OS module — the same way
`long-grass` consumes `@lavoisier/shapeshifter`, `@buhera/purpose`, and `@buhera/pylon`.

This is a working reference, not a marketing document. Every path and command below is
real and has been checked against the actual repositories.

---

## 0. What this project actually contains

Two separable things live under `web/`:

| Layer | Files | Nature | Buhera wants this? |
|---|---|---|---|
| **Engine** | `web/src/lib/agent-smith/*.js` | Pure JS, **zero runtime dependencies**, framework-agnostic. The DSL pipeline `parse → typecheck → compile → tick/town`, the identity math (χ, water-filling, realised floor), the four invariants. | **Yes** — this is the reusable OS module. |
| **Sandbox UI** | `web/src/sandbox/*.js`, `web/src/pages/sandbox.js` | React + Next Pages-router + Zustand. The VS-Code-style shell, the raw-SVG crossfilter charts, the economic-skin scripts. | Only if Buhera hosts a Next web surface. Optional. |

The engine is the payload. It is deliberately shaped like `@lavoisier/shapeshifter`:
**pure JavaScript, no runtime deps, `type: module`, framework-agnostic** — so it vendors
into any bundler-backed host with no build step. The sandbox is a *reference consumer* of
that engine, useful as a copy-paste template but not required by the OS.

### The one gotcha that governs everything below

The engine's internal imports are **extensionless**:

```js
// web/src/lib/agent-smith/compile.js
import { logGain } from "./identity";     // NOT "./identity.js"
import { typecheck } from "./typecheck";
import { parse } from "./parse";
```

There are **19** such imports across the engine. This matters:

- **Webpack / Next / Vite / esbuild** resolve `./identity` → `./identity.js` automatically.
  Vendoring into a bundler-backed host (Next, the Buhera web surface, `long-grass`) **just
  works**.
- **Node's native ESM resolver** and **`tsc` under `moduleResolution: NodeNext`** do **not**
  add the extension. Running the engine under raw Node (a CLI, a test runner without a
  bundler, a `purpose-kernel` subprocess) requires either an `exports`-mapped build step or
  an extension rewrite. See §4.

Pick your integration path in §2 by asking one question: **does the host bundle its JS?**

---

## 1. The Buhera vendoring convention (how `long-grass` does it)

Buhera's TypeScript OS modules are linked as **local `file:` dependencies pointing at a
`vendor/` directory**. From `long-grass/package.json`:

```jsonc
"dependencies": {
  "@buhera/purpose":        "file:./vendor/purpose",       // pre-built: ships dist/
  "@buhera/pylon":          "file:./vendor/pylon",
  "@lavoisier/shapeshifter":"file:./vendor/shapeshifter",  // source: ships raw .js
  "scope-lang":             "file:./vendor/scope-lang",
  "@sachikonye/sbs":        "file:sachikonye-sbs-0.1.0.tgz" // packed tarball
}
```

Each vendored directory carries **its own `package.json`** with an `exports` map. Two
shapes exist, and Agent Smith can use either:

- **Source shape** (`@lavoisier/shapeshifter`): `exports` points straight at `.js` source
  files, no `dist/`, no build. Works because the host bundles.
- **Built shape** (`@buhera/purpose`): ships a compiled `dist/index.js` + `.d.ts`, with
  `files: ["dist"]`. Works everywhere, including raw Node.

Agent Smith is pure JS like shapeshifter, so the **source shape** is the default and
simplest. Use the **built shape** only if a non-bundler host must consume it (§4).

---

## 2. Integration paths

### Path A — Vendor the engine into a bundler-backed Buhera host (recommended)

This is the shapeshifter path. Use it when the consumer is `long-grass`, the Buhera web
surface, or any Next/Vite/webpack app.

**Step 1 — give the engine a package identity.** Create
`web/src/lib/agent-smith/package.json` (this makes the engine directory a self-contained,
publishable unit without disturbing the Next app that imports it via `@/lib/agent-smith`):

```jsonc
{
  "name": "@buhera/agent-smith",
  "version": "0.1.0",
  "description": "Agent Smith — the runnable core of the split-attention paper: a DSL (agent/society) plus parse→typecheck→compile→tick/town, the χ identity invariant, water-filling attention, and the four invariants. Pure JS, no runtime dependencies.",
  "type": "module",
  "license": "MIT",
  "author": "Kundai Farai Sachikonye",
  "exports": {
    ".":            "./index.js",
    "./identity":   "./identity.js",
    "./parse":      "./parse.js",
    "./typecheck":  "./typecheck.js",
    "./compile":    "./compile.js",
    "./tick":       "./tick.js",
    "./town":       "./town.js"
  },
  "files": [
    "index.js", "parse.js", "typecheck.js", "identity.js",
    "compile.js", "tick.js", "town.js", "providers.js", "showcase.js"
  ],
  "sideEffects": false,
  "private": true
}
```

> Note: `providers.js` (LLM transport) and `showcase.js` (force-graph rendering for the web
> UI) are shipped for completeness but are **not** part of the deterministic OS core. A
> Buhera deployment that wants offline determinism ignores them and drives the engine with
> `defaultCtx({ useModel: false })` — see §5.

**Step 2 — vendor it into the host.** From the Buhera host repo (e.g. `long-grass`):

```bash
# copy the engine into vendor/ (git subtree, submodule, or plain copy — Buhera uses copy)
mkdir -p vendor/agent-smith
cp -r /path/to/musande/web/src/lib/agent-smith/* vendor/agent-smith/
```

**Step 3 — declare the dependency.** Add to the host's `package.json`:

```jsonc
"dependencies": {
  "@buhera/agent-smith": "file:./vendor/agent-smith"
}
```

**Step 4 — install and import.**

```bash
npm install    # links vendor/agent-smith into node_modules/@buhera/agent-smith
```

```js
import { build, makeTown, defaultCtx, runTown } from "@buhera/agent-smith";
```

That is the whole contract. Because the host bundles, the 19 extensionless imports resolve
transparently. No build step, no `tsc`, no `dist/`.

### Path B — Packed tarball (the `@sachikonye/sbs` path)

For a frozen, versioned drop rather than a live source copy:

```bash
cd web/src/lib/agent-smith
npm pack                      # → buhera-agent-smith-0.1.0.tgz
cp buhera-agent-smith-0.1.0.tgz /path/to/buhera-host/
```

In the host `package.json`:

```jsonc
"dependencies": {
  "@buhera/agent-smith": "file:buhera-agent-smith-0.1.0.tgz"
}
```

`npm pack` respects the `files` array from Step 1, so only the engine `.js` ships. Same
bundler assumption as Path A.

### Path C — TypeScript path alias (no npm, monorepo-style)

If the Buhera host and musande live in one tree and you would rather not vendor, point the
host's `tsconfig`/`jsconfig` at the engine directly:

```jsonc
// buhera-host/jsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@buhera/agent-smith": ["../../semantics/musande/web/src/lib/agent-smith/index.js"]
    }
  }
}
```

This is the loosest coupling and needs no copy, but it only works when both projects are
checked out together and the host bundles. Prefer Path A for anything shipped.

---

## 3. Verifying the link

After any path above, confirm the engine runs inside the host. This snippet exercises the
full pipeline offline (no model key, deterministic):

```js
import { build, makeTown, defaultCtx, runTown } from "@buhera/agent-smith";

const src = `
agent desk {
  purpose minimise inventory_risk
  scenes { scene make_market serves inventory_risk with quote_hook }
  self { parts { capital, risk_appetite } separations { (capital, risk_appetite: 3) } }
  budget 1.0
  floor  2.0
}`;

const built = build(src);
console.assert(built.ok, "build failed:", built.errors);

const town = makeTown(built.program);
const ctx = defaultCtx({ useModel: false });        // offline, deterministic
const history = await runTown(town, ctx, 30);

console.log("agent χ =", built.program.agents[0].chi);        // → 3
console.log("ticks:", history.length, "records:",
  history.reduce((n, s) => n + s.records.length, 0));
```

Expected: `built.ok === true`, `χ = 3`, and a multi-tick history whose per-agent `count`
never decreases (invariant I2). If `build.ok` is false with a "not a known strongly convex
potential" error, the host is on a stale copy of `typecheck.js` — the sandbox's economic
potentials (`inventory_risk`, `spread_cost`, `queue_risk`, `mispricing`,
`reconciliation_gap`, `joint_inventory`) must be present in `CONVEX_POTENTIALS`. Re-vendor.

---

## 4. Consuming the engine from a NON-bundler host (raw Node / tsc / a Rust subprocess)

If Buhera needs to run the engine under **plain Node ESM** — a CLI, a `purpose-kernel`
subprocess bridge (`node engine.mjs`), a test runner with no bundler — the 19 extensionless
imports will throw `ERR_MODULE_NOT_FOUND`. Two fixes, in order of preference:

**Option 1 — ship a built `dist/` (the `@buhera/purpose` shape).** Add a tiny build that
rewrites imports to include `.js` and emits an `exports`-mapped `dist/`. The cleanest is a
one-line esbuild bundle:

```bash
cd web/src/lib/agent-smith
npx esbuild index.js --bundle --format=esm --platform=node \
  --outfile=dist/index.js
```

Then change the vendored `package.json` to the built shape:

```jsonc
{
  "name": "@buhera/agent-smith",
  "type": "module",
  "main": "./dist/index.js",
  "exports": { ".": { "import": "./dist/index.js" } },
  "files": ["dist"]
}
```

esbuild inlines all 19 relative imports into one file, so extension resolution stops
mattering. This `dist/` runs under raw Node, tsc `NodeNext`, and any bundler alike.

**Option 2 — subprocess bridge (the CLI pattern).** If Buhera's kernel is Rust and wants
the engine as an out-of-process provider (exactly how the Purpose/Zangalewa doc wraps a
peer CLI), wrap the built engine in a thin stdin/stdout JSON script:

```js
// engine-bridge.mjs  — reads one JSON line {source, ticks}, writes one JSON line result
import { build, makeTown, defaultCtx, runTown } from "@buhera/agent-smith";
process.stdin.once("data", async (buf) => {
  const { source, ticks = 30 } = JSON.parse(buf.toString());
  const built = build(source);
  if (!built.ok) { process.stdout.write(JSON.stringify({ ok:false, errors:built.errors })+"\n"); return; }
  const history = await runTown(makeTown(built.program), defaultCtx({ useModel:false }), ticks);
  process.stdout.write(JSON.stringify({ ok:true, program:built.program, history })+"\n");
});
```

A Rust `Provider` then spawns `node engine-bridge.mjs`, writes the source, reads the
result — the same subprocess pattern the Rust integration doc uses for Python models and
peer CLIs. This is also the natural seam for the future `agent-smith` **Rust crate** (see
the port plan in `bright-skipping-fountain.md`): until that crate lands, this bridge gives
Buhera a Rust-callable Agent Smith today.

---

## 5. The engine's public surface (what Buhera can call)

Re-exported from `@buhera/agent-smith` (`index.js`):

| Symbol | From | What it does |
|---|---|---|
| `build(source)` | `compile` | `parse → typecheck → compile`. Returns `{ ok, errors, program }`. The one entry point most hosts need. |
| `parse`, `ParseError` | `parse` | Tokenize + recursive-descent → spec AST. |
| `typecheck`, `typecheckAgent`, `CONVEX_POTENTIALS` | `typecheck` | The four typing rules; the registry of strongly-convex potentials. Extend `CONVEX_POTENTIALS` to add domain vocabularies. |
| `compileAgent`, `compileProgram` | `compile` | Lower a typed spec to a runtime `Agent`/program. |
| `characterInvariant`, `realisedFloor`, `waterFill`, `logGain`, `isConnected` | `identity` | The paper's math: χ (exact min-cut bipartition), the realised floor β, water-filling attention division. |
| `tick`, `initFloorNorm`, `LIMIT`, `OUTCOME` | `tick` | One observe→diagnose→commit step and its constants. |
| `makeTown`, `makeOmega`, `defaultCtx`, `stepTown`, `runTown` | `town` | The town runtime: shared state Ω, context, stepping, society χ. |
| `EXAMPLE_TOWN`, `EXAMPLE_TASK` | `index` | Two working reference scripts — ground-truth syntax. |
| *(optional)* `think`, `PROVIDERS`, `hasModel`, … | `providers` | LLM transport. **Skip for the deterministic OS core**; a live Buhera deployment swaps in its own model hook. |
| *(optional)* `makeShowcase`, `initialGraph`, `applyStep` | `showcase` | Force-graph rendering — web UI only, not OS core. |

**The offline discipline** (mirrors `purpose`'s empty-dictionary / runs-anywhere rule):
drive the engine with `defaultCtx({ useModel: false })`. The model call is the single
non-deterministic seam; with `useModel:false` it is replaced by a deterministic residual
descent, and the whole engine runs with no network and no keys — exactly what an OS module
must guarantee.

---

## 6. (Optional) Vendoring the sandbox UI

Only relevant if Buhera exposes a Next web surface and wants the interactive tool, not just
the engine. The sandbox is a **reference consumer** — treat it as a copy-paste template:

1. It is Next **Pages router** (`web/src/pages/sandbox.js`), mounted client-only via
   `dynamic(() => import(...), { ssr: false })` — the same discipline as the lavoisier tools.
2. Its charts are **hand-written SVG, no D3, no monaco**. The crossfilter (brush a chart
   slice → highlight the code that produced it) runs through a shared **Zustand** store
   (`web/src/sandbox/store.js`). The host must have `zustand@^4.5` (already a `long-grass`
   dep).
3. The only engine coupling is `web/src/sandbox/runner.js`, which imports from
   `@/lib/agent-smith`. Repoint that import at `@buhera/agent-smith` after vendoring and the
   sandbox runs against the vendored engine unchanged.

For a Buhera host on the App router, the shell would need porting; the engine and store are
router-agnostic and move as-is.

---

## 7. What is intentionally NOT provided

- **No model weights, no keys, no network.** The engine's deterministic core runs offline;
  the LLM seam is a hook a deployment fills in (`providers.js` is the reference, replaced in
  a real Buhera deployment).
- **No content store.** Like `@buhera/purpose`, the engine carries the *math and the
  mechanism*, not domain facts. Scripts are the input; Ω is transient runtime state.
- **No build step in the default (source) path.** Pure JS + a bundler host = zero build.
  The `dist/` build in §4 exists only for non-bundler consumers.
- **No Rust crate yet.** The `agent-smith` Rust port (`smith` CLI + `agent-smith` lib) is
  planned (`bright-skipping-fountain.md`) but not built. Until then, §4 Option 2's
  subprocess bridge is the Rust-callable path.

---

## 8. Quick reference

| Want to … | Do this |
|---|---|
| Link the engine into `long-grass` or a Next/Vite Buhera host | §2 Path A: `cp` into `vendor/agent-smith`, add `"@buhera/agent-smith": "file:./vendor/agent-smith"`, `npm install`. |
| Ship a frozen versioned drop | §2 Path B: `npm pack` → copy the `.tgz` → `file:…​.tgz`. |
| Link without npm in a monorepo | §2 Path C: `tsconfig` path alias at the engine's `index.js`. |
| Run the engine under raw Node / tsc / a test runner | §4 Option 1: esbuild a `dist/` (built shape). |
| Call the engine from a Rust kernel | §4 Option 2: `node engine-bridge.mjs` subprocess, JSON in/out. |
| Guarantee offline determinism | Drive with `defaultCtx({ useModel: false })`; ignore `providers.js`. |
| Add a domain vocabulary (e.g. new potentials) | Extend `CONVEX_POTENTIALS` in `typecheck.js` before vendoring. |
| Also take the interactive sandbox UI | §6: vendor the engine, repoint `runner.js`'s import, ensure `zustand@^4.5`. |

---

*Checked against `long-grass/package.json` (the `file:./vendor/*` convention),
`vendor/purpose/package.json` (built shape) and `vendor/shapeshifter/package.json` (source
shape), and the live engine at `web/src/lib/agent-smith/` (pure JS, zero deps, 19
extensionless imports). Revise this doc when the `agent-smith` Rust crate lands — at that
point §4 Option 2 is superseded by a native crate dependency.*
