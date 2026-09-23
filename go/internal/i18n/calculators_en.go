package i18n

// See calculators_ru.go — new section, not present in the Python version.
var calculatorsEN = Dict{
	"calculators.title":    "Calculators",
	"calculators.subtitle": "Practical calculators: price per kilogram and sports-betting arbitrage.",

	"calculators.kg.title":       "Price per kilogram",
	"calculators.kg.subtitle":    "Enter the item's price for a given number of grams — the calculator converts it to a price per 1 kg.",
	"calculators.kg.price":       "Price",
	"calculators.kg.grams":       "For how many grams",
	"calculators.kg.result":      "Price per 1 kg",
	"calculators.kg.result_100g": "Price per 100 g",

	"calculators.surebet.title":         "Surebet calculator",
	"calculators.surebet.subtitle":      "Classic sports-betting arbitrage (\"surebet\") calculator: enter the odds and total stake — get the stake for each outcome and the guaranteed profit.",
	"calculators.surebet.two_outcomes":   "2 outcomes",
	"calculators.surebet.three_outcomes": "3 outcomes",
	"calculators.surebet.odds":           "Odds",
	"calculators.surebet.outcome":        "Outcome",
	"calculators.surebet.total_stake":    "Total stake",
	"calculators.surebet.stake":          "Stake",
	"calculators.surebet.margin":         "Arbitrage percentage",
	"calculators.surebet.profit":         "Guaranteed profit",
	"calculators.surebet.payout":         "Payout regardless of outcome",
	"calculators.surebet.arb_found":      "Arbitrage found — guaranteed profit regardless of outcome.",
	"calculators.surebet.arb_not_found":  "No arbitrage — the sum of implied probabilities exceeds 100%, no guaranteed profit.",
}
