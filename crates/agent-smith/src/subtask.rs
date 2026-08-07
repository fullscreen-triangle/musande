// =====================================================================
//  Agent Smith — subtasks and nodes.
//
//  This is the layer the runtime paper describes ("A Runtime Without a
//  Program"): a NODE is the convergence of a subtask with the executable
//  code that realises it, and it is the durable object of the system.
//
//      node = ( tau, chunks, values )
//
//  Three properties are load-bearing and are enforced here by construction:
//
//   * IDENTITY IS TAU. Nodes are individuated by subtask identity. Two
//     agents — from the same module or different ones — that decompose
//     their problems and arrive at the same subtask CONVERGE on one node.
//     `Graph::raise` is therefore idempotent under tau: raising an existing
//     subtask accretes chunks and values onto the existing node rather than
//     minting a second one. A node is a meeting point, not a possession.
//
//   * CHUNKS ARE A BAG, AND ALL OF THEM RUN. A subtask can be realised more
//     than one way — say one chunk in one module's DSL and another in a
//     different module's. These are NOT competing candidates to be selected
//     among. There is deliberately no "best chunk" accessor anywhere in this
//     file, because the runtime executes every chunk on a node.
//
//   * VALUES ARE THE ONLY SHARED SURFACE. A module can identify a node, read
//     its values, transform internally, and emit new values. There is no
//     fifth verb. In particular there is no way to ask whether a value is
//     correct, because correctness is not a property the graph represents —
//     the graph stores what WAS emitted, not what should have been. That
//     closure is what keeps adjudication out of this layer and in the
//     consumer where it belongs.
//
//  What this module does NOT do, and must not grow into: it does not execute
//  chunks (that is the OS), it does not judge a value against an expectation
//  (nothing here can), it does not order the graph, and it does not read the
//  content of a chunk. Chunk bodies are opaque bytes with a DSL tag. Nothing
//  in this crate understands any DSL, and nothing needs to.
// =====================================================================

use std::collections::HashMap;

// ---------------------------------------------------------------------
//  Subtask identity
// ---------------------------------------------------------------------

/// The identity `tau` of a subtask. Nodes are individuated by this and by
/// nothing else: two realisations converge exactly when their `Tau` is equal.
///
/// It is an opaque string chosen by the raising module. This crate never
/// parses it, and deliberately imposes no scheme — the address discipline of
/// the runtime paper is a module-side convention, not a constraint here.
#[derive(Debug, Clone, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct Tau(pub String);

impl Tau {
    pub fn new(s: impl Into<String>) -> Self {
        Tau(s.into())
    }
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl From<&str> for Tau {
    fn from(s: &str) -> Self {
        Tau(s.to_string())
    }
}

impl From<String> for Tau {
    fn from(s: String) -> Self {
        Tau(s)
    }
}

impl std::fmt::Display for Tau {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

// ---------------------------------------------------------------------
//  Chunks
// ---------------------------------------------------------------------

/// One executable realisation of a subtask: a body of DSL source, tagged with
/// which DSL it is written in.
///
/// The body is opaque. This crate does not parse it, validate it, or compare
/// two chunks for preference — it carries it to whoever executes it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Chunk {
    /// Which DSL the body is written in (e.g. "turbulance", "purpose",
    /// "vahera"). Uninterpreted here; meaningful only to a consumer.
    pub dsl: String,
    /// The source text. Opaque bytes as far as this crate is concerned.
    pub body: String,
    /// Which module generated this realisation. Provenance, not ownership —
    /// a node is not owned by anyone (see `Graph::raise`).
    pub by: Option<String>,
}

impl Chunk {
    pub fn new(dsl: impl Into<String>, body: impl Into<String>) -> Self {
        Chunk { dsl: dsl.into(), body: body.into(), by: None }
    }

    /// Record which module generated this chunk.
    pub fn by(mut self, module: impl Into<String>) -> Self {
        self.by = Some(module.into());
        self
    }
}

// ---------------------------------------------------------------------
//  Values
// ---------------------------------------------------------------------

/// A value carried on a node: the medium of exchange between modules.
///
/// A value is whatever a module cares to attach — a measurement, a derived
/// record, a finding, a partial result, or an anomaly. Anomalies are values
/// like any other: a chunk that raises produces an error record which is
/// emitted onto the graph exactly as a numeric result would be. Nothing in
/// this crate branches on a value's content, which is what makes
/// run-to-completion structural rather than a policy.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Value {
    /// Which module emitted it.
    pub by: String,
    /// A module-chosen key. Uninterpreted here.
    pub key: String,
    /// The payload, serialised by the emitter. Opaque.
    pub payload: String,
}

