package btc

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/redis/go-redis/v9"
)

// EntryPointDBName translates Derive's field names to the DB's
// entry_point_field enum (see db/sql/002_btc_conversion_log.sql) — a few
// entries have a "_uncompressed"/plain split in the UI but a "_c"/"_u"
// split in storage, matching Python's entry_point_map.
func EntryPointDBName(field string) string {
	switch field {
	case "private_wif_uncompressed":
		return "private_wif_u"
	case "public_key":
		return "public_key_c"
	case "public_key_uncompressed":
		return "public_key_u"
	case "ripemd160":
		return "ripemd160_c"
	case "ripemd160_uncompressed":
		return "ripemd160_u"
	case "address":
		return "address_c"
	case "address_uncompressed":
		return "address_u"
	default:
		return field
	}
}

func normalizeSignatureValue(dbField, value string) string {
	trimmed := strings.TrimSpace(value)
	if trimmed == "" {
		return ""
	}
	switch dbField {
	case "private_hex", "public_key_c", "public_key_u", "ripemd160_c", "ripemd160_u":
		return strings.TrimPrefix(strings.ToLower(trimmed), "0x")
	default:
		return trimmed
	}
}

// BuildRequestSignature is a deterministic cache key for one (entry field,
// entry value) pair — same idea as Python's _build_request_signature, but
// scoped to this rewrite's own btc_conversion_log table (a separate
// Postgres instance from the Python site), so it doesn't need to match the
// original's exact byte-for-byte JSON encoding, only be internally
// consistent.
func BuildRequestSignature(dbField, entryValue string) string {
	normalized := normalizeSignatureValue(dbField, entryValue)
	body, _ := json.Marshal(struct {
		EntryPointField string `json:"entry_point_field"`
		EntryValue      string `json:"entry_value"`
		CacheVersion    int    `json:"cache_version"`
	}{dbField, normalized, 1})
	sum := sha256.Sum256(body)
	return hex.EncodeToString(sum[:])
}

// Record is one derived conversion, cached/persisted keyed by
// RequestSignature. In/Out field names match the Postgres columns.
type Record struct {
	RequestSignature string `json:"request_signature"`
	EntryPointField  string `json:"entry_point_field"`

	InPrivateDec    string `json:"in_private_dec"`
	InPrivateHex    string `json:"in_private_hex"`
	InPrivateWIF    string `json:"in_private_wif"`
	InPrivateWIFU   string `json:"in_private_wif_u"`
	InSeedPhrase    string `json:"in_seed_phrase"`
	InPublicKeyC    string `json:"in_public_key_c"`
	InPublicKeyU    string `json:"in_public_key_u"`
	InRipemd160C    string `json:"in_ripemd160_c"`
	InRipemd160U    string `json:"in_ripemd160_u"`
	InAddressC      string `json:"in_address_c"`
	InAddressU      string `json:"in_address_u"`
	InAddressP2SH   string `json:"in_address_p2sh"`
	InAddressP2WPKH string `json:"in_address_p2wpkh"`

	OutPrivateDec           string `json:"out_private_dec"`
	OutPrivateHex           string `json:"out_private_hex"`
	OutPrivateHexNormalized string `json:"out_private_hex_normalized"`
	OutPrivateWIF           string `json:"out_private_wif"`
	OutPrivateWIFU          string `json:"out_private_wif_u"`
	OutPublicKeyC           string `json:"out_public_key_c"`
	OutPublicKeyU           string `json:"out_public_key_u"`
	OutRipemd160C           string `json:"out_ripemd160_c"`
	OutRipemd160U           string `json:"out_ripemd160_u"`
	OutAddressC             string `json:"out_address_c"`
	OutAddressU             string `json:"out_address_u"`
	OutAddressP2SH          string `json:"out_address_p2sh"`
	OutAddressP2WPKH        string `json:"out_address_p2wpkh"`
	OutAddressInfo          string `json:"out_address_info"`
	OutBalanceText          string `json:"out_balance_text"`
	OutAddressSummaryText   string `json:"out_address_summary_text"`
	OutUtxosText            string `json:"out_utxos_text"`
	OutTxsText              string `json:"out_txs_text"`

	// Curve visualization inputs + validation captions — not derivable from
	// the other fields alone, so they must round-trip through the cache too
	// (a cache hit that omits them silently breaks the curve SVG and the
	// address validation captions on the client).
	OutPubkeyXHex           string `json:"out_pubkey_x_hex"`
	OutPubkeyYHex           string `json:"out_pubkey_y_hex"`
	OutPubkeyOnCurve        bool   `json:"out_pubkey_on_curve"`
	OutAddressCStatus       string `json:"out_address_c_status"`
	OutAddressUStatus       string `json:"out_address_u_status"`
	OutAddressP2SHStatus    string `json:"out_address_p2sh_status"`
	OutAddressP2WPKHStatus  string `json:"out_address_p2wpkh_status"`
}

