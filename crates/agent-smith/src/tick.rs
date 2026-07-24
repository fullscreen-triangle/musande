// =====================================================================
//  Agent Smith — the tick-loop.
//  What a compiled agent does each tick: observe → diagnose → commit.
//  The agent acts on the STATE OF THE SOLUTION, not on internal reasoning.
//  Port of tick.js (the JS async is gone: the only reason it was async was
//  the model call, which is now the synchronous Hook seam).
//
//  observe : read a slice of the shared solution-state Omega (tier 0 cheap
//            probe; escalate to a model read only on residue). Never stores
//            the task; re-reads Omega. → residual gap + a candidate act.
//  diagnose: read the residual descent → a typed limit.
//  commit  : a RUNTIME-owned gate reading the OUTCOME of the candidate act.
//            Fires iff (sufficiency: outcome-gain clears the price) AND
//            (coherence). Else the agent stays a pure observer — valid,
//            almost free, contributes 0.
// =====================================================================

use crate::compile::{Agent, AgentState, Phase};
use crate::hook::{Candidate, HookResult, Slice};
use crate::identity::{water_fill_price, SceneCost};
use crate::town::{Ctx, Omega};

/// The diagnosed limit on the agent's descent this tick.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum Limit {
    Converging,
    #[serde(rename = "compute-limited")]
    Compute,
    #[serde(rename = "structure-limited")]
    Structure,
}

/// The outcome of a tick's commitment gate.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Outcome {
    Commit,
    Observe,   // gate did not fire; pure observer this tick
    Decline,   // off-purpose / incoherent for this interaction
    Quiescent, // task-agent reached its attainable outcome
}

impl Outcome {
    pub fn as_str(&self) -> &'static str {
        match self {
            Outcome::Commit => "commit",
            Outcome::Observe => "observe",
            Outcome::Decline => "decline",
            Outcome::Quiescent => "quiescent",
        }
    }
}

/// The per-tick record surfaced to the UI/CLI.
#[derive(Debug, Clone, serde::Serialize)]
pub struct TickRecord {
    pub agent: String,
    pub regime: Option<String>,
    pub outcome: Outcome,
    pub limit: Option<Limit>,
    pub tier: u8,
    pub price: f64,
    pub residual: f64,
    pub delta: f64,
    pub count: u64,
    pub scene: Option<String>,
    pub content: Option<String>,
    pub model: Option<String>,
    pub reason: Option<String>,
}

/// The result of the observe phase.
struct Obs {
    residual: f64,
    candidate: Option<Candidate>,
    tier: u8,
    slice: Slice,
    price: f64,
}

/// The result of the commit gate.
struct CommitResult {
    outcome: Outcome,
    delta: f64,
    act: Option<Act>,
    reason: Option<String>,
}

struct Act {
    scene: String,
    #[allow(dead_code)]
    hook: String,
    #[allow(dead_code)]
    count: u64,
    content: Option<String>,
    model: Option<String>,
}

/// Normalised floor: the residual level the agent treats as "at purpose".
/// Scale the graph floor into [0,1] residual space; a small positive number so
/// the gap never closes to zero (the floor theorem).
pub fn init_floor_norm(agent: &mut Agent) {
    agent.floor_norm = (0.02 + 0.01 * if agent.floor > 0.0 { agent.floor } else { 1.0 }).min(0.08);
    agent.disposition = 1.0;
    agent.last_residual = 1.0;
}

fn water_fill_price_for(agent: &Agent) -> f64 {
    let scenes: Vec<SceneCost> = agent
        .scenes
        .iter()
        .map(|s| SceneCost { id: s.id.clone(), gain: s.gain })
        .collect();
    water_fill_price(&scenes, agent.budget)
}

