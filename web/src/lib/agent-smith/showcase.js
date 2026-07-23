// =====================================================================
//  Agent Smith — showcase engine.
//  Turns a plain-language prompt into a small society of agents and drives
//  the tick-loop, emitting a live knowledge-graph the force-graph renders.
//
//  The graph IS the agents' knowledge: one cluster of nodes per agent (its
//  self-graph parts), plus a central PROMPT node and a SOLUTION node. Each
//  tick reshuffles the graph — because knowledge/experimentation is the
//  reshuffling of what has been individuated (marbles rearranged in a
//  conserved medium):
//    - a COMMIT individuates a new distinction: the acting agent grows a
//      fresh node (an act#count node) linked into its cluster, and an edge
//      lights up toward the SOLUTION (information flowing into the answer);
//    - cross-agent coordination: when an agent commits, a transient link is
//      drawn from its new node to other agents that share the target
//      (outcome-space coordination — they read the shared state);
//    - progressive solving: node/edge strengths track the falling residual,
//      so the graph tightens toward the solution as Omega approaches
//      quiescence.
//
//  This is a *showcase*: it uses the real engine (parse/typecheck/compile/
//  tick/town) but synthesises a society from the prompt so a user who has
//  not read the papers can still watch agents solve.
// =====================================================================

import { build } from "./compile";
import { makeTown, defaultCtx, stepTown } from "./town";
import { think } from "./providers";

// A small default society, parameterised by the prompt. Each agent is a
// "specialist" whose self-graph is its knowledge; all serve one shared
// solution target so they coordinate in outcome space.
function societyFor(prompt) {
  const target = "solution";
  // three specialists with distinct knowledge graphs (different parts), all
  // driving the same target. A character (analyst) that runs on, and two
  // task-agents (retriever, verifier) that contribute and quiesce.
  return `society solving {
  agent analyst {
    purpose minimise residual
    scenes {
      scene decompose serves residual with decompose_hook
      scene reason    serves residual with reason_hook
    }
    self {
      parts { premise, model, claim, gap }
      separations {
        (premise, model: 3), (model, claim: 2),
        (claim, gap: 2), (gap, premise: 2)
      }
    }
    budget 1.0
    floor 2.0
    coherence keeps { model, claim }
  }

  agent retriever {
    purpose reach ${target}
    scenes {
      scene search   serves ${target} with search_hook
      scene extract  serves ${target} with extract_hook
    }
    self {
      parts { query, source, evidence }
      separations { (query, source: 2), (source, evidence: 2), (evidence, query: 2) }
    }
    budget 1.0
    floor 2.0
    coherence keeps { evidence }
  }

  agent verifier {
    purpose reach ${target}
    scenes {
      scene check serves ${target} with check_hook
    }
    self {
      parts { candidate, test, verdict }
      separations { (candidate, test: 2), (test, verdict: 2), (verdict, candidate: 2) }
    }
    budget 1.0
    floor 2.0
    coherence keeps { test }
  }

  tie (analyst, retriever: 2)
  tie (retriever, verifier: 2)
  tie (analyst, verifier: 2)
  couple 4.0
}`;
}

const AGENT_COLORS = {
  analyst: "#8b83d6",
  retriever: "#1d9e75",
  verifier: "#e0a01e",
};
const PROMPT_COLOR = "#e5e5e5";
const SOLUTION_COLOR = "#ba5a17";

/**
 * Build the initial graph from a compiled program.
 * Returns { nodes, links } for react-force-graph-3d.
 * Node shape: { id, group, kind, label, val, color }
 * Link shape: { source, target, kind, strength }
 */
export function initialGraph(program, prompt) {
  const nodes = [];
  const links = [];

  nodes.push({ id: "__prompt", group: "prompt", kind: "prompt", label: truncate(prompt), val: 8, color: PROMPT_COLOR });
  nodes.push({ id: "__solution", group: "solution", kind: "solution", label: "solution", val: 10, color: SOLUTION_COLOR });

  for (const agent of program.agents) {
    const color = AGENT_COLORS[agent.name] || "#6b7280";
    // an anchor node for the agent (its identity χ)
    nodes.push({
      id: `${agent.name}::__self`,
      group: agent.name,
      kind: "agent",
      label: agent.name,
      val: 6,
      color,
    });
    // the agent's knowledge parts
    for (const p of agent.self.parts) {
      nodes.push({
        id: `${agent.name}::${p}`,
        group: agent.name,
        kind: "part",
        label: p,
        val: 3,
        color,
      });
      links.push({ source: `${agent.name}::__self`, target: `${agent.name}::${p}`, kind: "own", strength: 0.6 });
    }
    // the agent's separations (its internal boundaries)
    for (const e of agent.self.separations) {
      links.push({
        source: `${agent.name}::${e.a}`,
        target: `${agent.name}::${e.b}`,
        kind: "sep",
        strength: 0.3 + 0.1 * e.cost,
      });
    }
    // the prompt reaches every agent; every agent reaches the solution
    links.push({ source: "__prompt", target: `${agent.name}::__self`, kind: "prompt", strength: 0.2 });
    links.push({ source: `${agent.name}::__self`, target: "__solution", kind: "toward", strength: 0.15 });
  }
  return { nodes, links };
}

