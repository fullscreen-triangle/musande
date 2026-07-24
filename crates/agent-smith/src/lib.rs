// =====================================================================
//  Agent Smith — public engine API.
//  A bounded-agent DSL and tick-loop engine: the runnable core of the
//  split-attention synchronised-agents paper. A user (standalone) or a host
//  runtime (Buhera OS) drives the same pipeline:
//
//    let built = build(source);            // parse + typecheck + compile
//    let mut town = make_town(built.program.unwrap());
//    let ctx = Ctx::deterministic();       // offline; or Ctx::with_hook(..)
//    let history = run_town(&mut town, &ctx, 30);
//
//  The four invariants are honoured by construction:
//    I1 identity — chi(A), a conserved non-local graph invariant.
//    I2 count    — a monotone committed count that never resets.
//    I3 search   — the agent stores no answers; it re-reads Omega each tick.
//    I4 phase    — construction and commitment never share an instant.
//
//  The one non-deterministic point (the domain judgment) is the `Hook` seam;
//  the standalone default `DeterministicHook` runs the whole engine offline.
// =====================================================================

pub mod ast;
pub mod compile;
pub mod error;
pub mod examples;
pub mod hook;
pub mod identity;
pub mod parse;
pub mod tick;
pub mod town;
pub mod typecheck;

// ---- flat re-exports (the ergonomic surface) ----

pub use error::{Diagnostic, ParseError};

pub use ast::{
    AgentSpec, Coherence, Member, Purpose, Scene, SelfGraph, Separation, SocietySpec, Spec, Tie,
};
pub use parse::parse;

pub use identity::{
    character_invariant, is_connected, realised_floor, water_fill, water_fill_price, LogGain,
    SceneCost,
};

pub use typecheck::{
    typecheck, typecheck_agent, Derived, Regime, TypeCheck, TypedAgent, TypedMember, TypedProgram,
    CONVEX_POTENTIALS,
};

pub use compile::{
    build, compile_agent, compile_program, hash_unit, Agent, AgentState, BuildResult,
    CompiledPurpose, CompiledScene, CompiledSelf, Phase, Program, ProgramKind, PurposeMode,
};

pub use hook::{Candidate, DeterministicHook, HintEntry, Hook, HookResult, Slice};

pub use tick::{init_floor_norm, tick, Limit, Outcome, TickRecord};

pub use town::{
    make_omega, make_town, run_town, step_town, Ctx, LogEntry, Omega, Society, StepResult, Town,
};

pub use examples::{EXAMPLE_TASK, EXAMPLE_TOWN};
