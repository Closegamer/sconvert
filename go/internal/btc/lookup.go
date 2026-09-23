package btc

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"strings"
	"time"
)

const blockstreamBase = "https://blockstream.info/api"

var httpClient = &http.Client{Timeout: 10 * time.Second}

func fetchJSON(url string, out any) error {
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return err
	}
	resp, err := httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("blockstream: %s: status %d", url, resp.StatusCode)
	}
	return json.NewDecoder(resp.Body).Decode(out)
}

type chainStats struct {
	FundedTxoSum int64 `json:"funded_txo_sum"`
	SpentTxoSum  int64 `json:"spent_txo_sum"`
}

type addressInfoResponse struct {
	ChainStats   chainStats `json:"chain_stats"`
	MempoolStats chainStats `json:"mempool_stats"`
}

// LookupBalanceSats mirrors Python's _lookup_balance_sats.
func LookupBalanceSats(address string) (int64, error) {
	var info addressInfoResponse
	if err := fetchJSON(blockstreamBase+"/address/"+address, &info); err != nil {
		return 0, err
	}
	funded := info.ChainStats.FundedTxoSum + info.MempoolStats.FundedTxoSum
	spent := info.ChainStats.SpentTxoSum + info.MempoolStats.SpentTxoSum
	return funded - spent, nil
}

type AddressSummary struct {
	Received int64
	Sent     int64
	Balance  int64
}

// LookupAddressSummary mirrors Python's _lookup_address_summary.
func LookupAddressSummary(address string) (*AddressSummary, error) {
	var info addressInfoResponse
	if err := fetchJSON(blockstreamBase+"/address/"+address, &info); err != nil {
		return nil, err
	}
	funded := info.ChainStats.FundedTxoSum + info.MempoolStats.FundedTxoSum
	spent := info.ChainStats.SpentTxoSum + info.MempoolStats.SpentTxoSum
	return &AddressSummary{Received: funded, Sent: spent, Balance: funded - spent}, nil
}

// LookupTipHeight mirrors Python's _lookup_tip_height.
func LookupTipHeight() (int, error) {
	req, err := http.NewRequest(http.MethodGet, blockstreamBase+"/blocks/tip/height", nil)
	if err != nil {
		return 0, err
	}
	resp, err := httpClient.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return 0, fmt.Errorf("blockstream: tip height: status %d", resp.StatusCode)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return 0, err
	}
	return strconv.Atoi(strings.TrimSpace(string(body)))
}

type UTXOStatus struct {
	Confirmed   bool `json:"confirmed"`
	BlockHeight *int `json:"block_height"`
}

type UTXO struct {
	Txid   string     `json:"txid"`
	Vout   int        `json:"vout"`
	Value  int64      `json:"value"`
	Status UTXOStatus `json:"status"`
}

// LookupUTXOs mirrors Python's _lookup_utxos.
func LookupUTXOs(address string) ([]UTXO, error) {
	var utxos []UTXO
	if err := fetchJSON(blockstreamBase+"/address/"+address+"/utxo", &utxos); err != nil {
		return nil, err
	}
	return utxos, nil
}

type txPrevout struct {
	ScriptPubkeyAddress string `json:"scriptpubkey_address"`
	Value                int64 `json:"value"`
}

type txVin struct {
	Prevout      *txPrevout `json:"prevout"`
	Witness      []string   `json:"witness"`
	ScriptsigAsm string     `json:"scriptsig_asm"`
}

type txVout struct {
	ScriptPubkeyAddress string `json:"scriptpubkey_address"`
	Value                int64 `json:"value"`
}

type txStatus struct {
	Confirmed   bool `json:"confirmed"`
	BlockHeight *int `json:"block_height"`
}

type Tx struct {
	Txid   string   `json:"txid"`
	Fee    *int64   `json:"fee"`
	Status txStatus `json:"status"`
	Vin    []txVin  `json:"vin"`
	Vout   []txVout `json:"vout"`
}

// LookupTransactions mirrors Python's _lookup_transactions.
func LookupTransactions(address string) ([]Tx, error) {
	var txs []Tx
	if err := fetchJSON(blockstreamBase+"/address/"+address+"/txs", &txs); err != nil {
		return nil, err
	}
	return txs, nil
}

func isPubkeyHex(token string) bool {
	if len(token) != 66 && len(token) != 130 {
		return false
	}
	if !strings.HasPrefix(token, "02") && !strings.HasPrefix(token, "03") && !strings.HasPrefix(token, "04") {
		return false
	}
	_, err := hex.DecodeString(token)
	return err == nil
}