/**
 * Apply one tick's records to the graph, mutating a copy and returning the
 * new { nodes, links } plus a list of highlighted link ids (for the flow
 * animation). This is the reshuffle: commits grow new nodes and light up
 * flow edges; residual controls edge strength so the graph tightens.
 */
export function applyStep(graph, step, program) {
  const nodes = graph.nodes.map((n) => ({ ...n }));
  const links = graph.links.map((l) => ({ ...l }));
  const nodeById = new Map(nodes.map((n) => [n.id, n]));
  const flow = [];

  for (const rec of step.records) {
    const agent = rec.agent;
    const color = AGENT_COLORS[agent] || "#6b7280";

    if (rec.outcome === "commit") {
      // individuate a new distinction: an act node linked into the cluster.
      const actId = `${agent}::act#${rec.count}`;
      if (!nodeById.has(actId)) {
        const node = {
          id: actId,
          group: agent,
          kind: "act",
          label: rec.scene || `act ${rec.count}`,
          val: 2 + Math.min(4, rec.count * 0.4),
          color,
          content: rec.content || null,
        };
        nodes.push(node);
        nodeById.set(actId, node);
        // link the act into the agent's self and toward the solution (flow)
        links.push({ source: `${agent}::__self`, target: actId, kind: "own", strength: 0.7 });
        const flowLink = { source: actId, target: "__solution", kind: "flow", strength: 0.9 };
        links.push(flowLink);
        flow.push(`${actId}>__solution`);

        // outcome-space coordination: transient links to OTHER agents that
        // share this target (they read the shared state and may act next).
        const sharers = program.agents
          .filter((a) => a.name !== agent && a.purpose.target === targetOf(program, agent))
          .map((a) => a.name);
        for (const other of sharers) {
          links.push({ source: actId, target: `${other}::__self`, kind: "coord", strength: 0.4 });
          flow.push(`${actId}>${other}::__self`);
        }
      }
      // reshuffle: acting reweights the agent's own separations (knowledge
      // rearranges). Nudge the agent's part nodes' size by the residual.
      for (const n of nodes) {
        if (n.group === agent && n.kind === "part") {
          n.val = Math.max(1.5, 3 * (rec.residual ?? 1));
        }
      }
    }

    // progressive solving: the "toward solution" edge for this agent tightens
    // as its residual falls.
    for (const l of links) {
      if (l.kind === "toward" && String(l.source).startsWith?.(`${agent}::`)) {
        l.strength = 0.15 + 0.6 * (1 - (rec.residual ?? 1));
      }
    }
  }

  // the solution node grows as the overall residual falls.
  const avgRes =
    Object.values(step.residuals).reduce((a, b) => a + b, 0) /
    Math.max(1, Object.values(step.residuals).length);
  const sol = nodeById.get("__solution");
  if (sol) sol.val = 10 + 12 * (1 - avgRes);

  return { graph: { nodes, links }, flow, avgRes };
}

function targetOf(program, agentName) {
  const a = program.agents.find((x) => x.name === agentName);
  return a ? a.purpose.target : null;
}

/**
 * Run the whole showcase for a prompt. Yields the initial graph and a
 * per-tick callback so the page can animate. Returns a controller with
 * step()/reset(). Models are used for the acts (the domain work), via the
 * runHook passed in (wired to providers in the page).
 */
export function makeShowcase(prompt, { keys, crowd, runHook } = {}) {
  const source = societyFor(prompt);
  const built = build(source);
  if (!built.ok) {
    return { ok: false, errors: built.errors };
  }
  const program = built.program;
  const town = makeTown(program);
  const ctx = defaultCtx({ keys, crowd, runHook, useModel: !!runHook });
  let graph = initialGraph(program, prompt);

  return {
    ok: true,
    program,
    town,
    initialGraph: graph,
    async step() {
      const s = await stepTown(town, ctx);
      const applied = applyStep(graph, s, program);
      graph = applied.graph;
      return { step: s, graph, flow: applied.flow, avgRes: applied.avgRes };
    },
  };
}

/**
 * Ask a model to name, in one short line, the step an agent takes — used as
 * the act node's content so the graph shows real reasoning flowing in.
 */
export async function actContent(agent, scene, residual, opts) {
  const prompt =
    `You are the "${scene}" activity of a "${agent}" agent solving a user problem. ` +
    `Residual to solution: ${residual.toFixed(2)}. In one short phrase (max 8 words), ` +
    `state the concrete step you take now.`;
  try {
    const r = await think(prompt, opts);
    return { content: r.text?.slice(0, 80) || null, model: r.model };
  } catch (e) {
    return { content: null, model: null };
  }
}

function truncate(s, n = 40) {
  s = (s || "").trim();
  return s.length > n ? s.slice(0, n) + "…" : s;
}
