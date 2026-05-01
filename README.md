<h1 align="center">Musande</h1>
<p align="center"><em>An Equivalence Calculus for Bounded Cognition: The S-Entropy Framework</em></p>

<p align="center">
  <img src="assets/images/Scale_of_justice,_canon_law.svg.png" alt="Logo" width="300"/>
</p>

**Author:** Kundai Farai Sachikonye<sup>1</sup>
**Affiliation:** <sup>1</sup> AIMe Registry for Artificial Intelligence
**Classification:** 03B30 (Foundations of mathematics), 03F40 (Gödelian phenomena), 28D05 (Measure-preserving transformations), 47A10 (Spectral theory), 94A17 (Information theory)

---

## Abstract

This repository presents the development of *S-entropy*: a calculus
of distance to global truth measured on a bounded scale $[0,100]$
relative to a receiver, in which the global value of a problem
is asserted by an expression whose subtasks are *unconstrained*.
The calculus rests on three structural principles. First, the
**Triple Equivalence**: oscillatory, categorical, and partition
representations of any state form an equivalent triple under
explicit conversion functors, so any computation admits relocation
to whichever representation makes it cheapest. Second, the
**Unconstrained Subtask Theorem**: an expression $E$ resolving
to a global S-value $S^{\*}$ admits arbitrary subtask decomposition
— signed, fractional, type-mixed, locally infeasible — provided
composition under the receiver's evaluation map yields $S^{\*}$.
Third, the **Recursive No-Privileged-Level Theorem**: every S-value
decomposes into a triple of S-values at the next finer depth, each
being itself the global S-value of its sub-problem, with the same
algebraic laws holding at every depth. A floor theorem establishes
that no receiver in a bounded cognitive architecture can attain
$S = 0$; the smallest knowable error is a strict positive constant
characteristic of the receiver. **Information catalysts** are defined
as expression atoms whose application strictly decreases the
receiver's S-value, with multiplicative composition law
$\kappa_{12} = 1 - (1-\kappa_1)(1-\kappa_2)$. **Circular validation**
across at least three mutually-supporting expressions is shown to be
both necessary and sufficient for foundational coherence.

The framework is presented as pure mathematics with no physical
or empirical postulate required for its development. A complete
numerical validation suite of twenty independent experiments
verifies the principal theorems with maximum discrepancy below
$10^{-14}$ on identity statements and within the predicted analytic
bounds on inequality statements.

**Keywords:** S-entropy, bounded cognition, triple equivalence,
subtask freedom, information catalyst, recursive coordinates,
circular validation, smallest knowable error, partition algebra.

---

## 1. Repository Layout

The repository is organised into a foundational mathematical
treatment and a series of computational instantiations that
exercise different sub-domains of the calculus.

| Component | Location | Description |
|---|---|---|
| Foundational paper | `epistemology/unconstrained-subtask-recursion/` | Formal calculus, all theorems and proofs |
| Validation suite | `epistemology/unconstrained-subtask-recursion/validation/` | 20 numerical experiments, JSON results, publication panels |
| Companion manuscripts | `epistemology/sources/` | Domain-specific developments and applications |
| Computational demonstrations | `demos/` | Reference implementations across five problem classes |

## 2. Foundational Paper

The mathematical core is `unconstrained-subtask-recursion-equivalence.tex`,
a self-contained pure-mathematics treatment in twelve parts:

| Part | Subject |
|---|---|
| I | The S-scalar and the receiver |
| II | The Triple Equivalence |
| III | S-expressions and subtask freedom |
| IV | Information catalysts |
| V | Recursive structure |
| VI | Circular validation |
| VII | The calculus |
| VIII | Worked examples |
| IX | Connections to standard mathematics |
| X | Extended properties |
| XI | Beyond the calculus: open directions |
| XII | Numerical validation |

The three load-bearing theorems are:

1. **Floor Theorem** (Theorem 3.2). For every bounded receiver
   $\mathcal{R}$, the smallest knowable error
   $S_\flat(\mathcal{R}) > 0$ strictly. Perfect alignment is
   structurally unattainable.

2. **Triple Equivalence Theorem** (Theorem 6.1). The functors
   $F_{OC}$, $F_{CP}$, $F_{PO}$ are part of mutually inverse
   equivalences of categories on the oscillatory, categorical,
   and partition representations. Any computation in one
   representation may be relocated to either of the others
   at the conversion cost of the relevant functor.