func extractPubkeyFromVin(vin txVin) string {
	for _, item := range vin.Witness {
		token := strings.ToLower(item)
		if isPubkeyHex(token) {
			return token
		}
	}
	for _, token := range strings.Fields(strings.ToLower(vin.ScriptsigAsm)) {
		if isPubkeyHex(token) {
			return token
		}
	}
	return ""
}

// LookupPubkeyByAddress scans the address's transaction history for a past
// spend that reveals its public key (witness or scriptSig), mirroring
// Python's _lookup_pubkey_by_address. Returns "" (no error) if the address
// has never spent from, which is the common case for a fresh address.
func LookupPubkeyByAddress(address string) (string, error) {
	txs, err := LookupTransactions(address)
	if err != nil {
		return "", err
	}
	for _, tx := range txs {
		for _, vin := range tx.Vin {
			if vin.Prevout == nil || vin.Prevout.ScriptPubkeyAddress != address {
				continue
			}
			if pk := extractPubkeyFromVin(vin); pk != "" {
				return pk, nil
			}
		}
	}
	return "", nil
}

// FormatUTXOs renders a UTXO list as the same human-readable text block
// Python's _format_utxos_for_view produced, for the read-only textarea.
func FormatUTXOs(utxos []UTXO, yesWord, noWord string) string {
	var lines []string
	for i, u := range utxos {
		lines = append(lines, fmt.Sprintf("%d. txid: %s", i+1, u.Txid))
		lines = append(lines, fmt.Sprintf("   vout: %d", u.Vout))
		lines = append(lines, fmt.Sprintf("   value: %d sats (%.8f BTC)", u.Value, float64(u.Value)/1e8))
		confirmedWord := noWord
		if u.Status.Confirmed {
			confirmedWord = yesWord
		}
		lines = append(lines, "   confirmed: "+confirmedWord)
		if u.Status.BlockHeight != nil {
			lines = append(lines, fmt.Sprintf("   block: %d", *u.Status.BlockHeight))
		}
		lines = append(lines, "")
	}
	return strings.TrimSpace(strings.Join(lines, "\n"))
}

func txAmountsForAddress(tx Tx, address string) (received, sent int64) {
	for _, v := range tx.Vout {
		if v.ScriptPubkeyAddress == address {
			received += v.Value
		}
	}
	for _, vin := range tx.Vin {
		if vin.Prevout != nil && vin.Prevout.ScriptPubkeyAddress == address {
			sent += vin.Prevout.Value
		}
	}
	return received, sent
}

// FormatTransactions renders a transaction list as the same human-readable
// text block Python's _format_transactions_for_view produced. Like the
// original, "confirmed" here is always the literal English "yes"/"no"
// (unlike FormatUTXOs, which localizes it) — preserved for parity.
func FormatTransactions(txs []Tx, address string, tipHeight int) string {
	var lines []string
	for i, tx := range txs {
		lines = append(lines, fmt.Sprintf("%d. txid: %s", i+1, tx.Txid))
		confirmedWord := "no"
		confirmations := 0
		if tx.Status.Confirmed {
			confirmedWord = "yes"
			if tx.Status.BlockHeight != nil {
				confirmations = tipHeight - *tx.Status.BlockHeight + 1
				if confirmations < 0 {
					confirmations = 0
				}
			}
		}
		lines = append(lines, "   confirmed: "+confirmedWord)
		lines = append(lines, fmt.Sprintf("   confirmations: %d", confirmations))
		if tx.Status.BlockHeight != nil {
			lines = append(lines, fmt.Sprintf("   block: %d", *tx.Status.BlockHeight))
		}
		received, sent := txAmountsForAddress(tx, address)
		net := received - sent
		lines = append(lines, fmt.Sprintf("   received: %d sats (%.8f BTC)", received, float64(received)/1e8))
		lines = append(lines, fmt.Sprintf("   sent: %d sats (%.8f BTC)", sent, float64(sent)/1e8))
		lines = append(lines, fmt.Sprintf("   net: %+d sats (%+.8f BTC)", net, float64(net)/1e8))
		if tx.Fee != nil {
			lines = append(lines, fmt.Sprintf("   fee: %d sats", *tx.Fee))
		}
		lines = append(lines, "")
	}
	return strings.TrimSpace(strings.Join(lines, "\n"))
}
