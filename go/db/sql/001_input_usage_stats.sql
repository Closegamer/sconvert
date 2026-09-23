-- Anonymous per-input usage stats (no user identifiers, no IP addresses).
-- One row per (scope, category_key, input_key) — every use increments
-- hit_count in place rather than appending an unbounded event log.

CREATE TABLE IF NOT EXISTS input_usage_stats (
    id BIGSERIAL PRIMARY KEY,
    scope TEXT NOT NULL,         -- 'units' | 'currency' | 'btc'
    category_key TEXT NOT NULL,  -- unit category / 'currency' / btc form section
    input_key TEXT NOT NULL,     -- unit code / currency code / btc field name
    hit_count BIGINT NOT NULL DEFAULT 0,
    first_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (scope, category_key, input_key)
);

CREATE INDEX IF NOT EXISTS idx_input_usage_stats_scope_category
    ON input_usage_stats (scope, category_key);
