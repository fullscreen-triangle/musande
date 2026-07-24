// =====================================================================
//  Agent Smith — compiler (lowering).
//  Lowers a well-typed spec into a running Agent object. The compiler
//  installs the objects (self, drive, scenes) and seats the fixed runtime
//  (the tick-loop lives in tick.rs; the Agent just holds state). The four
//  invariants are honoured by construction:
//    I1 identity   — chi computed from the self-graph, label-independent
//    I2 count      — m starts at 0, only ever incremented (by tick commit)
//    I3 search     — the agent stores no answers; it re-reads Omega
//    I4 phase      — phase field flips construction <-> commitment
//  Port of compile.js.
// =====================================================================

use std::collections::HashSet;
use std::sync::atomic::{AtomicUsize, Ordering};

use crate::ast::{Purpose, Separation};
use crate::error::Diagnostic;
use crate::identity::LogGain;
use crate::parse::parse;
use crate::typecheck::{typecheck, Regime, TypedAgent, TypedMember, TypedProgram};

static UID: AtomicUsize = AtomicUsize::new(0);

/// A fresh cosmetic id (e.g. "agent_3", "scene_a"). Base-36 like the JS.
/// Ids are cosmetic — nothing in the runtime logic depends on their value.
fn uid(prefix: &str) -> String {
    let n = UID.fetch_add(1, Ordering::Relaxed);
    format!("{}_{}", prefix, to_base36(n))
}

fn to_base36(mut n: usize) -> String {
    const DIGITS: &[u8] = b"0123456789abcdefghijklmnopqrstuvwxyz";
    if n == 0 {
        return "0".to_string();
    }
    let mut out = Vec::new();
    while n > 0 {
        out.push(DIGITS[n % 36]);
        n /= 36;
    }
    out.reverse();
    String::from_utf8(out).unwrap()
}

/// A compiled scene: a runtime activity with a default concave gain profile.
#[derive(Debug, Clone)]
pub struct CompiledScene {
    pub id: String,
    pub name: String,
    pub serves: String,
    pub hook: String,
    pub gain: LogGain,
}

/// The self-graph carried on a compiled agent.
#[derive(Debug, Clone)]
pub struct CompiledSelf {
    pub parts: Vec<String>,
    pub separations: Vec<Separation>,
}

/// The agent's purpose reduced to (mode, target).
#[derive(Debug, Clone)]
pub struct CompiledPurpose {
    pub mode: PurposeMode,
    /// for reach: the outcome name; for minimise: the potential name.
    pub target: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PurposeMode {
    Minimise,
    Reach,
}

/// The agent's runtime lifecycle state.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "lowercase")]
pub enum AgentState {
    Running,
    Quiescent,
    Observing,
}

/// The instantaneous phase (I4: construction xor commitment).
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Phase {
    Construction,
    Commitment,
}

/// A compiled Agent instance — the object the runtime reads/writes.
#[derive(Debug, Clone)]
pub struct Agent {
    pub id: String,
    pub name: String,
    pub regime: Regime,
    pub self_graph: CompiledSelf,
    pub chi: f64,
    pub chi_side: Vec<String>,
    pub chi_non_local: bool,
    pub floor: f64,
    pub scenes: Vec<CompiledScene>,
    pub budget: f64,
    pub purpose: CompiledPurpose,
    pub coherence_keep: HashSet<String>,

    // runtime state
    pub disposition: f64, // in [0,1]: distance-to-purpose proxy, 1 = far, 0 = at
    pub count: u64,       // m: monotone committed count (I2)
    pub phase: Phase,     // I4
    pub trajectory: Vec<String>, // the address: sequence of committed step-labels
    pub last_residual: f64,
    pub stall_window: Vec<f64>, // recent residual deltas, for the diagnosis
    pub state: AgentState,

