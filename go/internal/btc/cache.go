package btc

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"strings"
	"time"

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

// Store is a short-lived Redis cache for derived conversions, keyed by
// request signature. Nothing is persisted: entries expire after cacheTTL.
// A nil client just disables caching.
type Store struct {
	rdb *redis.Client
}

func NewStore(rdb *redis.Client) *Store {
	return &Store{rdb: rdb}
}

func redisKey(signature string) string { return "btc:conv:v1:" + signature }

// Get returns a cached record, or (nil, false) on a miss or if Redis is
// unavailable — callers should then derive+look up fresh and call Save.
func (s *Store) Get(ctx context.Context, signature string) (*Record, bool) {
	if s == nil || s.rdb == nil {
		return nil, false
	}
	payload, err := s.rdb.Get(ctx, redisKey(signature)).Result()
	if err != nil {
		return nil, false
	}
	var rec Record
	if json.Unmarshal([]byte(payload), &rec) != nil {
		return nil, false
	}
	return &rec, true
}

// Save caches the record in Redis for cacheTTL.
func (s *Store) Save(ctx context.Context, rec *Record) {
	if s == nil || s.rdb == nil {
		return
	}
	payload, err := json.Marshal(rec)
	if err != nil {
		return
	}
	_ = s.rdb.Set(ctx, redisKey(rec.RequestSignature), payload, cacheTTL).Err()
}
