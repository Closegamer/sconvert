package web

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"

	"sconvert/internal/btc"
	"sconvert/internal/i18n"
)

type BTCPageData struct {
	PageData
	CurveOrderHex string
}

// BTCHandler renders /btc: the disclaimer, live price widget, and the
// 13-entry-point key/address converter form (empty on first load — all
// computation happens via POST /btc/convert, see ConvertHandler).
func BTCHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		lang := langFromRequest(r)
		data := &BTCPageData{
			PageData: NewPageData(
				lang,
				i18nOr(lang, "seo.title.btc", "Bitcoin - sConvert"),
				i18nOr(lang, "seo.description.btc", ""),
				"https://sconvert.ru/btc",
			),
			CurveOrderHex: btc.CurveOrderHex,
		}
		Render(w, "page:btc", data)
	}
}

// PriceHandler serves /api/btc/price, proxying CoinGecko through
// btc.PriceProvider's Redis cache.
func PriceHandler(provider *btc.PriceProvider) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		price, err := provider.Price(r.Context())
		if err != nil {
			http.Error(w, "price fetch failed", http.StatusBadGateway)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(price)
	}
}

type convertRequest struct {
	Field string `json:"field"`
	Value string `json:"value"`
}

type convertResponse struct {
	Error string `json:"error,omitempty"`

	PrivateDec     string `json:"privateDec"`
	PrivateHex     string `json:"privateHex"`
	PrivateHexNorm string `json:"privateHexNorm"`
	PrivateWIF     string `json:"privateWIF"`
	PrivateWIFU    string `json:"privateWIFU"`
	PublicKeyC     string `json:"publicKeyC"`
	PublicKeyU     string `json:"publicKeyU"`
	Ripemd160C     string `json:"ripemd160C"`
	Ripemd160U     string `json:"ripemd160U"`
	AddressC       string `json:"addressC"`
	AddressU       string `json:"addressU"`
	AddressP2SH    string `json:"addressP2SH"`
	AddressP2WPKH  string `json:"addressP2WPKH"`

	AddressCStatus      string `json:"addressCStatus"`
	AddressUStatus      string `json:"addressUStatus"`
	AddressP2SHStatus   string `json:"addressP2SHStatus"`
	AddressP2WPKHStatus string `json:"addressP2WPKHStatus"`

	AddressInfo    string `json:"addressInfo"`
	Balance        string `json:"balance"`
	AddressSummary string `json:"addressSummary"`
	Utxos          string `json:"utxos"`
	Txs            string `json:"txs"`

	PubkeyXHex    string `json:"pubkeyXHex"`
	PubkeyYHex    string `json:"pubkeyYHex"`
	PubkeyOnCurve bool   `json:"pubkeyOnCurve"`
}

// ConvertHandler is the single endpoint powering the whole /btc form: given
// one changed field, it derives every other representation (btc.Derive),
// checks/refreshes the two-tier cache, and — on a fresh (non-cached)
// derivation — looks up balance/tx/utxo data from blockstream.info. This
// mirrors app/components/btc_keys.py's per-rerun fan-out, but as one
// stateless request instead of Streamlit session-state diffing: since each
// entry recomputes everything from scratch anyway, statelessness is a
// simplification, not a loss.
func ConvertHandler(store *btc.Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		lang := langFromRequest(r)
		T := i18n.For(lang)

		var body convertRequest
		if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 8192)).Decode(&body); err != nil {
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}

		res, err := btc.Derive(body.Field, body.Value)
		if err != nil {
			resp := convertResponse{}
			switch err {
			case btc.ErrPrivateKeyRange:
				resp.Error = T["btc.error.range"]
			case btc.ErrPubKeyNotOnCurve:
				resp.Error = T["btc.error.pubkey_not_on_curve"]
			case btc.ErrInvalidSeedPhrase:
				resp.Error = T["btc.error.seed_phrase"]
			}
			writeJSON(w, resp)
			return
		}

		// P2SH addresses can't be reversed to a pubkey hash, so a p2sh
		// entry produces no derived AddressP2SH of its own — echo the
		// (trimmed) input back so the client can apply one uniform "always
		// overwrite from the response" rule instead of special-casing it.
		if body.Field == "address_p2sh" && res.AddressP2SH == "" {
			res.AddressP2SH = strings.TrimSpace(body.Value)
		}

		dbField := btc.EntryPointDBName(body.Field)
		signature := btc.BuildRequestSignature(dbField, body.Value)

		if cached, ok := store.Get(r.Context(), signature); ok {
			writeJSON(w, responseFromRecord(cached))
			return
		}

		resp := responseFromResult(res)
		resp.AddressCStatus = validationStatus(resp.AddressC, btc.IsValidP2PKHAddress, T)
		resp.AddressUStatus = validationStatus(resp.AddressU, btc.IsValidP2PKHAddress, T)
		resp.AddressP2SHStatus = validationStatus(resp.AddressP2SH, btc.IsValidP2SHAddress, T)
		resp.AddressP2WPKHStatus = validationStatus(resp.AddressP2WPKH, btc.IsValidP2WPKHAddress, T)

		if res.LookupAddress != "" {
			fillLookups(r, &resp, res.LookupAddress, T)
		}

		infoAddress := firstNonEmpty(resp.AddressC, resp.AddressU, resp.AddressP2WPKH, resp.AddressP2SH)
		if infoAddress != "" {
			info := btc.DescribeAddress(infoAddress)
			if info.Unknown {
				resp.AddressInfo = T["btc.address_info.unknown"]
			} else {
				resp.AddressInfo = fmt.Sprintf("%s: %s, %s: %s", T["btc.address_info.type"], info.Type, T["btc.address_info.network"], info.Network)
			}
		}

		store.Save(r.Context(), buildRecord(body.Field, body.Value, dbField, signature, res, &resp))
		writeJSON(w, resp)
	}
}

