package btc

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/redis/go-redis/v9"
)

const (
	priceCacheKey  = "btc:price:v1"
	priceTTL       = 60 * time.Second
	priceSourceURL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,rub"
)

type Price struct {
	USD       float64 `json:"usd"`
	RUB       float64 `json:"rub"`
	UpdatedAt string  `json:"updated_at"`
	Cached    bool    `json:"cached"`
}

// PriceProvider mirrors api/main.py's /api/btc/price: proxies CoinGecko,
// cached in Redis for 60s. Degrades to a direct fetch per request if Redis
// is unreachable, same pattern as currency.Provider.
type PriceProvider struct {
	rdb  *redis.Client
	http *http.Client
}

func NewPriceProvider(rdb *redis.Client) *PriceProvider {
	return &PriceProvider{rdb: rdb, http: &http.Client{Timeout: 10 * time.Second}}
}

func (p *PriceProvider) Price(ctx context.Context) (*Price, error) {
	if p.rdb != nil {
		if cached, err := p.rdb.Get(ctx, priceCacheKey).Result(); err == nil {
			var pr Price
			if json.Unmarshal([]byte(cached), &pr) == nil {
				pr.Cached = true
				return &pr, nil
			}
		}
	}

	pr, err := p.fetch(ctx)
	if err != nil {
		return nil, err
	}

	if p.rdb != nil {
		if payload, err := json.Marshal(pr); err == nil {
			_ = p.rdb.Set(ctx, priceCacheKey, payload, priceTTL).Err()
		}
	}
	return pr, nil
}

func (p *PriceProvider) fetch(ctx context.Context) (*Price, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, priceSourceURL, nil)
	if err != nil {
		return nil, err
	}
	resp, err := p.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("coingecko: status %d", resp.StatusCode)
	}

	var raw struct {
		Bitcoin struct {
			USD float64 `json:"usd"`
			RUB float64 `json:"rub"`
		} `json:"bitcoin"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&raw); err != nil {
		return nil, err
	}
	return &Price{
		USD:       raw.Bitcoin.USD,
		RUB:       raw.Bitcoin.RUB,
		UpdatedAt: time.Now().UTC().Format(time.RFC3339),
		Cached:    false,
	}, nil
}
