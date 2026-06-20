"""
run_validation.py -- comprehensive validation runner.

Sweeps many randomized bounded resolvable spaces (varying dimension, extent,
cell size, atom weight) and runs every theorem-validator on each. Aggregates
pass/fail across the whole sweep and writes a JSON report.

Usage:
    python run_validation.py [--seed N] [--spaces K] [--out results.json]

Exit code 0 iff every check on every space passed.
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

import brs
from validators import ALL_VALIDATORS


def random_space(rng: random.Random) -> Dict:
    """Draw a random bounded resolvable space spec, build it, return both."""
    dim = rng.choice([1, 2, 2, 3])  # bias to 2D
    if dim == 1:
        shape = [rng.choice([8, 12, 16, 20])]
    elif dim == 2:
        shape = [rng.choice([4, 6, 8, 10]), rng.choice([4, 6, 8, 10])]
    else:
        shape = [rng.choice([3, 4, 5]), rng.choice([3, 4, 5]),
                 rng.choice([3, 4])]
    cell_side = rng.choice([1, 2, 2, 3])
    # keep cell_side < smallest extent so >1 cell exists per axis
    cell_side = min(cell_side, max(1, min(shape) - 1))
    weight = rng.choice([0.5, 1.0, 2.0])
    sp = brs.make_box(shape, cell_side, weight)
    spec = {"dim": dim, "shape": shape, "cell_side": cell_side,
            "weight": weight, "n_atoms": len(sp.atoms),
            "n_cells": len(sp.cells), "delta": sp.delta,
            "mu_min": sp.mu_min, "total_measure": sp.total_measure,
            "connected": sp.is_connected()}
    return {"space": sp, "spec": spec}


def run(seed: int, n_spaces: int, out_path: str) -> int:
    rng = random.Random(seed)
    t0 = time.time()

    per_validator = defaultdict(lambda: {"passed": 0, "failed": 0,
                                         "checks": 0, "failures": []})
    space_reports: List[Dict] = []
    total_checks = 0
    all_passed = True

    for k in range(n_spaces):
        built = random_space(rng)
        sp, spec = built["space"], built["spec"]
        results = []
        for vfn in ALL_VALIDATORS:
            r = vfn(sp)
            results.append(r)
            agg = per_validator[r["name"]]
            agg["checks"] += r["checks"]
            total_checks += r["checks"]
            if r["passed"]:
                agg["passed"] += 1
            else:
                agg["failed"] += 1
                all_passed = False
                for f in r["failures"]:
                    agg["failures"].append({"space_index": k, "spec": spec,
                                            "failure": f})
        space_reports.append({"space_index": k, "spec": spec,
                              "results": results})

    elapsed = time.time() - t0

    summary = {}
    for name, agg in per_validator.items():
        summary[name] = {
            "spaces_passed": agg["passed"],
            "spaces_failed": agg["failed"],
            "total_checks": agg["checks"],
            "passed": agg["failed"] == 0,
            "sample_failures": agg["failures"][:5],
        }

    report = {
        "meta": {
            "paper": "The Irreducible Boundary of a Bounded Resolvable Space",
            "suite": "concrete-space numerics, all 7 theorem-groups, "
                     "randomized sweep",
            "seed": seed,
            "n_spaces": n_spaces,
            "total_checks": total_checks,
            "elapsed_seconds": round(elapsed, 4),
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "overall_passed": all_passed,
        "summary_by_theorem": summary,
        "spaces": space_reports,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # console summary
    print(f"Bounded Resolvable Space -- validation suite")
    print(f"  spaces swept : {n_spaces}")
    print(f"  total checks : {total_checks}")
    print(f"  elapsed      : {elapsed:.3f}s")
    print(f"  seed         : {seed}")
    print("-" * 60)
    for name, s in summary.items():
        flag = "PASS" if s["passed"] else "FAIL"
        print(f"  [{flag}] {name:<26} "
              f"spaces {s['spaces_passed']}/{s['spaces_passed']+s['spaces_failed']}"
              f"  checks={s['total_checks']}")
    print("-" * 60)
    print(f"  OVERALL: {'PASS' if all_passed else 'FAIL'}")
    print(f"  report written to {out_path}")
    return 0 if all_passed else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260619)
    ap.add_argument("--spaces", type=int, default=200)
    ap.add_argument("--out", type=str, default="validation_results.json")
    args = ap.parse_args()
    return run(args.seed, args.spaces, args.out)


if __name__ == "__main__":
    sys.exit(main())
