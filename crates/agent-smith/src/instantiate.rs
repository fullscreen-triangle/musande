// =====================================================================
//  Agent Smith — instantiation.
//
//  This framework generates agents. That is its whole job.
//
//  The rest of the crate (parse -> typecheck -> compile -> tick) is the path
//  a HUMAN takes: someone writes a `.smith` file declaring an agent, and the
//  engine builds and drives it. That path assumes the agents are known in
//  advance, which is true of a character and false of everything else.
//
//  This module is the other path. A module, mid-run, decomposes a problem
//  into subtasks and needs an agent per subtask — now, with no source file,
//  no declaration, and no pause. `instantiate` is that call. It lowers a
//  Subtask straight to a running Agent, skipping parse and typecheck because
//  there is no source text to parse and no human error to catch.
//
//  Two properties of the resulting agent matter more than anything else here:
//
//   * IT HOLDS ONE SUBTASK AND NOTHING ELSE. It cannot ask what the wider
//     task is, what came before it, or what comes after, because those
//     fields do not exist on it. A module decides the decomposition and the
//     coordination; the agent just carries its piece. This is not a
//     restriction imposed on a capable object — it is the shape of the
//     object.
//
//   * IT IS NOT PRIVILEGED. The module that generates DSL code is itself
//     built out of agents, so whatever calls `instantiate` may well have
//     been produced by `instantiate`. There is no layer above this one. The
//     function is therefore free of any assumption that its caller is a
//     human, a top-level orchestrator, or a distinguished module.
//
//  What an instantiated agent does NOT get is a self-graph. A self-graph
//  supports chi, identity conserved across change — which presupposes
//  something persisting to be identical to. A ticket holds one subtask and
//  has no ordering, so there is nothing for identity to be conserved across.
//  Callers building a standing character supply a self-graph via the DSL
//  path; callers building a ticket do not, and `chi` is left at zero rather
//  than fabricated. Same `Agent` type either way — the difference is what is
//  populated, not what is possible.
// =====================================================================

use std::collections::HashSet;
use std::sync::atomic::{AtomicUsize, Ordering};

use crate::compile::{
    hash_unit, Agent, AgentState, CompiledPurpose, CompiledScene, CompiledSelf, Phase, PurposeMode,
};
use crate::identity::LogGain;
use crate::subtask::{Graph, Raised, Subtask};
use crate::typecheck::Regime;

static TICKET_UID: AtomicUsize = AtomicUsize::new(0);

fn ticket_id() -> String {
    let n = TICKET_UID.fetch_add(1, Ordering::Relaxed);
    format!("ticket_{}", n)
}

/// How much attention an instantiated agent may spend. Defaulted rather than
/// required, because the raising module usually has no basis for a number and
/// a made-up one is worse than a uniform one.
const DEFAULT_BUDGET: f64 = 1.0;

/// An agent generated from a subtask.
///
/// It bundles the runtime `Agent` (the object the tick machinery reads and
/// writes) with the `Subtask` it carries, so a `Hook` at the seam can see
/// both the instruction and the chunks when the agent fires. Without this
/// pairing the hook would see a scene name and nothing else, and the DSL code
/// would have no route to the point of execution.
#[derive(Debug, Clone)]
pub struct Ticket {
    /// The runtime object.
    pub agent: Agent,
    /// The subtask it carries: instruction plus realising chunks.
    pub subtask: Subtask,
    /// Which module generated it. Provenance for the report; the agent
    /// itself never reads this.
    pub by: Option<String>,
}

impl Ticket {
    /// The instruction this agent carries.
    pub fn instruction(&self) -> &str {
        &self.subtask.instruction
    }

    /// The realisations this agent carries. All of them are to be executed;
    /// there is no accessor that selects one.
    pub fn chunks(&self) -> &[crate::subtask::Chunk] {
        &self.subtask.chunks
    }
}

/// Options for instantiation. Every field has a defensible default, so the
/// common call is `instantiate(subtask, Spawn::default())`.
#[derive(Debug, Clone)]
pub struct Spawn {
    /// Which module is raising this. Recorded as provenance.
    pub by: Option<String>,
    /// Attention budget. Defaults to `DEFAULT_BUDGET`.
    pub budget: f64,
    /// The resolution floor for this agent: the smallest residual it can
    /// distinguish from zero. A bounded reader cannot resolve below its own
    /// floor, so an agent that drives residual to its floor is as done as it
    /// can tell — which is what makes a ticket halt rather than grind.
    pub floor: f64,
}

