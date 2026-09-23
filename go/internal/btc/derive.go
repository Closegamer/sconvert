// Package btc ports app/components/btc_keys.py's key/address derivation:
// given any one of 13 possible entry fields (private key in dec/hex/WIF/
// seed-phrase form, a public key, a RIPEMD-160 hash, or an address), fan
// out to every other representation. The EC math (private->public key,
// pubkey parsing/validation) goes through the audited decred secp256k1
// package rather than a hand-rolled implementation.
package btc

import (
	"encoding/hex"
	"fmt"
	"math/big"
	"strings"

	secp256k1 "github.com/decred/dcrd/dcrec/secp256k1/v4"
	"github.com/tyler-smith/go-bip39"
)

// Result holds every derived representation of a key/address. Empty string
// fields mean that representation could not be derived from the given
// entry (e.g. entering a P2SH address alone can't recover a pubkey hash).
type Result struct {
	PrivateDec     string
	PrivateHex     string // compact (no leading zeros) — the primary display value
	PrivateHexNorm string // zero-padded to 64 hex chars
	PrivateWIF     string
	PrivateWIFU    string
	PublicKeyC     string
	PublicKeyU     string
	Ripemd160C     string
	Ripemd160U     string
	AddressC       string
	AddressU       string
	AddressP2SH    string
	AddressP2WPKH  string

	// PubkeyOnCurve/PubkeyXHex/PubkeyYHex feed the curve visualization;
	// populated whenever an uncompressed pubkey exists.
	PubkeyOnCurve bool
	PubkeyXHex    string
	PubkeyYHex    string

	// LookupAddress is the address the caller should use for external
	// balance/tx/utxo lookups (see internal/web/btc.go), matching Python's
	// target_address fallback: the derived compressed address, else the
	// uncompressed one, else (for a P2SH entry, which has no derivable
	// hash160) the raw entered value.
	LookupAddress string
}

// CurveOrderHex is n (the secp256k1 group order) as lowercase hex, used by
// the client to validate private key range without a second round trip.
var CurveOrderHex = fmt.Sprintf("%064x", secp256k1.S256().Params().N)

