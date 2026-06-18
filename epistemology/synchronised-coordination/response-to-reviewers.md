# Response to Reviewers

**Manuscript:** Coordination Regimes of Synchronised Agents: A Self-Contained
Variational Calculus on the S-Entropy Manifold, with External Validation
(formerly "On Cohesion Dynamics in Synchronised Intelligent Agents …")

We thank the three reviewers for criticism that materially improved the paper.
Two themes recurred and drove a substantial rewrite:

1. **Non-independence.** The submitted version relied on constructs (S-entropy,
   cell-truth receiver calculus, partition Lagrangian) defined in companion
   manuscripts. We have made the paper **fully self-contained**: every object is
   now derived from three stated axioms, every theorem is proved in the paper,
   and all citations to our own unpublished work have been removed.

2. **Validation was self-referential.** The 50 "experiments" checked closed
   forms against themselves. We have **replaced them with nine external
   experiments against public data** the theory did not generate
   (Section 7, Table 1). Critically, **two of the nine contradicted the
   submitted theory and forced corrections**, which we now report openly. We
   adopted a governing rule throughout the revision: *a claim that cannot be
   defended is removed, not softened.* Several claims were accordingly cut.

Below we answer every numbered point. Section/Theorem numbers refer to the
revised manuscript.

---

## Reviewer 1 (applicability / stochasticity / Lagrangian rationale)

