// =====================================================================
//  Agent Smith — type checker.
//  The four typing rules of the paper, as a decidable front-end check. A
//  spec that types denotes a well-formed agent object; the compiler
//  instantiates all and only well-typed specs. Port of typecheck.js.
//
//  Rule (Self):   parts connected, simple, nonempty; every cost >= floor > 0.
//  Rule (Drive):  purpose is strongly convex (minimise <phi>) or reach <o>.
//  Rule (Scene):  every scene serves the ONE declared purpose; has a hook.
//  Rule (Agent):  all of the above, plus budget > 0 and floor > 0.
// =====================================================================

use std::collections::HashSet;

use crate::ast::*;
use crate::error::Diagnostic;
use crate::identity::{character_invariant, is_connected, realised_floor};

/// The strongly-convex potentials the standalone tool knows by name. A
/// Buhera deployment can extend this registry; `reach <outcome>` always
/// types (squared distance is 1-strongly convex).
pub const CONVEX_POTENTIALS: &[&str] = &[
    "forge_residual",
    "verdict_confirmed",
    "bake_residual",
    "residual",
    "distance_to_goal",
];

fn is_convex_potential(name: &str) -> bool {
    CONVEX_POTENTIALS.contains(&name)
}

/// An agent's regime: a standing character (minimise) or a task-agent that
/// halts at quiescence (reach).
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Regime {
    Character,
    Task,
}

impl Regime {
    pub fn as_str(&self) -> &'static str {
        match self {
            Regime::Character => "character",
            Regime::Task => "task",
        }
    }
}

/// Quantities derived from a well-typed agent spec.
#[derive(Debug, Clone)]
pub struct Derived {
    pub chi: f64,
    pub chi_side: Vec<String>,
    pub chi_non_local: bool,
    pub realised_floor: f64,
    pub regime: Regime,
}

/// A well-typed agent: its spec plus the derived quantities.
#[derive(Debug, Clone)]
pub struct TypedAgent {
    pub spec: AgentSpec,
    pub derived: Derived,
}

/// A well-typed program.
#[derive(Debug, Clone)]
pub enum TypedProgram {
    Agent(TypedAgent),
    Society {
        name: String,
        members: Vec<TypedMember>,
        ties: Vec<Tie>,
        couple: Option<f64>,
    },
}

/// A typed society member: an inline typed agent or a carried-through ref.
/// The agent variant is boxed so the enum stays small (a `TypedAgent` carries
/// the full spec + derived quantities).
#[derive(Debug, Clone)]
pub enum TypedMember {
    Agent(Box<TypedAgent>),
    Ref { name: String },
}

/// The outcome of type-checking.
pub struct TypeCheck {
    pub ok: bool,
    pub errors: Vec<Diagnostic>,
    pub typed: Option<TypedProgram>,
}

fn err(errors: &mut Vec<Diagnostic>, message: impl Into<String>, line: Option<u32>) {
    errors.push(Diagnostic::new(message, line));
}

