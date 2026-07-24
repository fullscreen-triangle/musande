// =====================================================================
//  Agent Smith — the town (society) and the shared solution-state.
//  A town holds many agents and ONE solution-state Omega. Every tick, each
//  agent reads Omega, decides, and (if it commits) changes Omega — which the
//  others read next tick. This is outcome-space coordination: no agent holds
//  a model of any other; they meet in Omega. Port of town.js.
//
//  The runtime context (Ctx) supplies:
//    - probe(omega, agent): tier-0 deterministic read → { residual, hint }.
//      Empty-dictionary: derives the residual from Omega, stores nothing.
//    - coherent(agent, candidate): the coherence check.
//    - hook: the tier-1 domain work (the irreducible seam), see hook.rs.
//    - apply_to_omega(...): commit's effect on the shared state.
// =====================================================================

use std::collections::HashMap;

use crate::compile::{Agent, Program, ProgramKind};
use crate::hook::{Candidate, DeterministicHook, HintEntry, Hook, HookResult, Slice};
use crate::identity::character_invariant;
use crate::tick::{init_floor_norm, tick, Outcome, TickRecord};

/// A committed act as recorded in the shared outcome log.
#[derive(Debug, Clone, serde::Serialize)]
pub struct LogEntry {
    pub tick: u64,
    pub by: String,
    pub target: String,
    pub scene: String,
    pub delta: f64,
    pub content: Option<String>,
}

/// The solution-state Omega. Tracks, per purpose-target, a global residual in
/// [0,1] (1 = untouched, floor = as solved as a bounded reader can tell), and
/// a log of committed acts (the shared outcome record every agent reads).
#[derive(Debug, Clone, Default)]
pub struct Omega {
    pub residual: HashMap<String, f64>,
    pub log: Vec<LogEntry>,
    pub tick_index: u64,
}

/// Build a solution-state for a set of agents. A standalone agent (single
/// target) always has work: start far. In a mixed town, a task/reach agent
/// sharing the town with characters pursuing OTHER targets starts at its floor
/// (already satisfied) — a pure OBSERVER until another agent's act RAISES its
/// residual (the penguin-watcher: safe until danger).
pub fn make_omega(agents: &[Agent]) -> Omega {
    let mut residual: HashMap<String, f64> = HashMap::new();
    let targets: std::collections::HashSet<&str> =
        agents.iter().map(|a| a.purpose.target.as_str()).collect();
    let n_targets = targets.len();
    for a in agents {
        let t = &a.purpose.target;
        if residual.contains_key(t) {
            continue;
        }
        let standalone = n_targets == 1;
        let has_work = a.regime == crate::typecheck::Regime::Character || standalone;
        residual.insert(t.clone(), if has_work { 1.0 } else { a.floor_norm });
    }
    Omega { residual, log: Vec::new(), tick_index: 0 }
}

/// The society-level identity: chi over the agent quotient (ties as edges).
#[derive(Debug, Clone)]
pub struct Society {
    pub chi: f64,
    pub side: Vec<String>,
    pub couple: Option<f64>,
}

/// A Town: many agents, one Omega, an optional society identity.
pub struct Town {
    pub name: String,
    pub agents: Vec<Agent>,
    pub omega: Omega,
    pub society: Option<Society>,
    pub program: Program,
}

/// Build a Town from a compiled program.
pub fn make_town(program: Program) -> Town {
    let mut agents = program.agents.clone();
    for a in &mut agents {
        init_floor_norm(a);
    }
    let omega = make_omega(&agents);

    let mut society = None;
    if program.kind == ProgramKind::Society && !program.ties.is_empty() {
        let parts: Vec<String> = agents.iter().map(|a| a.name.clone()).collect();
        let separations: Vec<crate::ast::Separation> = program
            .ties
            .iter()
            .map(|t| crate::ast::Separation {
                a: t.a.clone(),
                b: t.b.clone(),
                cost: t.cost,
                line: 0,
            })
            .collect();
        let (chi, side) = character_invariant(&parts, &separations);
        // order side to match agent order for stable output
        let side_ordered: Vec<String> =
            parts.iter().filter(|p| side.contains(*p)).cloned().collect();
        society = Some(Society {
            chi,
            side: if side_ordered.is_empty() { side.into_iter().collect() } else { side_ordered },
            couple: program.couple,
        });
    }

    let name = program.name.clone().unwrap_or_else(|| "town".to_string());
    Town { name, agents, omega, society, program }
}

/// The runtime context: the model seam plus the deterministic reads/writes of
/// the shared state. `use_model` gates the tier-1 path (default off → fully
/// deterministic, offline).
pub struct Ctx {
    pub use_model: bool,
    pub hook: Box<dyn Hook>,
}

