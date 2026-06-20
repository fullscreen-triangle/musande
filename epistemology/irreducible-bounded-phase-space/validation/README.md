# Validation suite — *The Irreducible Boundary of a Bounded Resolvable Space*

Executable, numerical witnesses for every theorem-group of the paper. Each
abstract result is checked against **concrete bounded resolvable spaces** —
finite metric–measure spaces (integer-lattice boxes partitioned into cells of
diameter ≥ δ), exactly the embedded-agent picture of Axiom (BRS): the agent can
name only unions of cells, never sub-cell sets.

The runner sweeps hundreds of randomized spaces (varying dimension 1–3, extent,
cell size, atom weight) and runs all validators on each, aggregating into a JSON
report.

## Run

```bash
cd validation
python run_validation.py                       # 200 spaces, default seed
python run_validation.py --spaces 500 --seed 7 # larger sweep
python run_validation.py --out results.json    # choose output path
```

Exit code is `0` iff every check on every space passed.

## Files

| File | Role |
|------|------|
| `brs.py` | `Space` model + builders, measure μ, separators Σ, boundary thickness β |
| `validators.py` | one validator per theorem-group; each returns pass/fail + evidence |
| `run_validation.py` | randomized sweep, aggregation, JSON report, console summary |
| `validation_results.json` | latest report (overwritten per run) |

## Theorem ↔ validator map

| Validator | Paper result | What is checked numerically |
|-----------|--------------|------------------------------|
| `negation_uniqueness` | Thm: negation is the unique selector-free individuation | complement is an involution; A and N(A) partition Ω with no element named |
| `non_instantaneity_residue` | Thm: non-instantaneity | k=0 yields no proper part (Ω has empty complement); every proper region leaves a separator of measure ≥ μ_min |
| `boundary_thickness` | Thm: Boundary–Thickness | every realisable separator has measure ≥ μ_min > 0; **no sharp (zero-measure) cut ever realised** |
| `floor_agreement` | Thm: the floor is one constant | geometric, representational, and cost floors are all > 0 and each ≥ μ_min; cost g(t)=−log t diverges as t→0 |
| `detectability_sorites` | Thm: Detectability; Cor: sorites | distinguishable ⟺ σ(A) > β_A (interior content positive); sub-floor regions engulfed; no single sub-floor grain is decisive at the τ=1 crossing |
| `diagonal_residue` | Thm: diagonal obstruction; Thm: residue not exhibitable | the self-reference reduces to the Boolean fixpoint d = 1−d, which has **0 solutions** → no total self-applicable verifier → residue not exhibitable |
| `non_return_cessation` | Thm: Non-return; Thm: cessation | committed record M monotone non-decreasing; an "undo" increments M; same-config/different-record states distinct; diverging cost vs bounded return forces a halt at t\* > 0 |

## Notes on faithfulness

The validators check the paper's *exact* definitions, not paraphrases:

- **Detectability** uses β_A = μ(A ∩ Σ) (A's own share of the straddling
  separator), so that σ = interior + β_A makes `interior > 0 ⟺ σ > β_A` an
  identity, exactly as the theorem states. The full separator μ(Σ) counts both
  sides and is *not* the quantity the equivalence is stated with.
- **Sorites**: τ = β/σ legitimately starts ≫ 1 (a tiny aggregate is all
  boundary) and descends. A *decisive grain* is one whose own contribution
  exceeds the floor *and* dominates the aggregate it joins; a sub-floor grain can
  never be individually decisive, however abruptly τ moves while the aggregate is
  still smaller than its boundary — that abruptness is the predicted emergence.
- **Representational residue**: the discrepancy A △ Â between a non-realisable
  target and its named approximant lies *inside a separator cell*; the residue
  the paper bounds (≥ μ_min) is the whole separator cell, not the sub-cell
  sliver.

## Latest result

500 spaces × 7 theorem-groups, two independent seeds: **96,024 checks, all
pass.** See `validation_results.json`.
