# Каталог: микросервисный тестовый проект

Минимальный stateless-каталог товаров: Telegram-бот (aiogram 3), backend (FastAPI), Next.js-витрина (Telegram Mini App), PostgreSQL, MinIO.

> Код проекта написан с помощью ИИ-ассистентов (Cursor / Claude и т.п.), затем проверен и протестирован. Об этом я сообщаю прямо.

## Что делает

1. **Админ** (ID из `ADMIN_IDS`) отправляет боту одно сообщение: фото + подпись. Подпись - название товара. Бот скачивает фото в память, сервис загружает его в MinIO, запись сохраняется в PostgreSQL. Команда `/create` или текст «Создать товар» объясняет формат.
2. **Страница «Каталог»** (Next.js, App Router, TypeScript): заголовок «Каталог» и простой список «название + картинка», без CSS. Работает в браузере и внутри Telegram Mini App (подключён `telegram-web-app.js`).
3. **Любой не-админ** на `/start` или любое сообщение получает «У меня есть товар» и inline-кнопку WebApp, открывающую `WEBAPP_URL`.

## Архитектура

```
Telegram --webhook--> nginx --> backend (x2) --> PostgreSQL
Браузер / Mini App -> nginx --> frontend (x2) --(SSR fetch)--> backend
                           \--> backend /api/products/{id}/image --> MinIO (стрим)
```

```
backend/app/
  config.py        Pydantic Settings, всё из env
  db.py, models.py SQLAlchemy 2 (async, asyncpg)
  schemas.py       Pydantic-схемы ответа
  repositories/    доступ к БД
  services/        бизнес-логика (ProductService) и S3-хранилище
  routers/         HTTP: /health, /api/products, /bot/webhook/{secret}
  bot/             aiogram: handlers (общий код сервисов), polling для локальной разработки
  main.py          сборка приложения, lifespan, установка вебхука
backend/alembic/   миграция 0001 (таблица products)
frontend/          Next.js (standalone-сборка), /healthz
nginx/             балансировщик
```

Бот вызывает **тот же `ProductService`**, что и остальной backend (без внутреннего HTTP), поэтому логика создания товара одна.

## Запуск

```bash
cp .env.example .env     # заполнить BOT_TOKEN, ADMIN_IDS, WEBAPP_URL, WEBHOOK_BASE_URL, WEBHOOK_SECRET
make up                  # = docker compose up -d --build
```

Порядок старта: postgres, minio -> `minio-init` (создаёт бакет) и `migrate` (alembic upgrade head, одноразовая задача) -> backend x2 -> frontend x2 -> nginx. Каталог: http://localhost:8080, health: http://localhost:8080/health.

Тесты backend: `make test-backend`. Сборка фронтенда: `make build-frontend`.

## Вебхук (ngrok или домен)

Telegram требует HTTPS и публичный адрес.

- **ngrok:** `ngrok http 8080`, полученный `https://xxxx.ngrok-free.app` записать в `.env` как `WEBAPP_URL` и `WEBHOOK_BASE_URL`, затем `docker compose up -d`.
- **Домен:** TLS-терминация на внешнем прокси/балансировщике, который пробрасывает трафик на порт nginx; те же две переменные.

При старте каждая реплика backend вызывает `setWebhook` на `{WEBHOOK_BASE_URL}/bot/webhook/{WEBHOOK_SECRET}` с `secret_token`. Вызов идемпотентен, поэтому реплики не конфликтуют. Вручную:

```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook" -d "url=https://<домен>/bot/webhook/<WEBHOOK_SECRET>" -d "secret_token=<WEBHOOK_SECRET>"
```

URL Mini App для BotFather (необязательно, кнопка работает и без этого): `/newapp` или Menu Button -> `WEBAPP_URL`.

**Локальная разработка без туннеля:** `BOT_MODE=polling`, запустить `python -m app.bot.polling` (одна копия; в compose этот режим не используется).

## Stateless и отказоустойчивость

- Нет локальных файлов и состояния: изображения только в MinIO (бот держит фото в `BytesIO`), конфигурация только из env, FSM aiogram не используется (диалоги без состояния).
- Любая реплика обрабатывает любой запрос и любой webhook-апдейт; состояние только в PostgreSQL и MinIO.
- nginx балансирует между репликами через Docker DNS (перерезолв каждые 5 с) и делает `proxy_next_upstream` при ошибке реплики.
- `/health` (backend) и `/healthz` (frontend) используются в healthcheck'ах; `restart: unless-stopped`.
- Миграции вынесены в отдельную задачу `migrate`, реплики не мигрируют сами и не гоняются друг с другом.
- Порядок «сначала файл в MinIO, потом запись в БД»: при сбое остаётся максимум неиспользуемый объект, но не запись без картинки.
- Секрет вебхука проверяется в пути и в заголовке `X-Telegram-Bot-Api-Secret-Token`.

## Принятые решения и ограничения (честно)

- Картинки отдаются **через proxy-эндпоинт** `/api/products/{id}/image` со стримингом из MinIO, а не presigned URL: MinIO не нужно открывать наружу, Mini App работает через один домен.
- boto3 синхронный, вызовы обёрнуты в thread pool (`asyncio.to_thread`, `iterate_in_threadpool`). Для высокой нагрузки лучше aioboto3.
- Для фото из Telegram всегда сохраняется `image/jpeg` (Telegram пересжимает фото).
- Нет пагинации, удаления/редактирования товаров, авторизации Mini App через `initData` (не требовалось по заданию).
- Тесты используют SQLite (aiosqlite) и in-memory подмену MinIO; реальные Postgres/MinIO/Telegram в тестах не задействованы.
- Docker Compose и интеграция с настоящим Telegram в среде разработки автора на момент сдачи не прогонялись целиком: проверялись тесты, сборка фронтенда и миграция на SQLite. Перед использованием выполните `docker compose config` и `make up`.
