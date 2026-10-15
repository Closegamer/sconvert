// Package i18n будет прямым портом app/lang/ru.py и en.py.
// Пока — минимальный набор ключей для скелета (Фаза 1).
package i18n

type Dict map[string]string

// Base keys ported verbatim from app/lang/ru.py / en.py (dotted naming,
// matching the original — kept 1:1 so both sources stay easy to diff).
var RU = Dict{
	"nav.home":       "sConvert",
	"nav.units":      "Единицы измерения",
	"nav.currency":   "Валюты",
	"nav.btc":        "Биткоин (BTC)",
	"nav.latex":      "Формулы (LaTeX)",
	"nav.calculators": "Калькуляторы",
	"nav.about":      "О проекте",
	"footer.privacy": "Политика конфиденциальности",
	"home.splash":    "проект sConvert",
	"home.favorites.title": "Избранные компоненты",
	"search.placeholder": "Поиск...",
	"universal_yes_word": "Да",
	"universal_no_word":  "Нет",
	"about.title":           "О проекте",
	"about.subtitle_before": "Данный проект представляет собой попытку собрать воедино разрозненные инструменты для конвертации данных, величин и других практических задач. Возможно, это сделает вашу жизнь немного комфортнее. Учитывая, что представленные здесь интсрументы могут быть очень полезны для вас, мы не будем возражать, если вы пришлете все ваши биткоины или их часть на наш адрес - ",
	"about.subtitle_after":  ". Заранее спасибо!",
	"privacy.title": "Политика конфиденциальности",
	"privacy.text": "Сайт <b>sConvert (sconvert.ru)</b> не собирает, не хранит и не передаёт третьим лицам персональные данные посетителей." +
		"<br><br>" +
		"<b>Никакой аналитики и слежки</b><br>" +
		"На сайте нет счётчиков посещаемости (Яндекс.Метрика, Google Analytics и т.п.), рекламных трекеров, вебвизора и сторонних скриптов. " +
		"Ваш браузер не обращается ни к каким сторонним сервисам — все страницы, скрипты и изображения загружаются только с sconvert.ru." +
		"<br><br>" +
		"<b>Журналы сервера</b><br>" +
		"Сервер не ведёт журналы посещений: IP-адреса, данные браузера и история просмотра страниц не записываются." +
		"<br><br>" +
		"<b>Cookie и настройки</b><br>" +
		"Сайт использует единственный cookie <code>sconvert_lang</code> — выбранный язык интерфейса. " +
		"Тема оформления и избранные поля хранятся в localStorage вашего браузера и никуда не отправляются. " +
		"Эти данные не позволяют вас идентифицировать." +
		"<br><br>" +
		"<b>Обезличенная статистика полей</b><br>" +
		"Сервер считает, как часто используется каждое поле конвертеров (например, «метры» или «USD»), чтобы показывать популярные поля выше. " +
		"Хранится только общий счётчик по каждому полю — без привязки к посетителю, IP-адресу или времени визита." +
		"<br><br>" +
		"<b>Инструменты раздела Биткоин</b><br>" +
		"Введённые ключи и адреса используются только для вычисления результата и не сохраняются: результат держится в оперативной памяти сервера не более 2 минут для ускорения повторного запроса. " +
		"Баланс и транзакции адреса запрашиваются сервером sconvert.ru у blockstream.info — ваш браузер и IP-адрес туда не передаются. " +
		"Тем не менее настоятельно не рекомендуется вводить реальные приватные ключи на этом или любом другом сайте.",
	"privacy.contact_button": "Связаться",
	"privacy.contact_copied": "Скопировано",
}

var EN = Dict{
	"nav.home":       "sConvert",
	"nav.units":      "Units",
	"nav.currency":   "Currency",
	"nav.btc":        "Bitcoin (BTC)",
	"nav.latex":      "LaTeX formulas",
	"nav.calculators": "Calculators",
	"nav.about":      "About",
	"footer.privacy": "Privacy policy",
	"home.splash":    "project sConvert",
	"home.favorites.title": "Favorite components",
	"search.placeholder": "Search...",
	"universal_yes_word": "Yes",
	"universal_no_word":  "No",
	"about.title":           "About",
	"about.subtitle_before": "This project is an attempt to bring together scattered tools for converting data, units, and other everyday tasks in one place. Hopefully, it makes your life a little more comfortable. Presented tools can be very usefull for you that's why we don't mind if you transfer all your bitcoins or just some of them to our address - ",
	"about.subtitle_after":  ". Thank you in advance!",
	"privacy.title": "Privacy Policy",
	"privacy.text": "<b>sConvert (sconvert.ru)</b> does not collect, store, or share any personal data of its visitors." +
		"<br><br>" +
		"<b>No analytics, no tracking</b><br>" +
		"The site has no visitor counters (Yandex Metrica, Google Analytics, etc.), no advertising trackers, no session recording, and no third-party scripts. " +
		"Your browser contacts no third-party services — all pages, scripts, and images are served from sconvert.ru only." +
		"<br><br>" +
		"<b>Server logs</b><br>" +
		"The server keeps no access logs: IP addresses, browser details, and page history are not recorded." +
		"<br><br>" +
		"<b>Cookies and settings</b><br>" +
		"The site uses a single cookie, <code>sconvert_lang</code>, which stores your chosen interface language. " +
		"Your color theme and favorite fields are kept in your browser's localStorage and are never sent anywhere. " +
		"None of this can identify you." +
		"<br><br>" +
		"<b>Anonymous field statistics</b><br>" +
		"The server counts how often each converter field is used (e.g. \"meters\" or \"USD\") to show popular fields first. " +
		"Only a total count per field is stored — not linked to any visitor, IP address, or visit time." +
		"<br><br>" +
		"<b>Bitcoin section</b><br>" +
		"Entered keys and addresses are used only to compute the result and are not saved: the result is held in server memory for at most 2 minutes to speed up a repeated request. " +
		"Address balances and transactions are fetched from blockstream.info by the sconvert.ru server — your browser and IP address are never sent there. " +
		"Even so, it is strongly advised not to enter real private keys on this or any other website.",
	"privacy.contact_button": "Contact",
	"privacy.contact_copied": "Copied",
}

func For(lang string) Dict {
	if lang == "en" {
		return EN
	}
	return RU
}

func init() {
	for k, v := range unitsRU {
		RU[k] = v
	}
	for k, v := range unitsEN {
		EN[k] = v
	}
	for k, v := range currencyRU {
		RU[k] = v
	}
	for k, v := range currencyEN {
		EN[k] = v
	}
	for k, v := range btcRU {
		RU[k] = v
	}
	for k, v := range btcEN {
		EN[k] = v
	}
	for k, v := range latexRU {
		RU[k] = v
	}
	for k, v := range latexEN {
		EN[k] = v
	}
	for k, v := range seoRU {
		RU[k] = v
	}
	for k, v := range seoEN {
		EN[k] = v
	}
	for k, v := range calculatorsRU {
		RU[k] = v
	}
	for k, v := range calculatorsEN {
		EN[k] = v
	}
}
