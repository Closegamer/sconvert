// Package stats tracks anonymous, per-input usage counts (no user
// identifiers, no IP addresses) — one counter per (scope, category, input),
// incremented in place in Postgres. Used both to rank converters by
// popularity and to power the admin stats dashboard.
package stats

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

type Store struct {
	pool *pgxpool.Pool
}

func New(pool *pgxpool.Pool) *Store {
	return &Store{pool: pool}
}

// Hit records one anonymous use of input_key within category_key/scope
// (e.g. scope="units", category="length", input="km"). Best-effort: a
// missing/unreachable database must never break the page the beacon fired
// from, so errors are swallowed.
func (s *Store) Hit(ctx context.Context, scope, category, input string) {
	if s == nil || s.pool == nil {
		return
	}
	ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
	defer cancel()
	_, _ = s.pool.Exec(ctx, `
		INSERT INTO input_usage_stats (scope, category_key, input_key, hit_count, first_used_at, last_used_at)
		VALUES ($1, $2, $3, 1, NOW(), NOW())
		ON CONFLICT (scope, category_key, input_key)
		DO UPDATE SET hit_count = input_usage_stats.hit_count + 1, last_used_at = NOW()
	`, scope, category, input)
}

// CategoryTotals returns the summed hit_count for each of the given
// category keys within a scope, in the same order. Missing rows / DB
// errors resolve to 0 so ranking always falls back to the caller's
// default order.
func (s *Store) CategoryTotals(ctx context.Context, scope string, categoryKeys []string) []int64 {
	totals := make([]int64, len(categoryKeys))
	if s == nil || s.pool == nil || len(categoryKeys) == 0 {
		return totals
	}
	ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
	defer cancel()

	rows, err := s.pool.Query(ctx, `
		SELECT category_key, COALESCE(SUM(hit_count), 0)
		FROM input_usage_stats
		WHERE scope = $1 AND category_key = ANY($2)
		GROUP BY category_key
	`, scope, categoryKeys)
	if err != nil {
		return totals
	}
	defer rows.Close()

	byKey := make(map[string]int64, len(categoryKeys))
	for rows.Next() {
		var key string
		var total int64
		if err := rows.Scan(&key, &total); err == nil {
			byKey[key] = total
		}
	}
	for i, k := range categoryKeys {
		totals[i] = byKey[k]
	}
	return totals
}

// InputTotals returns the hit_count for each of the given input keys
// within a scope/category, in the same order — parallel to CategoryTotals
// but at input granularity. Used where each input ranks independently
// rather than being grouped into a category (e.g. currency, where every
// code is its own "category of one"). Missing rows / DB errors resolve to
// 0 so ranking always falls back to the caller's default order.
func (s *Store) InputTotals(ctx context.Context, scope, category string, inputKeys []string) []int64 {
	totals := make([]int64, len(inputKeys))
	if s == nil || s.pool == nil || len(inputKeys) == 0 {
		return totals
	}
	ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
	defer cancel()

	rows, err := s.pool.Query(ctx, `
		SELECT input_key, hit_count
		FROM input_usage_stats
		WHERE scope = $1 AND category_key = $2 AND input_key = ANY($3)
	`, scope, category, inputKeys)
	if err != nil {
		return totals
	}
	defer rows.Close()

	byKey := make(map[string]int64, len(inputKeys))
	for rows.Next() {
		var key string
		var count int64
		if err := rows.Scan(&key, &count); err == nil {
			byKey[key] = count
		}
	}
	for i, k := range inputKeys {
		totals[i] = byKey[k]
	}
	return totals
}

type Row struct {
	Scope       string
	CategoryKey string
	InputKey    string
	HitCount    int64
	LastUsedAt  time.Time
}

// All returns every tracked (scope, category, input) row, most-used first
// — the data source for the admin dashboard.
func (s *Store) All(ctx context.Context) ([]Row, error) {
	if s == nil || s.pool == nil {
		return nil, nil
	}
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	rows, err := s.pool.Query(ctx, `
		SELECT scope, category_key, input_key, hit_count, last_used_at
		FROM input_usage_stats
		ORDER BY hit_count DESC, last_used_at DESC
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []Row
	for rows.Next() {
		var r Row
		if err := rows.Scan(&r.Scope, &r.CategoryKey, &r.InputKey, &r.HitCount, &r.LastUsedAt); err != nil {
			return nil, err
		}
		out = append(out, r)
	}
	return out, rows.Err()
}
