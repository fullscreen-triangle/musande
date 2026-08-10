// =====================================================================
//  Agent Smith — the typed surface.
//
//  `index.js` is the barrel, and being JavaScript it can re-export values but
//  not types. Import types from here:
//
//    import { subtask, chunk, Graph, instantiateInto } from "@/lib/agent-smith";
//    import type { Subtask, Ticket, Value } from "@/lib/agent-smith/types";
//
//  Only the instantiation layer is typed. The older DSL path (parse,
//  typecheck, compile, tick, town) remains untyped JS and is unchanged.
// =====================================================================

export type {
  Tau,
  Chunk,
  Value,
  Subtask,
  Raised,
} from "./subtask";

export type { Agent, Gain, Scene, Spawn, Ticket } from "./instantiate";

export type {
  Executor,
  Executors,
  ExecContext,
  ExecResult,
  ChunkOutcome,
  RunHook,
} from "./execute";

// Classes are both a value and a type; re-exported here for the type
// position, and available as values from the barrel.
export type { Node, Graph } from "./subtask";
