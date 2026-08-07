// =====================================================================
//  Fidelity tests for the instantiation layer.
//
//  These check the properties the runtime paper makes load-bearing, not the
//  incidental behaviour of the API. Each test names the property it pins.
// =====================================================================

use agent_smith::{
    instantiate, instantiate_all, instantiate_into, Chunk, Graph, Raised, Spawn, Subtask, Tau, Value,
};

// ---------------------------------------------------------------------
//  Convergence: identity is tau
// ---------------------------------------------------------------------

#[test]
fn two_modules_raising_the_same_subtask_converge_on_one_node() {
    let mut g = Graph::new();

    // Two different modules decompose their own problems and both arrive at
    // the same subtask. They phrase the instruction differently and realise
    // it in different DSLs.
    let a = Subtask::new("normalise_spectrum", "normalise the spectrum")
        .with_chunk(Chunk::new("turbulance", "normalise(x)").by("kwasa-kwasa"));
    let b = Subtask::new("normalise_spectrum", "scale intensities to unit norm")
        .with_chunk(Chunk::new("purpose", "scale_unit(x)").by("purpose"));

    assert_eq!(g.raise(&a), Raised::Created);
    assert_eq!(g.raise(&b), Raised::Converged);

    // One node, not two.
    assert_eq!(g.len(), 1);

    let node = g.identify(&Tau::new("normalise_spectrum")).unwrap();

    // Both realisations co-reside. Neither displaced the other, and there is
    // no accessor that would pick between them.
    assert_eq!(node.chunks().len(), 2);
    let mut dsls = node.dsls();
    dsls.sort();
    assert_eq!(dsls, vec!["purpose", "turbulance"]);

    // Both phrasings are kept: neither module's wording is authoritative.
    assert_eq!(node.instructions.len(), 2);
}

#[test]
fn re_raising_an_identical_realisation_does_not_duplicate_it() {
    let mut g = Graph::new();
    let s = Subtask::new("t", "do it").with_chunk(Chunk::new("vahera", "f(x)").by("m"));

    g.raise(&s);
    g.raise(&s);
    g.raise(&s);

    // Convergence accretes distinct realisations, not repeated ones.
    assert_eq!(g.identify(&Tau::new("t")).unwrap().chunks().len(), 1);
}

#[test]
fn distinct_taus_do_not_converge() {
    let mut g = Graph::new();
    assert_eq!(g.raise(&Subtask::new("a", "x")), Raised::Created);
    assert_eq!(g.raise(&Subtask::new("b", "x")), Raised::Created);
    assert_eq!(g.len(), 2);
}

// ---------------------------------------------------------------------
//  The agent carries the subtask
// ---------------------------------------------------------------------

#[test]
fn an_instantiated_agent_carries_instruction_and_every_chunk() {
    let s = Subtask::new("align", "align the traces")
        .with_chunk(Chunk::new("turbulance", "align(a,b)"))
        .with_chunk(Chunk::new("shapeshifter", "warp(a,b)"));

    let t = instantiate(s, Spawn::default().by("kwasa-kwasa"));

    assert_eq!(t.instruction(), "align the traces");
    assert_eq!(t.chunks().len(), 2);

    // One scene per realisation: running a realisation is the outward act.
    assert_eq!(t.agent.scenes.len(), 2);
    // The scene's hook names the DSL, so a Hook can route on it.
    let hooks: Vec<&str> = t.agent.scenes.iter().map(|s| s.hook.as_str()).collect();
    assert!(hooks.contains(&"turbulance"));
    assert!(hooks.contains(&"shapeshifter"));
}

#[test]
fn an_unrealised_subtask_still_yields_a_working_agent() {
    // A module may raise a subtask before any code exists for it; a
    // code-generating module converges a chunk onto the same tau later.
    let s = Subtask::new("cluster", "cluster the peaks");
    assert!(!s.is_realised());

    let t = instantiate(s, Spawn::default());
    assert_eq!(t.agent.scenes.len(), 1);
    assert_eq!(t.agent.scenes[0].hook, "unrealised");
    // Every scene must serve the agent's declared purpose.
    assert_eq!(t.agent.scenes[0].serves, t.agent.purpose.target);
}

#[test]
fn every_scene_serves_the_declared_purpose() {
    let s = Subtask::new("tau_x", "i")
        .with_chunk(Chunk::new("d1", "a"))
        .with_chunk(Chunk::new("d2", "b"))
        .with_chunk(Chunk::new("d3", "c"));
    let t = instantiate(s, Spawn::default());
    assert!(t.agent.scenes.iter().all(|sc| sc.serves == t.agent.purpose.target));
}

// ---------------------------------------------------------------------
//  The ticket shape: no context, no ordering, no identity
// ---------------------------------------------------------------------

#[test]
fn a_ticket_has_no_self_graph_and_therefore_no_chi() {
    // chi is identity conserved across change, which presupposes something
    // persisting. A ticket holds one subtask and has no ordering, so there
    // is nothing for identity to be conserved across. Left empty, not faked.
    let t = instantiate(Subtask::new("t", "i"), Spawn::default());
    assert!(t.agent.self_graph.parts.is_empty());
    assert!(t.agent.self_graph.separations.is_empty());
    assert_eq!(t.agent.chi, 0.0);
    assert!(!t.agent.chi_non_local);
}