// Derive computes the full fan-out for one entry field. field must be one
// of: private_dec, private_hex, private_wif, private_wif_uncompressed,
// seed_phrase, public_key, public_key_uncompressed, ripemd160,
// ripemd160_uncompressed, address, address_uncompressed, address_p2sh,
// address_p2wpkh.
func Derive(field, rawValue string) (*Result, error) {
	value := strings.TrimSpace(rawValue)
	if value == "" {
		return nil, ErrInvalidInput
	}

	var privInt *big.Int
	var pubC, pubU []byte
	var h160, h160U []byte
	lookupAddress := ""

	switch field {
	case "private_dec":
		n, ok := new(big.Int).SetString(value, 10)
		if !ok {
			return nil, ErrInvalidInput
		}
		privInt = n
	case "private_hex":
		n, ok := new(big.Int).SetString(strings.TrimPrefix(strings.ToLower(value), "0x"), 16)
		if !ok {
			return nil, ErrInvalidInput
		}
		privInt = n
	case "private_wif", "private_wif_uncompressed":
		n, err := privateKeyFromWIF(value)
		if err != nil {
			return nil, err
		}
		privInt = n
	case "seed_phrase":
		n, err := privateKeyFromSeedPhrase(value)
		if err != nil {
			return nil, err
		}
		privInt = n

	case "public_key":
		b, err := hex.DecodeString(strings.TrimPrefix(strings.ToLower(value), "0x"))
		if err != nil || len(b) != 33 || (b[0] != 0x02 && b[0] != 0x03) {
			return nil, ErrInvalidInput
		}
		pk, err := secp256k1.ParsePubKey(b)
		if err != nil {
			return nil, ErrPubKeyNotOnCurve
		}
		pubC = pk.SerializeCompressed()
		pubU = pk.SerializeUncompressed()
	case "public_key_uncompressed":
		b, err := hex.DecodeString(strings.TrimPrefix(strings.ToLower(value), "0x"))
		if err != nil || len(b) != 65 || b[0] != 0x04 {
			return nil, ErrInvalidInput
		}
		pk, err := secp256k1.ParsePubKey(b)
		if err != nil {
			return nil, ErrPubKeyNotOnCurve
		}
		pubU = pk.SerializeUncompressed()
		pubC = pk.SerializeCompressed()

	case "ripemd160":
		b, err := hex.DecodeString(strings.TrimPrefix(strings.ToLower(value), "0x"))
		if err != nil || len(b) != 20 {
			return nil, ErrInvalidInput
		}
		h160 = b
	case "ripemd160_uncompressed":
		b, err := hex.DecodeString(strings.TrimPrefix(strings.ToLower(value), "0x"))
		if err != nil || len(b) != 20 {
			return nil, ErrInvalidInput
		}
		h160U = b

	case "address":
		h, err := hash160FromP2PKH(value)
		if err != nil {
			h, err = hash160FromP2WPKH(value)
		}
		if err != nil {
			if !isValidP2SHAddress(value) {
				return nil, ErrInvalidInput
			}
			// Valid P2SH address, but a script hash can't be reversed to a
			// pubkey hash — accepted as input, just doesn't fan out.
		} else {
			h160 = h
		}
		lookupAddress = value
	case "address_uncompressed":
		h, err := hash160FromP2PKH(value)
		if err != nil {
			return nil, err
		}
		h160U = h
		lookupAddress = value
	case "address_p2wpkh":
		h, err := hash160FromP2WPKH(value)
		if err != nil {
			return nil, err
		}
		h160 = h
		lookupAddress = value
	case "address_p2sh":
		if !isValidP2SHAddress(value) {
			return nil, ErrInvalidInput
		}
		lookupAddress = value

	default:
		return nil, ErrUnsupportedField
	}

	if privInt != nil {
		n := secp256k1.S256().Params().N
		if privInt.Sign() <= 0 || privInt.Cmp(n) >= 0 {
			return nil, ErrPrivateKeyRange
		}
		priv := secp256k1.PrivKeyFromBytes(leftPad32(privInt))
		pub := priv.PubKey()
		pubC = pub.SerializeCompressed()
		pubU = pub.SerializeUncompressed()
	}
	if pubC != nil {
		h160 = hash160(pubC)
	}
	if pubU != nil {
		h160U = hash160(pubU)
	}

	res := &Result{}

	if privInt != nil {
		res.PrivateDec = privInt.String()
		normHex := fmt.Sprintf("%064x", privInt)
		res.PrivateHexNorm = normHex
		res.PrivateHex = strings.TrimLeft(normHex, "0")
		if res.PrivateHex == "" {
			res.PrivateHex = "0"
		}
		res.PrivateWIF = privateKeyToWIF(privInt, true)
		res.PrivateWIFU = privateKeyToWIF(privInt, false)
	}
	if pubC != nil {
		res.PublicKeyC = hex.EncodeToString(pubC)
	}
	if pubU != nil {
		res.PublicKeyU = hex.EncodeToString(pubU)
		res.PubkeyXHex = hex.EncodeToString(pubU[1:33])
		res.PubkeyYHex = hex.EncodeToString(pubU[33:])
		res.PubkeyOnCurve = true // ParsePubKey above already rejected off-curve points
	}
	if h160 != nil {
		res.Ripemd160C = hex.EncodeToString(h160)
		res.AddressC = hash160ToP2PKH(h160)
		res.AddressP2SH = hash160ToP2SHP2WPKH(h160)
		if addr, err := hash160ToP2WPKH(h160); err == nil {
			res.AddressP2WPKH = addr
		}
	}
	if h160U != nil {
		res.Ripemd160U = hex.EncodeToString(h160U)
		res.AddressU = hash160ToP2PKH(h160U)
	}

	res.LookupAddress = res.AddressC
	if res.LookupAddress == "" {
		res.LookupAddress = res.AddressU
	}
	if res.LookupAddress == "" {
		res.LookupAddress = lookupAddress
	}

	return res, nil
}

// privateKeyFromSeedPhrase derives the private key at the fixed path
// m/44'/0'/0'/0/0 from a 12- or 24-word phrase. Deliberately permissive,
// matching the original Python: no BIP39 wordlist/checksum validation, just
// PBKDF2-HMAC-SHA512 over the NFKD-normalized phrase (go-bip39's NewSeed
// does exactly this and, like the Python, performs no checksum check).
func privateKeyFromSeedPhrase(phrase string) (*big.Int, error) {
	words := strings.Fields(phrase)
	if len(words) != 12 && len(words) != 24 {
		return nil, ErrInvalidSeedPhrase
	}
	seed := bip39.NewSeed(strings.Join(words, " "), "")

	master := hmacSHA512([]byte("Bitcoin seed"), seed)
	key, chainCode := master[:32], master[32:]

	for _, index := range []uint32{44 + hardenedOffset, 0 + hardenedOffset, 0 + hardenedOffset, 0, 0} {
		var err error
		key, chainCode, err = ckdPriv(key, chainCode, index)
		if err != nil {
			return nil, ErrInvalidSeedPhrase
		}
	}
	return new(big.Int).SetBytes(key), nil
}

// ckdPriv implements BIP32's CKD-priv for one derivation step.
func ckdPriv(parentKey, parentChainCode []byte, index uint32) (childKey, childChainCode []byte, err error) {
	var data []byte
	if index >= hardenedOffset {
		data = append([]byte{0x00}, parentKey...)
	} else {
		pub := secp256k1.PrivKeyFromBytes(parentKey).PubKey().SerializeCompressed()
		data = pub
	}
	data = append(data, u32be(index)...)

	i := hmacSHA512(parentChainCode, data)
	il, ir := i[:32], i[32:]

	n := secp256k1.S256().Params().N
	childInt := new(big.Int).Add(new(big.Int).SetBytes(il), new(big.Int).SetBytes(parentKey))
	childInt.Mod(childInt, n)
	if childInt.Sign() == 0 {
		return nil, nil, ErrInvalidInput
	}
	return leftPad32(childInt), ir, nil
}
