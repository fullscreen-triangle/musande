# Validation suite — *On the Necessary Substructures of Finite Contact Graphs*

Executable, numerical witnesses for every result of the flagship paper. Each
abstract theorem is checked against **concrete finite contact graphs** — finite,
connected, weighted graphs with a positive edge-weight floor and a distinguished
**medium** vertex (the reference against which parts are individuated).

The runner sweeps hundreds of randomized contact graphs (varying part count,
floor, edge density, weight spread), runs all validators on each, plus
fixed-construction standalone witnesses, and aggregates into a JSON report.

## Run

```bash
cd validation
python run_validation.py                       # 300 graphs, default seed
python run_validation.py --graphs 600 --seed 31
python run_validation.py --out results.json
```

Exit code is `0` iff every check on every graph passed.

## Files

| File | Role |
|------|------|
| `contact_graph.py` | `ContactGraph` model: vertices/edges/weights, medium, cuts, boundary cost, separation-from-medium, global residual (min cut), reshuffle (measurement) |
| `validators.py` | one validator per theorem-group + standalone region witness |
| `run_validation.py` | randomized sweep, aggregation, JSON report, console summary |
| `validation_results.json` | latest report (overwritten per run) |

## Theorem ↔ validator map

| Validator | Paper result | What is checked |
|-----------|--------------|------------------|
| `ground_floor_from_infinitude` | §2 Floor from Infinitude (`thm:floor-infinitude`) | every thing (proper part) has a strictly positive identification residual ≥ floor; no zero-cost (completed) comparison |
| `T0_floor` | T0 Floor Theorem (`thm:floor`) | every nonempty proper part has cut weight ≥ floor > 0; **no sharp cut ever** |
| `T1_negation` | T1 Individuation by negation (`thm:negation`) | complementation is a selector-free involution; part + complement partition the whole |
| `T2T3_residual` | T2/T3 residual (`thm:residual-region`, `thm:residual-invariant`) | residual ≥ floor and **invariant under reshuffling** (weighted iso fixing the medium) |
| `T2_region_not_point` | T2 non-locality (`cor:point-forbidden`) | on a two-cluster graph the min-cut is a **multi-vertex bipartition** (both sides regions), at exactly the bridge weight = floor — truth is a region, never a point |
| `T4_private` | T4 private invariant (`thm:private`) | every part's boundary cost to the medium is positive ≥ floor |
| `T5_gate` | T5 selection requires a gate (`thm:gate-necessary`) | branching vertices (deg ≥ 2) underdetermine the next step; reachability near-total |
| `T6_nonreturn` | T6 non-return (`thm:nonreturn`) + temporal (`thm:temporal-nonreturn`) | committed count strictly monotone; states never repeat; undo increments; growing complement distinguishes a thing from its earlier stage |
| `T7_quotient` | T7 quotient gate (`thm:single-gate`, `lem:quotient-floor`) | quotient inherits a positive floor; coherent collective gate is single-valued |
| `T8_authored` | T8 authored structures (`thm:authored-exist` + 3 bounds) | specify-then-instantiate yields a contact graph; forward-closure states all distinct (open-endedness); copy differs in committed count (non-duplication); no sub-floor edge (floor-limited authorship) |
| `measurement` | §12 measurement (`prop:measure-conserves`, `thm:self-defeat`, `thm:falsification`) | reshuffle conserves residual **and** total weight (the medium); separation-from-medium never falls to 0 (self-defeat); adding a boundary edge never decreases separation (resolution does not saturate) |

## How the concrete model realises the paper

- **Contact graph** = finite weighted graph; all edge weights ≥ `floor` (the Finiteness Premise, with the floor read as the derived identification residual).
- **Medium** = a distinguished vertex; individuation of a part is its **separation cost** (min cut) from the medium.
- **Residual** = the global minimum cut over all nontrivial bipartitions (the conserved interstice / "water").
- **Measurement = reshuffle** = a weight-preserving relabelling fixing the medium (permuting the non-medium "marbles"): conserves total weight and the residual, changes the labelling. This is "reshuffling the marbles in the water — the water is invariant."
- **Self-defeat**: resolving identity to a point = driving separation-from-medium to 0; reshuffling conserves it, so it never reaches 0 — identity is structurally unreachable.

## Latest result

600 graphs × 11 validators, two independent seeds: **149,793 checks, all pass.**
See `validation_results.json`.

Notes on faithfulness:
- Validators check the paper's *exact* quantities (cut weight, global min-cut residual, separation-from-medium, committed count), computed by brute force over subsets — exact, not sampled — so every supremum/infimum is the true value on these finite graphs.
- The `T2_region_not_point` witness is a fixed construction (two heavy 3-cliques joined by one floor-weight bridge, medium inside a cluster) chosen so the cheapest cut is provably the cluster split, not any singleton — a non-vacuous demonstration that the residual is region-valued.