impl Default for Spawn {
    fn default() -> Self {
        Spawn { by: None, budget: DEFAULT_BUDGET, floor: 0.0 }
    }
}

impl Spawn {
    /// Record the raising module.
    pub fn by(mut self, module: impl Into<String>) -> Self {
        self.by = Some(module.into());
        self
    }
    pub fn budget(mut self, b: f64) -> Self {
        self.budget = b;
        self
    }
    pub fn floor(mut self, f: f64) -> Self {
        self.floor = f;
        self
    }
}

/// Generate an agent from a subtask.
///
/// The agent's purpose is `reach <tau>` — a task-agent, which halts at
/// quiescence, rather than a character with a standing purpose. Its scenes
/// are derived from the subtask's chunks: one scene per realisation, since
/// running a realisation is the outward act available to this agent. A
/// subtask with no chunks yet still yields a working agent with a single
/// generic scene, so a module can raise an unrealised subtask and let a
/// code-generating module converge a chunk onto it later.
///
/// This does not touch a graph. Use [`instantiate_into`] to generate the
/// agent and publish its subtask as a node in one step.
pub fn instantiate(subtask: Subtask, spawn: Spawn) -> Ticket {
    let target = subtask.tau.as_str().to_string();

    // One scene per realisation. The scene's `hook` names the DSL, so a Hook
    // implementation can route on it — this is the only place the DSL tag is
    // read by this crate, and it is read as an opaque routing key, never
    // parsed.
    let mut scenes: Vec<CompiledScene> = subtask
        .chunks
        .iter()
        .enumerate()
        .map(|(i, c)| {
            let name = format!("run_{}_{}", c.dsl, i);
            CompiledScene {
                id: format!("scene_{}_{}", ticket_id(), i),
                serves: target.clone(),
                hook: c.dsl.clone(),
                gain: LogGain::new(1.0 + 0.5 * hash_unit(&name)),
                name,
            }
        })
        .collect();

    // An unrealised subtask still gets an agent: it has been raised but not
    // yet translated into code. Its single scene is the act of obtaining a
    // realisation.
    if scenes.is_empty() {
        let name = "realise".to_string();
        scenes.push(CompiledScene {
            id: format!("scene_{}_0", ticket_id()),
            serves: target.clone(),
            hook: "unrealised".to_string(),
            gain: LogGain::new(1.0 + 0.5 * hash_unit(&name)),
            name,
        });
    }

    let agent = Agent {
        id: ticket_id(),
        name: target.clone(),
        regime: Regime::Task,
        // No self-graph: a ticket has no persistence for an identity to be
        // conserved across. Left empty rather than fabricated.
        self_graph: CompiledSelf { parts: Vec::new(), separations: Vec::new() },
        chi: 0.0,
        chi_side: Vec::new(),
        chi_non_local: false,
        floor: spawn.floor,
        scenes,
        budget: spawn.budget,
        purpose: CompiledPurpose { mode: PurposeMode::Reach, target },
        coherence_keep: HashSet::new(),
        disposition: 1.0,
        count: 0,
        phase: Phase::Construction,
        trajectory: Vec::new(),
        last_residual: 1.0,
        stall_window: Vec::new(),
        state: AgentState::Running,
        floor_norm: 0.0, // set by tick::init_floor_norm before ticking
    };

    Ticket { agent, subtask, by: spawn.by }
}

/// Generate an agent and publish its subtask as a node in one step.
///
/// Returns the ticket and whether the subtask created a new node or converged
/// onto an existing one. Convergence is the normal case and is not a
/// collision to be resolved: two agents arriving at the same subtask meet at
/// one node, and the node accretes both realisations.
pub fn instantiate_into(subtask: Subtask, spawn: Spawn, graph: &mut Graph) -> (Ticket, Raised) {
    let raised = graph.raise(&subtask);
    (instantiate(subtask, spawn), raised)
}

/// Generate agents for a whole decomposition, publishing every subtask.
///
/// The order of the returned tickets is the order given, but that ordering
/// carries no meaning to the agents — none of them can observe its own
/// position, and nothing in a ticket refers to another. A module that needs
/// an ordering enforces it itself, by deciding when to raise what.
pub fn instantiate_all(
    subtasks: impl IntoIterator<Item = Subtask>,
    spawn: Spawn,
    graph: &mut Graph,
) -> Vec<Ticket> {
    subtasks
        .into_iter()
        .map(|s| instantiate_into(s, spawn.clone(), graph).0)
        .collect()
}
