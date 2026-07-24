// =====================================================================
//  Agent Smith — the model seam.
//  The tick-loop is deterministic everywhere EXCEPT one point: the domain
//  judgment inside observe/commit (the JS `providers.think`). We isolate
//  that behind a `Hook` trait. The standalone CLI ships `DeterministicHook`,
//  which declines to intervene — so the runtime falls back to its built-in
//  deterministic residual descent and runs fully offline. A real deployment
//  (Buhera OS) implements `Hook` with an LLM, exactly as providers.js did.
//
//  This is the empty-store discipline: the crate ships no domain answers,
//  only the seam where a judgment would be supplied.
// =====================================================================

use crate::compile::Agent;

/// A candidate act formed in the construction phase: which scene fires,
/// via which hook, and the residual it is expected to remove.
#[derive(Debug, Clone)]
pub struct Candidate {
    pub scene: String,
    pub hook: String,
    pub expected_gain: f64,
}

/// The tier-0 read of the solution-state for an agent: the residual gap and
/// an opaque hint (recent acts touching the same target).
#[derive(Debug, Clone)]
pub struct Slice {
    pub residual: f64,
    pub hint: Vec<HintEntry>,
}

/// One entry of the shared-outcome hint: who did what, and how much it moved.
#[derive(Debug, Clone)]
pub struct HintEntry {
    pub by: String,
    pub scene: String,
    pub delta: f64,
}

/// What a hook returns when it does the domain work at the irreducible seam.
/// A `reduction` overrides the deterministic descent; `content`/`model` are
/// carried onto the committed act for display.
#[derive(Debug, Clone, Default)]
pub struct HookResult {
    pub reduction: Option<f64>,
    pub content: Option<String>,
    pub model: Option<String>,
}

/// The model seam. Implement this to plug an LLM into the tick-loop.
pub trait Hook {
    /// Perform the domain work for a firing act and report its outcome.
    /// Return `None` to let the runtime apply its deterministic descent.
    fn run(&self, _agent: &Agent, _candidate: &Candidate, _slice: &Slice) -> Option<HookResult> {
        None
    }

    /// Tier-1 sufficiency judgment: is the current slice enough to act now?
    /// Default: yes (ACT). A model-backed hook can return WAIT here.
    fn judge_sufficiency(&self, _agent: &Agent, _slice: &Slice) -> bool {
        true
    }

    /// Whether this hook does real (model) work. When false, the runtime
    /// stays on its deterministic path and never calls `run`/`judge`.
    fn uses_model(&self) -> bool {
        false
    }
}

/// The offline default: declines to intervene. The runtime then uses its
/// built-in deterministic descent, so the CLI runs without any provider.
pub struct DeterministicHook;

impl Hook for DeterministicHook {}