/// observe: tier-0 deterministic probe; escalate to a model read only in the
/// "unsure" band near the floor, where a judgment is genuinely needed.
fn observe(agent: &mut Agent, omega: &Omega, ctx: &Ctx) -> Obs {
    let slice = ctx.probe(omega, agent);
    let mut residual = slice.residual;
    let mut tier = 0u8;
    let mut candidate: Option<Candidate> = None;

    let price = water_fill_price_for(agent);
    let gap = (residual - agent.floor_norm).max(0.0);
    // effective gain of a scene scales with the residual gap: acting pays in
    // proportion to how far the solution-state is from this agent's purpose.
    let eff_gain = |g0: f64| g0 * gap;

    let active: Vec<&crate::compile::CompiledScene> =
        agent.scenes.iter().filter(|s| eff_gain(s.gain.g0()) > price).collect();
    if active.is_empty() {
        // no scene clears the price for this state → nothing to do (observer)
        return Obs { residual, candidate: None, tier, slice, price };
    }

    // ambiguity: escalate to a model read only in the unsure band near floor.
    let unsure_band = gap > 0.0 && gap < 0.15;
    if unsure_band && ctx.use_model {
        tier = 1;
        let act = ctx.hook.judge_sufficiency(agent, &slice);
        if act {
            let s0 = &agent.scenes[0];
            candidate = Some(Candidate {
                scene: s0.name.clone(),
                hook: s0.hook.clone(),
                expected_gain: eff_gain(agent.scenes[0].gain.g0()),
            });
        }
        // residual unchanged in the deterministic-judgment fallback
        residual = slice.residual;
    } else {
        // deterministic candidate: the highest-gain active scene
        let scene = active
            .iter()
            .copied()
            .reduce(|a, b| if eff_gain(b.gain.g0()) > eff_gain(a.gain.g0()) { b } else { a })
            .unwrap();
        candidate = Some(Candidate {
            scene: scene.name.clone(),
            hook: scene.hook.clone(),
            expected_gain: eff_gain(scene.gain.g0()),
        });
    }

    Obs { residual, candidate, tier, slice, price }
}

/// diagnose: read the residual descent over recent ticks (agent.stall_window).
fn diagnose(agent: &Agent) -> Limit {
    let win = &agent.stall_window;
    if win.is_empty() {
        return Limit::Compute;
    }
    let recent: f64 = win.iter().rev().take(3).sum();
    if recent <= 1e-9 {
        return Limit::Structure; // no descent over the window: stall
    }
    let last = *win.last().unwrap();
    if last > 0.02 {
        Limit::Converging
    } else {
        Limit::Compute
    }
}

