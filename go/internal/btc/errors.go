package btc

import "errors"

// Sentinel errors that map to a specific user-facing message (the
// btc.error.* i18n keys, resolved in the web layer). Any other error from
// Derive means a malformed field: silently ignored, no message shown, wait
// for valid input.
var (
	ErrPrivateKeyRange  = errors.New("btc: private key out of secp256k1 range")
	ErrPubKeyNotOnCurve = errors.New("btc: public key not on secp256k1 curve")
	ErrInvalidSeedPhrase = errors.New("btc: seed phrase must be 12 or 24 words")
	ErrInvalidInput     = errors.New("btc: invalid input for field")
	ErrUnsupportedField = errors.New("btc: unsupported entry field")
)