func fillLookups(r *http.Request, resp *convertResponse, address string, T i18n.Dict) {
	if balance, err := btc.LookupBalanceSats(address); err == nil {
		resp.Balance = fmt.Sprintf("%d sats (%.8f BTC)", balance, float64(balance)/1e8)
	} else {
		resp.Balance = T["btc.balance.unavailable"]
	}

	if txs, err := btc.LookupTransactions(address); err == nil {
		if len(txs) == 0 {
			resp.Txs = T["btc.txs.empty"]
		} else {
			tip, _ := btc.LookupTipHeight()
			resp.Txs = btc.FormatTransactions(txs, address, tip)
		}
	} else {
		resp.Txs = T["btc.txs.unavailable"]
	}

	if utxos, err := btc.LookupUTXOs(address); err == nil {
		if len(utxos) == 0 {
			resp.Utxos = T["btc.utxos.empty"]
		} else {
			resp.Utxos = btc.FormatUTXOs(utxos, T["universal_yes_word"], T["universal_no_word"])
		}
	} else {
		resp.Utxos = T["btc.utxos.unavailable"]
	}

	if summary, err := btc.LookupAddressSummary(address); err == nil {
		resp.AddressSummary = fmt.Sprintf("%s: %d sats (%.8f BTC) | %s: %d sats (%.8f BTC) | %s: %d sats (%.8f BTC)",
			T["btc.address_summary.received"], summary.Received, float64(summary.Received)/1e8,
			T["btc.address_summary.sent"], summary.Sent, float64(summary.Sent)/1e8,
			T["btc.address_summary.balance"], summary.Balance, float64(summary.Balance)/1e8)
	} else {
		resp.AddressSummary = T["btc.address_summary.unavailable"]
	}
}

func responseFromResult(res *btc.Result) convertResponse {
	return convertResponse{
		PrivateDec:     res.PrivateDec,
		PrivateHex:     res.PrivateHex,
		PrivateHexNorm: res.PrivateHexNorm,
		PrivateWIF:     res.PrivateWIF,
		PrivateWIFU:    res.PrivateWIFU,
		PublicKeyC:     res.PublicKeyC,
		PublicKeyU:     res.PublicKeyU,
		Ripemd160C:     res.Ripemd160C,
		Ripemd160U:     res.Ripemd160U,
		AddressC:       res.AddressC,
		AddressU:       res.AddressU,
		AddressP2SH:    res.AddressP2SH,
		AddressP2WPKH:  res.AddressP2WPKH,
		PubkeyXHex:     res.PubkeyXHex,
		PubkeyYHex:     res.PubkeyYHex,
		PubkeyOnCurve:  res.PubkeyOnCurve,
	}
}

