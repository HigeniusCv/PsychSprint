# PsychSprint

Revealed-preference experiment engine for open-weight LLM pairs (base + instruct).
Pilot: law-clause x detection-probability factorial on Llama-3.1-8B.
Source of truth: kickoff doc 2026-08-13 + working paper "Rediscovering the
Optimization Function" (2026-08-13). All nontrivial choices: DECISIONS.md.

    stimuli/build_stimuli.py    vignette JSONs -> stimuli.csv (+QA gates)
    engine/make_design.py       -> design.csv (6 cells x 2 models)
    engine/run.py               expand, score, persist (idempotent SQLite)
    dash/plot.py                one-screen dashboard, partial-table safe
    analysis/simulate.py        STAT fake-data sizing (paraphrase saturation)

Full pilot = one command:

    python3 stimuli/build_stimuli.py && python3 engine/make_design.py
    python3 engine/run.py --scorer llamacpp \
      --endpoints "llama31_8b_instruct=http://127.0.0.1:8081,llama31_8b_base=http://127.0.0.1:8082"
    python3 dash/plot.py --db engine/runs.sqlite --out dash/pilot.png

DV = log p(unlawful) - log p(lawful), read off final-token logits
(greedy/temperature=-1 readout; raw softmax per llama.cpp server docs).