/// Rule (Self).
fn check_self(spec: &AgentSpec, errors: &mut Vec<Diagnostic>) -> bool {
    let start = errors.len();
    let self_graph = match &spec.self_graph {
        None => {
            err(errors, "agent has no \"self { ... }\" block", Some(spec.line));
            return false;
        }
        Some(s) => s,
    };
    if self_graph.parts.is_empty() {
        err(errors, "self has no parts", Some(self_graph.line));
        return false;
    }
    // simple: no self-loops, no duplicate part names
    let mut seen: HashSet<&String> = HashSet::new();
    for p in &self_graph.parts {
        if seen.contains(p) {
            err(errors, format!("duplicate part \"{}\"", p), Some(self_graph.line));
        }
        seen.insert(p);
    }
    for s in &self_graph.separations {
        if s.a == s.b {
            err(errors, format!("self-loop on \"{}\" is not allowed", s.a), Some(s.line));
        }
        if !seen.contains(&s.a) {
            err(errors, format!("separation references unknown part \"{}\"", s.a), Some(s.line));
        }
        if !seen.contains(&s.b) {
            err(errors, format!("separation references unknown part \"{}\"", s.b), Some(s.line));
        }
    }
    // floor: every cost >= floor > 0
    match spec.floor {
        None => err(errors, "agent has no \"floor\"", Some(spec.line)),
        Some(f) if f <= 0.0 || f.is_nan() => {
            err(errors, format!("floor must be > 0 (got {})", fmt(f)), Some(spec.line));
        }
        _ => {}
    }
    if let Some(floor) = spec.floor {
        for s in &self_graph.separations {
            if s.cost < floor || s.cost.is_nan() {
                err(
                    errors,
                    format!(
                        "separation ({}, {}) cost {} is below the floor {}",
                        s.a,
                        s.b,
                        fmt(s.cost),
                        fmt(floor)
                    ),
                    Some(s.line),
                );
            }
        }
    }
    // connected
    if self_graph.parts.len() > 1 && !is_connected(&self_graph.parts, &self_graph.separations) {
        err(
            errors,
            "self-graph is not connected (an agent must be one whole)",
            Some(self_graph.line),
        );
        return false;
    }
    errors.len() == start
}

/// Rule (Drive).
fn check_drive(spec: &AgentSpec, errors: &mut Vec<Diagnostic>) -> bool {
    match &spec.purpose {
        None => {
            err(errors, "agent has no \"purpose\"", Some(spec.line));
            false
        }
        // squared distance to an outcome is always 1-strongly convex: types.
        Some(Purpose::Reach { .. }) => true,
        Some(Purpose::Minimise { potential, line }) => {
            if !is_convex_potential(potential) {
                err(
                    errors,
                    format!(
                        "purpose \"minimise {}\" is not a known strongly convex potential; \
                         register it or use \"reach <outcome>\" for a task-agent",
                        potential
                    ),
                    Some(*line),
                );
                false
            } else {
                true
            }
        }
    }
}

/// Rule (Scene): every scene serves the one declared purpose and has a hook.
fn check_scenes(spec: &AgentSpec, errors: &mut Vec<Diagnostic>) -> bool {
    if spec.scenes.is_empty() {
        err(
            errors,
            "agent has no scenes (an agent must have at least one activity)",
            Some(spec.line),
        );
        return false;
    }
    let declared: Option<&str> = spec.purpose.as_ref().map(|p| p.declared());
    let mut ok = true;
    let mut names: HashSet<&String> = HashSet::new();
    for s in &spec.scenes {
        if names.contains(&s.name) {
            err(errors, format!("duplicate scene \"{}\"", s.name), Some(s.line));
            ok = false;
        }
        names.insert(&s.name);
        if Some(s.serves.as_str()) != declared {
            err(
                errors,
                format!(
                    "scene \"{}\" serves \"{}\" but the agent's purpose is \"{}\" \
                     (no dead scenes: every scene must serve the one purpose)",
                    s.name,
                    s.serves,
                    declared.unwrap_or("")
                ),
                Some(s.line),
            );
            ok = false;
        }
        if s.hook.is_empty() {
            err(errors, format!("scene \"{}\" has no hook", s.name), Some(s.line));
            ok = false;
        }
    }
    ok
}

/// Rule (Agent): budget and act floor positive; coherence parts exist.
fn check_agent_extras(spec: &AgentSpec, errors: &mut Vec<Diagnostic>) -> bool {
    let mut ok = true;
    match spec.budget {
        None => {
            err(errors, "agent has no \"budget\"", Some(spec.line));
            ok = false;
        }
        Some(b) if b <= 0.0 || b.is_nan() => {
            err(errors, format!("budget must be > 0 (got {})", fmt(b)), Some(spec.line));
            ok = false;
        }
        _ => {}
    }
    if let Some(coh) = &spec.coherence {
        let parts: HashSet<&String> = spec
            .self_graph
            .as_ref()
            .map(|s| s.parts.iter().collect())
            .unwrap_or_default();
        for k in &coh.keeps {
            if !parts.contains(k) {
                err(errors, format!("coherence keeps unknown part \"{}\"", k), Some(coh.line));
            }
        }
    }
    ok
}