const cacheTTL = 120 * time.Second

// Store is the two-tier (Redis -> Postgres) cache for derived conversions,
// keyed by request signature. Both backends degrade gracefully: a nil pool
// or nil client just skips that tier rather than erroring, matching
// stats.Store's pattern.
type Store struct {
	pool *pgxpool.Pool
	rdb  *redis.Client
}

func NewStore(pool *pgxpool.Pool, rdb *redis.Client) *Store {
	return &Store{pool: pool, rdb: rdb}
}

func redisKey(signature string) string { return "btc:conv:v1:" + signature }

// Get checks Redis, then Postgres, backfilling Redis on a Postgres hit.
// Returns (nil, false) on a genuine miss or if both backends are
// unavailable — callers should then derive+look up fresh and call Save.
func (s *Store) Get(ctx context.Context, signature string) (*Record, bool) {
	if s == nil {
		return nil, false
	}
	if s.rdb != nil {
		if payload, err := s.rdb.Get(ctx, redisKey(signature)).Result(); err == nil {
			var rec Record
			if json.Unmarshal([]byte(payload), &rec) == nil {
				return &rec, true
			}
		}
	}
	if s.pool == nil {
		return nil, false
	}
	rec, ok := s.loadFromPostgres(ctx, signature)
	if ok {
		s.setRedis(ctx, &rec)
	}
	return &rec, ok
}

func (s *Store) loadFromPostgres(ctx context.Context, signature string) (Record, bool) {
	ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
	defer cancel()
	var r Record
	err := s.pool.QueryRow(ctx, `
		SELECT
			request_signature, entry_point_field,
			COALESCE(in_private_dec, ''), COALESCE(in_private_hex, ''), COALESCE(in_private_wif, ''),
			COALESCE(in_private_wif_u, ''), COALESCE(in_seed_phrase, ''), COALESCE(in_public_key_c, ''),
			COALESCE(in_public_key_u, ''), COALESCE(in_ripemd160_c, ''), COALESCE(in_ripemd160_u, ''),
			COALESCE(in_address_c, ''), COALESCE(in_address_u, ''), COALESCE(in_address_p2sh, ''),
			COALESCE(in_address_p2wpkh, ''),
			COALESCE(out_private_dec, ''), COALESCE(out_private_hex, ''), COALESCE(out_private_hex_normalized, ''),
			COALESCE(out_private_wif, ''), COALESCE(out_private_wif_u, ''), COALESCE(out_public_key_c, ''),
			COALESCE(out_public_key_u, ''), COALESCE(out_ripemd160_c, ''), COALESCE(out_ripemd160_u, ''),
			COALESCE(out_address_c, ''), COALESCE(out_address_u, ''), COALESCE(out_address_p2sh, ''),
			COALESCE(out_address_p2wpkh, ''), COALESCE(out_address_info, ''), COALESCE(out_balance_text, ''),
			COALESCE(out_address_summary_text, ''), COALESCE(out_utxos_text, ''), COALESCE(out_txs_text, ''),
			COALESCE(out_pubkey_x_hex, ''), COALESCE(out_pubkey_y_hex, ''), COALESCE(out_pubkey_on_curve, false),
			COALESCE(out_address_c_status, ''), COALESCE(out_address_u_status, ''),
			COALESCE(out_address_p2sh_status, ''), COALESCE(out_address_p2wpkh_status, '')
		FROM btc_conversion_log
		WHERE request_signature = $1
	`, signature).Scan(
		&r.RequestSignature, &r.EntryPointField,
		&r.InPrivateDec, &r.InPrivateHex, &r.InPrivateWIF, &r.InPrivateWIFU, &r.InSeedPhrase,
		&r.InPublicKeyC, &r.InPublicKeyU, &r.InRipemd160C, &r.InRipemd160U,
		&r.InAddressC, &r.InAddressU, &r.InAddressP2SH, &r.InAddressP2WPKH,
		&r.OutPrivateDec, &r.OutPrivateHex, &r.OutPrivateHexNormalized, &r.OutPrivateWIF, &r.OutPrivateWIFU,
		&r.OutPublicKeyC, &r.OutPublicKeyU, &r.OutRipemd160C, &r.OutRipemd160U,
		&r.OutAddressC, &r.OutAddressU, &r.OutAddressP2SH, &r.OutAddressP2WPKH, &r.OutAddressInfo,
		&r.OutBalanceText, &r.OutAddressSummaryText, &r.OutUtxosText, &r.OutTxsText,
		&r.OutPubkeyXHex, &r.OutPubkeyYHex, &r.OutPubkeyOnCurve,
		&r.OutAddressCStatus, &r.OutAddressUStatus, &r.OutAddressP2SHStatus, &r.OutAddressP2WPKHStatus,
	)
	if err != nil {
		return Record{}, false
	}
	return r, true
}

