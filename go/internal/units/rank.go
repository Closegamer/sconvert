package units

import "sort"

// RankedBy returns a copy of All sorted by descending popularity count
// (counts[i] corresponds to All[i]). Ties keep the original relative order
// (stable sort), so with no traffic yet the list falls back to the current
// default ordering.
func RankedBy(counts []int64) []Category {
	ranked := make([]Category, len(All))
	copy(ranked, All)
	if len(counts) != len(All) {
		return ranked
	}
	idx := make([]int, len(All))
	for i := range idx {
		idx[i] = i
	}
	sort.SliceStable(idx, func(a, b int) bool {
		return counts[idx[a]] > counts[idx[b]]
	})
	for i, srcIdx := range idx {
		ranked[i] = All[srcIdx]
	}
	return ranked
}

// Keys returns the Key of every category in All, in the same order — used
// to fetch popularity counts in one batch (stats.Store.Counts).
func Keys() []string {
	keys := make([]string, len(All))
	for i, c := range All {
		keys[i] = c.Key
	}
	return keys
}
