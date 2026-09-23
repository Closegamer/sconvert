// Package currency proxies live USD-based exchange rates from
// open.er-api.com (same upstream and cache TTL as the old Python
// api/main.py /api/currency/rates endpoint), cached in Redis so the
// external API is hit at most once per hour regardless of traffic.
package currency

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"sort"
	"time"

	"github.com/redis/go-redis/v9"
)

type Entry struct {
	Code     string `json:"code"`
	LabelKey string `json:"labelKey"`
}

// List is a direct port of app/components/currency.py's _CURRENCIES, same
// order (used for the two-column layout on /currency).
var List = []Entry{
	{"USD", "curr.usd"}, {"EUR", "curr.eur"}, {"GBP", "curr.gbp"}, {"JPY", "curr.jpy"},
	{"CHF", "curr.chf"}, {"CNY", "curr.cny"},
	{"AUD", "curr.aud"}, {"CAD", "curr.cad"}, {"HKD", "curr.hkd"}, {"SGD", "curr.sgd"},
	{"NZD", "curr.nzd"}, {"NOK", "curr.nok"}, {"SEK", "curr.sek"}, {"DKK", "curr.dkk"},
	{"RUB", "curr.rub"}, {"UAH", "curr.uah"}, {"BYN", "curr.byn"}, {"KZT", "curr.kzt"},
	{"UZS", "curr.uzs"}, {"KGS", "curr.kgs"}, {"TJS", "curr.tjs"}, {"TMT", "curr.tmt"},
	{"AZN", "curr.azn"}, {"GEL", "curr.gel"}, {"AMD", "curr.amd"}, {"MDL", "curr.mdl"},
	{"PLN", "curr.pln"}, {"CZK", "curr.czk"}, {"HUF", "curr.huf"}, {"RON", "curr.ron"},
	{"BGN", "curr.bgn"}, {"HRK", "curr.hrk"}, {"RSD", "curr.rsd"}, {"MKD", "curr.mkd"},
	{"ALL", "curr.all"}, {"BAM", "curr.bam"}, {"ISK", "curr.isk"},
	{"TRY", "curr.try"}, {"ILS", "curr.ils"}, {"SAR", "curr.sar"}, {"AED", "curr.aed"},
	{"QAR", "curr.qar"}, {"KWD", "curr.kwd"}, {"BHD", "curr.bhd"}, {"OMR", "curr.omr"},
	{"JOD", "curr.jod"}, {"IQD", "curr.iqd"}, {"IRR", "curr.irr"}, {"LBP", "curr.lbp"},
	{"SYP", "curr.syp"}, {"YER", "curr.yer"},
	{"INR", "curr.inr"}, {"PKR", "curr.pkr"}, {"BDT", "curr.bdt"}, {"NPR", "curr.npr"},
	{"LKR", "curr.lkr"}, {"MVR", "curr.mvr"}, {"BTN", "curr.btn"}, {"AFN", "curr.afn"},
	{"KRW", "curr.krw"}, {"TWD", "curr.twd"}, {"THB", "curr.thb"}, {"MYR", "curr.myr"},
	{"IDR", "curr.idr"}, {"PHP", "curr.php"}, {"VND", "curr.vnd"}, {"MNT", "curr.mnt"},
	{"MOP", "curr.mop"}, {"KHR", "curr.khr"}, {"LAK", "curr.lak"}, {"MMK", "curr.mmk"},
	{"BND", "curr.bnd"},
	{"FJD", "curr.fjd"}, {"PGK", "curr.pgk"}, {"SBD", "curr.sbd"}, {"VUV", "curr.vuv"},
	{"WST", "curr.wst"}, {"TOP", "curr.top"}, {"XPF", "curr.xpf"},
	{"MXN", "curr.mxn"}, {"BRL", "curr.brl"}, {"ARS", "curr.ars"}, {"CLP", "curr.clp"},
	{"COP", "curr.cop"}, {"PEN", "curr.pen"}, {"BOB", "curr.bob"}, {"PYG", "curr.pyg"},
	{"UYU", "curr.uyu"}, {"VES", "curr.ves"}, {"DOP", "curr.dop"}, {"GTQ", "curr.gtq"},
	{"HNL", "curr.hnl"}, {"NIO", "curr.nio"}, {"CRC", "curr.crc"}, {"PAB", "curr.pab"},
	{"CUP", "curr.cup"}, {"JMD", "curr.jmd"}, {"TTD", "curr.ttd"}, {"BBD", "curr.bbd"},
	{"BSD", "curr.bsd"}, {"HTG", "curr.htg"}, {"XCD", "curr.xcd"}, {"BZD", "curr.bzd"},
	{"GYD", "curr.gyd"}, {"SRD", "curr.srd"}, {"AWG", "curr.awg"}, {"ANG", "curr.ang"},
	{"SVC", "curr.svc"}, {"KYD", "curr.kyd"}, {"BMD", "curr.bmd"},
	{"MAD", "curr.mad"}, {"TND", "curr.tnd"}, {"DZD", "curr.dzd"}, {"LYD", "curr.lyd"},
	{"EGP", "curr.egp"}, {"SDG", "curr.sdg"},
	{"ZAR", "curr.zar"}, {"NGN", "curr.ngn"}, {"KES", "curr.kes"}, {"GHS", "curr.ghs"},
	{"TZS", "curr.tzs"}, {"UGX", "curr.ugx"}, {"ETB", "curr.etb"}, {"XOF", "curr.xof"},
	{"XAF", "curr.xaf"}, {"CDF", "curr.cdf"}, {"AOA", "curr.aoa"}, {"MGA", "curr.mga"},
	{"MZN", "curr.mzn"}, {"ZMW", "curr.zmw"}, {"BWP", "curr.bwp"}, {"NAD", "curr.nad"},
	{"ZWL", "curr.zwl"}, {"MWK", "curr.mwk"}, {"RWF", "curr.rwf"}, {"BIF", "curr.bif"},
	{"SOS", "curr.sos"}, {"DJF", "curr.djf"}, {"ERN", "curr.ern"}, {"SCR", "curr.scr"},
	{"MUR", "curr.mur"}, {"CVE", "curr.cve"}, {"GMD", "curr.gmd"}, {"GNF", "curr.gnf"},
	{"SLL", "curr.sll"}, {"LRD", "curr.lrd"}, {"SZL", "curr.szl"}, {"LSL", "curr.lsl"},
	{"STN", "curr.stn"}, {"KMF", "curr.kmf"}, {"MRU", "curr.mru"},
	{"GIP", "curr.gip"}, {"FKP", "curr.fkp"},
}

