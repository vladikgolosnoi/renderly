# Renderly — no‑code студия лендингов для EdTech и SMB

[![tests](https://github.com/your-org/renderly/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/renderly/actions/workflows/ci.yml)

Renderly — это полнофункциональный конструктор одностраничных сайтов. В проекте объединены drag‑and‑drop редактор на Vue 3 + Pinia, API на FastAPI/SQLAlchemy, очередь фоновых заданий на Redis/RQ, файловое хранилище MinIO и edge‑прокси для кастомных доменов. Из коробки поддержаны пресеты блоков, общий предпросмотр, аналитика лидов, публикация на поддоменах и собственных доменах, а также каталог шаблонов для маркетплейса.

## Ключевые возможности

- **Редактор с живым предпросмотром**: `EditorView.vue`, `BlockPalette.vue`, `LivePreview.vue` и `BlockForm.vue` позволяют собирать страницу из готовых блоков hero/feature/grid/form, конфигурировать контент и переводы и моментально видеть результат.
- **Дизайнер тем**: `ThemeDesigner.vue` и API `/api/themes` позволяют менять типографику, цвета, spacing, сохранять пресеты и применять их к целым проектам.
- **Шеринг и совместная работа**: приватные/общие/публичные проекты, share‑links (`/api/projects/{id}/share-links`) с комментариями, аудит действий (`app/services/audit.py`) и ролевая модель (viewer/editor/owner).
- **Публикация и кастомные домены**: HTML собирается `services/publisher.py`, кладётся в MinIO и автоматически доступен на поддоменах `*.sites.<root>` или после верификации CNAME через сервис `apps/domain-manager`.
- **Формы и аналитика**: блок `form` отправляет данные на `/api/forms/submit`, submissions обрабатываются worker’ом (`services/forms.py`), а `/api/analytics/leads` и `AnalyticsView.vue` показывают конверсии и временные ряды.
- **Каталог шаблонов**: marketplace (`MarketplaceView.vue`, `/api/templates`) хранит снапшоты проектов, позволяет импортировать/публиковать шаблоны для команды.
- **Менеджер ассетов**: `assets.py` выдаёт presigned URL’ы, проверяет лимиты, генерирует thumbnail и отдаёт публичные ссылки через MinIO.

Подробное описание фич с указанием файлов см. в [`FEATURES.md`](FEATURES.md).

## Технологический стек

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2, Alembic, Postgres 16, Redis + RQ, MinIO SDK, Pydantic v2, JWT авторизация.
- **Frontend**: Vue 3 + `<script setup>`, Pinia, Vue Router, TypeScript, Vite, Vitest + Vue Test Utils, ESLint.
- **Инфраструктура**: Docker Compose, Nginx edge‑прокси, Certbot/Let’s Encrypt, отдельный Domain Manager (FastAPI + dnspython), bash‑скрипты и Makefile.

## Архитектура на ладони

```
[Vue SPA] --axios--> [FastAPI API] --SQLAlchemy--> [PostgreSQL]
   |                        | \
   |                        |  +-> [RQ Worker -> Redis]
   |                        |  +-> [MinIO buckets: renderly-pages / renderly-assets]
   |                        |  +-> [Domain Manager -> DNS]
   +--> Theme/Block stores  +--> Publisher -> HTML snapshot
```

Подробные диаграммы, модели данных и описание сервисов — в [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Структура репозитория

```
apps/
  api/             # FastAPI приложение, модели, сервисы, worker
  web/             # Vue 3 SPA, Pinia stores, Vitest
  domain-manager/  # микросервис проверки CNAME
infra/
  docker-compose.yml, env.* и конфиги Nginx
scripts/
  deploy.sh        # production-скрипт обновления
Makefile           # быстрые команды lint/test/compose
```

## Быстрый старт разработчика

### 1. Локальный запуск через Docker Compose

```bash
cp .env.example .env
# docker compose читает переменные из infra/.env — скопируйте туда тот же файл
cp .env infra/.env
cd infra
# (опционально) если разворачивали проект ранее и хотите чистый старт
# docker compose down -v
docker compose up -d --build
# дождитесь статуса Up у сервиса api (docker compose ps)
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seeds.seed_data
```

- Если `docker compose exec api ...` возвращает `service "api" is not running`, дайте контейнеру подняться и повторите команду.
- Если во время `docker compose up` появилось `container <project>-db-1 ... exited with code 1`, выполните `docker compose down -v` и повторите запуск — так база пересоберётся и миграции пройдут начисто.
- Если `renderly-redis-1` не стартует с ошибкой `port is already allocated`, на машине уже запущен Redis на 6379 — остановите его либо поменяйте порт в `.env` (`REDIS_PORT` + `REDIS_URL`).
- API: http://localhost:8000/api/docs  
- Web‑клиент: http://localhost:5173  
- Health‑check: `GET http://localhost:8000/api/healthz`

### 2. Раздельный запуск сервисов

```bash
# API
cd apps/api
pip install -r requirements-dev.txt
uvicorn app.main:app --reload

# Worker
RQ_WORKER=webhooks python app/worker.py

# Web
cd ../web
npm install
npm run dev
```

### 3. Тесты и статический анализ

```bash
make lint         # ruff + eslint
make test-api     # pytest
make test-web     # vitest
```

## Документация

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — глубоко про сервисы, модели и взаимодействия.
- [`FEATURES.md`](FEATURES.md) — пользовательские сценарии и модули продукта.
- [`DEPLOYMENT.md`](DEPLOYMENT.md) — подготовка серверов REG.RU, Docker, Nginx и Certbot.
- [`CRITERIA_TRACE.md`](CRITERIA_TRACE.md) — трассировка требований (оставлено для истории).

## Поддержка и обратная связь

- Любые проблемы — создавайте issue или пишите в чат проекта.
- Для продакшн‑инцидентов: подключайтесь к серверу, смотрите `docker compose logs -f api web proxy`.
- Улучшения и идеи приветствуются в виде PR (linters/tests обязательны).

Renderly стремится закрыть нишу «российского Tilda + Taplink» и уже готов к загрузке в репозиторий в актуальном состоянии.
