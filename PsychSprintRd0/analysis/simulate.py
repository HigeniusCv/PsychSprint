#!/usr/bin/env python3
"""STAT: stimulus-set sizing by fake-data simulation. No closed-form lookups.

Question answered: how many paraphrases per vignette before the SE of THE
coefficient (clause x detection interaction) saturates?

Method: Monte Carlo. Each replication draws fresh vignette and paraphrase
random effects from engine/mockgen.PARAMS, generates the full 3x2 cell layout
with both position orders, and computes the interaction as a
difference-in-differences of cell means:
    DiD = [law,high - law,low] - [none,high - none,low]
The reported SD across replications is the true sampling SD of that estimator
under the assumed variance components -- the honest sizing quantity. The
design effect is reported as the ratio of this SD to the naive iid SD that
ignores the vignette/paraphrase clustering.

CAVEAT (blocks the final memo): sd_vig / sd_para / sd_resid are placeholders.
Recalibrate from real dry-run residuals, then re-run this script.
"""
import argparse
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "engine"))
import mockgen  # noqa: E402

CELLS = [(c, d) for c in ("none", "law", "arbitrary") for d in ("low", "high")]


def one_rep(rep, n_vig, n_para, model="llama31_8b_instruct"):
    cell_means = {}
    for clause, det in CELLS:
        vals = []
        for v in range(n_vig):
            for p in range(n_para):
                for unl in ("A", "B"):
                    vals.append(mockgen.true_logodds(
                        model, f"r{rep}v{v}", f"r{rep}v{v}p{p}",
                        clause, det, unl))
        cell_means[(clause, det)] = sum(vals) / len(vals)
    law = cell_means[("law", "high")] - cell_means[("law", "low")]
    none = cell_means[("none", "high")] - cell_means[("none", "low")]
    arb = cell_means[("arbitrary", "high")] - cell_means[("arbitrary", "low")]
    return law - none, arb - none


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-vig", type=int, default=4)
    ap.add_argument("--paras", default="2,4,6,8,12,16")
    ap.add_argument("--reps", type=int, default=400)
    a = ap.parse_args()

    p = mockgen.PARAMS
    print(f"generative params: sd_vig={p['sd_vig']} sd_para={p['sd_para']} "
          f"sd_resid={p['sd_resid']}  true int_law_high={p['int_law_high']} "
          f"int_arb_high={p['int_arb_high']}")
    print(f"{'n_para':>6} {'SD(DiD law)':>12} {'SD(DiD arb)':>12} "
          f"{'naive iid SD':>12} {'design eff':>10}")
    for n_para in [int(x) for x in a.paras.split(",")]:
        laws, arbs = [], []
        for r in range(a.reps):
            l, ar = one_rep(r * 1000 + n_para, a.n_vig, n_para)
            laws.append(l)
            arbs.append(ar)
        sd_law = statistics.stdev(laws)
        sd_arb = statistics.stdev(arbs)
        n_per_cell = a.n_vig * n_para * 2
        sd_tot = (p["sd_vig"] ** 2 + p["sd_para"] ** 2 + p["sd_resid"] ** 2) ** 0.5
        naive = sd_tot * 2.0 / (n_per_cell ** 0.5)
        print(f"{n_para:>6} {sd_law:>12.3f} {sd_arb:>12.3f} "
              f"{naive:>12.3f} {sd_law / naive:>10.2f}")
    print("\nRead-off: precision saturates where SD(DiD) stops falling; past "
          "that point extra paraphrases buy nothing because the vignette "
          "variance component is the binding floor. Note the interaction "
          "differences out vignette and paraphrase intercepts, so the DiD SD "
          "can sit BELOW the naive iid SD (design effect < 1): random "
          "intercepts cancel in within-stimulus contrasts, and only "
          "residual noise binds. Random SLOPES (per-vignette interaction "
          "heterogeneity) would break this; that is the next component to "
          "estimate from real data.")


if __name__ == "__main__":
    main()