func responseFromRecord(rec *btc.Record) convertResponse {
	return convertResponse{
		PrivateDec:     rec.OutPrivateDec,
		PrivateHex:     rec.OutPrivateHex,
		PrivateHexNorm: rec.OutPrivateHexNormalized,
		PrivateWIF:     rec.OutPrivateWIF,
		PrivateWIFU:    rec.OutPrivateWIFU,
		PublicKeyC:     rec.OutPublicKeyC,
		PublicKeyU:     rec.OutPublicKeyU,
		Ripemd160C:     rec.OutRipemd160C,
		Ripemd160U:     rec.OutRipemd160U,
		AddressC:       rec.OutAddressC,
		AddressU:       rec.OutAddressU,
		AddressP2SH:    rec.OutAddressP2SH,
		AddressP2WPKH:  rec.OutAddressP2WPKH,

		AddressCStatus:      rec.OutAddressCStatus,
		AddressUStatus:      rec.OutAddressUStatus,
		AddressP2SHStatus:   rec.OutAddressP2SHStatus,
		AddressP2WPKHStatus: rec.OutAddressP2WPKHStatus,

		AddressInfo:    rec.OutAddressInfo,
		Balance:        rec.OutBalanceText,
		AddressSummary: rec.OutAddressSummaryText,
		Utxos:          rec.OutUtxosText,
		Txs:            rec.OutTxsText,

		PubkeyXHex:    rec.OutPubkeyXHex,
		PubkeyYHex:    rec.OutPubkeyYHex,
		PubkeyOnCurve: rec.OutPubkeyOnCurve,
	}
}

func buildRecord(field, value, dbField, signature string, res *btc.Result, resp *convertResponse) *btc.Record {
	rec := &btc.Record{
		RequestSignature:        signature,
		EntryPointField:         dbField,
		OutPrivateDec:           res.PrivateDec,
		OutPrivateHex:           res.PrivateHex,
		OutPrivateHexNormalized: res.PrivateHexNorm,
		OutPrivateWIF:           res.PrivateWIF,
		OutPrivateWIFU:          res.PrivateWIFU,
		OutPublicKeyC:           res.PublicKeyC,
		OutPublicKeyU:           res.PublicKeyU,
		OutRipemd160C:           res.Ripemd160C,
		OutRipemd160U:           res.Ripemd160U,
		OutAddressC:             res.AddressC,
		OutAddressU:             res.AddressU,
		OutAddressP2SH:          res.AddressP2SH,
		OutAddressP2WPKH:        res.AddressP2WPKH,
		OutAddressInfo:          resp.AddressInfo,
		OutBalanceText:          resp.Balance,
		OutAddressSummaryText:   resp.AddressSummary,
		OutUtxosText:            resp.Utxos,
		OutTxsText:              resp.Txs,
		OutPubkeyXHex:           res.PubkeyXHex,
		OutPubkeyYHex:           res.PubkeyYHex,
		OutPubkeyOnCurve:        res.PubkeyOnCurve,
		OutAddressCStatus:       resp.AddressCStatus,
		OutAddressUStatus:       resp.AddressUStatus,
		OutAddressP2SHStatus:    resp.AddressP2SHStatus,
		OutAddressP2WPKHStatus:  resp.AddressP2WPKHStatus,
	}
	trimmed := strings.TrimSpace(value)
	switch field {
	case "private_dec":
		rec.InPrivateDec = trimmed
	case "private_hex":
		rec.InPrivateHex = trimmed
	case "private_wif":
		rec.InPrivateWIF = trimmed
	case "private_wif_uncompressed":
		rec.InPrivateWIFU = trimmed
	case "seed_phrase":
		rec.InSeedPhrase = trimmed
	case "public_key":
		rec.InPublicKeyC = trimmed
	case "public_key_uncompressed":
		rec.InPublicKeyU = trimmed
	case "ripemd160":
		rec.InRipemd160C = trimmed
	case "ripemd160_uncompressed":
		rec.InRipemd160U = trimmed
	case "address":
		rec.InAddressC = trimmed
	case "address_uncompressed":
		rec.InAddressU = trimmed
	case "address_p2sh":
		rec.InAddressP2SH = trimmed
	case "address_p2wpkh":
		rec.InAddressP2WPKH = trimmed
	}
	return rec
}

func validationStatus(value string, valid func(string) bool, T i18n.Dict) string {
	if strings.TrimSpace(value) == "" {
		return ""
	}
	if valid(value) {
		return T["btc.validation.valid"]
	}
	return T["btc.validation.invalid"]
}

func firstNonEmpty(values ...string) string {
	for _, v := range values {
		if v != "" {
			return v
		}
	}
	return ""
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(v)
}
