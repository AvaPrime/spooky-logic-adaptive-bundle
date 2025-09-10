-- Persistent store for experiments/arms/results
CREATE TABLE IF NOT EXISTS experiments (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS experiment_arm (
  id SERIAL PRIMARY KEY,
  experiment_id INT REFERENCES experiments(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  UNIQUE(experiment_id, name)
);
CREATE TABLE IF NOT EXISTS experiment_result (
  id SERIAL PRIMARY KEY,
  arm_id INT REFERENCES experiment_arm(id) ON DELETE CASCADE,
  score DOUBLE PRECISION,
  cost DOUBLE PRECISION,
  latency_ms DOUBLE PRECISION,
  domain TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