func (s *Store) setRedis(ctx context.Context, rec *Record) {
	if s.rdb == nil {
		return
	}
	payload, err := json.Marshal(rec)
	if err != nil {
		return
	}
	_ = s.rdb.Set(ctx, redisKey(rec.RequestSignature), payload, cacheTTL).Err()
}

// Save upserts the record into Postgres (best-effort) and refreshes Redis.
func (s *Store) Save(ctx context.Context, rec *Record) {
	if s == nil {
		return
	}
	if s.pool != nil {
		ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
		defer cancel()
		_, _ = s.pool.Exec(ctx, `
			INSERT INTO btc_conversion_log (
				request_signature, entry_point_field,
				in_private_dec, in_private_hex, in_private_wif, in_private_wif_u, in_seed_phrase,
				in_public_key_c, in_public_key_u, in_ripemd160_c, in_ripemd160_u,
				in_address_c, in_address_u, in_address_p2sh, in_address_p2wpkh,
				out_private_dec, out_private_hex, out_private_hex_normalized, out_private_wif, out_private_wif_u,
				out_public_key_c, out_public_key_u, out_ripemd160_c, out_ripemd160_u,
				out_address_c, out_address_u, out_address_p2sh, out_address_p2wpkh, out_address_info,
				out_balance_text, out_address_summary_text, out_utxos_text, out_txs_text,
				out_pubkey_x_hex, out_pubkey_y_hex, out_pubkey_on_curve,
				out_address_c_status, out_address_u_status, out_address_p2sh_status, out_address_p2wpkh_status
			) VALUES (
				$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
				$16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33,
				$34, $35, $36, $37, $38, $39, $40
			)
			ON CONFLICT (request_signature) DO UPDATE SET updated_at = NOW()
		`,
			rec.RequestSignature, rec.EntryPointField,
			rec.InPrivateDec, rec.InPrivateHex, rec.InPrivateWIF, rec.InPrivateWIFU, rec.InSeedPhrase,
			rec.InPublicKeyC, rec.InPublicKeyU, rec.InRipemd160C, rec.InRipemd160U,
			rec.InAddressC, rec.InAddressU, rec.InAddressP2SH, rec.InAddressP2WPKH,
			rec.OutPrivateDec, rec.OutPrivateHex, rec.OutPrivateHexNormalized, rec.OutPrivateWIF, rec.OutPrivateWIFU,
			rec.OutPublicKeyC, rec.OutPublicKeyU, rec.OutRipemd160C, rec.OutRipemd160U,
			rec.OutAddressC, rec.OutAddressU, rec.OutAddressP2SH, rec.OutAddressP2WPKH, rec.OutAddressInfo,
			rec.OutBalanceText, rec.OutAddressSummaryText, rec.OutUtxosText, rec.OutTxsText,
			rec.OutPubkeyXHex, rec.OutPubkeyYHex, rec.OutPubkeyOnCurve,
			rec.OutAddressCStatus, rec.OutAddressUStatus, rec.OutAddressP2SHStatus, rec.OutAddressP2WPKHStatus,
		)
	}
	s.setRedis(ctx, rec)
}