impl Default for Ctx {
    fn default() -> Self {
        Ctx { use_model: false, hook: Box::new(DeterministicHook) }
    }
}

impl Ctx {
    /// A deterministic, offline context (no model).
    pub fn deterministic() -> Self {
        Ctx::default()
    }

    /// A context backed by a model hook (the tier-1 seam active).
    pub fn with_hook(hook: Box<dyn Hook>) -> Self {
        let use_model = hook.uses_model();
        Ctx { use_model, hook }
    }

    /// Tier-0 deterministic read of Omega for this agent's purpose. The agent
    /// reads Omega's residual as its disposition (it stores no task; it
    /// re-reads the state each tick — I3).
    pub fn probe(&self, omega: &Omega, agent: &mut Agent) -> Slice {
        let residual = *omega.residual.get(&agent.purpose.target).unwrap_or(&1.0);
        let hint: Vec<HintEntry> = omega
            .log
            .iter()
            .filter(|e| e.target == agent.purpose.target)
            .rev()
            .take(3)
            .map(|e| HintEntry { by: e.by.clone(), scene: e.scene.clone(), delta: e.delta })
            .collect::<Vec<_>>()
            .into_iter()
            .rev()
            .collect();
        agent.disposition = residual;
        Slice { residual, hint }
    }

    /// Coherence: the act must keep the agent's coherence condition. The
    /// standalone default is always coherent unless a hook says otherwise.
    pub fn coherent(&self, _agent: &Agent, _candidate: &Candidate) -> bool {
        true
    }

    /// Tier-1 domain work via the hook. Opaque to the runtime; we read only
    /// its outcome.
    pub fn run_hook(&self, agent: &Agent, candidate: &Candidate, slice: &Slice) -> Option<HookResult> {
        if !self.use_model {
            return None;
        }
        self.hook.run(agent, candidate, slice)
    }

    /// Commit's effect on Omega: lower the shared residual for the target and
    /// append the act to the shared log.
    pub fn apply_to_omega(
        &self,
        omega: &mut Omega,
        agent: &Agent,
        candidate: &Candidate,
        delta: f64,
        hook_result: &Option<HookResult>,
    ) {
        let t = &agent.purpose.target;
        let cur = *omega.residual.get(t).unwrap_or(&1.0);
        omega.residual.insert(t.clone(), (cur - delta).max(agent.floor_norm));
        omega.log.push(LogEntry {
            tick: omega.tick_index,
            by: agent.name.clone(),
            target: t.clone(),
            scene: candidate.scene.clone(),
            delta: round3(delta),
            content: hook_result.as_ref().and_then(|h| h.content.clone()),
        });
    }
}

/// The result of stepping the whole town once.
#[derive(Debug, Clone, serde::Serialize)]
pub struct StepResult {
    pub tick: u64,
    pub records: Vec<TickRecord>,
    pub residuals: HashMap<String, f64>,
    pub quiescent: bool,
    pub done: bool,
}

/// Step the whole town once: every agent takes a tick against the shared
/// Omega. Agents are stepped in order; commits apply immediately so later
/// agents in the same tick can see earlier commits (this is what makes the
/// penguin-watcher run in the same wave).
pub fn step_town(town: &mut Town, ctx: &Ctx) -> StepResult {
    town.omega.tick_index += 1;
    let mut records = Vec::with_capacity(town.agents.len());
    // Step agents by index: `&mut town.agents[i]` and `&mut town.omega` are
    // disjoint fields, so each tick can hold both mutable borrows.
    for i in 0..town.agents.len() {
        let rec = tick(&mut town.agents[i], &mut town.omega, ctx);
        records.push(rec);
    }
    let any_live = town.agents.iter().any(|a| a.state != crate::compile::AgentState::Quiescent);
    let any_progress = records.iter().any(|r| r.outcome == Outcome::Commit);
    let all_not_running = town
        .agents
        .iter()
        .all(|a| a.state != crate::compile::AgentState::Running);
    StepResult {
        tick: town.omega.tick_index,
        records,
        residuals: town.omega.residual.clone(),
        quiescent: !any_progress && all_not_running,
        done: !any_live,
    }
}

/// Run the town until quiescence or a max number of ticks.
pub fn run_town(town: &mut Town, ctx: &Ctx, max_ticks: usize) -> Vec<StepResult> {
    let mut history = Vec::new();
    for _ in 0..max_ticks {
        let step = step_town(town, ctx);
        let stop = step.done || step.quiescent;
        history.push(step);
        if stop {
            break;
        }
    }
    history
}

fn round3(v: f64) -> f64 {
    (v * 1000.0).round() / 1000.0
}
