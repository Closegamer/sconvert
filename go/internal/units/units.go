// Package units defines all unit-conversion categories.
//
// Every unit converts to/from its category's base unit via one affine
// formula: base = value*A + B. Plain factor-based units (length, mass, ...)
// are just B=0; temperature units (which need an offset, e.g. °C -> K) use
// the same struct instead of a separate code path. The struct is plain data
// (no funcs) so it can be exported as JSON and consumed by client-side JS
// for instant, round-trip-free conversion.
package units

import "math"

type Unit struct {
	Code     string  `json:"code"`
	LabelKey string  `json:"labelKey"`
	A        float64 `json:"a"`
	B        float64 `json:"b"`
}

func (u Unit) ToBase(v float64) float64      { return v*u.A + u.B }
func (u Unit) FromBase(base float64) float64 { return (base - u.B) / u.A }

type Category struct {
	Key      string `json:"key"`
	TitleKey string `json:"titleKey"`
	Units    []Unit `json:"units"`
}

func lin(code, labelKey string, factor float64) Unit {
	return Unit{Code: code, LabelKey: labelKey, A: factor, B: 0}
}

func aff(code, labelKey string, a, b float64) Unit {
	return Unit{Code: code, LabelKey: labelKey, A: a, B: b}
}

var Length = Category{
	Key: "length", TitleKey: "units.length.title",
	Units: []Unit{
		lin("nm", "units.length.nm", 1e-9),
		lin("um", "units.length.um", 1e-6),
		lin("mm", "units.length.mm", 0.001),
		lin("cm", "units.length.cm", 0.01),
		lin("in", "units.length.in", 0.0254),
		lin("vershok", "units.length.vershok", 0.04445),
		lin("dm", "units.length.dm", 0.1),
		lin("pyad", "units.length.pyad", 0.1778),
		lin("ft", "units.length.ft", 0.3048),
		lin("lokot", "units.length.lokot", 0.4445),
		lin("arshin", "units.length.arshin", 0.7112),
		lin("yd", "units.length.yd", 0.9144),
		lin("m", "units.length.m", 1.0),
		lin("fathom", "units.length.fathom", 1.8288),
		lin("sazhen", "units.length.sazhen", 2.1336),
		lin("kosaya_sazhen", "units.length.kosaya_sazhen", 2.48),
		lin("cable", "units.length.cable", 185.2),
		lin("km", "units.length.km", 1000.0),
		lin("mi", "units.length.mi", 1609.344),
		lin("nmi", "units.length.nmi", 1852.0),
		lin("league", "units.length.league", 4828.032),
		lin("au", "units.length.au", 149597870700.0),
		lin("ly", "units.length.ly", 9.4607304725808e15),
		lin("pc", "units.length.pc", 3.085677581491367e16),
	},
}

var Mass = Category{
	Key: "mass", TitleKey: "units.mass.title",
	Units: []Unit{
		lin("mg", "units.mass.mg", 1e-6),
		lin("g", "units.mass.g", 0.001),
		lin("oz", "units.mass.oz", 0.028349523125),
		lin("lb", "units.mass.lb", 0.45359237),
		lin("kg", "units.mass.kg", 1.0),
		lin("st", "units.mass.st", 6.35029318),
		lin("pood", "units.mass.pood", 16.3804964),
		lin("t", "units.mass.t", 1000.0),
	},
}

var Area = Category{
	Key: "area", TitleKey: "units.area.title",
	Units: []Unit{
		lin("mm2", "units.area.mm2", 1e-6),
		lin("cm2", "units.area.cm2", 1e-4),
		lin("in2", "units.area.in2", 0.00064516),
		lin("dm2", "units.area.dm2", 0.01),
		lin("ft2", "units.area.ft2", 0.09290304),
		lin("yd2", "units.area.yd2", 0.83612736),
		lin("m2", "units.area.m2", 1.0),
		lin("perch_lk", "units.area.perch_lk", 25.29285264),
		lin("are", "units.area.are", 100.0),
		lin("sotka", "units.area.sotka", 100.0),
		lin("acre", "units.area.acre", 4046.8564224),
		lin("ha", "units.area.ha", 10000.0),
		lin("km2", "units.area.km2", 1_000_000.0),
	},
}

var Volume = Category{
	Key: "volume", TitleKey: "units.volume.title",
	Units: []Unit{
		lin("mm3", "units.volume.mm3", 1e-9),
		lin("cm3", "units.volume.cm3", 1e-6),
		lin("ml", "units.volume.ml", 1e-6),
		lin("in3", "units.volume.in3", 1.6387064e-5),
		lin("dm3", "units.volume.dm3", 0.001),
		lin("l", "units.volume.l", 0.001),
		lin("pt", "units.volume.pt", 0.000473176473),
		lin("qt", "units.volume.qt", 0.000946352946),
		lin("gal", "units.volume.gal", 0.003785411784),
		lin("ft3", "units.volume.ft3", 0.028316846592),
		lin("m3", "units.volume.m3", 1.0),
	},
}

