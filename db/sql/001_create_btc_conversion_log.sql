-- BTC conversion persistence schema for sconvert
-- Lookup flow target:
--   1) Redis by request_signature
--   2) PostgreSQL by request_signature
--   3) If not found -> calculate + INSERT

CREATE TABLE IF NOT EXISTS btc_conversion_log (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Deterministic signature of normalized input payload.
    -- Expected to be SHA-256 hex generated in application code.
    request_signature TEXT NOT NULL UNIQUE,

    -- Which field user used as entry point for conversion.
    entry_point_field TEXT NOT NULL CHECK (
        entry_point_field IN (
            'private_dec',
            'private_hex',
            'private_wif',
            'private_wif_u',
            'seed_phrase',
            'public_key_c',
            'public_key_u',
            'ripemd160_c',
            'ripemd160_u',
            'address_c',
            'address_u',
            'address_p2sh',
            'address_p2wpkh'
        )
    ),

    -- Raw user inputs snapshot (store full form state at request time)
    in_private_dec TEXT,
    in_private_hex TEXT,
    in_private_wif TEXT,
    in_private_wif_u TEXT,
    in_seed_phrase TEXT,
    in_public_key_c TEXT,
    in_public_key_u TEXT,
    in_ripemd160_c TEXT,
    in_ripemd160_u TEXT,
    in_address_c TEXT,
    in_address_u TEXT,
    in_address_p2sh TEXT,
    in_address_p2wpkh TEXT,

    -- Derived / converted values snapshot
    out_private_dec TEXT,
    out_private_hex TEXT,
    out_private_hex_normalized TEXT,
    out_private_wif TEXT,
    out_private_wif_u TEXT,
    out_public_key_c TEXT,
    out_public_key_u TEXT,
    out_ripemd160_c TEXT,
    out_ripemd160_u TEXT,
    out_address_c TEXT,
    out_address_u TEXT,
    out_address_p2sh TEXT,
    out_address_p2wpkh TEXT,
    out_address_info TEXT,
    out_balance_text TEXT,
    out_address_summary_text TEXT,
    out_utxos_text TEXT,
    out_txs_text TEXT,

    -- Visualization-related derived values
    out_private_key_position_percent NUMERIC(20, 12),
    out_pubkey_on_curve BOOLEAN,
    out_pubkey_curve_error TEXT,

    -- Optional cache metadata (written by app for observability)
    redis_cache_key TEXT,
    redis_ttl_seconds INTEGER,
    cache_version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_btc_conversion_log_created_at
    ON btc_conversion_log (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_btc_conversion_log_entry_point
    ON btc_conversion_log (entry_point_field);

CREATE INDEX IF NOT EXISTS idx_btc_conversion_log_in_address_c
    ON btc_conversion_log (in_address_c);

CREATE INDEX IF NOT EXISTS idx_btc_conversion_log_out_address_c
    ON btc_conversion_log (out_address_c);

CREATE INDEX IF NOT EXISTS idx_btc_conversion_log_out_address_u
    ON btc_conversion_log (out_address_u);

CREATE INDEX IF NOT EXISTS idx_btc_conversion_log_out_address_p2wpkh
    ON btc_conversion_log (out_address_p2wpkh);

CREATE INDEX IF NOT EXISTS idx_btc_conversion_log_out_address_p2sh
    ON btc_conversion_log (out_address_p2sh);

-- Keep updated_at fresh on updates
CREATE OR REPLACE FUNCTION set_btc_conversion_log_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_btc_conversion_log_updated_at ON btc_conversion_log;
CREATE TRIGGER trg_btc_conversion_log_updated_at
BEFORE UPDATE ON btc_conversion_log
FOR EACH ROW
EXECUTE FUNCTION set_btc_conversion_log_updated_at();
