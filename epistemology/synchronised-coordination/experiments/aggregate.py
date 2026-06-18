"""
Aggregate all external (EXT*) experiment results into one master record and a
compact verdict table for the revised papers. Verdicts are honest:
  CONFIRMED      - external data supports the claim
  CONFIRMED*     - supported but scoped/qualified (caveat required)
  CORRECTION     - external data contradicts the stated claim; paper must change
"""
import json
from pathlib import Path

RES = Path(__file__).parent / "results"

verdicts = [
    ("EXT01", "Shell capacity C(n)=2n^2", "CONFIRMED*",
     "Exact as level degeneracy & reproduces period lengths via n+l rule; "
     "pure-2n^2 nesting alone does NOT give noble-gas closures (Aufbau needed)."),
    ("EXT02", "Kuramoto critical coupling", "CORRECTION",
     "Paper's Kc=2 sigma/pi is wrong by sqrt(2pi)~2.51 even for Gaussian; "
     "correct law Kc=2/(pi g(0)) (=1.596 sigma Gaussian). Simulation confirms "
     "corrected law; 2 sigma/pi fails for uniform/Lorentzian/bimodal."),
    ("EXT03", "Wiedemann-Franz universality", "CONFIRMED",
     "Predicted L0=2.443e-8; measured mean 2.511e-8 over 11 metals, 20/22 "
     "within 15%. (Reproduces standard physics; not a novel prediction.)"),
    ("EXT04", "Sleep-stage R ordering", "CORRECTION",
     "On real Sleep-EDF EEG the cross-channel order parameter gives "
     "W>REM>N1>N2>N3, INVERTING the claimed N3>W>N1>N2>REM (N3 lowest). "
     "Channel-geometry caveat noted; claim must be cut or heavily scoped."),
    ("EXT05", "Enzyme efficiency anti-correlation", "CONFIRMED*",
     "log(kcat/Km) vs substrate heavy-atom count: Pearson r=-0.67 (p=0.05), "
     "matches claimed ~-0.57 in sign/magnitude; but weak (r^2=0.45), "
     "Spearman -0.40, extremes-driven. Qualitative only."),
    ("EXT06", "Antidepressant response convergence", "CONFIRMED*",
     "Cipriani 2018 ORs cluster tightly (CV=0.10); binding breadth does not "
     "predict response (r=0.39, n.s.). Supports convergence; aperture "
     "mechanism is one interpretation, not proven cause."),
    ("EXT07", "Partition extinction (exact vanishing)", "CONFIRMED*",
     ">=14 orders-of-magnitude resistivity drop (operationally exact zero) at "
     "sharp Tc across 10 superconductors + He-4 lambda. Reproduces BCS/Landau "
     "phenomenology; does not predict Tc."),
    ("EXT08", "Common-Cell Convergence", "CONFIRMED",
     "Four representation-DISJOINT agents (digits) agree on labels 0.51 vs "
     "0.10 chance; when all agree (29%) they are 100% correct. Real instance "
     "of coordination without shared representation."),
    ("EXT09", "Catalytic composition / replication", "CONFIRMED*",
     "Ensemble error 0.16 < best individual 0.26 (composition lowers floor). "
     "But exact multiplicative law assumes independence agents violate "
     "(err-corr 0.15); state as independence-limit bound, not equality."),
]

master = {"experiments": [], "summary": []}
for eid, name, verdict, note in verdicts:
    # attach the raw result file if present
    matches = list(RES.glob(f"{eid}*".replace("EXT08", "EXT08_09")
                            if eid in ("EXT08", "EXT09") else f"{eid}*.json"))
    raw = None
    for m in RES.glob("*.json"):
        if m.stem.startswith(eid) or (eid in ("EXT08", "EXT09")
                                      and m.stem.startswith("EXT08_09")):
            raw = m.name
            break
    master["experiments"].append(
        {"id": eid, "claim": name, "verdict": verdict, "note": note,
         "result_file": raw})
    master["summary"].append(f"{eid}  {verdict:11s}  {name}")

n_conf = sum(1 for *_, v, _ in [(0,0,e[2],0) for e in verdicts] if v == "CONFIRMED")
counts = {}
for *_, v, _ in [(e[0], e[1], e[2], e[3]) for e in verdicts]:
    counts[v] = counts.get(v, 0) + 1
master["verdict_counts"] = counts
master["headline"] = (
    "9 external experiments against public data. "
    f"{counts.get('CONFIRMED',0)} confirmed outright, "
    f"{counts.get('CONFIRMED*',0)} confirmed-with-scope, "
    f"{counts.get('CORRECTION',0)} corrections forced by data "
    "(Kuramoto Kc factor; sleep-stage ordering). Unlike the original "
    "self-referential suite, these test claims against data the framework did "
    "not generate, and two of them changed the papers.")

out = RES / "MASTER_external.json"
out.write_text(json.dumps(master, indent=2))
print("\n".join(master["summary"]))
print("\nverdict counts:", counts)
print("\n" + master["headline"])
print(f"\nwritten -> {out}")