var Speed = Category{
	Key: "speed", TitleKey: "units.speed.title",
	Units: []Unit{
		lin("mm_s", "units.speed.mm_s", 0.001),
		lin("cm_s", "units.speed.cm_s", 0.01),
		lin("km_h", "units.speed.km_h", 1.0/3.6),
		lin("fps", "units.speed.fps", 0.3048),
		lin("mph", "units.speed.mph", 0.44704),
		lin("kt", "units.speed.kt", 0.5144444444444445),
		lin("m_s", "units.speed.m_s", 1.0),
		lin("c", "units.speed.c", 299_792_458.0),
	},
}

var Time = Category{
	Key: "time", TitleKey: "units.time.title",
	Units: []Unit{
		lin("ms", "units.time.ms", 0.001),
		lin("s", "units.time.s", 1.0),
		lin("min", "units.time.min", 60.0),
		lin("h", "units.time.h", 3600.0),
		lin("day", "units.time.day", 86400.0),
		lin("week", "units.time.week", 604800.0),
		lin("month", "units.time.month", 2629800.0),
		lin("year", "units.time.year", 31557600.0),
	},
}

var Pressure = Category{
	Key: "pressure", TitleKey: "units.pressure.title",
	Units: []Unit{
		lin("pa", "units.pressure.pa", 1.0),
		lin("hpa", "units.pressure.hpa", 100.0),
		lin("mmhg", "units.pressure.mmhg", 133.322387415),
		lin("kpa", "units.pressure.kpa", 1000.0),
		lin("psi", "units.pressure.psi", 6894.757293168),
		lin("bar", "units.pressure.bar", 100000.0),
		lin("atm", "units.pressure.atm", 101325.0),
	},
}

var Energy = Category{
	Key: "energy", TitleKey: "units.energy.title",
	Units: []Unit{
		lin("ev", "units.energy.ev", 1.602176634e-19),
		lin("j", "units.energy.j", 1.0),
		lin("cal", "units.energy.cal", 4.184),
		lin("kj", "units.energy.kj", 1000.0),
		lin("btu", "units.energy.btu", 1055.05585262),
		lin("wh", "units.energy.wh", 3600.0),
		lin("kcal", "units.energy.kcal", 4184.0),
		lin("kwh", "units.energy.kwh", 3_600_000.0),
	},
}

var Power = Category{
	Key: "power", TitleKey: "units.power.title",
	Units: []Unit{
		lin("mw", "units.power.mw", 0.001),
		lin("w", "units.power.w", 1.0),
		lin("btu_h", "units.power.btu_h", 0.29307107),
		lin("hp", "units.power.hp", 745.6998715822702),
		lin("kw", "units.power.kw", 1000.0),
		lin("mwatt", "units.power.mwatt", 1_000_000.0),
		lin("gw", "units.power.gw", 1_000_000_000.0),
	},
}

var Force = Category{
	Key: "force", TitleKey: "units.force.title",
	Units: []Unit{
		lin("mn", "units.force.mn", 0.001),
		lin("n", "units.force.n", 1.0),
		lin("lbf", "units.force.lbf", 4.4482216152605),
		lin("kgf", "units.force.kgf", 9.80665),
		lin("kn", "units.force.kn", 1000.0),
		lin("mnw", "units.force.mnw", 1_000_000.0),
	},
}

var Frequency = Category{
	Key: "frequency", TitleKey: "units.frequency.title",
	Units: []Unit{
		lin("rpm", "units.frequency.rpm", 1.0/60.0),
		lin("hz", "units.frequency.hz", 1.0),
		lin("khz", "units.frequency.khz", 1_000.0),
		lin("mhz", "units.frequency.mhz", 1_000_000.0),
		lin("ghz", "units.frequency.ghz", 1_000_000_000.0),
	},
}

var Angle = Category{
	Key: "angle", TitleKey: "units.angle.title",
	Units: []Unit{
		lin("grad", "units.angle.grad", math.Pi/200.0),
		lin("deg", "units.angle.deg", math.Pi/180.0),
		lin("rad", "units.angle.rad", 1.0),
		lin("turn", "units.angle.turn", 2.0*math.Pi),
	},
}

var Density = Category{
	Key: "density", TitleKey: "units.density.title",
	Units: []Unit{
		lin("kg_m3", "units.density.kg_m3", 1.0),
		lin("lb_ft3", "units.density.lb_ft3", 16.01846337396),
		lin("g_cm3", "units.density.g_cm3", 1000.0),
	},
}

