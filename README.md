# Renderly — no-code студия лендингов для EdTech и SMB

[![tests](https://github.com/your-org/renderly/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/renderly/actions/workflows/ci.yml)

Соберите и опубликуйте лендинг за минуты: drag-and-drop редактор на Vue 3, API на FastAPI, фоновые задачи на Redis/RQ, MinIO для ассетов и edge-прокси для кастомных доменов — всё в одном репозитории.

- 🚀 Публикация за 5 минут: пресеты блоков, темы, предпросмотр, мгновенный деплой.
- 🧠 Умный редактор: hero/feature/form, локализации, аналитика лидов.
- 🔗 Команда: роли, share-links с комментариями, аудит действий.
- 🌐 Кастомные домены: верификация CNAME, edge-прокси, CDN снапшоты в MinIO.
- 🛠 Готовая инфраструктура: Docker Compose, Nginx, Domain Manager, Makefile.

## Быстрые ссылки
- Web: http://localhost:5173
- API: http://localhost:8000/api/docs
- Proxy: http://localhost:8088
- Domain Manager: http://localhost:8085
- MinIO: http://localhost:9000 (console 9001)
- Health: `GET http://localhost:8000/api/healthz`

## Технологический стек
- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2, Alembic, Postgres 16, Redis + RQ, MinIO, Pydantic v2, JWT.
- **Frontend**: Vue 3 + `<script setup>`, Pinia, Vue Router, TypeScript, Vite, Vitest, ESLint.
- **Инфраструктура**: Docker Compose, Nginx edge-прокси, Certbot/Let's Encrypt, Domain Manager (FastAPI + dnspython), Makefile.

## Архитектура на ладони
```
[Vue SPA] --axios--> [FastAPI API] --SQLAlchemy--> [PostgreSQL]
   |                        | \
   |                        |  +-> [RQ Worker -> Redis]
   |                        |  +-> [MinIO buckets: renderly-pages / renderly-assets]
   |                        |  +-> [Domain Manager -> DNS]
   +--> Theme/Block stores  +--> Publisher -> HTML snapshot
```
Подробнее — в [`ARCHITECTURE.md`](ARCHITECTURE.md) и [`FEATURES.md`](FEATURES.md).

## Быстрый запуск через Docker (проверено)
**Зависимости**
- Docker Engine + Compose plugin. macOS без Docker Desktop: `brew install docker docker-compose colima` и добавьте в `~/.docker/config.json`:
  ```json
  { "cliPluginsExtraDirs": ["/opt/homebrew/lib/docker/cli-plugins"] }
  ```
- Colima как runtime: `colima start --cpu 4 --memory 8 --disk 60` (подстройте под машину).

**Шаги**
```bash
cp .env.example .env
cp .env infra/.env
cd infra
docker compose up -d --build
# дождитесь Up у api: docker compose ps
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seeds.seed_data
```

**Учётки из сидов**
- Пользователь: `demo@renderly.dev` / `renderly123`
- Админ: `admin@renderly.dev` / `renderlyAdmin123`

**Перезапуск/остановка**
- Перезапуск: `docker compose restart`
- Чистый старт: `docker compose down -v` (пересоздаст БД/volumes)

## Раздельный запуск сервисов
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

## Тесты и статический анализ
```bash
make lint         # ruff + eslint
make test-api     # pytest
make test-web     # vitest
```

## Troubleshooting
- **401 в UI при кликах**: залогиньтесь `demo@renderly.dev` / `renderly123`; токен сохранится в `localStorage`.
- **Redis порт занят**: остановите локальный Redis или измените `REDIS_PORT` и `REDIS_URL` в `.env` / `infra/.env`.
- **Postgres контейнер упал**: `docker compose down -v && docker compose up -d --build`.
- **apt-get update в api/worker**: образы учитывают `sources.list.d/debian.sources`; при медленных зеркалах задайте `DEBIAN_MIRROR` и `DEBIAN_SECURITY_MIRROR` в `.env` и пересоберите.
- **Windows line endings**: если `entrypoint.sh` не исполняется — `git checkout -- apps/api/entrypoint.sh`, убедитесь `core.autocrlf=false`.

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

## Документация
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — сервисы, модели, взаимодействия.
- [`FEATURES.md`](FEATURES.md) — пользовательские сценарии и модули.
- [`DEPLOYMENT.md`](DEPLOYMENT.md) — подготовка серверов, Docker, Nginx, Certbot.
- [`CRITERIA_TRACE.md`](CRITERIA_TRACE.md) — историческая трассировка требований.

## Поддержка
- Проблемы — issue или чат проекта.
- Продакшн-инциденты: `docker compose logs -f api web proxy`.
- Улучшения — PR с линтерами/тестами обязательны.