**R1.1 — Entropy parameters are content-free shape-of-distribution measures and
cannot capture ecological, content-laden information.**
Agreed. We now state this explicitly (Remark 2.12, "What the S-entropy
coordinates are, and are not"): the coordinates measure the *informational
geometry* of the agent's state, not salience or content. We **withdraw** any
claim that the framework models the specific information a biological agent
attends to (Scope item 2, Section 8). The applicability claims are
correspondingly narrowed.

**R1.2 — Real systems (insect colonies, neural systems) are strongly stochastic
and multiscale; this is not represented.**
We concede the limitation directly (Scope item 3): the model is
overdamped/mean-field and represents fluctuations only through the
Onsager–Machlup noise term; it does not model metastability or time-varying
connectivity. Claims about such systems are now explicitly downgraded to
qualitative structure.

**R1.3 — The Lagrangian rationale is not justified; the system is deterministic,
which is a problem.**
The variational principle is now justified (Section 3.2): because the dynamics
are first-order/overdamped (Kuramoto is first-order), the correct variational
object is the **Onsager–Machlup action** — the most-probable path of a
*stochastic* Langevin process — not a conservative L = T − V. The dynamics are
therefore not fundamentally deterministic; the gradient flow is the zero-noise
limit (Theorem 3.5). This is stated where the action is introduced.

**R1.4 — Phase space itself would be constantly changing (fungibility,
metastability).**
Acknowledged as a limitation (Scope item 3). We do not claim a fixed phase
space models a remodelling network; we restrict claims accordingly.

**R1.5 — Can a real-world Lagrangian / real-world examples be exhibited?**
Yes. Section 7 now grounds the framework in external data, including a
real-data instance of the central coordination claim (EXT08:
representation-disjoint classifiers on a benchmark dataset) and physical
instances of partition extinction (EXT03 Wiedemann–Franz across 11 metals;
EXT07 superconductors). We are explicit that the physical cases *reproduce*
standard results rather than predict new ones (Scope item 6).

**R1.6 — Temper the applicability claims.**
Done throughout, and consolidated in Section 8 (Scope and Limitations).

---

## Reviewer 2 (mathematical rigour; novelty delineation)

**R2.1 — What principle determines the thresholds 0.3/0.5/0.8/0.95? Why are
they not arbitrary?**
We **retract** the claim that these are derived/critical values. They are
operational classification cut-offs (Definition 3.10), and we **prove they are
NOT phase transitions** (Proposition 3.11: ∂²Φ/∂R² does not change sign there).
The only genuine transition in the model is the Kuramoto bifurcation. This
removes the circularity the reviewer detected.

**R2.2 — Theorem 4.9 claimed regime boundaries are second-order transitions
but it was imposed by definition. Prove Φ''(R) changes sign there.**
We could not defend it, so we removed it and proved the opposite
(Proposition 3.11). The genuine second-order transition (the Kuramoto pitchfork)
is proved properly in Theorem 3.7.

**R2.3 — Is Proposition 4.2 (Landau pitchfork) new or just Kuramoto mean-field?**
It is standard Kuramoto mean-field theory; we now say so explicitly (Section 1.3
"what is and is not new" and Theorem 3.7 and Theorem 3.8). It is used as an imported tool,
not claimed as novel.

**R2.4 — Provide the complete Euler–Lagrange derivation instead of "standard
calculus of variations."**
Done in full: Theorem 3.5 derives the Euler–Lagrange system explicitly
(momentum term, coordinate term, cancellation of the first-order terms via the
symmetry of ∂ᵢ∂ⱼΦ, and the gradient-flow zero-noise limit), with the component
equations in Corollary 3.6.

**R2.5 — Precise topological/differentiable structure of M? Compact? Smooth?
Connected? Boundaryless?**
Specified in Definition 2.13 and Remark 2.14: M is a compact, connected,
smooth-in-the-interior manifold with corners (hence *not* boundaryless), with an
explicit block-diagonal metric.

**R2.6 — Is the projection functor to the receiver-agent framework unique?**
The cell-truth/receiver projection material depended on an unpublished companion
paper and could not be made self-contained without importing it. Per the
independence requirement we **removed** the projection-functor construction
rather than rely on external results. The conservative core (coordination is
representation-independent) is retained and proved directly (Theorem 5.2).

**R2.7 — Theorem 5.2 (projection consistency): nontrivial or a restatement?**
Removed with the projection material (see R2.6).

**R2.8 — Definition 6.1 trajectory compatibility: why measure-preserving
reparametrisation; what fails without it?**
The trajectory-compatibility apparatus belonged to the cell-truth layer and was
removed in the self-containment rewrite (see R2.6). It is not used by any
retained theorem.

**R2.9 — Theorem 6.3 "by construction": give a genuine necessity/sufficiency
proof.**
Removed with the trajectory-compatibility material (R2.8). Retained coordination
results are now proved from the axioms, not "by construction."

**R2.10 — Under what assumptions is R_ens invariant under coordinate
transformations?**
R_ens (Definition 4.2) is defined from the scalar reductions (R_i, φ_i) of each
agent's state; Theorem 5.2 states and proves the relevant invariance
(independence of the internal frameworks K_i).

**R2.11 — Why do the same thresholds hold at the ensemble level? Derivation?**
The thresholds are operational at both levels (now bands, not transitions;
Proposition 3.11). The genuine ensemble transition is the Kuramoto bifurcation
applied with the empirical frequency density (Theorem 4.5).

**R2.12 — Theorem 8.2 (regime equations of state): what principle justifies the
functional forms?**
We now label these **phenomenological/descriptive summaries**, not derived laws
(Remark 4.6). We make no claim that they are derived or that the bands they
describe are transitions.

**R2.13 — Theorem 8.3 (all transitions second-order): compute the order
parameter derivatives and show criticality.**
Withdrawn (see R2.1/R2.2); only the Kuramoto transition is claimed, and it is
shown critical in Theorem 3.7.

**R2.14 — Synchronisation Theorem (11.4): several implications heuristic; prove
each separately.**
Recast as the partition-extinction theorem (Theorem 6.4) with a four-step
proof (binary distinguishability → phase-locking ⇒ indistinguishable → lag
undefined/zero → discontinuity), plus the correspondence stated separately and
with explicit scope (Proposition 6.9, Remark 6.10). Heuristic "iff" chains were
replaced by the parts we can prove.

**R2.15 — Why is 0.95 mathematically special? Would 0.94 or 0.96 work?**
It is not special; it is an operational cut-off (Definition 3.10,
Proposition 3.11). Partition extinction is defined at exact phase-locking
(φ_i = φ_j), not at R = 0.95; the threshold is only a label for "near-locked."

**R2.16 — Formal definition of "partition extinction" independent of physical
analogy.**
Provided: Definition 6.3 defines it purely from finite resolution and partition
operations, with no reference to any physical system. Superconductivity etc. are
then *instances* (EXT07), not the definition.

**R2.17 — Theorem 13.1 (aperture sharing): does decoder isomorphism imply
aperture equality or only equivalence classes?**
The aperture-sharing theorem depended on the removed cell-truth layer and was
cut. The retained, defensible statement is the observable-commutation theorem
(Theorem 6.7) distinguishing functional from ontological equivalence.

**R2.18 — Theorem 14.1 (memory congruence): assumptions on the noise η_ij?**
The one-way memory construct M = ∫ max(dH/dt,0) dt lacked grounding and was
**removed** (we could not defend the cognitive interpretation; per the governing
rule it was cut rather than hedged).

**R2.19 — How is machine-precision agreement across 50 experiments independent
validation?**
It is not; the reviewer is correct. We **replaced** the suite with nine external
experiments (Section 7) and now call the original closed-form checks by their
correct name, *internal consistency checks*, which we do not count as validation.

**R2.20 — Identify which theorems are genuinely new vs. reformulations.**
Done explicitly in Section 1.3 ("Imported … / New here …").

---

## Reviewer 3 (novelty emphasis; analogy strength; intuition; idealisations)

**R3.1 — Novelty and contributions not adequately emphasised; no comparison to
Kuramoto / cell-truth / partition extinction.**
Section 1.3 now separates imported tools from new contributions and compares to
the prior literature; Section 7 (EXT02) states precisely how our corrected
critical coupling relates to standard Kuramoto theory.

**R3.2 — Irreplaceable advantage of the Lagrangian framework vs. traditional
synchronisation models?**
Stated in Section 3.2: the Onsager–Machlup action unifies the synchronisation
order parameter, the variance floor, and the S-entropy dynamics under one
variational principle with explicit Euler–Lagrange equations (Theorem 3.5); we
do not claim it supersedes Kuramoto, only that it embeds it in a fuller state
space.

**R3.3 — The partition-extinction analogy may be forced (quantum statistics /
indistinguishability vs. classical agent coordination).**
Addressed head-on. We give an analogy-free definition (Definition 6.3) and an
**observable-commutation theorem** (Theorem 6.7) that *separates* functional
from ontological indistinguishability. We explicitly state (Remark 6.8,
Remark 6.10) that synchronised agents are equivalent only on *categorical*
observables and do **not** lose physical identity as bosons do. The
correspondence is now structural, not an identity (Proposition 6.9).

**R3.4 — Definitions/symbols (S-entropy, psychon, aperture, partition potential)
lack intuitive explanation; why a 5-D manifold; is reduction feasible?**
The S-entropy coordinates are now derived and interpreted (Section 2.3, Remark
2.9); the partition potential's four terms each have a stated provenance
(Remark 3.2); the five dimensions are motivated (two synchronisation variables
R, σ² plus the three S-entropy coordinates) in Definition 2.13. The "psychon
triple" and trajectory/memory apparatus were **removed** as undefendable in a
self-contained treatment.

**R3.5 — Threshold values lack theoretical derivation / explicit Landau
expansion.**
See R2.1/R2.2: the thresholds are operational, proved not to be transitions
(Proposition 3.11); the one genuine transition has its Landau analysis
(Theorem 3.7).

**R3.6 — Heavy reliance on the unpublished cell-truth framework (circular
dependency).**
Eliminated. The cell-truth dependency was removed entirely; the paper is
self-contained (Section 1.1).

**R3.7 — The three axioms are overly general (low discriminatory power).**
Conceded explicitly (Remark 2.4 and Scope item 1): the axioms fix the state
space, not the conclusions; discriminating content is in the dynamics and the
external tests.

**R3.8 — Almost no detail on the 50 experiments' design/hyperparameters/
significance.**
Moot: that suite is replaced. The nine external experiments (Section 7) report
data sources, methods, statistics (p-values, CV, correlation), and ship with
reproducible code and JSON results.

**R3.9 — No comparative validation against real-world multi-agent / robotic /
animal / database systems; figures only show theory curves.**
Section 7 now validates against real data: real atomic structure (EXT01),
direct Kuramoto simulation (EXT02), measured Lorenz numbers (EXT03), real
PhysioNet sleep EEG (EXT04), literature enzyme kinetics (EXT05), a clinical
meta-analysis (EXT06), superconductor data (EXT07), and a real benchmark
multi-classifier system (EXT08–09).

**R3.10 — Conflating functional equivalence with ontological indistinguishability
("decoder equivalence" = "categorical indistinguishability").**
Resolved by Theorem 6.7 and Remarks 13.7/13.9 (see R3.3): functional
(categorical-observable) equivalence is explicitly distinguished from physical
identity.

**R3.11 — "Coordination friction is exactly zero" is a mathematical
idealisation; real systems have delay/noise/drift.**
We now state that the exact zero holds *in the categorical model* and that real
systems retain small positive friction (Remark 6.5, Remark 6.10, Scope item 5).
The exactness is a model property, not a claim about hardware.

**R3.12 — Corollary 12.2 (reversibility) conflicts with hysteresis in physical
partition extinction.**
We **withdraw** the reversibility corollary. The gradient variational model
makes no hysteresis claim, so we make none (Remark 6.10(ii), Scope item 5).

**R3.13 — One-way cumulative memory M = ∫ max(dH/dt,0) dt lacks cognitive
grounding.**
**Removed** (see R2.18).

**R3.14 — Zero-work aperture (Theorem 3.5) uses an infinite-barrier idealisation;
real categorical filtering costs attention/compute.**
The zero-work aperture was a hard-wall idealisation we could not defend as
cost-free for real agents; the aperture apparatus was removed from the
self-contained core, and we make no zero-cost-filtering claim for real systems.

---

## Summary of changes

- Full self-containment: S-entropy, partition potential, and Lagrangian all
  derived in-paper from three axioms; all citations to our unpublished work
  removed.
- **Correction (data-forced):** critical coupling K_c = 2/[π g(0)]
  (= 1.596 σ for Gaussian), replacing the erroneous 2σ/π; confirmed by
  simulation (EXT02).
- **Correction (data-forced):** the sleep-stage ordering inverts on real EEG
  and is **withdrawn** (EXT04).
- Thresholds demoted to operational cut-offs; proved not to be transitions.
- Explicit Euler–Lagrange derivation supplied.
- Partition extinction given an analogy-free definition and an
  observable-commutation theorem; ontological-identity language removed.
- Validation replaced by nine external experiments with honest verdicts
  (2 confirmed, 5 confirmed-with-scope, 2 corrections).
- New "Scope and Limitations" section.
- Removed (undefendable in a self-contained, data-checked treatment): the
  cell-truth projection functor, trajectory/memory-compatibility apparatus,
  one-way memory, the zero-work aperture as cost-free, the reversibility
  corollary, and the "equations of state as derived laws" claim.

We believe the manuscript is now both self-contained and empirically grounded,
and that the two data-forced corrections demonstrate the external tests are
genuine.
