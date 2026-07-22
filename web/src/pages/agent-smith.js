// =====================================================================
//  Agent Smith — the tool page.
//  Left:  spec editor + compile (character invariant chi, water-fill price,
//         typing errors).  Right: live town run — each tick shows which
//         agents commit / observe / decline, the tier used, and the shared
//         solution-state moving.  Models are required: a key panel up top.
//
//  Standalone (this page alone) and embeddable in Buhera OS.
// =====================================================================
import { useState, useEffect, useMemo, useCallback } from "react";
import Head from "next/head";
import {
  build,
  makeTown,
  defaultCtx,
  stepTown,
  PROVIDERS,
  loadKeys,
  saveKeys,
  hasModel,
  think,
  EXAMPLE_TOWN,
  EXAMPLE_TASK,
} from "@/lib/agent-smith";

const OUTCOME_STYLE = {
  commit: "text-emerald-700 bg-emerald-50 border-emerald-300",
  observe: "text-sky-700 bg-sky-50 border-sky-300",
  decline: "text-neutral-500 bg-neutral-100 border-neutral-300",
  quiescent: "text-amber-700 bg-amber-50 border-amber-300",
};

export default function AgentSmithPage() {
  const [source, setSource] = useState(EXAMPLE_TOWN);
  const [compiled, setCompiled] = useState(null); // { ok, errors, program, typed }
  const [town, setTown] = useState(null);
  const [history, setHistory] = useState([]);
  const [running, setRunning] = useState(false);
  const [keys, setKeys] = useState({});
  const [crowd, setCrowd] = useState(false);
  const [status, setStatus] = useState("");

  useEffect(() => {
    setKeys(loadKeys());
  }, []);

  const modelReady = hasModel(keys);

  const doCompile = useCallback(() => {
    const result = build(source);
    setCompiled(result);
    setHistory([]);
    setTown(null);
    if (result.ok) {
      setStatus(`compiled: ${result.program.agents.length} agent(s)`);
    } else {
      setStatus(`${result.errors.length} error(s)`);
    }
  }, [source]);

  // compile once on mount
  useEffect(() => {
    doCompile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // the tier-1 hook: run the scene's domain work via a model. Opaque to the
  // runtime; returns a residual reduction + content. This is the seam.
  const runHook = useCallback(
    async (agent, candidate, obs, omega) => {
      const prompt =
        `You are the "${candidate.scene}" activity of an agent whose purpose is ` +
        `"${agent.purpose.target}". The shared solution-state residual is ` +
        `${(omega.residual.get(agent.purpose.target) ?? 1).toFixed(2)}. In one short ` +
        `sentence, state the concrete step you take now toward that purpose.`;
      try {
        const r = await think(prompt, { keys, crowd, crowdSize: 3 });
        return { content: r.text, model: r.model, reduction: null };
      } catch (e) {
        return { content: `(model error: ${e.message})`, model: null, reduction: null };
      }
    },
    [keys, crowd]
  );

  const ctx = useMemo(
    () => defaultCtx({ keys, crowd, runHook, useModel: true }),
    [keys, crowd, runHook]
  );

  const startRun = useCallback(async () => {
    if (!compiled?.ok) return;
    if (!modelReady) {
      setStatus("add an API key first — models are required to run agents");
      return;
    }
    const t = makeTown(compiled.program);
    setTown(t);
    setHistory([]);
    setRunning(true);
    setStatus("running…");
    for (let i = 0; i < 24; i++) {
      // eslint-disable-next-line no-await-in-loop
      const step = await stepTown(t, ctx);
      setHistory((h) => [...h, step]);
      if (step.done || step.quiescent) {
        setStatus(step.quiescent ? "quiescent — no lowering move remains" : "done");
        break;
      }
    }
    setRunning(false);
  }, [compiled, ctx, modelReady]);

  const stepOnce = useCallback(async () => {
    if (!compiled?.ok) return;
    if (!modelReady) {
      setStatus("add an API key first — models are required to run agents");
      return;
    }
    let t = town;
    if (!t) {
      t = makeTown(compiled.program);
      setTown(t);
      setHistory([]);
    }
    const step = await stepTown(t, ctx);
    setHistory((h) => [...h, step]);
    setStatus(step.quiescent ? "quiescent" : `tick ${step.tick}`);
  }, [compiled, town, ctx, modelReady]);

  return (
    <>
      <Head>
        <title>Agent Smith — specify & instantiate agents</title>
      </Head>
      <main className="min-h-screen w-full bg-neutral-50 px-4 py-6 font-sans text-neutral-900 md:px-8">
        <header className="mx-auto mb-4 max-w-7xl">
          <h1 className="text-2xl font-bold tracking-tight">Agent&nbsp;Smith</h1>
          <p className="text-sm text-neutral-600">
            Specify an agent by what it is <em>for</em>; the compiler instantiates it. Every
            script is an Agent Smith. Agents read the state of the solution, not their own
            reasoning.
          </p>
        </header>

        <KeyPanel keys={keys} setKeys={setKeys} crowd={crowd} setCrowd={setCrowd} />

        <div className="mx-auto grid max-w-7xl grid-cols-1 gap-4 lg:grid-cols-2">
          {/* LEFT: spec editor + compile */}
          <section className="flex flex-col rounded-lg border border-neutral-300 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-neutral-200 px-3 py-2">
              <span className="text-sm font-semibold">specification</span>
              <div className="flex gap-2 text-xs">
                <button
                  className="rounded border border-neutral-300 px-2 py-1 hover:bg-neutral-100"
                  onClick={() => setSource(EXAMPLE_TOWN)}
                >
                  town
                </button>
                <button
                  className="rounded border border-neutral-300 px-2 py-1 hover:bg-neutral-100"
                  onClick={() => setSource(EXAMPLE_TASK)}
                >
                  task-agent
                </button>
                <button
                  className="rounded bg-neutral-900 px-3 py-1 font-semibold text-white hover:bg-neutral-700"
                  onClick={doCompile}
                >
                  compile
                </button>
              </div>
            </div>
            <textarea
              value={source}
              onChange={(e) => setSource(e.target.value)}
              spellCheck={false}
              className="h-[420px] w-full resize-none bg-neutral-950 p-3 font-mono text-[12px] leading-relaxed text-neutral-100 outline-none"
            />
            <CompileResult compiled={compiled} />
          </section>

          {/* RIGHT: town run */}
          <section className="flex flex-col rounded-lg border border-neutral-300 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-neutral-200 px-3 py-2">
              <span className="text-sm font-semibold">run</span>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-neutral-500">{status}</span>
                <button
                  disabled={!compiled?.ok || running}
                  className="rounded border border-neutral-300 px-2 py-1 hover:bg-neutral-100 disabled:opacity-40"
                  onClick={stepOnce}
                >
                  step
                </button>
                <button
                  disabled={!compiled?.ok || running}
                  className="rounded bg-emerald-600 px-3 py-1 font-semibold text-white hover:bg-emerald-500 disabled:opacity-40"
                  onClick={startRun}
                >
                  {running ? "running…" : "run ▶"}
                </button>
              </div>
            </div>
            <RunView history={history} town={town} modelReady={modelReady} />
          </section>
        </div>

        <footer className="mx-auto mt-4 max-w-7xl text-center text-xs text-neutral-400">
          standalone tool · embeddable in Buhera OS · the four invariants held by construction
        </footer>
      </main>
    </>
  );
}

// ---- key panel (models are required) --------------------------------

function KeyPanel({ keys, setKeys, crowd, setCrowd }) {
  const [open, setOpen] = useState(!hasModel(keys));
  const ready = hasModel(keys);

  const update = (id, value) => {
    const next = { ...keys, [id]: value };
    setKeys(next);
    saveKeys(next);
  };

  return (
    <div className="mx-auto mb-4 max-w-7xl rounded-lg border border-neutral-300 bg-white shadow-sm">
      <button
        className="flex w-full items-center justify-between px-3 py-2 text-sm"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="font-semibold">
          model providers{" "}
          <span className={ready ? "text-emerald-600" : "text-red-600"}>
            {ready ? "● configured" : "● required — add a key"}
          </span>
        </span>
        <span className="text-neutral-400">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="border-t border-neutral-200 px-3 py-3">
          <p className="mb-2 text-xs text-neutral-500">
            Models are the point: every agent’s work runs through a model. Keys stay in your
            browser and are sent only to this tool’s own API route. HuggingFace enables the
            many-models crowd (several models vote; consensus sharpens the judgment).
          </p>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {Object.values(PROVIDERS).map((p) => (
              <label key={p.id} className="flex items-center gap-2 text-xs">
                <span className="w-32 shrink-0 font-medium">{p.label}</span>
                <input
                  type="password"
                  placeholder={p.keyLabel}
                  value={keys[p.id] || ""}
                  onChange={(e) => update(p.id, e.target.value)}
                  className="flex-1 rounded border border-neutral-300 px-2 py-1 font-mono"
                />
              </label>
            ))}
          </div>
          <label className="mt-3 flex items-center gap-2 text-xs">
            <input type="checkbox" checked={crowd} onChange={(e) => setCrowd(e.target.checked)} />
            <span>
              crowd mode — poll several HuggingFace / Ollama models per judgment and take the
              consensus (many cheap readers over one expensive one)
            </span>
          </label>
        </div>
      )}
    </div>
  );
}

