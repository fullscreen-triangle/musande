// =====================================================================
//  Stub compiler: parse + check + run.
//  This will be replaced by the real TypeScript compiler.
//  For now it does enough to drive the UI: it parses the DSL into AST,
//  runs the math, and produces step records.
// =====================================================================

import {
  SmithFile, AgentDecl, SocietyDecl, SceneDecl, SelfDecl,
  SeparationDecl, PurposeDecl, CheckResult, AgentCheck,
  Diagnostic, StepRecord, RunResult, CompiledProgram,
} from "./types";
import {
  characterInvariant, realisedFloor, waterFill, logGainProfile,
  kuramotoStep, orderParameter, type WeightedGraph, type GainProfile,
} from "../engine/math";

// --- Parser (simplified regex-based, to be replaced) ---

export function parse(source: string): { file: SmithFile; errors: Diagnostic[] } {
  const errors: Diagnostic[] = [];
  const items: (AgentDecl | SocietyDecl)[] = [];

  // Strip comments
  const lines = source.split("\n");
  const cleaned = lines.map(l => l.replace(/\/\/.*$/, "")).join("\n");

  // Try to parse society blocks first, then standalone agents
  const societyRegex = /society\s+(\w+)\s*\{([\s\S]*?)\n\}/g;
  let match: RegExpExecArray | null;
  const consumed = new Set<number>();

  while ((match = societyRegex.exec(cleaned)) !== null) {
    const name = match[1];
    const body = match[2];
    const society = parseSociety(name, body, lines, errors);
    if (society) items.push(society);
    // Mark these lines as consumed
    const startLine = cleaned.substring(0, match.index).split("\n").length;
    const endLine = startLine + match[0].split("\n").length - 1;
    for (let i = startLine; i <= endLine; i++) consumed.add(i);
  }

  // Parse standalone agents
  const agentRegex = /agent\s+(\w+)\s*\{([\s\S]*?)\n\}/g;
  while ((match = agentRegex.exec(cleaned)) !== null) {
    const startLine = cleaned.substring(0, match.index).split("\n").length;
    if (consumed.has(startLine)) continue;
    const name = match[1];
    const body = match[2];
    const agent = parseAgent(name, body, lines, errors);
    if (agent) items.push(agent);
  }

  if (items.length === 0 && errors.length === 0) {
    errors.push({ message: "No agent or society declarations found", severity: "error" });
  }

  return { file: { kind: "file", items }, errors };
}

function parseAgent(name: string, body: string, _lines: string[], errors: Diagnostic[]): AgentDecl | null {
  // Purpose
  const purposeMatch = body.match(/purpose\s+(minimise|reach)\s+(\w+)/);
  if (!purposeMatch) {
    errors.push({ message: `Agent "${name}": missing purpose declaration`, severity: "error" });
    return null;
  }
  const purpose: PurposeDecl = {
    kind: "purpose",
    mode: purposeMatch[1] as "minimise" | "reach",
    target: purposeMatch[2],
  };

  // Scenes
  const scenes: SceneDecl[] = [];
  const sceneRegex = /scene\s+(\w+)\s+serves\s+(\w+)\s+with\s+(\w+)/g;
  let sm: RegExpExecArray | null;
  while ((sm = sceneRegex.exec(body)) !== null) {
    scenes.push({
      kind: "scene",
      name: sm[1],
      serves: sm[2],
      hook: sm[3],
      gainK: 1 + Math.random() * 2, // Default gain parameter; will be configurable
    });
  }

  // Self
  const partsMatch = body.match(/parts\s*\{([^}]+)\}/);
  const parts = partsMatch
    ? partsMatch[1].split(",").map(p => p.trim()).filter(Boolean)
    : [];

  const separations: SeparationDecl[] = [];
  const sepRegex = /\((\w+),\s*(\w+):\s*([\d.]+)\)/g;
  let sepM: RegExpExecArray | null;
  while ((sepM = sepRegex.exec(body)) !== null) {
    separations.push({ from: sepM[1], to: sepM[2], cost: parseFloat(sepM[3]) });
  }

  // Budget & floor
  const budgetMatch = body.match(/budget\s+([\d.]+)/);
  const floorMatch = body.match(/floor\s+([\d.]+)/);
  const budget = budgetMatch ? parseFloat(budgetMatch[1]) : 1.0;
  const floor = floorMatch ? parseFloat(floorMatch[1]) : 2.0;

  // Coherence
  const cohMatch = body.match(/coherence\s+keeps\s*\{([^}]+)\}/);
  const coherence = cohMatch
    ? { keeps: cohMatch[1].split(",").map(s => s.trim()).filter(Boolean) }
    : undefined;

  return {
    kind: "agent",
    name,
    purpose,
    scenes,
    self: { kind: "self", parts, separations },
    budget,
    floor,
    coherence,
  };
}

function parseSociety(name: string, body: string, lines: string[], errors: Diagnostic[]): SocietyDecl | null {
  const agents: AgentDecl[] = [];
  const agentRegex = /agent\s+(\w+)\s*\{([\s\S]*?)\n\s*\}/g;
  let am: RegExpExecArray | null;
  while ((am = agentRegex.exec(body)) !== null) {
    const agent = parseAgent(am[1], am[2], lines, errors);
    if (agent) agents.push(agent);
  }

  const ties: { from: string; to: string; cost: number }[] = [];
  const tieRegex = /tie\s*\((\w+),\s*(\w+):\s*([\d.]+)\)/g;
  let tm: RegExpExecArray | null;
  while ((tm = tieRegex.exec(body)) !== null) {
    ties.push({ from: tm[1], to: tm[2], cost: parseFloat(tm[3]) });
  }

  const coupleMatch = body.match(/couple\s+([\d.]+)/);
  const couple = coupleMatch ? parseFloat(coupleMatch[1]) : 1.0;

  return { kind: "society", name, agents, ties, couple };
}

