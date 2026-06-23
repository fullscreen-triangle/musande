"""
run_validation.py -- validation runner for
"On the Necessary Substructures of Finite Contact Graphs".

Sweeps many randomized finite contact graphs (varying part count, floor, edge
density, weight spread) and runs every theorem-validator on each, plus the
standalone witnesses. Aggregates pass/fail and writes a JSON report.

Usage:
    python run_validation.py [--seed N] [--graphs K] [--out results.json]

Exit code 0 iff every check on every graph passed.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import sys
import time
from collections import defaultdict
from typing import Dict, List

import contact_graph as cg
from validators import ALL_VALIDATORS, STANDALONE_VALIDATORS


def random_graph(rng: random.Random) -> Dict:
    n_parts = rng.choice([3, 4, 5, 6, 7])
    floor = rng.choice([0.5, 1.0, 2.0])
    dens = rng.choice([0.2, 0.4, 0.6, 0.8])
    wmax = rng.choice([2.0, 4.0, 6.0])
    G = cg.make_medium_graph(rng, n_parts, floor, extra_edge_prob=dens,
                             wmax_mult=wmax)
    spec = {"n_parts": n_parts, "floor": floor, "density": dens,
            "wmax_mult": wmax, "n_vertices": len(G.vertices),
            "n_edges": len(G.edges), "connected": G.is_connected(),
            "min_edge_weight": G.min_edge_weight}
    return {"graph": G, "spec": spec}


def run(seed: int, n_graphs: int, out_path: str) -> int:
    rng = random.Random(seed)
    t0 = time.time()

    per = defaultdict(lambda: {"passed": 0, "failed": 0, "checks": 0,
                              "failures": []})
    graph_reports: List[Dict] = []
    total_checks = 0
    all_passed = True

    for k in range(n_graphs):
        built = random_graph(rng)
        G, spec = built["graph"], built["spec"]
        results = []
        for vfn in ALL_VALIDATORS:
            r = vfn(G)
            results.append(r)
            agg = per[r["name"]]
            agg["checks"] += r["checks"]
            total_checks += r["checks"]
            if r["passed"]:
                agg["passed"] += 1
            else:
                agg["failed"] += 1
                all_passed = False
                for f in r["failures"]:
                    agg["failures"].append({"graph_index": k, "spec": spec,
                                            "failure": f})
        graph_reports.append({"graph_index": k, "spec": spec,
                              "results": results})

    # standalone witnesses (fixed constructions, run once)
    standalone = []
    for vfn in STANDALONE_VALIDATORS:
        r = vfn(None)
        standalone.append(r)
        agg = per[r["name"]]
        agg["checks"] += r["checks"]
        total_checks += r["checks"]
        if r["passed"]:
            agg["passed"] += 1
        else:
            agg["failed"] += 1
            all_passed = False
            for f in r["failures"]:
                agg["failures"].append({"standalone": True, "failure": f})

    elapsed = time.time() - t0

    summary = {}
    for name, agg in per.items():
        summary[name] = {
            "graphs_passed": agg["passed"],
            "graphs_failed": agg["failed"],
            "total_checks": agg["checks"],
            "passed": agg["failed"] == 0,
            "sample_failures": agg["failures"][:5],
        }

    report = {
        "meta": {
            "paper": "On the Necessary Substructures of Finite Contact Graphs",
            "suite": "concrete contact-graph numerics; ground premise (floor "
                     "from infinitude), T0-T8, and measurement (self-defeat, "
                     "falsification); randomized sweep + standalone witnesses",
            "seed": seed,
            "n_graphs": n_graphs,
            "total_checks": total_checks,
            "elapsed_seconds": round(elapsed, 4),
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "overall_passed": all_passed,
        "summary_by_theorem": summary,
        "standalone_witnesses": standalone,
        "graphs": graph_reports,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("Finite Contact Graphs -- validation suite")
    print(f"  graphs swept : {n_graphs}")
    print(f"  total checks : {total_checks}")
    print(f"  elapsed      : {elapsed:.3f}s")
    print(f"  seed         : {seed}")
    print("-" * 64)
    for name, s in summary.items():
        flag = "PASS" if s["passed"] else "FAIL"
        tot = s["graphs_passed"] + s["graphs_failed"]
        print(f"  [{flag}] {name:<28} runs {s['graphs_passed']}/{tot}"
              f"  checks={s['total_checks']}")
    print("-" * 64)
    print(f"  OVERALL: {'PASS' if all_passed else 'FAIL'}")
    print(f"  report written to {out_path}")
    return 0 if all_passed else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260623)
    ap.add_argument("--graphs", type=int, default=300)
    ap.add_argument("--out", type=str, default="validation_results.json")
    args = ap.parse_args()
    return run(args.seed, args.graphs, args.out)


if __name__ == "__main__":
    sys.exit(main())
