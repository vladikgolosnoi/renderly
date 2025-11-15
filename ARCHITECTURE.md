# Архитектура Renderly

Документ описывает то, как устроена платформа изнутри: из каких сервисов она состоит, где лежат критичные данные и какие потоки информации нужно учитывать при сопровождении и развитии.

## 1. Высокоуровневая схема

```
┌──────────────┐      https       ┌────────────────────────┐
│ Vue SPA (web)├──axios/json─────▶│ FastAPI BFF (apps/api) │
└─────┬────────┘                  └─────┬─────────┬────────┘
      │ assets/upload/export            │         │
      │                                 │         │
      │                       SQLAlchemy│         │RQ (Redis)
      │                                 │         │
      ▼                                 ▼         ▼
┌──────────────┐      S3 API     ┌──────────────┐ ┌──────────────┐
│ MinIO buckets│◀───────────────▶│ PostgreSQL   │ │ Worker (RQ)  │
│ pages/assets │                 │ (state)      │ │ forms/tasks  │
└──────────────┘                 └──────────────┘ └──────────────┘
                                         │
                                         │HTTP
                                         ▼
                                  ┌──────────────┐
                                  │Domain manager│
                                  │ + nginx edge │
                                  └──────────────┘
```

## 2. Веб‑клиент (`apps/web`)

- SPA на Vue 3 + TypeScript. Точка входа: `src/main.ts`, глобальная компоновка — `App.vue`.
- Pinia‑stores (`src/stores/*`):
  - `auth.ts` — управление токеном, профилем, ролью администратора.
  - `project.ts` — текущее дерево блоков, порядок, локализации, undo/redo история.
  - `blockAdmin.ts` — CRUD для библиотечных дефиниций.
  - `onboarding.ts`, `history.ts` — вспомогательные UI‑состояния.
- Основные вьюхи (`src/views`):
  - `DashboardView.vue` — список проектов, карточки, быстрые действия.
  - `EditorView.vue` — трёхпанельный редактор (палитра блоков, форма настроек, предпросмотр).
  - `ProjectSettings.vue` — домены, участники, публикации, share‑links.
  - `MarketplaceView.vue` — каталог шаблонов и импорт.
  - `AnalyticsView.vue` — графики и таблицы по лидам.
  - `LoginView.vue` + `ShareView.vue` — отдельные режимы (авторизация и публичный просмотр).
- Компоненты:
  - `BlockPalette.vue`, `BlockForm.vue`, `LivePreview.vue` — ядро редактора.
  - `TemplatePreview.vue`, `ThemeDesigner.vue`, `BlockAdminView.vue` — управление библиотекой.
  - `ThemeToggle.vue`, `AssetUploader`, `FormBuilder` (внутри `components/BlockForm.vue`) — вспомогательные элементы.
- Взаимодействие с API через `axios` экземпляр (`src/api/http.ts`), глобально прокинутые baseURL (`VITE_API_URL`). Ошибки централизованно перехватываются в interceptors (flash‑уведомления, 401 → logout).

## 3. API/Backend (`apps/api/app`)

### 3.1 Каркас

- `main.py` — создание приложения FastAPI, подключение CORS, регистрация роутеров и middleware логирования запросов.
- Конфигурация (`app/core/config.py`) на Pydantic Settings: Postgres, Redis, MinIO, параметры доменов, лимиты ассетов.
- Подсистемы:
  - `app/api/routes/*` — модули FastAPI, сгруппированные по контекстам (projects, analytics, forms, share_links, templates, publish, assets, themes, auth, users, audit, health).
  - `app/models/*` — SQLAlchemy 2.0 модели (Project, BlockDefinition/Instance, ThemeTemplate, ProjectMember, ShareLink, FormSubmission, Asset, AuditEvent и т.д.).
  - `app/schemas/*` — Pydantic DTO для валидации/ответов.
  - `app/services/*` — доменная логика: publisher (генерация HTML), access (RBAC), localization, audit, forms (enqueue), assets (MinIO), custom_domains, domain_manager.
  - `app/core/tasks.py` + `worker.py` — инициализация очереди RQ и запуск воркера.

### 3.2 Ключевые эндпоинты

- **Аутентификация (`auth.py`)**: выдача JWT (email+password), refresh, текущий пользователь.
- **Каталог блоков/тем (`catalog.py`, `themes.py`, `block_admin` внутри `projects.py`)**: CRUD блоков, дефолтные конфиги, предпросмотры.
- **Проекты (`projects.py`)**: CRUD проектов, операции с блоками, импорт/экспорт JSON/HTML, управление ревизиями (`services/revision_service.py`) и локалями.
- **Публикация (`publish.py`)**: сборка HTML (`render_project_html`), выгрузка в MinIO (`rendered_pages`), получение публичной ссылки и метаданных.
- **Share links (`share_links.py`)**: генерация токенов, публичные SSR ответы `/api/shares/{token}`, комментарии гостей.
- **Настройки/домены (`project_domains` внутри `projects.py`)**: выпуск и проверка токена CNAME, сохранение HTML в FS (`services/custom_domains.py`).
- **Формы и аналитика (`forms.py`, `analytics.py`)**: запись submissions, постановка в очередь `enqueue_submission`, статистика по проектам/датам/статусам.
- **Ассеты (`assets.py`, `assets_router.py`)**: presign URL, скачивание контента через защищённый proxy, миниатюры.
- **Marketplace (`templates.py`)**: публикация шаблонов в таблицу `community_template`, импорт в проект.

