#!/usr/bin/env python3
"""Emit engine/design.csv: 6 cells x 2 models; quota = stimulus rows per cell."""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
stim = os.path.join(HERE, "..", "stimuli", "stimuli.csv")
with open(stim, newline="") as f:
    quota = sum(1 for _ in csv.DictReader(f))
rows = []
for clause in ("none", "law", "arbitrary"):
    for det in ("low", "high"):
        for model in ("llama31_8b_instruct", "llama31_8b_base"):
            rows.append(dict(cell_id=f"{clause}-{det}", clause_level=clause,
                             detection=det, temptation="moderate",
                             model=model, quota=quota))
out = os.path.join(HERE, "design.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(f"wrote {len(rows)} design rows (quota {quota}/cell/model) -> {out}")
