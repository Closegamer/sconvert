# sConvert

Онлайн-сервис с конвертером единиц и валют, Bitcoin-инструментами, LaTeX-редактором и калькуляторами.
Сайт: **sconvert.ru**

---

## Стек

| Слой | Технология |
|---|---|
| Приложение | Go 1.25 · `net/http`, `html/template`, статика встроена через `embed` |
| Кэш | Redis 7 |
| База данных | PostgreSQL 16 (`pgx`) |
| Реверс-прокси и SSL | Nginx 1.27 · Let's Encrypt (certbot) |
| Контейнеризация | Docker · Docker Compose |
| CI/CD | GitHub Actions |

---

## Разделы сайта

| Адрес | Что там |
|---|---|
| `/` | Главная |
| `/units` | Конвертер единиц: 22 категории (длина, масса, давление, данные и т. д.). Порядок категорий зависит от популярности |
| `/currency` | Конвертер валют. Курсы с open.er-api.com, кэш в Redis на 1 час |
| `/btc` | Bitcoin-инструменты: seed-фраза ↔ приватный ключ ↔ публичный ключ ↔ адреса (P2PKH, P2SH-P2WPKH, P2WPKH), баланс и транзакции через blockstream.info, QR-код |
| `/latex`, `/latex_guide` | LaTeX-редактор с предпросмотром (KaTeX) и справочник |
| `/calculators` | Цена за килограмм и вилки в ставках. Считается в браузере |
| `/about`, `/privacy` | О проекте и политика конфиденциальности |
| `/claude-pod-klyuch-akula` | Личный туториал по MCP для Акулы. Статическая страница: раздаётся nginx, в меню и sitemap её нет, индексация запрещена. Старый адрес `/claude-pod-klyuch` перенаправляет сюда |

Курс BTC (USD и RUB) показывается виджетом вверху страницы и обновляется JS-поллингом `/api/btc/price` (CoinGecko, кэш 60 с).

Языки: русский (по умолчанию) и английский. Выбор хранится в cookie `sconvert_lang`, строки интерфейса лежат в `go/internal/i18n/`.

---

## Архитектура

```
Браузер → Nginx (SSL, robots.txt, sitemap.xml, статические страницы)
            ↓
          app-go :8080
            ├─ Redis    кэш курсов валют (1 ч), курса BTC (60 с), BTC-конвертаций (120 с)
            └─ Postgres анонимные счётчики использования (input_usage_stats)
```

**Счётчики.** Таблица `input_usage_stats` хранит по одной строке на пару «категория + единица/валюта/поле» и увеличивает `hit_count` на месте. IP-адресов и идентификаторов пользователей нет. Счётчики используются для сортировки категорий на `/units` и для панели статистики.

**Панель статистики** подключается, только если заданы `ADMIN_PATH`, `ADMIN_USER` и `ADMIN_PASSWORD`, и закрыта Basic Auth. Путь хранится только в `.env` на сервере, в репозиторий его не коммитим.

**Без Redis и Postgres приложение тоже работает:** кэш отключается, счётчики становятся no-op, категории идут в порядке по умолчанию.

**Логи посетителей не пишутся:** в nginx `access_log off`.

### Структура проекта

```
sconvert/
├── go/
│   ├── cmd/server/          # main.go, маршруты; static/ — CSS, JS, KaTeX
│   ├── internal/
│   │   ├── web/             # обработчики страниц и шаблоны (templates/)
│   │   ├── units/           # категории единиц и сортировка по популярности
│   │   ├── currency/        # курсы валют
│   │   ├── btc/             # ключи, адреса, курс BTC, кэш
│   │   ├── stats/           # счётчики использования
│   │   ├── i18n/            # строки ru/en
│   │   └── latexguide/      # справочник LaTeX (Markdown → HTML)
│   ├── db/sql/              # схема Postgres
│   └── Dockerfile
├── nginx/
│   ├── default.go.conf      # боевой конфиг
│   ├── default.paused.conf  # заглушка «сайт временно недоступен»
│   ├── paused.html
│   └── static/              # статические страницы вне приложения
├── docker-compose.yml           # nginx + certbot
├── docker-compose.go.yml        # Go-стек для локальной разработки
└── docker-compose.go.prod.yml   # Go-стек на сервере
```

---

## Запуск локально

С Docker (приложение, Redis и Postgres):

```bash
docker compose -f docker-compose.go.yml up -d --build
```

Сайт откроется на `http://localhost:8090`. Схема БД применится автоматически при первом запуске.

Без Docker (без кэша и счётчиков):

```bash
cd go
go run ./cmd/server     # http://localhost:8080
go test ./...
```

---

## Продакшн

Сервер: `/home/deploy/sconvert`, пользователь `deploy`. Там работают два набора контейнеров с общим именем проекта `sconvert`:

| Файл | Сервисы |
|---|---|
| `docker-compose.yml` | `nginx`, `certbot` |
| `docker-compose.go.prod.yml` | `app-go`, `db-go`, `redis-go` |

Переменные окружения описаны в `.env.example`. На сервере `NGINX_CONF=./nginx/default.go.conf`.

### Выкладка Go-приложения

Образ собирается не на сервере: сборка на сервере однажды заполнила кэшем весь диск (5,8 ГБ). Собираем локально и загружаем:

```bash
docker build -t sconvert-app-go:latest ./go
docker save sconvert-app-go:latest | gzip | ssh deploy@SERVER 'gunzip | docker load'
ssh deploy@SERVER 'cd ~/sconvert && git pull && docker compose -f docker-compose.go.prod.yml up -d app-go'
```

### Миграции БД

Файлы из `go/db/sql/` применяются автоматически только при создании пустой базы. Новую миграцию на работающей базе применяем вручную:

```bash
docker compose -f docker-compose.go.prod.yml exec -T db-go psql -U sconvert -d sconvert < go/db/sql/002_....sql
```

### Временно закрыть сайт

В `.env` на сервере поставить `NGINX_CONF=./nginx/default.paused.conf` и пересоздать nginx: `docker compose up -d nginx`. Все страницы будут вести на заглушку. Чтобы открыть сайт, вернуть `default.go.conf`.

### Статическая страница вне приложения

Положить HTML-файл в `nginx/static/` и добавить в `nginx/default.go.conf` правило:

```nginx
location = /имя-страницы {
    default_type text/html;
    charset utf-8;
    alias /usr/share/nginx/static/имя-страницы.html;
    add_header X-Robots-Tag "noindex, nofollow" always;  # если страница только по прямой ссылке
}
```

---

## CI/CD

**CI** (`ci.yml`) — на каждый push и PR в `main`:
- `actionlint` проверяет workflow-файлы
- `docker compose config` и сборка образа Go-приложения

**CD** (`deploy.yml`) — на push в `main` и вручную через Actions:
- SSH на сервер → `git reset --hard origin/main` → пересоздание nginx и certbot
- Go-приложение CD не выкатывает, см. «Выкладка Go-приложения»

Секреты в GitHub: `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_APP_PATH`.