var codes = func() map[string]bool {
	m := make(map[string]bool, len(List))
	for _, e := range List {
		m[e.Code] = true
	}
	return m
}()

// Contains reports whether code is a known currency (used to validate
// /api/stats/hit payloads before writing a row).
func Contains(code string) bool { return codes[code] }

// Codes returns the Code of every entry in List, in the same order — used
// to fetch popularity counts in one batch (stats.Store.InputTotals).
func Codes() []string {
	out := make([]string, len(List))
	for i, e := range List {
		out[i] = e.Code
	}
	return out
}

// RankedBy returns a copy of List sorted by descending popularity count
// (counts[i] corresponds to List[i]). Ties keep the original relative
// order (stable sort), so with no traffic yet the list falls back to the
// default region-grouped order. Mirrors units.RankedBy, but at individual
// currency granularity rather than category granularity — each currency
// ranks on its own hit count, same one incremented by both typing a value
// and clicking a search result (see static/js/currency.js).
func RankedBy(counts []int64) []Entry {
	ranked := make([]Entry, len(List))
	copy(ranked, List)
	if len(counts) != len(List) {
		return ranked
	}
	idx := make([]int, len(List))
	for i := range idx {
		idx[i] = i
	}
	sort.SliceStable(idx, func(a, b int) bool {
		return counts[idx[a]] > counts[idx[b]]
	})
	for i, srcIdx := range idx {
		ranked[i] = List[srcIdx]
	}
	return ranked
}

const (
	sourceURL = "https://open.er-api.com/v6/latest/USD"
	cacheKey  = "currency:rates:v1"
	cacheTTL  = time.Hour
)

type Rates struct {
	Base      string             `json:"base"`
	Rates     map[string]float64 `json:"rates"`
	UpdatedAt string             `json:"updatedAt"`
}

// Provider fetches Rates, preferring a Redis cache. A nil *redis.Client
// (Redis unreachable at startup) degrades gracefully to fetching from
// open.er-api.com on every request rather than failing the page.
type Provider struct {
	rdb  *redis.Client
	http *http.Client
}

func NewProvider(rdb *redis.Client) *Provider {
	return &Provider{rdb: rdb, http: &http.Client{Timeout: 8 * time.Second}}
}

func (p *Provider) Rates(ctx context.Context) (*Rates, error) {
	if p.rdb != nil {
		if cached, err := p.rdb.Get(ctx, cacheKey).Result(); err == nil {
			var r Rates
			if json.Unmarshal([]byte(cached), &r) == nil {
				return &r, nil
			}
		}
	}

	r, err := p.fetch(ctx)
	if err != nil {
		return nil, err
	}

	if p.rdb != nil {
		if payload, err := json.Marshal(r); err == nil {
			_ = p.rdb.Set(ctx, cacheKey, payload, cacheTTL).Err() // best-effort
		}
	}
	return r, nil
}

func (p *Provider) fetch(ctx context.Context) (*Rates, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, sourceURL, nil)
	if err != nil {
		return nil, err
	}
	resp, err := p.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, errors.New("currency: upstream status " + resp.Status)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var raw struct {
		Rates             map[string]float64 `json:"rates"`
		TimeLastUpdateUTC string              `json:"time_last_update_utc"`
	}
	if err := json.Unmarshal(body, &raw); err != nil {
		return nil, err
	}
	return &Rates{Base: "USD", Rates: raw.Rates, UpdatedAt: raw.TimeLastUpdateUTC}, nil
}
