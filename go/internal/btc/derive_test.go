package btc

import "testing"

// These tests deliberately avoid hardcoding external "known-answer" address/
// WIF strings from memory (risk of a silent transcription error passing a
// test that's actually wrong — see the Delisle-scale lesson from
// internal/units). Instead they check: (a) the on-curve validation the
// audited secp256k1 library performs internally, and (b) round-trip
// consistency across every encode/decode pair. The seed-phrase (BIP32) path
// is verified separately by diffing against the live Python reference site
// (see project notes) rather than a memorized fixture.

func TestDeriveFromPrivateDec_RoundTrips(t *testing.T) {
	res, err := Derive("private_dec", "1")
	if err != nil {
		t.Fatalf("Derive(private_dec, 1): %v", err)
	}
	if !res.PubkeyOnCurve {
		t.Fatalf("expected private key 1's pubkey to be on curve")
	}
	if res.PrivateHex != "1" {
		t.Errorf("PrivateHex = %q, want %q", res.PrivateHex, "1")
	}
	if res.PrivateHexNorm != "0000000000000000000000000000000000000000000000000000000000000001" {
		t.Errorf("PrivateHexNorm = %q", res.PrivateHexNorm)
	}

	// WIF round-trip.
	wifRes, err := Derive("private_wif", res.PrivateWIF)
	if err != nil {
		t.Fatalf("Derive(private_wif, %q): %v", res.PrivateWIF, err)
	}
	if wifRes.PrivateDec != res.PrivateDec {
		t.Errorf("WIF round-trip: got private_dec %q, want %q", wifRes.PrivateDec, res.PrivateDec)
	}
	if wifRes.AddressC != res.AddressC {
		t.Errorf("WIF round-trip: got address %q, want %q", wifRes.AddressC, res.AddressC)
	}

	// hex round-trip.
	hexRes, err := Derive("private_hex", res.PrivateHex)
	if err != nil {
		t.Fatalf("Derive(private_hex, %q): %v", res.PrivateHex, err)
	}
	if hexRes.AddressC != res.AddressC {
		t.Errorf("hex round-trip: got address %q, want %q", hexRes.AddressC, res.AddressC)
	}

	// address round-trip: decoding the derived P2PKH address must recover
	// the same hash160 (and therefore the same address back out).
	addrRes, err := Derive("address", res.AddressC)
	if err != nil {
		t.Fatalf("Derive(address, %q): %v", res.AddressC, err)
	}
	if addrRes.Ripemd160C != res.Ripemd160C {
		t.Errorf("address round-trip: got ripemd160 %q, want %q", addrRes.Ripemd160C, res.Ripemd160C)
	}

	// P2WPKH round-trip.
	p2wpkhRes, err := Derive("address_p2wpkh", res.AddressP2WPKH)
	if err != nil {
		t.Fatalf("Derive(address_p2wpkh, %q): %v", res.AddressP2WPKH, err)
	}
	if p2wpkhRes.Ripemd160C != res.Ripemd160C {
		t.Errorf("p2wpkh round-trip: got ripemd160 %q, want %q", p2wpkhRes.Ripemd160C, res.Ripemd160C)
	}

	// pubkey round-trip.
	pubRes, err := Derive("public_key", res.PublicKeyC)
	if err != nil {
		t.Fatalf("Derive(public_key, %q): %v", res.PublicKeyC, err)
	}
	if pubRes.AddressC != res.AddressC {
		t.Errorf("pubkey round-trip: got address %q, want %q", pubRes.AddressC, res.AddressC)
	}
	if pubRes.PublicKeyU != res.PublicKeyU {
		t.Errorf("pubkey round-trip: got uncompressed pubkey %q, want %q", pubRes.PublicKeyU, res.PublicKeyU)
	}
}

func TestDerivePrivateKeyRange(t *testing.T) {
	if _, err := Derive("private_dec", "0"); err != ErrPrivateKeyRange {
		t.Errorf("private key 0: got err %v, want ErrPrivateKeyRange", err)
	}
	if _, err := Derive("private_dec", CurveOrderHex); err == nil {
		t.Errorf("private key == curve order (decimal string would be invalid anyway, sanity only)")
	}
	over, err := Derive("private_hex", CurveOrderHex) // hex of N itself is out of [1, N-1]
	if err != ErrPrivateKeyRange {
		t.Errorf("private key == N: got err %v (res=%v), want ErrPrivateKeyRange", err, over)
	}
}

func TestDeriveSeedPhraseWordCount(t *testing.T) {
	if _, err := Derive("seed_phrase", "one two three"); err != ErrInvalidSeedPhrase {
		t.Errorf("3-word phrase: got err %v, want ErrInvalidSeedPhrase", err)
	}
}

func TestDeriveSeedPhraseDeterministic(t *testing.T) {
	phrase := "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
	a, err := Derive("seed_phrase", phrase)
	if err != nil {
		t.Fatalf("Derive(seed_phrase): %v", err)
	}
	b, err := Derive("seed_phrase", phrase)
	if err != nil {
		t.Fatalf("Derive(seed_phrase) second call: %v", err)
	}
	if a.PrivateDec != b.PrivateDec {
		t.Errorf("seed phrase derivation not deterministic: %q vs %q", a.PrivateDec, b.PrivateDec)
	}
	if a.PrivateDec == "" {
		t.Errorf("expected a non-empty derived private key")
	}

	other, err := Derive("seed_phrase", "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon")
	if err != nil {
		t.Fatalf("Derive(seed_phrase) different phrase: %v", err)
	}
	if other.PrivateDec == a.PrivateDec {
		t.Errorf("different seed phrases produced the same private key")
	}
}

// TestDeriveSeedPhraseKnownVector checks the fixed path m/44'/0'/0'/0/0
// against the widely-published BIP44 test vector for the canonical
// "abandon...about" mnemonic (used across many wallets' own test suites,
// e.g. iancoleman.io/bip39's BIP44 tab) — this specific address is well
// known enough to trust as a known-answer check, unlike an ad-hoc
// hand-recalled fixture.
func TestDeriveSeedPhraseKnownVector(t *testing.T) {
	phrase := "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
	res, err := Derive("seed_phrase", phrase)
	if err != nil {
		t.Fatalf("Derive(seed_phrase): %v", err)
	}
	const wantAddress = "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA"
	if res.AddressC != wantAddress {
		t.Errorf("AddressC = %q, want %q", res.AddressC, wantAddress)
	}
}

func TestDescribeAddress(t *testing.T) {
	res, err := Derive("private_dec", "1")
	if err != nil {
		t.Fatalf("Derive: %v", err)
	}
	info := DescribeAddress(res.AddressC)
	if info.Unknown || info.Type != "P2PKH" || info.Network != "mainnet" {
		t.Errorf("DescribeAddress(%q) = %+v, want P2PKH/mainnet", res.AddressC, info)
	}
	info = DescribeAddress(res.AddressP2WPKH)
	if info.Unknown || info.Type != "Bech32 (P2WPKH)" || info.Network != "mainnet" {
		t.Errorf("DescribeAddress(%q) = %+v, want Bech32 (P2WPKH)/mainnet", res.AddressP2WPKH, info)
	}
	info = DescribeAddress(res.AddressP2SH)
	if info.Unknown || info.Type != "P2SH" || info.Network != "mainnet" {
		t.Errorf("DescribeAddress(%q) = %+v, want P2SH/mainnet", res.AddressP2SH, info)
	}
}