#[test]
fn tickets_are_indistinguishable_by_position_in_the_decomposition() {
    // A module supplies an ordering when it hands over a decomposition, but
    // nothing in a ticket records its position, and no ticket refers to
    // another. Two tickets built from the same subtask at different indices
    // are identical in everything the agent can observe.
    let mut g = Graph::new();
    let subs = vec![
        Subtask::new("p", "first").with_chunk(Chunk::new("d", "code")),
        Subtask::new("q", "second").with_chunk(Chunk::new("d", "code")),
        Subtask::new("r", "third").with_chunk(Chunk::new("d", "code")),
    ];
    let tickets = instantiate_all(subs, Spawn::default(), &mut g);
    assert_eq!(tickets.len(), 3);

    for t in &tickets {
        // Nothing positional: the count is the never-reset monotone count,
        // which starts at zero for every agent regardless of where it sits.
        assert_eq!(t.agent.count, 0);
        // The trajectory is empty until the agent itself commits.
        assert!(t.agent.trajectory.is_empty());
        // Its purpose target is its own tau and no one else's.
        assert_eq!(t.agent.purpose.target, t.subtask.tau.as_str());
    }
}

#[test]
fn instantiate_into_publishes_and_reports_convergence() {
    let mut g = Graph::new();

    let (t1, r1) = instantiate_into(
        Subtask::new("shared", "a").with_chunk(Chunk::new("d1", "x")),
        Spawn::default().by("module_a"),
        &mut g,
    );
    let (t2, r2) = instantiate_into(
        Subtask::new("shared", "b").with_chunk(Chunk::new("d2", "y")),
        Spawn::default().by("module_b"),
        &mut g,
    );

    assert_eq!(r1, Raised::Created);
    assert_eq!(r2, Raised::Converged);

    // Two agents were generated — convergence is about the node, not the
    // agents. Both modules got a worker.
    assert_ne!(t1.agent.id, t2.agent.id);
    assert_eq!(t1.by.as_deref(), Some("module_a"));
    assert_eq!(t2.by.as_deref(), Some("module_b"));

    // But they meet at one node, which now holds both realisations.
    assert_eq!(g.len(), 1);
    assert_eq!(g.identify(&Tau::new("shared")).unwrap().chunks().len(), 2);
}

// ---------------------------------------------------------------------
//  Values: the only shared surface
// ---------------------------------------------------------------------

#[test]
fn modules_exchange_only_values_and_an_anomaly_is_an_ordinary_value() {
    let mut g = Graph::new();
    g.raise(&Subtask::new("measure", "measure it"));
    let tau = Tau::new("measure");

    g.emit(&tau, Value::new("mass_spec", "intensity", "1.24e6"));
    // A chunk that raised produces an error record, emitted exactly as a
    // numeric result would be. Nothing here branches on its content.
    g.emit(&tau, Value::new("mass_spec", "anomaly", "detector saturated"));
    g.emit(&tau, Value::new("purpose", "intensity", "1.19e6"));

    let node = g.identify(&tau).unwrap();
    assert_eq!(node.read().len(), 3);
    assert_eq!(node.read_by("mass_spec").count(), 2);
    assert_eq!(node.read_key("intensity").count(), 2);

    // The anomaly sits alongside the results, readable by anyone.
    assert_eq!(node.read_key("anomaly").count(), 1);
}

#[test]
fn emitting_to_an_unraised_tau_reports_false_rather_than_creating_a_node() {
    let mut g = Graph::new();
    assert!(!g.emit(&Tau::new("never_raised"), Value::new("m", "k", "v")));
    assert!(g.is_empty());
}

#[test]
fn node_iteration_is_stable_in_raise_order() {
    // Unstable iteration would make reports gratuitously irreproducible.
    let mut g = Graph::new();
    for name in ["one", "two", "three", "four", "five"] {
        g.raise(&Subtask::new(name, "i"));
    }
    let seen: Vec<&str> = g.nodes().map(|n| n.tau.as_str()).collect();
    assert_eq!(seen, vec!["one", "two", "three", "four", "five"]);

    // And stable across repeated traversals.
    let again: Vec<&str> = g.nodes().map(|n| n.tau.as_str()).collect();
    assert_eq!(seen, again);
}

// ---------------------------------------------------------------------
//  No privileged level
// ---------------------------------------------------------------------

#[test]
fn an_instantiated_agent_can_itself_instantiate() {
    // The module that generates DSL code is built out of agents, so whatever
    // calls instantiate may itself have been produced by instantiate. There
    // is no layer above this one, and nothing in the call assumes its caller
    // is a human or a distinguished orchestrator.
    let mut g = Graph::new();

    let (generator, _) = instantiate_into(
        Subtask::new("write_code_for_align", "generate a turbulance chunk for align"),
        Spawn::default().by("zangalewa"),
        &mut g,
    );

    // The generator does its work and raises the subtask it was asked to
    // realise — using exactly the same entry point it was created by.
    let (realised, _) = instantiate_into(
        Subtask::new("align", "align the traces")
            .with_chunk(Chunk::new("turbulance", "align(a,b)").by("zangalewa")),
        Spawn::default().by("zangalewa"),
        &mut g,
    );

    assert_eq!(g.len(), 2);
    assert!(realised.subtask.is_realised());
    // Both are the same kind of object; neither outranks the other.
    assert_eq!(generator.agent.regime, realised.agent.regime);
}
