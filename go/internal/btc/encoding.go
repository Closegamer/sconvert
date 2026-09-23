package btc

import (
	"crypto/hmac"
	"crypto/sha256"
	"crypto/sha512"
	"encoding/binary"
	"math/big"
	"strings"

	"github.com/btcsuite/btcd/btcutil/base58"
	"github.com/btcsuite/btcd/btcutil/bech32"
	"golang.org/x/crypto/ripemd160"
)

// hash160 is SHA-256 followed by RIPEMD-160 — the standard Bitcoin pubkey
// hash used by every address format below.
func hash160(data []byte) []byte {
	sha := sha256.Sum256(data)
	r := ripemd160.New()
	r.Write(sha[:])
	return r.Sum(nil)
}

func leftPad32(n *big.Int) []byte {
	b := n.Bytes()
	if len(b) >= 32 {
		return b[len(b)-32:]
	}
	out := make([]byte, 32)
	copy(out[32-len(b):], b)
	return out
}

// --- WIF (Wallet Import Format) ---

func privateKeyToWIF(priv *big.Int, compressed bool) string {
	payload := leftPad32(priv)
	if compressed {
		payload = append(payload, 0x01)
	}
	return base58.CheckEncode(payload, 0x80)
}

func privateKeyFromWIF(wif string) (*big.Int, error) {
	payload, version, err := base58.CheckDecode(strings.TrimSpace(wif))
	if err != nil || version != 0x80 {
		return nil, ErrInvalidInput
	}
	if len(payload) != 32 && len(payload) != 33 {
		return nil, ErrInvalidInput
	}
	if len(payload) == 33 && payload[32] != 0x01 {
		return nil, ErrInvalidInput
	}
	return new(big.Int).SetBytes(payload[:32]), nil
}

// --- P2PKH (base58check, version 0x00) ---

func hash160ToP2PKH(h160 []byte) string {
	return base58.CheckEncode(h160, 0x00)
}

func hash160FromP2PKH(address string) ([]byte, error) {
	payload, version, err := base58.CheckDecode(strings.TrimSpace(address))
	if err != nil || version != 0x00 || len(payload) != 20 {
		return nil, ErrInvalidInput
	}
	return payload, nil
}

// --- P2SH-wrapped P2WPKH (nested SegWit, base58check version 0x05) ---

func hash160ToP2SHP2WPKH(h160 []byte) string {
	redeemScript := append([]byte{0x00, 0x14}, h160...)
	return base58.CheckEncode(hash160(redeemScript), 0x05)
}

func isValidP2SHAddress(address string) bool {
	payload, version, err := base58.CheckDecode(strings.TrimSpace(address))
	if err != nil || len(payload) != 20 {
		return false
	}
	return version == 0x05 || version == 0xC4
}

// --- P2WPKH (bech32, BIP173, mainnet HRP "bc") ---

func hash160ToP2WPKH(h160 []byte) (string, error) {
	converted, err := bech32.ConvertBits(h160, 8, 5, true)
	if err != nil {
		return "", err
	}
	data := append([]byte{0}, converted...)
	return bech32.Encode("bc", data)
}

func hash160FromP2WPKH(address string) ([]byte, error) {
	hrp, data, err := bech32.Decode(strings.ToLower(strings.TrimSpace(address)))
	if err != nil || hrp != "bc" || len(data) == 0 || data[0] != 0 {
		return nil, ErrInvalidInput
	}
	decoded, err := bech32.ConvertBits(data[1:], 5, 8, false)
	if err != nil || len(decoded) != 20 {
		return nil, ErrInvalidInput
	}
	return decoded, nil
}

// IsValidP2PKHAddress, IsValidP2WPKHAddress, and IsValidP2SHAddress
// checksum-validate an address for the read-only "validation status"
// caption — distinct from DescribeAddress below, which only sniffs the
// prefix/version byte for a human-readable type/network description and
// deliberately does not validate a bech32 checksum (matching Python's
// _describe_address_type_network, which has the same split).
func IsValidP2PKHAddress(address string) bool {
	_, err := hash160FromP2PKH(address)
	return err == nil
}

func IsValidP2WPKHAddress(address string) bool {
	_, err := hash160FromP2WPKH(address)
	return err == nil
}

func IsValidP2SHAddress(address string) bool { return isValidP2SHAddress(address) }

// --- Address type/network sniffing (for the read-only "address info" field) ---

type AddressInfo struct {
	Type    string // "P2PKH", "P2SH", "Bech32 (P2WPKH)"
	Network string // "mainnet", "testnet"
	Unknown bool
}

// DescribeAddress mirrors Python's _describe_address_type_network: sniff the
// bech32 HRP or base58check version byte to report address type/network,
// without needing to know which field the address came from.
func DescribeAddress(address string) AddressInfo {
	candidate := strings.TrimSpace(address)
	if candidate == "" {
		return AddressInfo{Unknown: true}
	}
	lower := strings.ToLower(candidate)
	if strings.HasPrefix(lower, "bc1") {
		return AddressInfo{Type: "Bech32 (P2WPKH)", Network: "mainnet"}
	}
	if strings.HasPrefix(lower, "tb1") {
		return AddressInfo{Type: "Bech32 (P2WPKH)", Network: "testnet"}
	}
	payload, version, err := base58.CheckDecode(candidate)
	if err != nil || len(payload) < 1 {
		return AddressInfo{Unknown: true}
	}
	switch version {
	case 0x00:
		return AddressInfo{Type: "P2PKH", Network: "mainnet"}
	case 0x05:
		return AddressInfo{Type: "P2SH", Network: "mainnet"}
	case 0x6F:
		return AddressInfo{Type: "P2PKH", Network: "testnet"}
	case 0xC4:
		return AddressInfo{Type: "P2SH", Network: "testnet"}
	default:
		return AddressInfo{Unknown: true}
	}
}

// --- BIP32 (fixed path m/44'/0'/0'/0/0, hardened-index math only) ---
//
// The EC point multiplication needed for non-hardened child derivation
// (steps 0/0 at the end of the path) goes through the audited secp256k1
// package (see privkeyFromBytesForCKD in derive.go); everything here is
// just the deterministic HMAC-SHA512 bookkeeping BIP32 specifies, which is
// public and has no secret math of its own.

const hardenedOffset = 0x80000000

func hmacSHA512(key, data []byte) []byte {
	h := hmac.New(sha512.New, key)
	h.Write(data)
	return h.Sum(nil)
}

func u32be(v uint32) []byte {
	b := make([]byte, 4)
	binary.BigEndian.PutUint32(b, v)
	return b
}
