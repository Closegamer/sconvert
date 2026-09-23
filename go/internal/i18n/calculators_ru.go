package i18n

// New section (not present in the Python version): /calculators —
// price-per-kilogram and sports-betting arbitrage ("вилка"/surebet)
// calculators. Both are pure client-side arithmetic, no server round trip.
var calculatorsRU = Dict{
	"calculators.title":    "Калькуляторы",
	"calculators.subtitle": "Практические калькуляторы: цена за килограмм и вилки в ставках на спорт.",

	"calculators.kg.title":        "Цена за килограмм",
	"calculators.kg.subtitle":     "Введите цену товара за указанное количество грамм — калькулятор пересчитает цену за 1 кг.",
	"calculators.kg.price":        "Цена",
	"calculators.kg.grams":        "За сколько грамм",
	"calculators.kg.result":       "Цена за 1 кг",
	"calculators.kg.result_100g":  "Цена за 100 г",

	"calculators.surebet.title":         "Калькулятор вилок",
	"calculators.surebet.subtitle":      "Классический калькулятор вилок в ставках на спорт: коэффициенты и общая сумма ставки — на выходе размер ставки на каждый исход и гарантированная прибыль.",
	"calculators.surebet.two_outcomes":   "2 исхода",
	"calculators.surebet.three_outcomes": "3 исхода",
	"calculators.surebet.odds":           "Коэффициент",
	"calculators.surebet.outcome":        "Исход",
	"calculators.surebet.total_stake":    "Общая сумма ставки",
	"calculators.surebet.stake":          "Ставка",
	"calculators.surebet.margin":         "Вилочный процент",
	"calculators.surebet.profit":         "Гарантированная прибыль",
	"calculators.surebet.payout":         "Выплата при любом исходе",
	"calculators.surebet.arb_found":      "Вилка есть — гарантированная прибыль при любом исходе.",
	"calculators.surebet.arb_not_found":  "Вилки нет — сумма обратных коэффициентов больше 100%, гарантированной прибыли не будет.",
}