3. **Unconstrained Subtask Theorem** (Theorem 10.1). Given an
   expression $\xi$ with $\mathrm{eval}_{\mathcal{R}}(\xi) =
   k^{*}$ and global S-value $S^{*}$, every subtask
   $\eta \in \mathrm{Sub}(\xi)$ admits replacement by any
   $\eta' \in \mathcal{E}$ in the receiver-evaluation
   equivalence class $[\eta]$ without changing the global
   S-value. Subtasks may take any local S-value, including
   $S_{\mathrm{local}} = 100$ (locally infeasible).

## 3. Numerical Validation

The validation suite consists of twenty experiments, each a
self-contained test of a named theorem. All twenty pass; identity
theorems hold to machine precision.

### 3.1 Aggregate Results

| # | Theorem | Type | Tests | Outcome |
|---|---|---|---|---|
| 01 | Floor Positivity | Bound | 12 capacities | Floor strictly positive at every capacity |
| 02 | Triple Equivalence | Identity | 40 round-trips | Round-trip identity within discretisation |
| 03 | Composition Multiplicity | Identity | $n=1..12$ | Exact match to $2^{n-1}$ at every $n$ |
| 04 | Unconstrained Subtask | Identity | 19 expressions | All evaluate to global target |
| 05 | Local-Global Decoupling | Identity | 8 extremes | Global preserved under arbitrary subtask values |
| 06 | Multiplicative Catalytic Power | Identity | 81 $(\kappa_1,\kappa_2)$ pairs | Max error $1.11\times 10^{-16}$ |
| 07 | Catalyst Convergence | Identity | 6 $\kappa$, 50 steps | Geometric decay $(1-\kappa)^n$, max error $3.55\times 10^{-15}$ |
| 08 | Recursive Multiplicity | Lower bound | depths 1..7 | $T(n,d) = d(d+1)^{n-1}$ saturated |
| 09 | Stability | Bound | sizes 3..50 | Predicted budget matched |
| 10 | Coherence Threshold | Boundary | 63 samples | Threshold transition exact |
| 11 | Information Bound | Bound | 24 $(S_\flat,\epsilon)$ pairs | Shannon bound respected at every point |
| 12 | Cascade Composition | Identity | 8 cascades | $1-\prod_i(1-\kappa_i)$ matched exactly |
| 13 | Linear Justification Failure | Bound | 24 chains | No chain reaches 0; floor respected |
| 14 | Floor Information | Monotone | 9 floors | Information diverges as $S_\flat \to 0$ |
| 15 | $S_3$ Symmetry | Identity | 4 triples | Multiset, sum, product invariant |
| 16 | No Privileged Level | Identity | 20 embeddings | S-value preserved under recursive extension |
| 17 | Cross-Representation | Identity | 4 expressions | Mixed-type expressions evaluate to global value |
| 18 | Recursive Functor | Identity | 12 pairs | $\rho_d(\xi_1+\xi_2) = \rho_d(\xi_1)+\rho_d(\xi_2)$ |
| 19 | Asymptotic Floor | Boundary | 4 cascades | Borel–Cantelli analogue confirmed |
| 20 | Receiver Perturbation | Bound | 4 perturbations | $\|\Delta S\| \leq C\epsilon$ |

**Pass rate:** 20/20.

### 3.2 Headline Findings

- **Identity theorems are exact.** Every theorem asserting an
  algebraic identity is verified to machine precision.
- **Bound theorems are tight.** Every inequality is verified
  with the predicted bound saturated or respected at every
  test point.
- **Multiplicity theorems are saturated.** The composition count
  $2^{n-1}$ and the recursive labelled count $d(d+1)^{n-1}$ are
  matched exactly by direct enumeration up to $n = 12$ and
  $d = 7$ respectively.
- **Convergence theorems are geometric.** Catalyst-driven
  convergence matches $(1-\kappa)^n$ at every step over 50-step
  cascades for all six tested $\kappa$ values.
- **Symmetry invariants hold.** The $S_3$ group action on triples
  preserves the multiset, sum, and product without exception.

### 3.3 Reproducibility

All twenty experiments are reproducible from a seeded Python
script. The full suite runs in under one second on commodity
hardware.