var Flow = Category{
	Key: "flow", TitleKey: "units.flow.title",
	Units: []Unit{
		lin("ml_s", "units.flow.ml_s", 1e-6),
		lin("l_min", "units.flow.l_min", 1e-3/60.0),
		lin("gpm", "units.flow.gpm", 6.30901964e-5),
		lin("m3_h", "units.flow.m3_h", 1.0/3600.0),
		lin("l_s", "units.flow.l_s", 1e-3),
		lin("m3_s", "units.flow.m3_s", 1.0),
	},
}

var Acceleration = Category{
	Key: "acc", TitleKey: "units.acc.title",
	Units: []Unit{
		lin("gal", "units.acc.gal", 0.01),
		lin("ft_s2", "units.acc.ft_s2", 0.3048),
		lin("m_s2", "units.acc.m_s2", 1.0),
		lin("g", "units.acc.g", 9.80665),
	},
}

var Current = Category{
	Key: "current", TitleKey: "units.current.title",
	Units: []Unit{
		lin("ma", "units.current.ma", 0.001),
		lin("a", "units.current.a", 1.0),
		lin("ka", "units.current.ka", 1000.0),
	},
}

var Voltage = Category{
	Key: "voltage", TitleKey: "units.voltage.title",
	Units: []Unit{
		lin("mv", "units.voltage.mv", 0.001),
		lin("v", "units.voltage.v", 1.0),
		lin("kv", "units.voltage.kv", 1000.0),
	},
}

var Resistance = Category{
	Key: "resistance", TitleKey: "units.resistance.title",
	Units: []Unit{
		lin("mohm", "units.resistance.mohm", 0.001),
		lin("ohm", "units.resistance.ohm", 1.0),
		lin("kohm", "units.resistance.kohm", 1000.0),
		lin("mohm_big", "units.resistance.mohm_big", 1_000_000.0),
	},
}

var Illuminance = Category{
	Key: "illuminance", TitleKey: "units.illuminance.title",
	Units: []Unit{
		lin("lx", "units.illuminance.lx", 1.0),
		lin("fc", "units.illuminance.fc", 10.7639104167),
		lin("ph", "units.illuminance.ph", 10000.0),
	},
}

var Radiation = Category{
	Key: "radiation", TitleKey: "units.radiation.title",
	Units: []Unit{
		lin("rad", "units.radiation.rad", 0.01),
		lin("rem", "units.radiation.rem", 0.01),
		lin("gy", "units.radiation.gy", 1.0),
		lin("sv", "units.radiation.sv", 1.0),
	},
}

var Data = Category{
	Key: "data", TitleKey: "units.data.title",
	Units: []Unit{
		lin("bit", "units.data.bit", 1.0),
		lin("byte", "units.data.byte", 8.0),
		lin("kb", "units.data.kb", 8000.0),
		lin("kib", "units.data.kib", 8192.0),
		lin("mb", "units.data.mb", 8_000_000.0),
		lin("mib", "units.data.mib", 8_388_608.0),
		lin("gb", "units.data.gb", 8_000_000_000.0),
		lin("gib", "units.data.gib", 8_589_934_592.0),
	},
}

// Temperature: base unit is Kelvin. Every conversion in the original Python
// (temperature.py: _to_kelvin/_from_kelvin) is affine (K = value*A + B), so
// it fits the same Unit struct as every other category, coefficients solved
// from the original piecewise functions.
var Temperature = Category{
	Key: "temperature", TitleKey: "units.temperature.title",
	Units: []Unit{
		aff("f", "units.temperature.f", 5.0/9.0, 459.67*5.0/9.0),
		aff("r", "units.temperature.r", 5.0/9.0, 0),
		aff("de", "units.temperature.de", -2.0/3.0, 373.15),
		aff("c", "units.temperature.c", 1.0, 273.15),
		aff("k", "units.temperature.k", 1.0, 0),
		aff("re", "units.temperature.re", 1.25, 273.15),
		aff("ro", "units.temperature.ro", 40.0/21.0, 273.15-7.5*40.0/21.0),
		aff("n", "units.temperature.n", 100.0/33.0, 273.15),
	},
}

// All categories, in the display order used on the /units page.
var All = []Category{
	Length, Mass, Area, Volume, Speed, Time, Pressure, Energy, Power, Force,
	Frequency, Angle, Density, Flow, Acceleration, Current, Voltage,
	Resistance, Illuminance, Radiation, Data, Temperature,
}

var byKey = func() map[string]Category {
	m := make(map[string]Category, len(All))
	for _, c := range All {
		m[c.Key] = c
	}
	return m
}()

func ByKey(key string) (Category, bool) {
	c, ok := byKey[key]
	return c, ok
}
