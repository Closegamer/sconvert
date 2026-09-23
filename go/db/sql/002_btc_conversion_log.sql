-- BTC conversion persistence schema (ported from db/sql/001_create_btc_conversion_log.sql).
-- Lookup flow: 1) Redis by request_signature  2) Postgres by request_signature
-- 3) not found -> derive + look up on blockstream.info + INSERT
--
-- Trimmed vs. the original Python schema: dropped out_private_key_position_percent,
-- out_pubkey_curve_error, redis_cache_key, redis_ttl_seconds, cache_version —
-- all were observability-only columns never read back by the app. The Go
-- rewrite computes the curve/key-line visualizations client-side from the
-- hex/dec values below instead of persisting server-rendered SVGs.
-- out_pubkey_on_curve IS kept (see further down) — unlike the others it's an
-- actual response field the client needs on a cache hit, not just telemetry.

CREATE TABLE IF NOT EXISTS btc_conversion_log (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    request_signature TEXT NOT NULL UNIQUE,

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

    -- Curve visualization inputs (not derivable from the hex/dec fields
    -- alone without redoing the secp256k1 parse) and the four address
    -- validation captions — all must be cached too, or a cache hit silently
    -- loses them (found via browser verification: a repeat query returned
    -- an empty curve visualization and blank validation captions).
    out_pubkey_x_hex TEXT,
    out_pubkey_y_hex TEXT,
    out_pubkey_on_curve BOOLEAN,
    out_address_c_status TEXT,
    out_address_u_status TEXT,
    out_address_p2sh_status TEXT,
    out_address_p2wpkh_status TEXT
);

CREATE INDEX IF NOT EXISTS idx_btc_conversion_log_created_at
    ON btc_conversion_log (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_btc_conversion_log_entry_point
    ON btc_conversion_log (entry_point_field);

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
