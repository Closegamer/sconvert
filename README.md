# sConvert

Онлайн-сервис с конвертером единиц измерения, Bitcoin-инструментами и LaTeX-редактором.
Сайт: **sconvert.ru**

---

## Стек

| Слой | Технология |
|---|---|
| Веб-интерфейс | Python · Streamlit ≥ 1.31 |
| API сервис | Python · FastAPI + Uvicorn |
| Кэш | Redis 7 |
| База данных | PostgreSQL 16 |
| Реверс-прокси | Nginx 1.27 |
| Контейнеризация | Docker · Docker Compose |
| CI/CD | GitHub Actions |

Зависимости приложения: `streamlit`, `matplotlib` (PNG-рендер формул), `ecdsa` (BTC-криптография), `psycopg` (PostgreSQL), `redis`, `streamlit-local-storage`.
Зависимости API: `fastapi`, `uvicorn[standard]`, `httpx`, `redis`.

---

## Разделы приложения

### Конвертер единиц
22 категории: длина, масса, площадь, объём, скорость, время, давление, энергия, мощность, сила, частота, угол, плотность, расход, ускорение, ток, напряжение, сопротивление, освещённость, радиация, данные.

Каждую категорию можно добавить в избранное — порядок избранного сохраняется в `localStorage` браузера между сессиями.

### Bitcoin-инструменты
Двунаправленная конвертация между всеми представлениями ключей и адресов:

```
Seed-фраза (12/24 слов)
       ↕
Приватный ключ  ─── DEC / HEX / WIF (compressed) / WIF (uncompressed)
       ↓
Публичный ключ  ─── compressed (33 байта) / uncompressed (65 байт)
       ↓
RIPEMD160 (hash160)
       ↓
Адреса  ─── P2PKH · P2SH-P2WPKH · P2WPKH (Bech32)
```

Дополнительно для адреса: баланс, история транзакций и UTXO (через blockstream.info), QR-код, тип и сеть адреса.

Визуализации: положение ключа на линии допустимых значений secp256k1, проекция публичного ключа на кривую y² = x³ + 7.

**Текущий курс BTC** отображается виджетом в верхней части страницы. Курс (USD и RUB) обновляется каждые 30 секунд через JS-поллинг к FastAPI-сервису без перезагрузки страницы.

### LaTeX-редактор
Предпросмотр формул через встроенный KaTeX-рендерер Streamlit. Поддерживает голый TeX и разделители `\(...\)`, `$...$`, `$$...$$`. Экспорт формулы в PNG через matplotlib (подмножество TeX — результат может отличаться от KaTeX).

---

## Архитектура

### Маршрутизация
Приложение — одностраничный Streamlit (`app/Home.py`) с маршрутизацией через `st.session_state.view`. Папка `app/pages/` пуста намеренно: Streamlit не генерирует боковую навигацию при пустой директории. URL-параметр `?view=units|btc|latex|latex_guide|about` задаёт раздел при открытии и сразу сбрасывается. Параметр `?policy=1` показывает оверлей политики конфиденциальности.

### Кэширование BTC-конвертаций (двухуровневое)
При каждом вводе строится `request_signature` — SHA-256 от нормализованного входного значения. Поиск результата идёт по уровням:

```
1. Redis  (ключ btc:conv:v1:{signature}, TTL 120 с)
       ↓ промах
2. PostgreSQL  (таблица btc_conversion_log)
       ↓ промах
3. Вычисление  →  запись в PostgreSQL  →  запись в Redis
```

### Курс BTC (FastAPI)
```
Браузер  →  /api/btc/price  →  Nginx  →  FastAPI
                                              ↓
                                         Redis (ключ btc:price:v1, TTL 60 с)
                                              ↓ промах
                                         CoinGecko API
```
FastAPI работает отдельным сервисом (`api/`). Nginx проксирует `/api/` на порт 8000, все остальные запросы — на Streamlit (порт 8501).

### Структура проекта
```
sconvert/
├── app/                        # Streamlit-приложение
│   ├── Home.py                 # Точка входа, маршрутизация, состояние
│   ├── components/             # UI-компоненты (конвертеры, BTC, LaTeX, прочее)
│   ├── views/                  # Страницы (home, units, btc, latex, about)
│   ├── layout/                 # Header и footer
│   ├── lang/                   # Локализация (ru.py, en.py)
│   ├── static/                 # CSS и JS (clipboard, SEO)
│   ├── content/                # Markdown-справочники (LaTeX guide)
│   └── pages/                  # Пуст — блокирует автонавигацию Streamlit
├── api/                        # FastAPI-сервис (курс BTC)
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── db/sql/                     # Миграции PostgreSQL
├── nginx/                      # Конфиги nginx (local / http / https+SSL)
├── Dockerfile                  # Образ Streamlit-приложения
├── docker-compose.yml
└── docker-compose.override.yml # Dev-оверрайд (hot reload, volume mounts)
```

### База данных
Таблица `btc_conversion_log` хранит снапшоты входных и выходных значений каждой уникальной конвертации. Уникальность — по `request_signature`. Индексы — по адресам и дате создания. Триггер поддерживает `updated_at` актуальным.

### Локализация
Два языка: русский (по умолчанию) и английский. Все строки интерфейса — в словарях `app/lang/ru.py` и `app/lang/en.py`. Переключение — в сайдбаре, выбранный язык хранится в `st.session_state.lang`.

---

## Запуск локально

**Требования:** Docker, Docker Compose.

```bash
cp .env.example .env
# Задать POSTGRES_PASSWORD в .env

docker compose up -d --build
```

Приложение доступно на `http://localhost` (через nginx).

При разработке `docker-compose.override.yml` подключает volume-маунты и включает `--reload` для FastAPI и `STREAMLIT_SERVER_RUN_ON_SAVE=true` для Streamlit — изменения подхватываются без пересборки образов.

### Миграции БД

```bash
docker compose exec db psql -U sconvert -d sconvert < db/sql/001_create_btc_conversion_log.sql
```

---

## CI/CD

**CI** (`ci.yml`) — запускается на каждый push и PR в `main`:
- `actionlint` — проверка workflow-файлов
- `docker compose build` — проверка сборки образов

**CD** (`deploy.yml`) — запускается на push в `main` и вручную через Actions:
- SSH-подключение к продакшн-серверу
- `git reset --hard origin/main` → `docker compose up -d --build --force-recreate`
- Применение миграций БД

Секреты в GitHub: `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_APP_PATH`.

### Nginx-конфиги

| Файл | Назначение |
|---|---|
| `nginx/default.local.conf` | Локальная разработка (HTTP, `server_name _`) |
| `nginx/default.http.conf` | Продакшн HTTP (sconvert.ru) |
| `nginx/default.conf` | Продакшн HTTPS + редирект HTTP→HTTPS |

Активный конфиг задаётся переменной `NGINX_CONF` в `.env` (по умолчанию `./nginx/default.local.conf`).
