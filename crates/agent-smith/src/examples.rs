// =====================================================================
//  Agent Smith — bundled example programs.
//  A ready-to-run town and a ready-to-run task-agent, shown by the CLI's
//  `smith show` and used in the fidelity tests. Ported verbatim from the
//  EXAMPLE_TOWN / EXAMPLE_TASK strings in index.js.
// =====================================================================

/// A town: a character, a pure observer, tied and coupled.
/// The smith runs on (character); the watcher observes free until the shared
/// outcome-state calls for it (its purpose is a different target).
pub const EXAMPLE_TOWN: &str = r#"// A town: a character and a pure observer.
society village {

  // the smith — a CHARACTER: standing purpose, runs on.
  agent smith {
    purpose minimise forge_residual
    scenes {
      scene hammer   serves forge_residual with forge_hook
      scene contract serves forge_residual with contract_hook
      scene source   serves forge_residual with source_ore_hook
    }
    self {
      parts { skill, stock, orders, reputation }
      separations {
        (skill, stock: 3), (stock, orders: 2),
        (orders, reputation: 2), (reputation, skill: 2)
      }
    }
    budget 1.0
    floor  2.0
    coherence keeps { reputation, skill }
  }

  // the watcher — a pure OBSERVER: its purpose is a different target, so a
  // forge interaction never clears its price. It observes, free, until the
  // shared outcome-state calls for it.
  agent watcher {
    purpose reach safety
    scenes {
      scene flee serves safety with flee_hook
    }
    self {
      parts { alert, position }
      separations { (alert, position: 2) }
    }
    budget 1.0
    floor  2.0
    coherence keeps { alert }
  }

  tie (smith, watcher: 2)
  couple 4.0
}
"#;

/// A task-agent: purpose is an attainable outcome, so it HALTS at quiescence.
pub const EXAMPLE_TASK: &str = r#"// A task-agent: purpose is an attainable outcome, so it HALTS at quiescence.
agent rerun_exp {
  purpose reach verdict_confirmed
  scenes {
    scene integrate serves verdict_confirmed with kuramoto_hook
    scene tabulate  serves verdict_confirmed with aggregate_hook
    scene report    serves verdict_confirmed with emit_hook
  }
  self {
    parts { data, method, result, verdict }
    separations {
      (data, method: 2), (method, result: 2),
      (result, verdict: 2), (verdict, data: 2)
    }
  }
  budget 1.0
  floor  2.0
  coherence keeps { method, result }
}
"#;
