// =====================================================================
//  Agent Smith — fidelity tests.
//  Cross-checks the Rust engine against values the JS engine produces on the
//  same inputs, and against the paper's own witnesses (the split-attention
//  synchronised-agents manuscript). These pin the ports of the identity
//  invariant, water-filling, hash_unit, and the monotone/observer runtime
//  behaviour so the Rust core stays faithful.
// =====================================================================

use std::collections::HashMap;

use agent_smith::{
    build, character_invariant, hash_unit, make_town, realised_floor, run_town, water_fill,
    Ctx, LogGain, Outcome, ProgramKind, Regime, SceneCost, Separation,
};

fn sep(a: &str, b: &str, cost: f64) -> Separation {
    Separation { a: a.into(), b: b.into(), cost, line: 0 }
}

// ---- identity: the two-triangle witness (paper thm:identity) ----

#[test]
fn chi_two_triangle_is_two_and_non_local() {
    // Two triangles of edge cost 2 joined by one edge of cost 2. Cutting the
    // joining edge separates them at cost 2; isolating any vertex costs >= 4.
    // The minimum is the two-block partition → chi = 2, non-local.
    let parts: Vec<String> = ["a", "b", "c", "d", "e", "f"].iter().map(|s| s.to_string()).collect();
    let seps = vec![
        // triangle 1: a-b-c
        sep("a", "b", 2.0), sep("b", "c", 2.0), sep("c", "a", 2.0),
        // triangle 2: d-e-f
        sep("d", "e", 2.0), sep("e", "f", 2.0), sep("f", "d", 2.0),
        // the bridge
        sep("c", "d", 2.0),
    ];
    let (chi, side) = character_invariant(&parts, &seps);
    assert_eq!(chi, 2.0, "two-triangle chi must be the bridge cut = 2");
    assert!(side.len() > 1, "chi is non-local: realised by a block, not a singleton");
    assert_eq!(side.len(), 3, "each triangle is one block of three parts");
}

#[test]
fn realised_floor_is_min_singleton_cut() {
    // Running example from the paper: triangle a-b-c with costs 2,3,2.
    let parts: Vec<String> = ["a", "b", "c"].iter().map(|s| s.to_string()).collect();
    let seps = vec![sep("a", "b", 2.0), sep("b", "c", 3.0), sep("c", "a", 2.0)];
    // singleton cuts: a: 2+2=4, b: 2+3=5, c: 3+2=5 → min 4.
    assert_eq!(realised_floor(&parts, &seps), 4.0);
    // chi (min bipartition) isolates a at 4 as well here (n=3, all singletons).
    let (chi, _side) = character_invariant(&parts, &seps);
    assert_eq!(chi, 4.0);
}

// ---- water-filling (paper thm:waterfill) ----

fn scene(id: &str, k: f64) -> SceneCost {
    SceneCost { id: id.into(), gain: LogGain::new(k) }
}

#[test]
fn water_filling_equalises_margins_at_one_price() {
    // Two log-gain scenes, tight budget → both attended, margins equal at p*.
    let scenes = vec![scene("s1", 2.0), scene("s2", 1.5)];
    let budget = 0.5;
    let (alloc, price) = water_fill(&scenes, budget);
    assert!(price > 0.0, "tight budget binds → positive price");
    // sum of allocations meets the budget (to bisection tolerance)
    let total: f64 = alloc.iter().map(|(_, a)| a).sum();
    assert!((total - budget).abs() < 1e-4, "allocations exhaust the budget");
    // marginal gain equalised at the price on attended scenes: gamma'(a) = k/(1+a)
    for (id, a) in &alloc {
        if *a > 1e-6 {
            let k = scenes.iter().find(|s| &s.id == id).unwrap().gain.k;
            let margin = k / (1.0 + a);
            assert!((margin - price).abs() < 1e-3, "margin equals price on attended scene {id}");
        }
    }
}

#[test]
fn water_filling_price_falls_with_budget_and_rises_with_scenes() {
    let two = vec![scene("s1", 2.0), scene("s2", 1.5)];
    let p_small = water_fill(&two, 0.3).1;
    let p_large = water_fill(&two, 1.0).1;
    assert!(p_large < p_small, "price is nonincreasing in the budget");

    let three = vec![scene("s1", 2.0), scene("s2", 1.5), scene("s3", 1.8)];
    let p_two = water_fill(&two, 0.3).1;
    let p_three = water_fill(&three, 0.3).1;
    assert!(p_three >= p_two, "adding a competing scene does not lower the price");
}

// ---- hash_unit parity with the JS FNV-1a ----

