#!/usr/bin/env python3
"""DASH. One screen, nothing else.

Panels: (1) instruct cell means, (2) base cell means, (3) instruct-minus-base
delta per stimulus (the recovered post-training tilt, estimand 5), all as
clause x detection interaction plots with cluster-bootstrap 95% CIs.
Cluster = vignette when >1 vignette is present, else paraphrase.
Renders from a partial runs table mid-run.
"""
import argparse
import random
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

CLAUSES = ["none", "law", "arbitrary"]
DETS = ["low", "high"]
COLORS = {"low": "#4a86c8", "high": "#A63228"}


def boot_ci(vals, clusters, B=2000, seed=7):
    keys = sorted(set(clusters))
    if len(vals) == 0:
        return (float("nan"), float("nan"))
    by = {k: [v for v, c in zip(vals, clusters) if c == k] for k in keys}
    rng = random.Random(seed)
    means = []
    for _ in range(B):
        samp = []
        for _ in keys:
            samp.extend(by[rng.choice(keys)])
        means.append(sum(samp) / len(samp))
    means.sort()
    return means[int(0.025 * B)], means[int(0.975 * B)]


def fetch(con, sql, args=()):
    return list(con.execute(sql, args))


def panel(ax, cells, title):
    """cells: {(clause, det): (mean, lo, hi, n)}"""
    x = range(len(CLAUSES))
    for det in DETS:
        ys, los, his = [], [], []
        for cl in CLAUSES:
            m, lo, hi, _n = cells.get((cl, det), (float("nan"),) * 3 + (0,))
            ys.append(m)
            los.append(m - lo)
            his.append(hi - m)
        ax.errorbar(x, ys, yerr=[los, his], marker="o", capsize=3,
                    label=f"detection {det}", color=COLORS[det])
    ax.set_xticks(list(x), CLAUSES)
    ax.axhline(0, lw=0.6, color="#999")
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("clause")


def summarize(rows):
    out = {}
    for cl in CLAUSES:
        for det in DETS:
            sub = [(v, c) for v, c, cl2, d2 in rows if cl2 == cl and d2 == det
                   and v is not None]
            if not sub:
                continue
            vals = [v for v, _ in sub]
            clus = [c for _, c in sub]
            m = sum(vals) / len(vals)
            lo, hi = boot_ci(vals, clus)
            out[(cl, det)] = (m, lo, hi, len(vals))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="engine/runs.sqlite")
    ap.add_argument("--out", default="dash/dashboard.png")
    ap.add_argument("--instruct", default="llama31_8b_instruct")
    ap.add_argument("--base", default="llama31_8b_base")
    a = ap.parse_args()

    con = sqlite3.connect(a.db)
    nvig = fetch(con, "SELECT COUNT(DISTINCT vignette_id) FROM runs")[0][0]
    cluster_col = "vignette_id" if nvig > 1 else "paraphrase_id"

    def model_rows(model):
        return fetch(con, f"""SELECT logodds_unlawful, {cluster_col},
                              clause_level, detection
                              FROM runs WHERE model=? AND ok=1""", (model,))

    delta_rows = fetch(con, f"""
        SELECT i.logodds_unlawful - b.logodds_unlawful, i.{cluster_col},
               i.clause_level, i.detection
        FROM runs i JOIN runs b
          ON i.stimulus_id = b.stimulus_id AND i.cell_id = b.cell_id
        WHERE i.model=? AND b.model=? AND i.ok=1 AND b.ok=1""",
        (a.instruct, a.base))

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4), sharey=False)
    panel(axes[0], summarize(model_rows(a.instruct)), f"instruct: {a.instruct}")
    panel(axes[1], summarize(model_rows(a.base)), f"base: {a.base}")
    panel(axes[2], summarize(delta_rows),
          "instruct - base  (recovered tilt, estimand 5)")
    axes[0].set_ylabel("log p(unlawful) - log p(lawful)")
    axes[2].set_ylabel("delta log-odds")
    axes[0].legend(fontsize=8)
    n = fetch(con, "SELECT COUNT(*) FROM runs")[0][0]
    fig.suptitle(f"PsychSprint pilot - {n} scored rows - "
                 f"cluster={cluster_col} bootstrap 95% CI", fontsize=10)
    fig.tight_layout()
    fig.savefig(a.out, dpi=160)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
