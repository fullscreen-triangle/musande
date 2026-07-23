// =====================================================================
//  Agent Smith — public engine API.
//  A user (standalone) or Buhera OS imports from here.
//
//    import { build, makeTown, defaultCtx, stepTown, runTown } from
//      "@/lib/agent-smith";
//
//  Standalone flow:
//    const { ok, program, errors } = build(source);   // parse+type+compile
//    const town = makeTown(program);
//    const ctx  = defaultCtx({ keys, crowd, runHook });
//    const step = await stepTown(town, ctx);           // one tick
//
//  Buhera OS: setThinkTransport(chatCascadeTransport) to route models
//  centrally; replace ctx.probe with `purpose ask`.
// =====================================================================

export { parse, ParseError } from "./parse";
export { typecheck, typecheckAgent, CONVEX_POTENTIALS } from "./typecheck";
export { compileAgent, compileProgram, build } from "./compile";
export {
  characterInvariant,
  realisedFloor,
  waterFill,
  logGain,
  isConnected,
} from "./identity";
export { tick, initFloorNorm, LIMIT, OUTCOME } from "./tick";
export { makeTown, makeOmega, defaultCtx, stepTown, runTown } from "./town";
export {
  PROVIDERS,
  loadKeys,
  saveKeys,
  configuredProviders,
  hasModel,
  think,
  setThinkTransport,
} from "./providers";
export { makeShowcase, initialGraph, applyStep, actContent } from "./showcase";

// A ready-to-run example program: a town with a character (smith), two
// decliners (scribe, crier — off-purpose to a forge interaction), and a
// pure observer (watcher). Shown in the tool by default.
export const EXAMPLE_TOWN = `// A town: a character, two decliners, and a pure observer.
society village {

  // the smith — a CHARACTER: standing purpose, runs on.
  agent smith {
    purpose minimise forge_residual
    scenes {
      scene hammer   serves forge_residual with forge_hook
      scene contract serves forge_residual with contract_hook
      scene source   serves forge_residual with source_ore_hook
    }
    self {
      parts { skill, stock, orders, reputation }
      separations {
        (skill, stock: 3), (stock, orders: 2),
        (orders, reputation: 2), (reputation, skill: 2)
      }
    }
    budget 1.0
    floor  2.0
    coherence keeps { reputation, skill }
  }

  // the watcher — a pure OBSERVER: its purpose is a different target, so a
  // forge interaction never clears its price. It observes, free, until the
  // shared outcome-state calls for it.
  agent watcher {
    purpose reach safety
    scenes {
      scene flee serves safety with flee_hook
    }
    self {
      parts { alert, position }
      separations { (alert, position: 2) }
    }
    budget 1.0
    floor  2.0
    coherence keeps { alert }
  }

  tie (smith, watcher: 2)
  couple 4.0
}
`;

export const EXAMPLE_TASK = `// A task-agent: purpose is an attainable outcome, so it HALTS at quiescence.
agent rerun_exp {
  purpose reach verdict_confirmed
  scenes {
    scene integrate serves verdict_confirmed with kuramoto_hook
    scene tabulate  serves verdict_confirmed with aggregate_hook
    scene report    serves verdict_confirmed with emit_hook
  }
  self {
    parts { data, method, result, verdict }
    separations {
      (data, method: 2), (method, result: 2),
      (result, verdict: 2), (verdict, data: 2)
    }
  }
  budget 1.0
  floor  2.0
  coherence keeps { method, result }
}
`;