// ---- compile result -------------------------------------------------

function CompileResult({ compiled }) {
  if (!compiled) return null;
  if (!compiled.ok) {
    return (
      <div className="border-t border-neutral-200 bg-red-50 px-3 py-2 text-xs">
        <div className="mb-1 font-semibold text-red-700">typing errors</div>
        <ul className="space-y-1">
          {compiled.errors.map((e, i) => (
            <li key={i} className="font-mono text-red-800">
              {e.line ? `line ${e.line}: ` : ""}
              {e.message}
            </li>
          ))}
        </ul>
      </div>
    );
  }
  const agents = compiled.program.agents;
  return (
    <div className="border-t border-neutral-200 bg-neutral-50 px-3 py-2 text-xs">
      <div className="mb-1 font-semibold text-emerald-700">
        typed OK — instantiated {agents.length} agent(s)
      </div>
      <div className="space-y-1">
        {agents.map((a) => (
          <div key={a.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 font-mono">
            <span className="font-semibold">{a.name}</span>
            <Badge>{a.regime === "task" ? "task · halts" : "character · runs on"}</Badge>
            <span>
              χ={a.chi}
              {a.chiNonLocal ? " (non-local)" : ""}
            </span>
            <span>floor={a.floor}</span>
            <span>budget={a.budget}</span>
            <span className="text-neutral-500">
              scenes: {a.scenes.map((s) => s.name).join(", ")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---- run view -------------------------------------------------------

function RunView({ history, town, modelReady }) {
  if (!modelReady) {
    return (
      <div className="flex h-[420px] items-center justify-center p-6 text-center text-sm text-neutral-500">
        Add a model provider key above, then compile and run. Every agent’s work runs through
        a real model — that is the point of the tool.
      </div>
    );
  }
  if (history.length === 0) {
    return (
      <div className="flex h-[420px] items-center justify-center p-6 text-center text-sm text-neutral-400">
        Press <span className="mx-1 font-mono">step</span> or{" "}
        <span className="mx-1 font-mono">run ▶</span> to watch the town tick: who commits, who
        observes, who declines, and the shared solution-state moving.
      </div>
    );
  }
  return (
    <div className="h-[420px] overflow-y-auto p-3">
      {history
        .slice()
        .reverse()
        .map((step) => (
          <div key={step.tick} className="mb-3 rounded border border-neutral-200">
            <div className="flex items-center justify-between bg-neutral-100 px-2 py-1 text-xs">
              <span className="font-semibold">tick {step.tick}</span>
              <span className="font-mono text-neutral-600">
                Ω{" "}
                {Object.entries(step.residuals)
                  .map(([k, v]) => `${k}=${v.toFixed(2)}`)
                  .join("  ")}
              </span>
            </div>
            <div className="divide-y divide-neutral-100">
              {step.records.map((r, i) => (
                <AgentRow key={i} r={r} />
              ))}
            </div>
          </div>
        ))}
    </div>
  );
}

function AgentRow({ r }) {
  const style = OUTCOME_STYLE[r.outcome] || OUTCOME_STYLE.decline;
  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 px-2 py-1.5 text-xs">
      <span className="w-20 shrink-0 font-mono font-semibold">{r.agent}</span>
      <span className={`rounded border px-1.5 py-0.5 font-mono uppercase ${style}`}>
        {r.outcome}
      </span>
      {r.scene && <span className="font-mono text-neutral-500">{r.scene}</span>}
      <span className="font-mono text-neutral-400">
        m={r.count} · Δ={r.delta} · res={r.residual} · p★={r.price}
      </span>
      {r.tier === 1 && <Badge>tier-1 model</Badge>}
      {r.limit === "structure-limited" && (
        <span className="rounded border border-amber-300 bg-amber-50 px-1 py-0.5 text-amber-700">
          stall → re-route
        </span>
      )}
      {r.content && (
        <span className="w-full truncate pl-20 font-normal italic text-neutral-600">
          “{r.content}” {r.model ? `— ${r.model}` : ""}
        </span>
      )}
      {r.reason && !r.content && (
        <span className="text-neutral-400">({r.reason})</span>
      )}
    </div>
  );
}

function Badge({ children }) {
  return (
    <span className="rounded bg-neutral-200 px-1.5 py-0.5 text-[10px] font-medium text-neutral-700">
      {children}
    </span>
  );
}
