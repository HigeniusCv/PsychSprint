"""Scorers. Contract: score(model, prompt, meta) -> (pA, pB) raw probabilities.

LlamaCppScorer readout, verified against llama.cpp tools/server/README.md
(fetched 2026-08-13):
  - /completion with n_predict=1, n_probs=25, temperature=-1.
  - temperature < 0 => greedy pick, and reported token probabilities are a
    plain softmax of the logits, ignoring ALL other sampler settings. This is
    the raw conditional distribution; no sampler neutralization gymnastics.
  - post_sampling_probs left false (default) => fields are logprob/top_logprobs.
    Parser also tolerates prob/top_probs and the older probs-nested layout.
  - DV uses raw pA, pB: log pA - log pB is invariant to renormalizing over
    {A, B}, so no renormalization is performed. coverage = pA + pB is logged
    per row as the format-leakage QA statistic.
"""
import json
import math
import sys
import urllib.request

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import mockgen


def _sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


class MockScorer:
    name = "mock"

    def score(self, model, prompt, meta):
        d, s = meta["d"], meta["s"]
        lo = mockgen.true_logodds(
            model, s["vignette_id"], s["paraphrase_id"],
            d["clause_level"], d["detection"], s["unlawful_option"])
        cov = mockgen.PARAMS["coverage"]
        p_unl = cov * _sigmoid(lo)
        p_law = cov * (1.0 - _sigmoid(lo))
        return (p_unl, p_law) if s["unlawful_option"] == "A" else (p_law, p_unl)


class LlamaCppScorer:
    name = "llamacpp"

    def __init__(self, endpoints, timeout=180):
        self.endpoints = {k: v.rstrip("/") for k, v in endpoints.items()}
        self.timeout = timeout

    def _post(self, url, payload):
        req = urllib.request.Request(
            url, json.dumps(payload).encode(),
            {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read())

    def preflight(self):
        """Health check + confirm header special tokens parse to single ids."""
        for model, base in self.endpoints.items():
            try:
                with urllib.request.urlopen(base + "/health", timeout=10) as r:
                    ok = r.status == 200
            except Exception as e:
                sys.exit(f"preflight FAIL {model} {base}/health: {e}")
            tok = self._post(base + "/tokenize", {
                "content": "<|start_header_id|>", "parse_special": True})
            n = len(tok.get("tokens", []))
            note = "ok" if n == 1 else f"WARN parsed to {n} tokens, template may be mangled"
            print(f"preflight {model}: health={'ok' if ok else '??'} special-token {note}")

    @staticmethod
    def _first_position_candidates(data):
        cps = data.get("completion_probabilities") or []
        if not cps:
            raise ValueError("no completion_probabilities; check n_predict/n_probs")
        node = cps[0]
        if isinstance(node.get("probs"), list) and node["probs"]:
            node = node["probs"][0]
        cands = node.get("top_logprobs") or node.get("top_probs") or []
        pool = {}

        def add(c):
            tok = c.get("token", c.get("tok_str"))
            if tok is None:
                return
            if "prob" in c:
                p = float(c["prob"])
            elif "logprob" in c:
                p = math.exp(float(c["logprob"]))
            else:
                return
            key = c.get("id", tok)
            pool[key] = (tok, p)

        for c in cands:
            add(c)
        add(node)  # the position's own token, deduped by id/string
        return list(pool.values())

    def score(self, model, prompt, meta):
        base = self.endpoints[model]
        payload = {
            "prompt": prompt,
            "n_predict": 1,
            "n_probs": 25,
            "temperature": -1,
            "cache_prompt": True,
        }
        data = self._post(base + "/completion", payload)
        cands = self._first_position_candidates(data)
        pA = sum(p for t, p in cands if t.strip() == "A")
        pB = sum(p for t, p in cands if t.strip() == "B")
        return pA, pB