### 3.3 Доступы и аудит

- `services/access.py` — резолв проекта + роль (owner/editor/viewer) из `ProjectMember`.
- `services/audit.py` — запись JSON‑payload в `audit_event`, просмотр истории `/api/audit/project/{id}`.
- `ProjectVisibility` и share‑links позволяют публичный просмотр без авторизации (read‑only Pydantic модели).

## 4. Асинхронная обработка

- Очередь `webhooks` в Redis (`core/tasks.py`) обслуживается воркером `app/worker.py`.
- `services/forms.enqueue_submission` ставит задачу `process_submission`, которая:
  1. Помечает submission как `processing`, увеличивает счётчик попыток.
  2. Имитирует webhook (`_perform_webhook`) либо отправляет реальный POST (можно расширить).
  3. Логирует попытки в `form_webhook_log` (успех/ошибка).
- В воркере также можно триггерить другие задачи (например, offload публикации или генерацию превью) — очередь уже готова.

## 5. Хранилища и ключевые сущности

| Слой           | Сущности/файлы                                                | Назначение |
|----------------|---------------------------------------------------------------|------------|
| PostgreSQL     | `project`, `block_definition`, `block_instance`, `project_member`, `project_domain`, `project_share_link`, `project_share_comment`, `project_revision`, `theme_template`, `form_submission`, `form_webhook_log`, `asset`, `audit_event`, `community_template` | Состояние редактора, доступы, публикации, marketplace, аудит |
| MinIO bucket `renderly-pages` | HTML снапшоты (`services/publisher.py`, `publish.py`) | Хостинг опубликованных версий по поддоменам |
| MinIO bucket `renderly-assets` | Загруженные файлы пользователей (`services/assets.py`) | Используется блоками галереи/форм, выдаётся через presigned URL |
| Redis          | Очереди RQ, хэш заданий                                      | Асинхронная обработка, повторные попытки |
| Файловая система (`custom-domains` volume) | `services/custom_domains.py` | HTML для кастомных доменов, которые обслуживает `infra/nginx/domains` |

## 6. Критические пользовательские потоки

1. **Редактирование проекта**
   - SPA вызывает `/api/projects/{id}` и `/api/catalog/definitions`.
   - Изменения блоков → `PUT /projects/{id}/blocks/{block_id}`, ревизии пишутся через `revision_service`.
   - Настройки темы/локалей → `PUT /projects/{id}` с полями `theme`, `settings.locales`.

2. **Публикация**
   - `POST /api/publish/{project_id}` вызывает `snapshot_project`, рендерит HTML, кладёт файл в MinIO и отдаёт ссылку `/preview`.
   - Для кастомных доменов HTML складывается в локальную директорию (`/var/renderly/domains/<domain>/index.html`), nginx обслуживает статику.

3. **Совместный доступ**
   - Editor создаёт share‑link (`POST /projects/{id}/share-links`), получает токен.
   - Гость открывает `/share/:token` (SPA), который дергает `/api/shares/{token}`, получает HTML и JSON.
   - Комментарии пишутся анонимно (`POST /api/shares/{token}/comments`), сохраняются в Postgres.

4. **Заявка через форму**
   - Публичная страница отправляет POST на `/api/forms/submit` (без авторизации, но с `project_id`/`block_id`).
   - Submission попадает в таблицу и очередь. Worker эмулирует webhook, меняет статус на `sent/failed`.
   - Аналитика считывает агрегаты напрямую из `form_submission`.

5. **Кастомный домен**
   - Пользователь добавляет домен в `ProjectSettings.vue`, API создаёт запись `project_domain` с токеном.
   - Domain Manager (`apps/domain-manager`) через `/verify` проверяет CNAME.
   - После успеха публикуется HTML и nginx (контейнер `proxy`) начинает обслуживать домен.

## 7. Наблюдаемость, безопасность и качество

- **Логирование**: `app/core/logging.py` настраивает формат JSON + stdout. Middleware `request_logging_middleware` фиксирует латентность каждого запроса.
- **Health**: `/api/healthz` (DB ping + версия). Domain Manager — `/healthz`.
- **OpenAPI & docs**: `/api/docs` (Swagger) и `/api/openapi.json`.
- **Тесты**: `apps/api/tests` (pytest), `apps/web/src/views/__tests__` и `stores/__tests__` (Vitest).
- **CI**: `.github/workflows/ci.yml` (линтеры, pytest, vitest, docker build).
- **Безопасность**:
  - JWT + refresh, хранение токена в Pinia + localStorage.
  - Ролевая модель (`ProjectRole`) защищает роуты.
  - Пресайн ссылки на ассеты подписаны HMAC (`assets.generate_asset_token`), проверяются при скачивании.
  - Share‑links имеют срок действия и счётчик обращений.
  - Доменные операции вынесены в отдельный сервис без прямого доступа в основное API.

## 8. Связанные документы

- [`README.md`](README.md) — обзор и быстрый старт.
- [`FEATURES.md`](FEATURES.md) — пользовательские сценарии, соответствие UI ↔ API.
- [`DEPLOYMENT.md`](DEPLOYMENT.md) — как развернуть стек в production.

Если требуется доработать архитектуру (например, добавить фоновые билд‑пайплайны или метрики Prometheus) — внесите изменения сюда и ссылку в README.
