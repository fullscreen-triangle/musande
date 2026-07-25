// =====================================================================
//  Agent Smith Sandbox — the economic skin.
//
//  These are the virtual files in the sandbox explorer. They are ordinary
//  .smith scripts, but written in the vocabulary of ECONOMIC AGENTS — a
//  trading desk, a market maker, a floor of dealers — so a reader who knows
//  nothing of the framework's theory can still follow what the agent is
//  doing. The charts underneath show the framework quantities (character χ,
//  water-filling price p*, the irreducible floor β, the monotone count) as a
//  by-product of running an economic story the reader already understands.
//
//  The trick: every economic knob is a real DSL construct.
//    - "a desk that never stops trading"      → a CHARACTER (standing purpose)
//    - "attention split across order books"    → water-filling over scenes
//    - "the edge you can never arbitrage away" → the floor β > 0
//    - "positions only accumulate"             → the monotone count (I2)
//    - "two desks that never share a book"     → disjoint internals, one Ω
//
//  The learner meets the punchline (β > 0: some residual is irreducible)
//  as the answer to a question they already asked ("why can't the desk get
//  its inventory risk to zero?"), not as an axiom handed down first.
// =====================================================================

export const SCRIPTS = [
  {
    id: "01",
    name: "01-desk.smith",
    title: "A trading desk",
    blurb:
      "One desk, one book. The whole attention budget goes to the one market. The simplest thing that runs.",
    source: `// 01 — A trading desk with a single book.
//
// The desk's purpose is to drive down "inventory_risk" — the gap between the
// position it holds and the position it wants. One market to watch, so the
// whole attention budget lands there. Run it and read the Attention tab:
// with one scene, water-filling is trivial — price p* is zero, all budget
// flows to the one book.
//
// But watch the Structure tab: even a one-book desk has an internal make-up
// (its capital and its risk-appetite are separable but coupled). That
// coupling has a *cost to sever* — that cost is the desk's character χ.

agent desk {
  purpose minimise inventory_risk
  scenes {
    scene make_market serves inventory_risk with quote_hook
  }
  self {
    parts { capital, risk_appetite }
    separations { (capital, risk_appetite: 3) }
  }
  budget 1.0
  floor  2.0
}`,
  },
  {
    id: "02",
    name: "02-two-books.smith",
    title: "Attention divides",
    blurb:
      "Two books compete for the same trader's attention. Water-filling is NOT a 50/50 split — the steeper book gets more.",
    source: `// 02 — One trader, two books: attention must divide.
//
// The trader quotes in two markets at once. There is only one budget of
// attention. The framework does NOT split it evenly — it runs water-filling:
// pour attention where the marginal edge is steepest, until every attended
// book returns the same marginal edge p*. Open the Attention tab and watch
// the water line settle to a single price across both books.
//
// This is the market maker's real problem: you cannot quote everything
// tightly. The price p* is the shadow cost of your own attention.

agent trader {
  purpose minimise spread_cost
  scenes {
    scene bonds    serves spread_cost with quote_hook
    scene equities serves spread_cost with quote_hook
  }
  self {
    parts { book, nerve, discipline }
    separations {
      (book, nerve: 2), (nerve, discipline: 3), (discipline, book: 2)
    }
  }
  budget 1.0
  floor  2.0
}`,
  },
  {
    id: "03",
    name: "03-five-books.smith",
    title: "Some books go dark",
    blurb:
      "Five books, one tight budget. When attention is scarce, the marginal books fall below the water line and get quoted at zero.",
    source: `// 03 — Five books, one scarce budget: the threshold.
//
// A desk covering five markets on one trader's attention. When the budget is
// tight, water-filling does something decisive: the books whose marginal edge
// never clears the price p* get ZERO attention — they go dark. This is not a
// bug; it is the optimal allocation. The Attention tab shows which books are
// "active" and which are "dry".
//
// Economically: a stretched desk rationally stops quoting its weakest
// markets. The theory just tells you exactly where the cutoff is.

agent multi_desk {
  purpose minimise queue_risk
  scenes {
    scene fx_spot   serves queue_risk with quote_hook
    scene fx_fwd    serves queue_risk with quote_hook
    scene rates     serves queue_risk with quote_hook
    scene credit    serves queue_risk with hedge_hook
    scene vol       serves queue_risk with hedge_hook
  }
  self {
    parts { liquidity, models, limits, judgment }
    separations {
      (liquidity, models: 3), (models, limits: 2),
      (limits, judgment: 2), (judgment, liquidity: 2)
    }
  }
  budget 0.35
  floor  2.0
}`,
  },
  {
    id: "04",
    name: "04-quiet-book.smith",
    title: "Silence is a position",
    blurb:
      "Construction vs commitment. The desk goes quiet while it re-forms its view — and quiet is productive, not idle.",
    source: `// 04 — Phase exclusion: the desk that goes quiet.
//
// Every tick has two phases. In CONSTRUCTION the desk observes and diagnoses
// — it forms a view but does not trade. In COMMITMENT it may act. The two
// never overlap. On the Execution tab the timeline is blue while the desk is
// building its view (silent) and orange when it commits.
//
// The lesson traders learn late: not-quoting is a decision, not an absence.
// A desk re-forming its book is doing work even while it shows no fills.

agent strat_desk {
  purpose minimise mispricing
  scenes {
    scene research serves mispricing with read_hook
    scene execute  serves mispricing with trade_hook
  }
  self {
    parts { thesis, sizing, timing }
    separations {
      (thesis, sizing: 3), (sizing, timing: 2), (timing, thesis: 2)
    }
  }
  budget 1.0
  floor  2.0
}`,
  },
  {
    id: "05",
    name: "05-positions.smith",
    title: "Positions only accumulate",
    blurb:
      "The committed count never resets. Run 30 ticks: the staircase only goes up. A desk reset to zero is a different desk.",
    source: `// 05 — The monotone staircase.
//
// Every committed trade increments a count that NEVER decreases. Run for 30
// ticks and watch the count staircase on the Execution tab: it only climbs.
// This is identity invariant I2 — the desk's history is monotone. You cannot
// un-trade. A "fresh copy" of the desk started at count zero is, by this
// measure, a different individual, even with identical parameters.
//
// This is why a trading book carries its scars: the count is the desk's age.

agent book_keeper {
  purpose minimise reconciliation_gap
  scenes {
    scene mark   serves reconciliation_gap with mark_hook
    scene settle serves reconciliation_gap with settle_hook
  }
  self {
    parts { ledger, method, care }
    separations {
      (ledger, method: 4), (method, care: 2), (care, ledger: 3)
    }
  }
  budget 1.0
  floor  2.0
}`,
  },
  {
    id: "06",
    name: "06-two-desks.smith",
    title: "Two desks, one market",
    blurb:
      "A maker and a hedger share a purpose but nothing internal. They never see each other's book — they meet only in the market state.",
    source: `// 06 — Coordination without a shared book.
//
// A market maker and a hedger work the same purpose (keep the joint position
// flat) but share NOTHING internally — different capital, different risk
// engines, different instincts. They never read each other's book. They meet
// only in Ω, the shared market state: when the maker takes on inventory, the
// hedger reads the changed state next tick and offsets it.
//
// This is the framework's claim about teams: coordination lives in the shared
// OUTCOME, not in shared internals. The "tie" is how tightly their fortunes
// are linked; "couple" is how strongly their timing locks.

society trading_floor {
  agent maker {
    purpose minimise joint_inventory
    scenes {
      scene quote serves joint_inventory with quote_hook
    }
    self {
      parts { capital, appetite }
      separations { (capital, appetite: 3) }
    }
    budget 1.0
    floor  2.0
  }
  agent hedger {
    purpose minimise joint_inventory
    scenes {
      scene offset serves joint_inventory with hedge_hook
    }
    self {
      parts { mandate, models }
      separations { (mandate, models: 2) }
    }
    budget 0.5
    floor  2.0
  }
  tie (maker, hedger: 2)
  couple 3.0
}`,
  },
  {
    id: "07",
    name: "07-the-edge.smith",
    title: "The edge you can't arbitrage away",
    blurb:
      "The punchline. Run any desk to quiescence and the residual stops at β > 0, never zero. Some inventory risk is irreducible — that IS the desk's private edge.",
    source: `// 07 — The floor: why the risk never reaches zero.
//
// Run this desk and watch the residual on the Execution tab. It falls... and
// then STOPS, above zero, at the floor β. It never reaches zero no matter how
// long you run it. The framework's central theorem: for any bounded reader of
// its own state, a strictly positive residual is irreducible.
//
// For a trading desk this is not a failure — it is the whole business. The
// gap you cannot close is the private information only you hold: your edge.
// An efficient market would drive β to zero and there would be nothing to
// trade. β > 0 is the reason the desk exists. The Structure tab shows the
// realised floor as the least-cost way to sever one part from the rest —
// the cheapest piece of yourself you could give away, and still not zero.

agent edge_desk {
  purpose minimise inventory_risk
  scenes {
    scene make_market serves inventory_risk with quote_hook
    scene hedge       serves inventory_risk with hedge_hook
    scene source_flow serves inventory_risk with flow_hook
  }
  self {
    parts { capital, flow, models, reputation }
    separations {
      (capital, flow: 3), (flow, models: 2),
      (models, reputation: 2), (reputation, capital: 2)
    }
  }
  budget 1.0
  floor  2.0
  coherence keeps { reputation, capital }
}`,
  },
];

export function scriptByName(name) {
  return SCRIPTS.find((s) => s.name === name);
}