// --- Checker ---

export function check(file: SmithFile): CheckResult {
  const errors: Diagnostic[] = [];
  const agents: AgentCheck[] = [];

  for (const item of file.items) {
    if (item.kind === "agent") {
      const ac = checkAgent(item, errors);
      if (ac) agents.push(ac);
    } else if (item.kind === "society") {
      for (const agent of item.agents) {
        const ac = checkAgent(agent, errors);
        if (ac) agents.push(ac);
      }
      // Check ties
      for (const tie of item.ties) {
        if (tie.cost < (item.agents[0]?.floor ?? 2)) {
          errors.push({
            message: `Tie (${tie.from}, ${tie.to}) cost ${tie.cost} is below the floor`,
            severity: "error",
          });
        }
      }
    }
  }

  return { ok: errors.filter(e => e.severity === "error").length === 0, errors, agents };
}

function checkAgent(agent: AgentDecl, errors: Diagnostic[]): AgentCheck | null {
  const graph = agentToGraph(agent);

  // Check floor
  for (const sep of agent.self.separations) {
    if (sep.cost < agent.floor) {
      errors.push({
        message: `Separation (${sep.from}, ${sep.to}) cost ${sep.cost} is below the floor ${agent.floor}`,
        severity: "error",
        line: sep.line,
      });
    }
  }

  // Check scenes serve the purpose
  for (const scene of agent.scenes) {
    if (scene.serves !== agent.purpose.target) {
      errors.push({
        message: `Scene "${scene.name}" serves "${scene.serves}" but the agent's purpose is "${agent.purpose.target}"`,
        severity: "error",
        line: scene.line,
      });
    }
  }

  // Compute invariants
  const { chi, partition } = characterInvariant(graph);
  const floor = realisedFloor(graph);
  const nonLocal = partition.blocks.every(b => b.length > 1);

  return {
    name: agent.name,
    regime: agent.purpose.mode === "minimise" ? "character" : "task",
    chi,
    floor,
    nonLocal,
    chiPartition: partition.blocks,
  };
}

// --- Runtime (deterministic tick loop) ---

export function run(file: SmithFile, maxTicks: number = 30): RunResult {
  const steps: StepRecord[] = [];
  const counts: Record<string, number> = {};
  const residuals: Record<string, number> = {};

  // Collect all agents
  const allAgents: AgentDecl[] = [];
  for (const item of file.items) {
    if (item.kind === "agent") allAgents.push(item);
    else if (item.kind === "society") allAgents.push(...item.agents);
  }

  // Initialize
  for (const agent of allAgents) {
    counts[agent.name] = 0;
    residuals[agent.name] = 10; // Initial residual
  }

  for (let tick = 1; tick <= maxTicks; tick++) {
    for (const agent of allAgents) {
      // Phase alternation: construction on odd ticks, commitment on even
      const phase: "construction" | "commitment" = tick % 3 === 0 ? "construction" : "commitment";

      if (phase === "construction") {
        steps.push({
          tick,
          agent: agent.name,
          outcome: "observe",
          price: 0,
          residual: residuals[agent.name],
          delta: 0,
          count: counts[agent.name],
          phase,
        });
        continue;
      }

      // Water-fill across scenes
      const profiles: GainProfile[] = agent.scenes.map(s =>
        logGainProfile(s.name, s.gainK ?? 1.5)
      );
      const wf = waterFill(profiles, agent.budget);

      // Pick the best scene to act in
      const bestAlloc = wf.allocations.reduce((best, a) =>
        a.allocation > best.allocation ? a : best
      , wf.allocations[0]);

      if (bestAlloc && bestAlloc.allocation > 0) {
        const delta = bestAlloc.allocation * 0.3 * Math.exp(-tick * 0.05);
        residuals[agent.name] = Math.max(0.01, residuals[agent.name] - delta);
        counts[agent.name]++;

        steps.push({
          tick,
          agent: agent.name,
          outcome: residuals[agent.name] <= 0.02 ? "quiescent" : "commit",
          scene: bestAlloc.scene,
          price: wf.price,
          residual: residuals[agent.name],
          delta,
          count: counts[agent.name],
          phase,
          disposition: [residuals[agent.name], wf.price],
        });
      } else {
        steps.push({
          tick,
          agent: agent.name,
          outcome: "decline",
          price: wf.price,
          residual: residuals[agent.name],
          delta: 0,
          count: counts[agent.name],
          phase,
        });
      }
    }
  }

  return { steps, finalCounts: counts };
}

// --- Helpers ---

export function agentToGraph(agent: AgentDecl): WeightedGraph {
  return {
    parts: agent.self.parts,
    separations: agent.self.separations.map(s => ({
      from: s.from,
      to: s.to,
      cost: s.cost,
    })),
  };
}

export function compile(source: string): CompiledProgram {
  const { file, errors: parseErrors } = parse(source);
  const checkResult = check(file);
  checkResult.errors = [...parseErrors, ...checkResult.errors];
  checkResult.ok = checkResult.errors.filter(e => e.severity === "error").length === 0;
  return { file, check: checkResult };
}