    /// Normalised floor in [0,1] residual space; set by tick::init_floor_norm.
    pub floor_norm: f64,
}

/// Lower a well-typed agent into a compiled Agent instance.
pub fn compile_agent(typed: &TypedAgent) -> Agent {
    let spec = &typed.spec;
    let derived = &typed.derived;

    let scenes = spec
        .scenes
        .iter()
        .map(|s| CompiledScene {
            id: uid("scene"),
            name: s.name.clone(),
            serves: s.serves.clone(),
            hook: s.hook.clone(),
            // default concave gain profile; a Buhera deployment can override
            // per hook. Richness varies a little by scene so water-filling has
            // something to do.
            gain: LogGain::new(1.0 + 0.5 * hash_unit(&s.name)),
        })
        .collect();

    let sg = spec.self_graph.as_ref().unwrap();
    let purpose = match spec.purpose.as_ref().unwrap() {
        Purpose::Reach { outcome, .. } => CompiledPurpose {
            mode: PurposeMode::Reach,
            target: outcome.clone(),
        },
        Purpose::Minimise { potential, .. } => CompiledPurpose {
            mode: PurposeMode::Minimise,
            target: potential.clone(),
        },
    };
    let coherence_keep = spec
        .coherence
        .as_ref()
        .map(|c| c.keeps.iter().cloned().collect())
        .unwrap_or_default();

    Agent {
        id: uid("agent"),
        name: spec.name.clone(),
        regime: derived.regime,
        self_graph: CompiledSelf {
            parts: sg.parts.clone(),
            separations: sg.separations.clone(),
        },
        chi: derived.chi,
        chi_side: derived.chi_side.clone(),
        chi_non_local: derived.chi_non_local,
        floor: derived.realised_floor,
        scenes,
        budget: spec.budget.unwrap(),
        purpose,
        coherence_keep,
        disposition: 1.0,
        count: 0,
        phase: Phase::Construction,
        trajectory: Vec::new(),
        last_residual: 1.0,
        stall_window: Vec::new(),
        state: AgentState::Running,
        floor_norm: 0.0, // set by init_floor_norm before ticking
    }
}

/// A compiled program: a single agent or a society.
#[derive(Debug, Clone)]
pub struct Program {
    pub kind: ProgramKind,
    pub name: Option<String>,
    pub agents: Vec<Agent>,
    pub ties: Vec<crate::ast::Tie>,
    pub couple: Option<f64>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProgramKind {
    Agent,
    Society,
}

/// Compile a whole program (agent or society) from a typed program.
pub fn compile_program(typed: &TypedProgram) -> Program {
    match typed {
        TypedProgram::Society { name, members, ties, couple } => {
            let agents = members
                .iter()
                .filter_map(|m| match m {
                    TypedMember::Agent(a) => Some(compile_agent(a)),
                    TypedMember::Ref { .. } => None,
                })
                .collect();
            Program {
                kind: ProgramKind::Society,
                name: Some(name.clone()),
                agents,
                ties: ties.clone(),
                couple: *couple,
            }
        }
        TypedProgram::Agent(a) => Program {
            kind: ProgramKind::Agent,
            name: None,
            agents: vec![compile_agent(a)],
            ties: Vec::new(),
            couple: None,
        },
    }
}

/// The result of the full build pipeline.
pub struct BuildResult {
    pub ok: bool,
    pub errors: Vec<Diagnostic>,
    pub program: Option<Program>,
}

/// Full pipeline: source -> parse -> typecheck -> compile.
pub fn build(source: &str) -> BuildResult {
    let spec = match parse(source) {
        Ok(s) => s,
        Err(e) => {
            return BuildResult {
                ok: false,
                errors: vec![e.into_diagnostic()],
                program: None,
            };
        }
    };
    let tc = typecheck(&spec);
    if !tc.ok {
        return BuildResult { ok: false, errors: tc.errors, program: None };
    }
    let program = compile_program(tc.typed.as_ref().unwrap());
    BuildResult { ok: true, errors: Vec::new(), program: Some(program) }
}

/// Deterministic FNV-1a hash -> [0,1), so scene richness is stable across
/// runs. Ported bit-for-bit from compile.js `hashUnit` (32-bit wrapping,
/// then `% 1000 / 1000`).
pub fn hash_unit(s: &str) -> f64 {
    let mut h: u32 = 2166136261;
    for byte in s.bytes() {
        h ^= byte as u32;
        h = h.wrapping_mul(16777619);
    }
    ((h % 1000) as f64) / 1000.0
}
