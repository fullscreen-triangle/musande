// =====================================================================
//  Showcase — a chat-style front for the agent society.
//  A user types a prompt; a society of agents is spawned and runs the
//  tick-loop; a 3d force graph shows their knowledge graphs RESHUFFLING as
//  they solve (commits grow nodes, flow edges pulse toward the solution,
//  coordination edges light up between agents). Progressive problem-solving
//  is the graph tightening as the shared residual falls.
//
//  For a user who has not read the papers: type a question, watch the
//  agents think, see the answer assemble.
// =====================================================================
import { useState, useRef, useCallback, useEffect } from "react";
import Head from "next/head";
import dynamic from "next/dynamic";
import {
  makeShowcase,
  actContent,
  loadKeys,
  hasModel,
  PROVIDERS,
  saveKeys,
} from "@/lib/agent-smith";

const ForceGraph = dynamic(() => import("@/components/ForceGraph"), { ssr: false });

const AGENT_COLORS = {
  analyst: "#8b83d6",
  retriever: "#1d9e75",
  verifier: "#e0a01e",
};

export default function ShowcasePage() {
  const [prompt, setPrompt] = useState("");
  const [graph, setGraph] = useState({ nodes: [], links: [] });
  const [flow, setFlow] = useState([]);
  const [feed, setFeed] = useState([]); // narration of each tick
  const [running, setRunning] = useState(false);
  const [keys, setKeys] = useState({});
  const [showKeys, setShowKeys] = useState(false);
  const [selected, setSelected] = useState(null);
  const showcaseRef = useRef(null);
  const stopRef = useRef(false);

  useEffect(() => {
    const k = loadKeys();
    setKeys(k);
    setShowKeys(!hasModel(k));
  }, []);

  const runHook = useCallback(
    async (agent, candidate, obs, omega) => {
      const residual = omega.residual.get(agent.purpose.target) ?? 1;
      const r = await actContent(agent.name, candidate.scene, residual, {
        keys,
        crowd: false,
      });
      return { content: r.content, model: r.model, reduction: null };
    },
    [keys]
  );

  const submit = useCallback(async () => {
    if (!prompt.trim() || running) return;
    if (!hasModel(keys)) {
      setShowKeys(true);
      setFeed([{ kind: "err", text: "Add a model provider key to run the agents." }]);
      return;
    }
    stopRef.current = false;
    setRunning(true);
    setFeed([{ kind: "user", text: prompt }]);
    setSelected(null);

    const sc = makeShowcase(prompt, { keys, runHook });
    if (!sc.ok) {
      setFeed((f) => [...f, { kind: "err", text: "could not build society" }]);
      setRunning(false);
      return;
    }
    showcaseRef.current = sc;
    setGraph(sc.initialGraph);
    setFlow([]);

    for (let i = 0; i < 16 && !stopRef.current; i++) {
      // eslint-disable-next-line no-await-in-loop
      const { step, graph: g, flow: fl } = await sc.step();
      setGraph({ nodes: [...g.nodes], links: [...g.links] });
      setFlow(fl);
      setFeed((f) => [...f, ...narrate(step)]);
      // let the force sim breathe + the particles show the flow
      // eslint-disable-next-line no-await-in-loop
      await sleep(650);
      if (step.done || step.quiescent) {
        setFeed((f) => [...f, { kind: "sys", text: step.quiescent ? "quiescent — the answer has assembled" : "done" }]);
        break;
      }
    }
    setFlow([]);
    setRunning(false);
  }, [prompt, keys, running, runHook]);

  const stop = () => {
    stopRef.current = true;
  };

  return (
    <>
      <Head>
        <title>Showcase — a society of agents solving</title>
      </Head>
      <div className="relative h-screen w-screen overflow-hidden bg-[#0a0a0a] text-light">
        {/* the graph fills the screen */}
        <div className="absolute inset-0">
          {graph.nodes.length > 0 ? (
            <ForceGraph data={graph} flow={flow} onNodeClick={(n) => setSelected(n)} />
          ) : (
            <EmptyState />
          )}
        </div>

        {/* narration feed, top-right */}
        {feed.length > 0 && (
          <div className="pointer-events-none absolute right-3 top-16 z-10 max-h-[60vh] w-80 overflow-hidden">
            <div className="pointer-events-auto max-h-[60vh] space-y-1 overflow-y-auto rounded-lg border border-white/10 bg-black/50 p-3 text-xs backdrop-blur">
              {feed.slice(-40).map((e, i) => (
                <FeedRow key={i} e={e} />
              ))}
            </div>
          </div>
        )}

        {/* selected node detail */}
        {selected && (
          <div className="absolute left-3 top-16 z-10 w-72 rounded-lg border border-white/10 bg-black/60 p-3 text-xs backdrop-blur">
            <div className="mb-1 flex items-center justify-between">
              <span className="font-mono font-semibold" style={{ color: selected.color }}>
                {selected.label}
              </span>
              <button className="text-neutral-500 hover:text-light" onClick={() => setSelected(null)}>
                ✕
              </button>
            </div>
            <div className="text-neutral-400">
              {selected.kind === "act"
                ? "a committed act — an individuated distinction"
                : selected.kind === "part"
                ? "a part of an agent's knowledge graph"
                : selected.kind}
            </div>
            {selected.content && <div className="mt-2 italic text-neutral-200">“{selected.content}”</div>}
          </div>
        )}

        {/* the chat prompt bar, bottom-centre */}
        <div className="absolute bottom-6 left-1/2 z-20 w-full max-w-2xl -translate-x-1/2 px-4">
          <div className="flex items-center gap-2 rounded-full border border-white/15 bg-black/60 px-2 py-2 backdrop-blur">
            <input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              placeholder="Ask the society to solve something…"
              className="flex-1 bg-transparent px-3 text-sm text-light placeholder-neutral-500 outline-none"
            />
            {running ? (
              <button
                onClick={stop}
                className="rounded-full bg-red-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-red-500"
              >
                stop
              </button>
            ) : (
              <button
                onClick={submit}
                className="rounded-full bg-white px-4 py-1.5 text-sm font-semibold text-black hover:bg-neutral-200"
              >
                solve
              </button>
            )}
          </div>
          <div className="mt-2 flex justify-center gap-3 text-[11px] text-neutral-500">
            <button className="hover:text-light" onClick={() => setShowKeys((s) => !s)}>
              {hasModel(keys) ? "● models configured" : "● add model key"}
            </button>
            <Legend />
          </div>
        </div>

        {/* key panel */}
        {showKeys && (
          <div className="absolute bottom-24 left-1/2 z-30 w-full max-w-md -translate-x-1/2 rounded-lg border border-white/15 bg-black/80 p-3 backdrop-blur">
            <p className="mb-2 text-xs text-neutral-400">
              Models power the agents’ work. Keys stay in your browser.
            </p>
            <div className="grid grid-cols-1 gap-2">
              {Object.values(PROVIDERS).map((p) => (
                <label key={p.id} className="flex items-center gap-2 text-xs">
                  <span className="w-28 shrink-0">{p.label}</span>
                  <input
                    type="password"
                    placeholder={p.keyLabel}
                    value={keys[p.id] || ""}
                    onChange={(e) => {
                      const next = { ...keys, [p.id]: e.target.value };
                      setKeys(next);
                      saveKeys(next);
                    }}
                    className="flex-1 rounded border border-white/20 bg-black/40 px-2 py-1 font-mono text-light"
                  />
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}

function narrate(step) {
  const out = [];
  for (const r of step.records) {
    if (r.outcome === "commit") {
      out.push({
        kind: "commit",
        agent: r.agent,
        text: `${r.agent} · ${r.scene} — ${r.content || "committed"}`,
      });
    } else if (r.outcome === "observe") {
      out.push({ kind: "observe", agent: r.agent, text: `${r.agent} observes (waiting on the state)` });
    } else if (r.outcome === "quiescent") {
      out.push({ kind: "sys", text: `${r.agent} done` });
    }
  }
  return out;
}

function FeedRow({ e }) {
  if (e.kind === "user") return <div className="text-neutral-300">“{e.text}”</div>;
  if (e.kind === "err") return <div className="text-red-400">{e.text}</div>;
  if (e.kind === "sys") return <div className="text-amber-400">{e.text}</div>;
  const color = AGENT_COLORS[e.agent] || "#9ca3af";
  return (
    <div className="flex items-start gap-1.5">
      <span className="mt-1 h-2 w-2 shrink-0 rounded-full" style={{ background: color }} />
      <span className={e.kind === "observe" ? "text-neutral-500" : "text-neutral-200"}>{e.text}</span>
    </div>
  );
}

function Legend() {
  return (
    <span className="flex gap-2">
      <span className="text-[#ba5a17]">▬ flow→solution</span>
      <span className="text-[#1d9e75]">▬ coordination</span>
    </span>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <p className="max-w-md text-center text-sm text-neutral-500">
        A society of agents — an analyst, a retriever, a verifier — each with its own knowledge
        graph. Ask a question below; watch their graphs reshuffle as they solve it together.
      </p>
    </div>
  );
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
