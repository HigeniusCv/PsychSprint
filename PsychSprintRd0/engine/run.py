#!/usr/bin/env python3
"""Runner. Full pilot = one command from the two CSVs. Idempotent, resumable.

Cache key: UNIQUE(model, stimulus_id, cell_id). Re-running skips scored rows.
Deterministic given inputs (greedy readout; mock is hash-keyed).

Examples
  python3 engine/run.py --scorer mock --engine-version 0.1.0
  python3 engine/run.py --scorer llamacpp \
      --endpoints "llama31_8b_instruct=http://127.0.0.1:8081,llama31_8b_base=http://127.0.0.1:8082" \
      --cells law-high --engine-version 0.1.0
"""
import argparse
import csv
import hashlib
import json
import math
import os
import sqlite3
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from prompts import render            # noqa: E402
from scorers import MockScorer, LlamaCppScorer  # noqa: E402


def load_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def build_item(d, s, manip):
    if d["clause_level"] == "arbitrary":
        clause = s["arbitrary_clause"]
    else:
        clause = manip["clauses"][d["clause_level"]]
    system = manip["system_preamble"] + " " + clause
    det = s["detection_low"] if d["detection"] == "low" else s["detection_high"]
    user = s["prompt_text"].replace("{DETECTION}", det) + manip["menu_scaffold"].format(
        a=s["option_A_text"], b=s["option_B_text"])
    return system, user


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default="engine/design.csv")
    ap.add_argument("--stimuli", default="stimuli/stimuli.csv")
    ap.add_argument("--manipulanda", default="stimuli/manipulanda.json")
    ap.add_argument("--db", default="engine/runs.sqlite")
    ap.add_argument("--scorer", choices=["mock", "llamacpp"], default="mock")
    ap.add_argument("--endpoints", default="", help="model=url,model=url")
    ap.add_argument("--cells", default="", help="comma filter, e.g. law-high")
    ap.add_argument("--models", default="", help="comma filter")
    ap.add_argument("--engine-version", default="0.1.0")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    design = load_csv(a.design)
    stims = load_csv(a.stimuli)
    manip = json.load(open(a.manipulanda))
    if a.cells:
        keep = set(a.cells.split(","))
        design = [d for d in design if d["cell_id"] in keep]
    if a.models:
        keep = set(a.models.split(","))
        design = [d for d in design if d["model"] in keep]

    if a.scorer == "mock":
        scorer = MockScorer()
    else:
        if not a.endpoints:
            sys.exit("--endpoints required for llamacpp scorer")
        eps = dict(kv.split("=", 1) for kv in a.endpoints.split(",") if kv)
        missing = {d["model"] for d in design} - set(eps)
        if missing:
            sys.exit(f"no endpoint for models: {sorted(missing)}")
        scorer = LlamaCppScorer(eps)
        scorer.preflight()

    con = sqlite3.connect(a.db)
    con.executescript(open(os.path.join(HERE, "schema.sql")).read())
    seen = {tuple(r) for r in con.execute(
        "SELECT model, stimulus_id, cell_id FROM runs")}

    todo = [(d, s) for d in design for s in stims
            if (d["model"], s["stimulus_id"], d["cell_id"]) not in seen]
    if a.limit:
        todo = todo[: a.limit]
    print(f"{len(todo)} items to score ({len(seen)} already cached in {a.db})")

    t0 = time.time()
    n = 0
    for d, s in todo:
        system, user = build_item(d, s, manip)
        prompt = render(system, user)
        pA, pB = scorer.score(d["model"], prompt, {"d": d, "s": s})
        ok = 1 if (pA > 0 and pB > 0) else 0
        logpA = math.log(pA) if pA > 0 else None
        logpB = math.log(pB) if pB > 0 else None
        if ok:
            lu = (logpA - logpB) if s["unlawful_option"] == "A" else (logpB - logpA)
        else:
            lu = None
        con.execute(
            """INSERT OR IGNORE INTO runs
               (cell_id, stimulus_id, model, clause_level, detection,
                vignette_id, paraphrase_id, position_order, unlawful_option,
                logp_A, logp_B, logodds_unlawful, coverage, ok,
                prompt_sha1, engine_version)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (d["cell_id"], s["stimulus_id"], d["model"], d["clause_level"],
             d["detection"], s["vignette_id"], s["paraphrase_id"],
             s["position_order"], s["unlawful_option"], logpA, logpB, lu,
             pA + pB, ok, hashlib.sha1(prompt.encode()).hexdigest(),
             a.engine_version))
        n += 1
        if n % 25 == 0:
            con.commit()
            print(f"  {n}/{len(todo)}  {time.time() - t0:.1f}s")
    con.commit()
    dt = time.time() - t0
    print(f"done: {n} scored in {dt:.1f}s "
          f"({(dt / n * 1000):.0f} ms/item)" if n else "nothing to do")
    for m, cnt, cov, bad in con.execute(
            "SELECT model, COUNT(*), AVG(coverage), SUM(1-ok) FROM runs GROUP BY model"):
        print(f"  {m}: {cnt} rows, mean coverage {cov:.3f}, {bad} degenerate")


if __name__ == "__main__":
    main()
