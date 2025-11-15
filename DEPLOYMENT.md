# Развёртывание Renderly

Документ описывает, как подготовить инфраструктуру, заполнить переменные окружения, запустить стек в Docker и сопровождать продакшн‑установку (REG.RU VPS, bare‑metal или любой Linux‑сервер).

## 1. Предварительные требования

| Компонент          | Требование / Пример                                |
|--------------------|----------------------------------------------------|
| ОС                 | Ubuntu 22.04 LTS (root или sudo‑права)             |
| DNS                | `studio.<domain>`, `api.<domain>`, `sites.<domain>`, `*.sites.<domain>` указывают на внешний IP сервера |
| Docker             | Docker Engine + compose‑plugin `v2`                |
| SSL                | Доступ к 80/443 портам для Certbot                 |
| E‑mail             | Системные уведомления (опционально)                |

Пример DNS‑зон для `vladikgolosnoi.ru`:

| Host                     | Type | Value            |
|--------------------------|------|------------------|
| `studio`                 | A    | `91.197.97.75`   |
| `api`                    | A    | `91.197.97.75`   |
| `sites`                  | A    | `91.197.97.75`   |
| `*.sites`                | A    | `91.197.97.75`   |
| пользовательские домены | CNAME → `sites.vladikgolosnoi.ru` (см. `CUSTOM_DOMAIN_CNAME_TARGET`) |

## 2. Настройка окружения

1. Установите системные пакеты:

   ```bash
   sudo apt update
   sudo apt install -y git docker.io docker-compose-plugin nginx certbot python3-certbot-nginx
   sudo usermod -aG docker $USER
   ```

2. Склонируйте репозиторий и переключитесь в каталог:

   ```bash
   git clone https://github.com/your-org/renderly.git /opt/renderly
   cd /opt/renderly
   ```

3. Создайте файл `infra/.env.production` на основе `infra/env.production.example` и заполните:

   | Переменная | Назначение |
   |------------|------------|
   | `POSTGRES_*` | учётные данные базы (желательно заменить на уникальные) |
   | `JWT_SECRET_KEY` | секрет подписи токенов |
   | `MINIO_ROOT_PASSWORD`, `MINIO_SECRET_KEY` | ключи доступа к MinIO |
   | `MINIO_PORT`, `MINIO_CONSOLE_PORT` | наружные порты MinIO (если нужно) |
   | `API_PORT`, `WEB_PORT` | локальные публикации контейнеров (используются Nginx‑ом) |
   | `CUSTOM_DOMAIN_*` | схема/домены для публикации проектов |
   | `DOMAIN_MANAGER_PORT` | порт микросервиса проверки доменов |
   | `PORTAL_URL`, `VITE_*` | ссылки, которые попадут во фронтенд |

4. Скопируйте `.env.example` → `.env` в корне, если хотите запускать compose из корня (dev‑режим).

## 3. Первый запуск в Docker

```bash
cd infra
docker compose --env-file .env.production up -d --build

# миграции и тестовые данные
docker compose --env-file .env.production exec api alembic upgrade head
docker compose --env-file .env.production exec api python -m app.seeds.seed_data
```

Сервисы внутри `infra/docker-compose.yml`:

- `api` — FastAPI с hot‑reload (можно отключать `--reload` в prod).
- `web` — собранный Vite билд, отдаётся nginx внутри контейнера.
- `db` — PostgreSQL 16 (volume `db-data`).
- `redis` — очередь для воркеров.
- `storage` — MinIO (данные в `minio-data`).
- `worker` — RQ обработчик форм.
- `domain-manager` — верификация CNAME.
- `proxy` — nginx, отдающий статическую выдачу для кастомных доменов.

## 4. Edge‑proxy и HTTPS

1. Скопируйте `infra/nginx/prod.renderly.conf` → `/etc/nginx/conf.d/renderly.conf`. Замените `server_name` на свои домены и, при необходимости, порты `proxy_pass` (по умолчанию 8080/8081/8088).
2. Проверьте конфиг и перезапустите Nginx:

   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. Выпустите сертификаты Let’s Encrypt:

   ```bash
   sudo certbot --nginx -d studio.example.ru -d api.example.ru -d sites.example.ru
   sudo certbot --nginx -d '*.sites.example.ru' --server https://acme-v02.api.letsencrypt.org/directory
   ```

Certbot автоматически пропишет `listen 443 ssl` и пути к `fullchain.pem/privkey.pem`.

## 5. Обновление и откат

Для повторных деплоев используйте скрипт `scripts/deploy.sh` (выполнять из репозитория на сервере):

```bash
./scripts/deploy.sh
```

Скрипт делает `git pull --ff-only`, пересобирает контейнеры с `infra/docker-compose.yml` и прогоняет `alembic upgrade head`.

Откат:

1. `git checkout <commit>` (например, тэг/хеш).
2. `./scripts/deploy.sh`.
3. При необходимости `alembic downgrade <revision>` и восстановление бэкапов БД.

## 6. Проверка после релиза

| Что проверить | Команда/URL |
|---------------|-------------|
| API живёт     | `curl https://api.example.ru/api/healthz` |
| Swagger       | `https://api.example.ru/api/docs` |
| SPA           | `https://studio.example.ru` (войти под демо-аккаунтом) |
| Публикация    | Создать share-link и открыть `https://share.example` либо любой `*.sites.example.ru` |
| Домены        | `docker compose logs proxy domain-manager` (нет ошибок) |
| Очереди       | `docker compose logs worker` (submission sent) |

## 7. Эксплуатация

- **Логи**: `cd infra && docker compose logs -f api web worker proxy`.
- **Резервное копирование**:
  - базы данных: `docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql`.
  - MinIO: `mc mirror minio/renderly-pages s3-backup/` (через `mc` или `aws s3`).
- **Обновление зависимостей**:
  - backend: обновить `requirements*.txt`, пересобрать контейнер `api/worker`.
  - frontend: npm deps → `docker compose build web`.
- **Очистка**:
  - удалить неиспользуемые тома: `docker volume prune`.
  - чистка share‑links/доменных записей — API имеет соответствующие DELETE‑эндпоинты.

## 8. Частые проблемы

| Симптом | Решение |
|---------|---------|
| `docker compose up` падает на `db` | Проверьте переменные `POSTGRES_*` и привилегии пользователя Docker |
| SPA не выходит в интернет | Убедитесь, что `VITE_API_URL` в `.env.production` указывает на публичный домен `https://api.../api` |
| Кастомный домен не верифицируется | Выполните `dig CNAME <domain>` и сравните с `CUSTOM_DOMAIN_CNAME_TARGET`; перезапустите `domain-manager` |
| Формы зависают в `queued` | Проверьте контейнер `worker`, наличие соединения с Redis (`redis://redis:6379/0`) и корректность `webhook_url` |
| Статические сайты отдают старую версию | Очистите локальный каталог `custom-domains` (`docker volume rm renderly_custom-domains`) и переиздайте проект |

---

После вычитки этого документа репозиторий готов к загрузке: в README/ARCHITECTURE/FEATURES указаны актуальные ссылки, а деплой описан шаг за шагом.