impl Value {
    pub fn new(by: impl Into<String>, key: impl Into<String>, payload: impl Into<String>) -> Self {
        Value { by: by.into(), key: key.into(), payload: payload.into() }
    }
}

// ---------------------------------------------------------------------
//  The subtask an agent carries
// ---------------------------------------------------------------------

/// A subtask: the instruction, plus the code chunks that are a translation of
/// that instruction into DSL.
///
/// Both halves travel together. The instruction is the information — what is
/// to be done, in whatever terms the raising module thinks in. The chunks are
/// its realisation. An agent carries this and nothing else about the wider
/// problem: it holds no task identity beyond its own subtask, no position in
/// an ordering, and no knowledge of what came before or comes next, because
/// those fields do not exist on it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Subtask {
    /// The identity under which this subtask converges with others.
    pub tau: Tau,
    /// The instruction — the information half of the subtask.
    pub instruction: String,
    /// The realisations — the code half. A bag: order carries no meaning and
    /// every chunk is to be executed, none selected over another.
    pub chunks: Vec<Chunk>,
}

impl Subtask {
    /// A subtask with an instruction and no realisation yet. A subtask may
    /// legitimately have no chunks — it has been raised but not yet realised
    /// (Zangalewa generates code for it later, converging on the same tau).
    pub fn new(tau: impl Into<Tau>, instruction: impl Into<String>) -> Self {
        Subtask { tau: tau.into(), instruction: instruction.into(), chunks: Vec::new() }
    }

    /// Add a realisation.
    pub fn with_chunk(mut self, chunk: Chunk) -> Self {
        self.chunks.push(chunk);
        self
    }

    /// Add several realisations.
    pub fn with_chunks(mut self, chunks: impl IntoIterator<Item = Chunk>) -> Self {
        self.chunks.extend(chunks);
        self
    }

    /// Whether any realisation exists yet.
    pub fn is_realised(&self) -> bool {
        !self.chunks.is_empty()
    }
}

// ---------------------------------------------------------------------
//  The node
// ---------------------------------------------------------------------

/// A node of the causal knowledge graph: `(tau, chunks, values)`.
///
/// The node is the durable object. It is not owned by the agent or module
/// that first raised it: because the subtask individuates it and many agents
/// converge on the same subtask, a node accretes chunks and values from every
/// agent that reaches it.
#[derive(Debug, Clone)]
pub struct Node {
    /// Subtask identity. The whole of the node's individuation.
    pub tau: Tau,
    /// The instructions raised against this tau, in raise order. Usually one,
    /// but two modules may phrase the same subtask differently and still
    /// converge — both phrasings are kept, since neither is authoritative.
    pub instructions: Vec<String>,
    /// The chunk bag. Every chunk is a co-resident realisation; all run.
    pub chunks: Vec<Chunk>,
    /// The values carried, in emit order.
    pub values: Vec<Value>,
}

impl Node {
    fn new(tau: Tau) -> Self {
        Node { tau, instructions: Vec::new(), chunks: Vec::new(), values: Vec::new() }
    }

    /// Read the values on this node. One of the four verbs.
    ///
    /// There is deliberately no companion that reports whether a value is
    /// correct or expected: the graph stores what was emitted, not what
    /// should have been.
    pub fn read(&self) -> &[Value] {
        &self.values
    }

