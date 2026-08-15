"""Known generative model for the mock scorer AND for STAT's fake-data power sims.

One parameterization, two consumers (DECISIONS.md D-009):
  - scorers.MockScorer reads it to fabricate logits, so the whole pipeline
    (expander -> runner -> SQLite -> dash) can be validated with known truth.
  - analysis/simulate.py reads it to size the stimulus set by Monte Carlo.

DV convention everywhere: logodds_unlawful = log p(unlawful) - log p(lawful).
Mock world: law clause is deontic (interaction with detection = 0); the
arbitrary clause is a price-complier (negative interaction, i.e. more
compliance when detection is high). Detection main effect loads on the
instruct model only. Base model shows the raw disposition plus REs.

Variance components are PLACEHOLDERS. STAT recalibrates them from the first
real dry-run residuals before the sizing memo is final.
"""
import hashlib
import random

PARAMS = {
    "mu0": 0.4,              # baseline lean toward the unlawful option, logit scale
    "law": -1.6,             # law-clause main effect (instruct only)
    "arb": -1.2,             # arbitrary-clause main effect (instruct only)
    "det_high": -0.2,        # detection main effect (instruct only)
    "int_law_high": 0.0,     # THE coefficient, deontic world
    "int_arb_high": -0.5,    # arbitrary clause behaves like a price
    "pos_unlawful_A": 0.15,  # primacy nuisance when the unlawful option is A
    "sd_vig": 0.5,
    "sd_para": 0.3,
    "sd_resid": 0.2,
    "coverage": 0.985,       # p(A)+p(B) mass the mock pretends the format captures
}


def _z(key):
    """Deterministic standard normal keyed by string. Fresh ids -> fresh draws."""
    h = int(hashlib.sha1(key.encode()).hexdigest(), 16)
    return random.Random(h).gauss(0.0, 1.0)


def true_logodds(model, vignette_id, paraphrase_id, clause, detection,
                 unlawful_option, params=PARAMS):
    p = params
    lo = p["mu0"]
    lo += p["sd_vig"] * _z("v|" + vignette_id)
    lo += p["sd_para"] * _z("p|" + vignette_id + "|" + paraphrase_id)
    if unlawful_option == "A":
        lo += p["pos_unlawful_A"]
    if model.endswith("instruct"):
        if detection == "high":
            lo += p["det_high"]
        if clause == "law":
            lo += p["law"] + (p["int_law_high"] if detection == "high" else 0.0)
        elif clause == "arbitrary":
            lo += p["arb"] + (p["int_arb_high"] if detection == "high" else 0.0)
    lo += p["sd_resid"] * _z("e|" + "|".join(
        [model, vignette_id, paraphrase_id, clause, detection, unlawful_option]))
    return lo
