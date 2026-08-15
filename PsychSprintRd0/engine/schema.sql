CREATE TABLE IF NOT EXISTS runs (
  run_id INTEGER PRIMARY KEY AUTOINCREMENT,
  cell_id TEXT NOT NULL,
  stimulus_id TEXT NOT NULL,
  model TEXT NOT NULL,
  clause_level TEXT,
  detection TEXT,
  vignette_id TEXT,
  paraphrase_id TEXT,
  position_order TEXT,
  unlawful_option TEXT,
  logp_A REAL,
  logp_B REAL,
  logodds_unlawful REAL,
  coverage REAL,
  ok INTEGER DEFAULT 1,
  prompt_sha1 TEXT,
  ts TEXT DEFAULT (datetime('now')),
  engine_version TEXT,
  UNIQUE(model, stimulus_id, cell_id)
);
CREATE INDEX IF NOT EXISTS idx_runs_cell ON runs(cell_id, model);
