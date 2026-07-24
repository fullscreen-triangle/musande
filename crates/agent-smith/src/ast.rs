// =====================================================================
//  Agent Smith — the specification AST.
//  The shapes the parser produces and the typechecker consumes. A direct
//  port of the plain objects the JS parser builds (parse.js), made into
//  Rust enums/structs. Deliberately structural: typing (typecheck.rs),
//  not parsing, is where an agent is rejected.
//
//  Grammar (concrete surface):
//    agent <id> {
//      purpose (minimise <phi> | reach <outcome>)
//      scenes { scene <id> serves <purpose> with <hook> ... }
//      self { parts { a, b, ... } separations { (a, b: cost), ... } }
//      budget <num>
//      floor  <num>
//      coherence keeps { a, b, ... }
//    }
//    society <id> { <agent-or-ref> ... tie (a,b: cost) ... couple <K> }
// =====================================================================

/// A purpose: minimise a strongly-convex potential (a standing character),
/// or reach an attainable outcome (a task-agent that halts at quiescence).
#[derive(Debug, Clone, PartialEq)]
pub enum Purpose {
    /// `minimise <potential>`
    Minimise { potential: String, line: u32 },
    /// `reach <outcome>`
    Reach { outcome: String, line: u32 },
}

impl Purpose {
    /// The single declared target name: the potential (minimise) or the
    /// outcome (reach). Every scene must `serve` this.
    pub fn declared(&self) -> &str {
        match self {
            Purpose::Minimise { potential, .. } => potential,
            Purpose::Reach { outcome, .. } => outcome,
        }
    }
    pub fn line(&self) -> u32 {
        match self {
            Purpose::Minimise { line, .. } | Purpose::Reach { line, .. } => *line,
        }
    }
}

/// A scene: an outward activity `scene <name> serves <serves> with <hook>`.
#[derive(Debug, Clone, PartialEq)]
pub struct Scene {
    pub name: String,
    pub serves: String,
    pub hook: String,
    pub line: u32,
}

/// A separation: an internal boundary `(a, b: cost)`.
#[derive(Debug, Clone, PartialEq)]
pub struct Separation {
    pub a: String,
    pub b: String,
    pub cost: f64,
    pub line: u32,
}

/// The self-graph: `self { parts { ... } separations { ... } }`.
#[derive(Debug, Clone, PartialEq)]
pub struct SelfGraph {
    pub parts: Vec<String>,
    pub separations: Vec<Separation>,
    pub line: u32,
}

/// The coherence condition: `coherence keeps { a, b, ... }`.
#[derive(Debug, Clone, PartialEq)]
pub struct Coherence {
    pub keeps: Vec<String>,
    pub line: u32,
}

/// An agent specification (the parsed `agent { ... }` block).
#[derive(Debug, Clone, PartialEq)]
pub struct AgentSpec {
    pub name: String,
    pub line: u32,
    pub purpose: Option<Purpose>,
    pub scenes: Vec<Scene>,
    pub self_graph: Option<SelfGraph>,
    pub budget: Option<f64>,
    pub floor: Option<f64>,
    pub coherence: Option<Coherence>,
}

/// An inter-agent separation in a society: `tie (a, b: cost)`.
#[derive(Debug, Clone, PartialEq)]
pub struct Tie {
    pub a: String,
    pub b: String,
    pub cost: f64,
}

/// A society member: either an inline agent or a bare reference by name
/// (resolved by the caller against a registry; carried through here).
#[derive(Debug, Clone, PartialEq)]
pub enum Member {
    Agent(AgentSpec),
    Ref { name: String, line: u32 },
}

/// A society specification (the parsed `society { ... }` block).
#[derive(Debug, Clone, PartialEq)]
pub struct SocietySpec {
    pub name: String,
    pub line: u32,
    pub members: Vec<Member>,
    pub ties: Vec<Tie>,
    pub couple: Option<f64>,
}

/// A whole program: a single agent or a society.
#[derive(Debug, Clone, PartialEq)]
pub enum Spec {
    Agent(AgentSpec),
    Society(SocietySpec),
}
