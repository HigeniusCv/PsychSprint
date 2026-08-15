# DECISIONS.md — append-only. decision · options · chosen · why · timestamp
Sources of truth: (1) kickoff doc 2026-08-13, (2) working paper PDF "Rediscovering the Optimization Function" 2026-08-13. Conflicts resolve in that order and get logged here.

**D-000** · 2026-08-13 · Kickoff doc adopted as source of truth #1; working paper #2. Sign convention fixed: DV = log p(unlawful) − log p(lawful); compliance lift = DV(none) − DV(law), H1 predicts > 0.

**D-001** · 2026-08-13 · §6 consumed: MBPro M4 Max / 64GB / Tahoe 26.5.2; llama.cpp; no hosted fallback keys; repo github.com/HigeniusCv/PsychSprint; $10 API cap moot (pilot fully local); PARADIGM proposals pre-approved for this session. Zero-interruption reading of the batch rule adopted: residual unknowns resolved by default + logged here for async veto, per COS one-interruption cap.

**D-002** · 2026-08-13 · Container/Mac split. Options: (a) attempt in-sandbox inference, (b) build+validate here on a mock scorer, serve on the Mac. Chose (b): sandbox has no GPU and no huggingface egress. Everything except model serving is built and dry-run validated in-container; swap to real inference = `--scorer llamacpp`.

**D-003** · 2026-08-13 · Base-model inputs = byte-identical templated strings as instruct. The log-odds identity is per-sequence in x; input identity is non-negotiable, so the base model sees the chat-template special tokens as raw context. Caveat logged: public Llama-3.1-8B base is NOT Meta's post-training reference policy (that was the SFT checkpoint), so the recovered Δ log-odds = total post-training tilt (SFT + preference-tuning composite), one member of the Ng–Russell equivalence class. Wording for CIMC: "post-training tilt," not "the RLHF reward."

**D-004** · 2026-08-13 · Probability readout: `/completion`, `n_predict=1`, `n_probs=25`, `temperature=-1`. Verified against llama.cpp `tools/server/README.md` (fetched today): with temperature < 0, sampling is greedy and reported top-token probabilities are a plain softmax of the logits, independent of all other sampler settings. p(A), p(B) summed over surface variants ("A", " A") deduped by token id. No renormalization needed: log pA − log pB is renorm-invariant. coverage = pA + pB stored per row as the format-leakage QA stat.

**D-005** · 2026-08-13 · Arbitrary-rule clause implemented as BINDING, not the literal letter-q placebo. Read literally, "labels containing q" never binds on A/B menus and estimand 3 (law vs. obedience-in-general) is unidentified. Implemented: each vignette carries an incidental proper-noun attribute unique to the unlawful option (v1: "Corridor K"); the arbitrary clause bans that attribute. Same extension as the law clause within-vignette, arbitrary intension; attribute varies across vignettes. Residual risk (SEVERITY seed): model infers attribute ≈ illegality proxy → inflates arbitrary compliance → biases H2 (law − arbitrary) toward zero → conservative for the lawfulness-in-particular claim. NS flagged in-session; veto async.

**D-006** · 2026-08-13 · Clause-absent cell carries a length-matched neutral filler sentence (17 words), not true absence. Kills the clause-length / instruction-salience confound on SEVERITY's list. All three system suffixes 17–21 words.

**D-007** · 2026-08-13 · The attribute noun appears in ALL cells' vignette text; only the system suffix varies across clause levels. Vignette body is constant within (vignette, paraphrase, detection, position).

**D-008** · 2026-08-13 · Chat template omits `<|begin_of_text|>`: the server auto-inserts BOS when model metadata `add_bos_token=true` (Llama-3.1: true); literal inclusion would double it. Runner preflights `/tokenize` with `parse_special=true` to confirm header specials map to single ids before any scoring.

**D-009** · 2026-08-13 · Mock scorer embeds a known generative model (engine/mockgen.py: law clause deontic, interaction 0; arbitrary clause priced, interaction −0.5) and doubles as STAT's fake-data engine. One parameterization validates the pipeline against known truth AND drives the sizing sim. Variance components are placeholders pending real dry-run residuals.

**D-010** · 2026-08-13 · Repo built on top of existing origin/main initial commit (README + LICENSE found at HEAD ffd4a50). Pablo pushes from the Mac; no credentials handled in-sandbox by policy.

**D-011** · 2026-08-13 · stimuli.csv ships `approx_tokens` (0.75 words/token heuristic); exact `n_tokens` backfilled from the server `/tokenize` endpoint on first Mac run. Length QA today runs on word counts, ±10% within vignette.

**D-012** · 2026-08-13 · `runs` table is a superset of the kickoff schema: adds denormalized clause_level, detection, vignette_id, paraphrase_id, position_order, unlawful_option, coverage, ok, prompt_sha1 so DASH and analysis need no joins. Kickoff-named columns all present. `quota` in design.csv = stimulus instances per (cell, model) given current stimuli.csv; runner reports actual vs. quota.

**D-013** · 2026-08-13 · PARADIGM's four domains (pre-approved per §6): v1_customs (import mis-declaration; Allingham–Sandmo detection paradigm), v2_privacy (contact-data scraping vs. named data-protection act; consent-norm violation), v3_coldchain (falsifying a temperature-excursion log vs. discard+reorder; Mazar–Ariely record-falsification), v4_licensing (dispatching under a lapsed district permit vs. delay; regulatory compliance under enforcement probability). Spread chosen to vary WHO is harmed and WHAT kind of rule binds (fiscal / privacy / safety-records / permitting). Only v1 is written; v2–v4 + the two-confounds-per-vignette memo are the next PARADIGM cycle.

**D-014** · 2026-08-13 · GGUF sources verified on Hugging Face: instruct = bartowski/Meta-Llama-3.1-8B-Instruct-GGUF (Q4_K_M present), base = QuantFactory/Meta-Llama-3.1-8B-GGUF (quantized from meta-llama/Meta-Llama-3.1-8B). Both ungated mirrors; `llama-server -hf` pulls directly.
