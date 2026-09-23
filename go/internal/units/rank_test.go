package units

import "testing"

func TestRankedByOrdersDescending(t *testing.T) {
	counts := make([]int64, len(All))
	// Make the last category the most popular, everything else 0.
	counts[len(counts)-1] = 100
	ranked := RankedBy(counts)
	if ranked[0].Key != All[len(All)-1].Key {
		t.Fatalf("expected %q first, got %q", All[len(All)-1].Key, ranked[0].Key)
	}
}

func TestRankedByFallsBackOnMismatch(t *testing.T) {
	ranked := RankedBy([]int64{1, 2, 3}) // wrong length
	if len(ranked) != len(All) || ranked[0].Key != All[0].Key {
		t.Fatal("expected fallback to default order on count/category length mismatch")
	}
}

func TestKeysMatchesAll(t *testing.T) {
	keys := Keys()
	if len(keys) != len(All) {
		t.Fatalf("expected %d keys, got %d", len(All), len(keys))
	}
	for i, k := range keys {
		if k != All[i].Key {
			t.Fatalf("key mismatch at %d: %q != %q", i, k, All[i].Key)
		}
	}
}