```bash
cd epistemology/unconstrained-subtask-recursion/validation
python s_entropy_validation.py
python generate_panels.py
```

Outputs:
- `validation/results/01_floor_theorem.json` … `validation/results/20_receiver_perturbation.json`
- `validation/results/master_summary.json`
- `validation/figures/panel_1_floor.png` … `validation/figures/panel_5_cascade.png`

## 4. Companion Manuscripts

The folder `epistemology/sources/` collects companion manuscripts
that develop specific aspects of the calculus:

| Manuscript | Topic |
|---|---|
| `bounded-phase-space-law.tex` | The bounded-phase-space axiom and its dynamical consequences |
| `composition-inflation.tex` | The composition-inflation count $T(n,d) = d(d+1)^{n-1}$ |
| `loschmidt-paradox-resolution.tex` | Time as partition count; resolution of microscopic reversibility |
| `recursive-depths.tex` | Recursive ternary depth and four-tier precision refinement |
| `spectroscopic-derivation-of-elements.tex` | Atomic shell structure from partition coordinates |
| `st_stellas_categories.pdf` | Categorical formulation of bounded oscillatory dynamics |
| `ternary-unit-representation.pdf` | Ternary encoding of three-dimensional partition space |
| `trajectory-completion-mechanism.tex` | Backward navigation in bounded phase space |
| `necessity-for-circular-validation.pdf` | Three-tier hierarchy of formal incompleteness |

Each manuscript is a self-contained development; the foundational
calculus in `unconstrained-subtask-recursion-equivalence.tex` is
the formal core to which the others may be referred for the
underlying algebraic structure.

## 5. Computational Demonstrations

The folder `demos/` contains reference implementations exercising
the calculus across five distinct problem classes. Each
implementation produces persisted JSON measurements of execution
time relative to a domain-standard baseline and of the variance
reduction profile under iterated catalysis.

| Implementation | Operations tested | Mean variance reduction | Mean speedup over baseline |
|---|---|---|---|
| Semantic navigation | $[10, 50, 100, 500, 1000]$ | $14.2\times$ | $273.5\times$ |
| Consciousness system | $[5, 25, 50, 100, 200]$ | $14.8\times$ | $525.8\times$ |
| Genomic analysis | $[100, 500, 1000, 2000, 5000]$ | $13.0\times$ | $307.2\times$ |
| Miraculous circuits | $[10, 50, 100, 500, 1000]$ | $26.0\times$ | $892.3\times$ |
| Molecular transformation | $[50, 250, 500, 1000, 2500]$ | $20.5\times$ | $483.3\times$ |

The variance reductions trace exponential decay consistent with the
catalyst-convergence theorem: starting variances in $[0.78, 0.91]$
reduce to terminal variances in $[0.03, 0.07]$ within ten iterations.
The accompanying speedups are properties of the specific
implementation against its specific baseline and are not invariants
of the underlying calculus.

```bash
cd demos
python quick_demo.py             # Single-implementation walkthrough
python run_all_demonstrations.py # Full suite, ~5–10 minutes
```

Persisted measurements are written to `demos/demo_results/` as
JSON files of the form `<system>_<timestamp>.json` together with
performance and variance-evolution plots.

## 6. Installation

The validation suite has only `numpy` and `matplotlib` as external
dependencies. The demonstrations additionally use the standard
scientific-computing stack.

```bash
pip install numpy matplotlib scipy pandas scikit-learn seaborn plotly
```

No specialised dependencies are required; the implementations are
written in pure Python.

## 7. Citation

If this work is useful to your research, please cite the
foundational paper:

```
@unpublished{sachikonye2025sentropy,
  author = {Sachikonye, Kundai Farai},
  title  = {S-Entropy: An Equivalence Calculus of Unconstrained Subtask Recursion},
  year   = {2025},
  note   = {Manuscript, AIMe Registry for Artificial Intelligence},
}
```

## 8. License and Status

The mathematical content of the repository is presented for open
academic use under the conditions stated in the
`LICENSE` file at the repository root. The validation suite, the
publication panels, and the companion manuscripts are reproducible
from the seeded sources without external data.

The framework is under active development; the foundational
calculus is settled and validated, while the companion
manuscripts and computational demonstrations continue to expand.