/// commit: the runtime sufficiency gate. Reads the OUTCOME of the candidate
/// act. Fires iff sufficiency AND coherence. On fire: deposit act, increment
/// count (I2), extend trajectory, and change omega.
fn commit(agent: &mut Agent, obs: &Obs, omega: &mut Omega, ctx: &Ctx) -> CommitResult {
    let residual = obs.residual;
    let price = obs.price;

    // task-agent that has reached its attainable outcome → quiescent, halts —
    // but only if it actually did work to get there (committed >= 1 act). A
    // task-agent that starts already at its floor never had work: it is a pure
    // OBSERVER (ready to act if the shared state raises its residual).
    if agent.regime == crate::typecheck::Regime::Task && residual <= agent.floor_norm + 1e-6 {
        if agent.count > 0 {
            agent.state = AgentState::Quiescent;
            return CommitResult { outcome: Outcome::Quiescent, delta: 0.0, act: None, reason: None };
        }
        agent.state = AgentState::Observing;
        return CommitResult { outcome: Outcome::Observe, delta: 0.0, act: None, reason: None };
    }

    // no candidate cleared the price → pure observer (floor case). Free.
    let candidate = match &obs.candidate {
        None => {
            agent.state = AgentState::Observing;
            return CommitResult { outcome: Outcome::Observe, delta: 0.0, act: None, reason: None };
        }
        Some(c) => c.clone(),
    };

    // sufficiency: does the candidate's OUTCOME-gain clear the attention price?
    let gain = candidate.expected_gain;
    let sufficient = gain > price;

    // coherence: would the act break the agent's coherence condition?
    let coherent = ctx.coherent(agent, &candidate);

    if !sufficient || !coherent {
        agent.state = if coherent { AgentState::Observing } else { AgentState::Running };
        return CommitResult {
            outcome: if coherent { Outcome::Observe } else { Outcome::Decline },
            delta: 0.0,
            act: None,
            reason: Some(if !sufficient { "below price" } else { "incoherent" }.to_string()),
        };
    }

    // FIRE. Perform the domain work via the hook (model at the irreducible
    // seam) and read its outcome. The hook is opaque; we read only its effect.
    let hook_result: Option<HookResult> = ctx.run_hook(agent, &candidate, &obs.slice);

    // outcome effect on the residual (deterministic descent scaled by gain, or
    // the model-reported reduction if the hook returned one).
    let reduction = match hook_result.as_ref().and_then(|h| h.reduction) {
        Some(r) => r,
        None => {
            let det = 0.15 + 0.1 * (gain / (price + 1e-9) - 1.0);
            (residual - agent.floor_norm).min(det)
        }
    };
    let before = agent.disposition;
    agent.disposition = (before - reduction.max(0.0)).max(agent.floor_norm);

    // I2: increment the monotone committed count; extend the trajectory.
    agent.count += 1;
    agent.trajectory.push(label_step(&candidate, agent.count));
    agent.last_residual = agent.disposition;
    agent.state = AgentState::Running;

    let delta = before - agent.disposition;
    // update omega: the committed act changes the shared solution-state every
    // other agent reads next tick (outcome-space coordination).
    ctx.apply_to_omega(omega, agent, &candidate, delta, &hook_result);

    let content = hook_result.as_ref().and_then(|h| h.content.clone());
    let model = hook_result.as_ref().and_then(|h| h.model.clone());
    CommitResult {
        outcome: Outcome::Commit,
        delta,
        act: Some(Act {
            scene: candidate.scene.clone(),
            hook: candidate.hook.clone(),
            count: agent.count,
            content,
            model,
        }),
        reason: None,
    }
}

/// tick: one full observe → diagnose → commit cycle, respecting phase
/// exclusion (observe/diagnose in construction; commit in commitment).
pub fn tick(agent: &mut Agent, omega: &mut Omega, ctx: &Ctx) -> TickRecord {
    if agent.state == AgentState::Quiescent {
        return TickRecord {
            agent: agent.name.clone(),
            regime: Some(agent.regime.as_str().to_string()),
            outcome: Outcome::Quiescent,
            limit: None,
            tier: 0,
            price: 0.0,
            residual: round3(agent.disposition),
            delta: 0.0,
            count: agent.count,
            scene: None,
            content: None,
            model: None,
            reason: None,
        };
    }

    // construction phase: observe + diagnose (no act)
    agent.phase = Phase::Construction;
    let obs = observe(agent, omega, ctx);
    let limit = diagnose(agent);

    // commitment phase: the gate
    agent.phase = Phase::Commitment;
    let res = commit(agent, &obs, omega, ctx);

    // record the residual delta for the next diagnosis
    agent.stall_window.push(res.delta);
    if agent.stall_window.len() > 8 {
        agent.stall_window.remove(0);
    }

    let scene = res
        .act
        .as_ref()
        .map(|a| a.scene.clone())
        .or_else(|| obs.candidate.as_ref().map(|c| c.scene.clone()));

    TickRecord {
        agent: agent.name.clone(),
        regime: Some(agent.regime.as_str().to_string()),
        outcome: res.outcome,
        limit: Some(limit),
        tier: obs.tier,
        price: round3(obs.price),
        residual: round3(agent.disposition),
        delta: round3(res.delta),
        count: agent.count,
        scene,
        content: res.act.as_ref().and_then(|a| a.content.clone()),
        model: res.act.as_ref().and_then(|a| a.model.clone()),
        reason: res.reason,
    }
}

fn label_step(candidate: &Candidate, count: u64) -> String {
    // the trajectory ADDRESS: how we got here (scene + count), not the content.
    format!("{}#{}", candidate.scene, count)
}

fn round3(v: f64) -> f64 {
    (v * 1000.0).round() / 1000.0
}
