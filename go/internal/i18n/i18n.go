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
	"privacy.text": "Сайт <b>sConvert (sconvert.ru)</b> использует счётчик <b>Яндекс.Метрика</b> для анализа посещаемости и улучшения качества сервиса." +
		"<br><br>" +
		"<b>Оператор персональных данных</b><br>" +
		"Оператором обработки персональных данных, собираемых через сайт sconvert.ru, является физическое лицо, подавшее уведомление об обработке персональных данных в Роскомнадзор в соответствии со статьёй 22 Федерального закона от 27.07.2006 № 152-ФЗ «О персональных данных» (уведомление № 100320759). Контакты оператора для вопросов, связанных с обработкой персональных данных, указаны в разделе «Связаться» ниже." +
		"<br><br>" +
		"<b>Что собирается</b><br>" +
		"Яндекс.Метрика автоматически фиксирует технические данные: IP-адрес (в обезличенном виде), тип браузера и устройства, страницы и разделы сайта, которые вы посещаете, время и продолжительность визита. " +
		"Эти данные используются исключительно в агрегированном виде для статистики." +
		"<br><br>" +
		"<b>Что не собирается</b><br>" +
		"Сайт не запрашивает и не хранит личные данные: имя, email, номер телефона, платёжные реквизиты и иную персональную информацию." +
		"<br><br>" +
		"<b>Файлы cookie</b><br>" +
		"Яндекс.Метрика устанавливает cookie-файлы для идентификации повторных визитов. " +
		"Вы можете отключить cookie в настройках браузера или установить расширение для блокировки трекеров — функциональность сайта от этого не пострадает." +
		"<br><br>" +
		"<b>Обработка данных Яндексом</b><br>" +
		"Собранные данные обрабатываются ООО «Яндекс» в соответствии с " +
		"<a href='https://yandex.ru/legal/confidential/' target='_blank' rel='noopener noreferrer'>политикой конфиденциальности Яндекса</a>." +
		"<br><br>" +
		"<b>Инструменты раздела Биткоин</b><br>" +
		"При работе с Bitcoin-инструментами введённые данные (ключи, адреса) могут кэшироваться на сервере в обезличенном виде для ускорения повторных запросов. " +
		"Настоятельно не рекомендуется вводить реальные приватные ключи на этом или любом другом сайте.",
	"privacy.contact_button": "Связаться",
	"privacy.contact_copied": "Скопировано",
}

var EN = Dict{
	"nav.home":       "sConvert",
	"nav.units":      "Units",
	"nav.currency":   "Currency",
	"nav.btc":        "Bitcoin (BTC)",
	"nav.latex":      "LaTeX formulas",
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
	"privacy.text": "<b>sConvert (sconvert.ru)</b> uses the <b>Yandex Metrica</b> analytics counter to understand site traffic and improve the service." +
		"<br><br>" +
		"<b>Personal Data Controller</b><br>" +
		"The personal data collected through sconvert.ru is processed by an individual who has submitted a personal data processing notification to Roskomnadzor (the Russian data protection authority) in accordance with Article 22 of Federal Law No. 152-FZ \"On Personal Data\" (notification No. 100320759). The controller's contact details for privacy-related enquiries are provided in the \"Contact\" section below." +
		"<br><br>" +
		"<b>What is collected</b><br>" +
		"Yandex Metrica automatically records technical data: IP address (anonymised), browser and device type, pages and sections you visit, time and duration of the visit. " +
		"This data is used exclusively in aggregate form for statistics." +
		"<br><br>" +
		"<b>What is not collected</b><br>" +
		"The site does not request or store personal details: name, email, phone number, payment information, or any other personally identifiable data." +
		"<br><br>" +
		"<b>Cookies</b><br>" +
		"Yandex Metrica sets cookies to recognise returning visitors. " +
		"You can disable cookies in your browser settings or install a tracker-blocking extension — the site's functionality is unaffected." +
		"<br><br>" +
		"<b>Data processing by Yandex</b><br>" +
		"Collected data is processed by Yandex LLC in accordance with the " +
		"<a href='https://yandex.com/legal/confidential/' target='_blank' rel='noopener noreferrer'>Yandex Privacy Policy</a>." +
		"<br><br>" +
		"<b>Bitcoin section</b><br>" +
		"When using the Bitcoin tools, entered data (keys, addresses) may be cached server-side in anonymised form to speed up repeated lookups. " +
		"It is strongly advised not to enter real private keys on this or any other website.",
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
}