/// Type-check a single agent spec.
pub fn typecheck_agent(spec: &AgentSpec) -> TypeCheck {
    let mut errors: Vec<Diagnostic> = Vec::new();
    let s_ok = check_self(spec, &mut errors);
    let d_ok = check_drive(spec, &mut errors);
    let sc_ok = check_scenes(spec, &mut errors);
    let a_ok = check_agent_extras(spec, &mut errors);
    let ok = s_ok && d_ok && sc_ok && a_ok && errors.is_empty();

    let typed = if ok {
        let sg = spec.self_graph.as_ref().unwrap();
        let (chi, side) = character_invariant(&sg.parts, &sg.separations);
        let floor = realised_floor(&sg.parts, &sg.separations);
        let regime = match spec.purpose.as_ref().unwrap() {
            Purpose::Reach { .. } => Regime::Task,
            Purpose::Minimise { .. } => Regime::Character,
        };
        // chi_side ordered to match the parts order (stable output)
        let mut chi_side: Vec<String> = sg.parts.iter().filter(|p| side.contains(*p)).cloned().collect();
        if chi_side.is_empty() {
            chi_side = side.into_iter().collect();
        }
        let chi_non_local = chi_side.len() > 1;
        Some(TypedProgram::Agent(TypedAgent {
            spec: spec.clone(),
            derived: Derived {
                chi,
                chi_side,
                chi_non_local,
                realised_floor: floor,
                regime,
            },
        }))
    } else {
        None
    };

    TypeCheck { ok, errors, typed }
}

/// Type-check a program (agent or society).
pub fn typecheck(spec: &Spec) -> TypeCheck {
    match spec {
        Spec::Agent(a) => typecheck_agent(a),
        Spec::Society(soc) => {
            let mut errors: Vec<Diagnostic> = Vec::new();
            let mut typed_members: Vec<TypedMember> = Vec::new();
            for m in &soc.members {
                match m {
                    Member::Ref { name, .. } => {
                        typed_members.push(TypedMember::Ref { name: name.clone() });
                    }
                    Member::Agent(a) => {
                        let r = typecheck_agent(a);
                        if !r.ok {
                            for e in r.errors {
                                errors.push(Diagnostic::new(
                                    format!("member \"{}\": {}", a.name, e.message),
                                    e.line,
                                ));
                            }
                        } else if let Some(TypedProgram::Agent(ta)) = r.typed {
                            typed_members.push(TypedMember::Agent(Box::new(ta)));
                        }
                    }
                }
            }
            // ties: floor on inter-agent separations
            for t in &soc.ties {
                if t.cost <= 0.0 || t.cost.is_nan() {
                    errors.push(Diagnostic::new(
                        format!("tie ({}, {}) must have cost > 0", t.a, t.b),
                        Some(soc.line),
                    ));
                }
            }
            let ok = errors.is_empty();
            let typed = if ok {
                Some(TypedProgram::Society {
                    name: soc.name.clone(),
                    members: typed_members,
                    ties: soc.ties.clone(),
                    couple: soc.couple,
                })
            } else {
                None
            };
            TypeCheck { ok, errors, typed }
        }
    }
}

/// Format a number the way JS String() would for the integer/float cases in
/// these scripts (used only in diagnostic messages, for JS parity).
fn fmt(v: f64) -> String {
    if v.fract() == 0.0 && v.is_finite() {
        format!("{}", v as i64)
    } else {
        format!("{}", v)
    }
}