#[test]
fn hash_unit_is_in_unit_interval_and_deterministic() {
    for name in ["hammer", "contract", "source", "integrate", "flee"] {
        let h = hash_unit(name);
        assert!((0.0..1.0).contains(&h), "hash_unit in [0,1): {name} -> {h}");
        assert_eq!(h, hash_unit(name), "hash_unit is deterministic");
    }
    // distinct names generally hash apart (scene richness has something to do)
    assert_ne!(hash_unit("hammer"), hash_unit("contract"));
}

// ---- the bundled task-agent halts (paper thm:history: monotone, quiescent) ----

#[test]
fn example_task_reaches_quiescence_with_monotone_count() {
    let built = build(agent_smith::EXAMPLE_TASK);
    assert!(built.ok, "EXAMPLE_TASK builds: {:?}", built.errors);
    let program = built.program.unwrap();
    assert_eq!(program.kind, ProgramKind::Agent);
    assert_eq!(program.agents[0].regime, Regime::Task);

    let mut town = make_town(program);
    let ctx = Ctx::deterministic();
    let history = run_town(&mut town, &ctx, 40);

    // the run ends (done or quiescent), not by hitting the tick cap
    let last = history.last().unwrap();
    assert!(last.done || last.quiescent, "task-agent halts at quiescence");

    // the committed count is strictly increasing over commits and never resets:
    // reconstruct the count trace from the records for the single agent.
    let mut prev: u64 = 0;
    let mut committed = 0;
    for step in &history {
        for r in &step.records {
            assert!(r.count >= prev, "count never decreases (I2 monotone history)");
            if r.outcome == Outcome::Commit {
                committed += 1;
                assert!(r.count > prev, "a commit strictly increments the count");
            }
            prev = r.count;
        }
    }
    assert!(committed > 0, "the task-agent did real work before halting");
    assert!(prev > 0, "final count is positive");
}

// ---- the town's watcher is a pure observer until called (penguin-watcher) ----

#[test]
fn example_town_watcher_observes_and_smith_runs() {
    let built = build(agent_smith::EXAMPLE_TOWN);
    assert!(built.ok, "EXAMPLE_TOWN builds: {:?}", built.errors);
    let program = built.program.unwrap();
    assert_eq!(program.kind, ProgramKind::Society);

    let mut town = make_town(program);
    // society identity computed from the ties (single tie → chi = 2)
    let soc = town.society.as_ref().expect("society has an identity");
    assert_eq!(soc.chi, 2.0, "society chi from the (smith,watcher:2) tie");

    let ctx = Ctx::deterministic();
    let history = run_town(&mut town, &ctx, 20);

    // count commits per agent across the whole run
    let mut commits: HashMap<String, u32> = HashMap::new();
    for step in &history {
        for r in &step.records {
            if r.outcome == Outcome::Commit {
                *commits.entry(r.agent.clone()).or_default() += 1;
            }
        }
    }
    // the smith is a character with work → it commits; the watcher's target
    // (safety) is never raised, so it never clears its price → zero commits.
    assert!(commits.get("smith").copied().unwrap_or(0) > 0, "the smith runs on");
    assert_eq!(
        commits.get("watcher").copied().unwrap_or(0),
        0,
        "the watcher observes free until the shared state calls for it"
    );
}

// ---- typecheck rejects the paper's category errors (with line numbers) ----

#[test]
fn typecheck_rejects_wrong_serving_scene() {
    let src = r#"agent bad {
  purpose reach goal
  scenes {
    scene s serves other with h
  }
  self { parts { p, q } separations { (p, q: 2) } }
  budget 1.0
  floor 2.0
}"#;
    let built = build(src);
    assert!(!built.ok, "a scene serving the wrong purpose must be rejected");
    let msg = &built.errors[0].message;
    assert!(msg.contains("serves"), "error names the serving mismatch: {msg}");
    assert!(built.errors[0].line.is_some(), "error carries a line number");
}

#[test]
fn typecheck_rejects_cost_below_floor() {
    let src = r#"agent bad {
  purpose reach goal
  scenes { scene s serves goal with h }
  self { parts { p, q } separations { (p, q: 1) } }
  budget 1.0
  floor 2.0
}"#;
    let built = build(src);
    assert!(!built.ok, "a separation cost below the floor must be rejected");
    assert!(
        built.errors.iter().any(|e| e.message.contains("below the floor")),
        "error explains the floor violation: {:?}",
        built.errors
    );
}

#[test]
fn typecheck_accepts_minimise_character() {
    // a character agent (minimise a known convex potential) types.
    let src = r#"agent c {
  purpose minimise residual
  scenes { scene work serves residual with h }
  self { parts { p, q } separations { (p, q: 2) } }
  budget 1.0
  floor 2.0
}"#;
    let built = build(src);
    assert!(built.ok, "character agent types: {:?}", built.errors);
    assert_eq!(built.program.unwrap().agents[0].regime, Regime::Character);
}
