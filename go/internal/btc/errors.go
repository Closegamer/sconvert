package btc

import "errors"

// Sentinel errors that map to a specific user-facing message (see
// app/lang/*.py's btc.error.* keys, ported to i18n in the web layer). Any
// other error from Derive is treated the same way the original Python did
// for a malformed field: silently ignored, no message shown, wait for
// valid input.
var (
	ErrPrivateKeyRange  = errors.New("btc: private key out of secp256k1 range")
	ErrPubKeyNotOnCurve = errors.New("btc: public key not on secp256k1 curve")
	ErrInvalidSeedPhrase = errors.New("btc: seed phrase must be 12 or 24 words")
	ErrInvalidInput     = errors.New("btc: invalid input for field")
	ErrUnsupportedField = errors.New("btc: unsupported entry field")
)
