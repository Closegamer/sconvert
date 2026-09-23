package units

import (
	"math"
	"testing"
)

func approxEqual(t *testing.T, got, want, tol float64) {
	t.Helper()
	if math.Abs(got-want) > tol {
		t.Errorf("got %v, want %v (tol %v)", got, want, tol)
	}
}

func unit(t *testing.T, cat Category, code string) Unit {
	t.Helper()
	for _, u := range cat.Units {
		if u.Code == code {
			return u
		}
	}
	t.Fatalf("unit %q not found in category %q", code, cat.Key)
	return Unit{}
}

func TestLinearRoundTrip(t *testing.T) {
	for _, cat := range All {
		for _, u := range cat.Units {
			base := u.ToBase(3.5)
			back := u.FromBase(base)
			approxEqual(t, back, 3.5, 1e-9)
		}
	}
}

func TestKnownLengthConversions(t *testing.T) {
	km := unit(t, Length, "km")
	mi := unit(t, Length, "mi")
	inch := unit(t, Length, "in")
	m := unit(t, Length, "m")

	approxEqual(t, km.ToBase(1), 1000, 1e-9)               // 1 km = 1000 m
	approxEqual(t, mi.FromBase(1609.344), 1, 1e-9)         // 1609.344 m = 1 mile
	approxEqual(t, inch.FromBase(m.ToBase(1)), 39.3700787, 1e-6) // 1 m in inches
}

func TestTemperatureFixedPoints(t *testing.T) {
	c := unit(t, Temperature, "c")
	f := unit(t, Temperature, "f")
	k := unit(t, Temperature, "k")
	r := unit(t, Temperature, "r")
	re := unit(t, Temperature, "re")
	de := unit(t, Temperature, "de")
	n := unit(t, Temperature, "n")
	ro := unit(t, Temperature, "ro")

	// 0 C = 273.15 K = 32 F = 491.67 R = 0 Re = 150 De = 0 N = 7.5 Ro
	// (Delisle is inverted: 0 De = boiling, 150 De = freezing)
	base := c.ToBase(0)
	approxEqual(t, base, 273.15, 1e-9)
	approxEqual(t, f.FromBase(base), 32, 1e-9)
	approxEqual(t, k.FromBase(base), 273.15, 1e-9)
	approxEqual(t, r.FromBase(base), 491.67, 1e-9)
	approxEqual(t, re.FromBase(base), 0, 1e-9)
	approxEqual(t, de.FromBase(base), 150, 1e-9)
	approxEqual(t, n.FromBase(base), 0, 1e-9)
	approxEqual(t, ro.FromBase(base), 7.5, 1e-9)

	// -40 C = -40 F (the famous crossover point)
	approxEqual(t, f.FromBase(c.ToBase(-40)), -40, 1e-9)

	// 100 C = boiling point = 212 F = 373.15 K = 80 Re = 0 De
	boiling := c.ToBase(100)
	approxEqual(t, f.FromBase(boiling), 212, 1e-9)
	approxEqual(t, re.FromBase(boiling), 80, 1e-9)
	approxEqual(t, de.FromBase(boiling), 0, 1e-9)
}

func TestByKey(t *testing.T) {
	if _, ok := ByKey("length"); !ok {
		t.Fatal("expected length category to exist")
	}
	if _, ok := ByKey("does-not-exist"); ok {
		t.Fatal("expected missing category to be absent")
	}
	if len(All) != 22 {
		t.Fatalf("expected 22 categories, got %d", len(All))
	}
}