    /// Read only the values emitted by a given module.
    pub fn read_by<'a>(&'a self, module: &'a str) -> impl Iterator<Item = &'a Value> + 'a {
        self.values.iter().filter(move |v| v.by == module)
    }

    /// Read only the values under a given key.
    pub fn read_key<'a>(&'a self, key: &'a str) -> impl Iterator<Item = &'a Value> + 'a {
        self.values.iter().filter(move |v| v.key == key)
    }

    /// Emit a value onto this node. One of the four verbs.
    pub fn emit(&mut self, value: Value) {
        self.values.push(value);
    }

    /// Every chunk on this node. The runtime executes all of them; there is
    /// no accessor that picks one, by design.
    pub fn chunks(&self) -> &[Chunk] {
        &self.chunks
    }

    /// The chunks written in a given DSL. A filter for a consumer that can
    /// only run one DSL — still not a selection among competing candidates.
    pub fn chunks_in<'a>(&'a self, dsl: &'a str) -> impl Iterator<Item = &'a Chunk> + 'a {
        self.chunks.iter().filter(move |c| c.dsl == dsl)
    }

    /// The distinct DSLs realised on this node.
    pub fn dsls(&self) -> Vec<&str> {
        let mut out: Vec<&str> = Vec::new();
        for c in &self.chunks {
            if !out.contains(&c.dsl.as_str()) {
                out.push(&c.dsl);
            }
        }
        out
    }
}

// ---------------------------------------------------------------------
//  The graph
// ---------------------------------------------------------------------

/// The shared node medium: the set of distinct subtasks that agents have
/// raised, each carrying its chunk bag and its values.
///
/// Note what is absent: there is no edge set. A causal edge — "a value
/// emitted at u was read at v" — exists only once the reading has happened,
/// so it is a product of a run, not an input to it. Storing edges here would
/// be storing a schedule, and the trajectory is not storable as a plan.
#[derive(Debug, Clone, Default)]
pub struct Graph {
    nodes: HashMap<Tau, Node>,
    /// Raise order, so iteration is stable across runs (a HashMap's order is
    /// not, and unstable iteration would make reports gratuitously
    /// irreproducible).
    order: Vec<Tau>,
}

/// What `raise` did: minted a new node, or converged onto an existing one.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Raised {
    /// This tau had not been raised before; a node was created.
    Created,
    /// This tau already existed; chunks and instructions accreted onto it.
    Converged,
}

impl Graph {
    pub fn new() -> Self {
        Graph::default()
    }

    /// Publish a subtask as a node.
    ///
    /// Idempotent under tau: raising a subtask that already exists merges its
    /// chunks and instruction onto the existing node rather than creating a
    /// second. This is convergence, and it is the norm rather than the
    /// exception, because different problems share sub-structure.
    ///
    /// Duplicate chunks (same DSL, same body, same author) are not appended
    /// twice — re-raising an identical realisation is not a second
    /// realisation. Distinct realisations always co-reside.
    pub fn raise(&mut self, subtask: &Subtask) -> Raised {
        let existed = self.nodes.contains_key(&subtask.tau);
        if !existed {
            self.order.push(subtask.tau.clone());
            self.nodes.insert(subtask.tau.clone(), Node::new(subtask.tau.clone()));
        }
        let node = self.nodes.get_mut(&subtask.tau).expect("just inserted");
        if !node.instructions.contains(&subtask.instruction) {
            node.instructions.push(subtask.instruction.clone());
        }
        for c in &subtask.chunks {
            if !node.chunks.contains(c) {
                node.chunks.push(c.clone());
            }
        }
        if existed {
            Raised::Converged
        } else {
            Raised::Created
        }
    }

    /// Identify a node by subtask identity. One of the four verbs.
    pub fn identify(&self, tau: &Tau) -> Option<&Node> {
        self.nodes.get(tau)
    }

    /// Identify a node for emission.
    pub fn identify_mut(&mut self, tau: &Tau) -> Option<&mut Node> {
        self.nodes.get_mut(tau)
    }

    /// Emit a value onto the node bearing `tau`. Returns false if no such
    /// node has been raised.
    pub fn emit(&mut self, tau: &Tau, value: Value) -> bool {
        match self.nodes.get_mut(tau) {
            Some(n) => {
                n.emit(value);
                true
            }
            None => false,
        }
    }

    /// All nodes, in raise order.
    pub fn nodes(&self) -> impl Iterator<Item = &Node> {
        self.order.iter().filter_map(move |t| self.nodes.get(t))
    }

    /// How many distinct subtasks have been raised.
    pub fn len(&self) -> usize {
        self.order.len()
    }

    pub fn is_empty(&self) -> bool {
        self.order.is_empty()
    }
}
