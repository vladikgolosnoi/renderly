# ARCHITECTURE

Документ описывает устройство Renderly: компоненты, хранилища данных, пайплайны публикации и marketplace.

## 1. Сервисы и окружение
`
┌──────────────┐      https       ┌────────────────────────┐
│ Vue SPA      ├──axios/json────▶│ FastAPI BFF            │
│ (apps/web)   │                  │ (apps/api)             │
└─────┬────────┘                  └─────┬─────────┬────────┘
      │ assets / export                 │         │
      │                                 │         │RQ (Redis)
      ▼                                 ▼         ▼
┌──────────────┐      S3 API     ┌──────────────┐ ┌──────────────┐
│ MinIO        │◀───────────────▶│ PostgreSQL   │ │ Worker (RQ)  │
│ pages/assets │                 │ state/config │ │ webhooks etc │
└──────────────┘                 └──────────────┘ └──────────────┘
                                         │
                                         │HTTP
                                         ▼
                                  ┌──────────────┐
                                  │Domain Manager│
                                  │+ nginx proxy │
                                  └──────────────┘
`
- **apps/web** — SPA на Vue 3 + Pinia. Основные страницы: Dashboard, Editor, ProjectSettings, Marketplace, BlockAdmin, ShareView. API-клиент (src/api/client.ts) автоматически прокидывает JWT.
- **apps/api** — FastAPI, SQLAlchemy 2.0, Alembic. Слои: pp/api/routes/*, pp/models/*, pp/schemas/*, pp/services/* (publisher, localization, block registry и т.д.).
- **infra** — docker-compose (api, web, db, redis, minio, worker, domain-manager, nginx proxy). По умолчанию VITE_API_URL=http://localhost:8000/api и BACKEND_CORS_ORIGINS=["http://localhost:5173"].

## 2. Данные
| Сущность | Назначение |
| --- | --- |
| Project | Заголовок, slug, описание, theme, settings (loc/locale, footer, etc.), список блоков (BlockInstance). |
| BlockDefinition | Каталог блоков. Поля schema, default_config, ui_meta, 	emplate_markup, 	emplate_styles. Управляется через Block Admin. |
| BlockInstance | Конкретный блок в проекте: definition_id, config, 	ranslations, order_index. |
| CommunityTemplate | Marketplace-шаблон: snapshot проекта + метаданные (owner, category, tags). |
| TemplateSnapshot (JSON) | Результат snapshot_project: project + locks. Каждый блок хранит definition_key, config, 	ranslations и сериализованное определение (schema + markup + styles). |
| ThemeTemplate, ProjectDomain, ProjectShareLink, FormSubmission, AuditEvent | дополнительные подсистемы (темы, домены, шаринг, формы, аудит). |

## 3. Рендеринг и предпросмотр
1. **Editor** использует LivePreview.vue, который собирает HTML через /api/projects/{id}/render (SSR) и позволяет inline-редактировать поля (Bridge-плагин добавляет data-field-path).
2. **Publisher** (pp/services/publisher.py) рендерит проект целиком (ender_project_html). Для кастомных блоков используется _render_dynamic_block: берётся Jinja-шаблон из BlockDefinition.template_markup, helper-обёртки (TemplateHelpers) проставляют data-field-* и плейсхолдеры ассетов. CSS (	emplate_styles) вставляется один раз на страницу.
3. **snapshot_project** сохраняет project metadata и список блоков с их определениями — это позволяет воспроизводить шаблоны на любой инсталляции.

## 4. Marketplace и шаблоны
- Публикация (POST /api/templates): берём проект → snapshot_project → сохраняем CommunityTemplate + thumbnail. Проект должен быть shared/public.
- Предпросмотр (GET /api/templates/{id}/preview):
  1. Достаём snapshot.
  2. Создаём PreviewProject (title/theme/settings + список PreviewBlock). Если Definition с таким ключом есть в БД — берём его; иначе строим inline-Definition из snapshot (schema + markup/styles).
  3. Рендерим через ender_project_html, возвращаем HTML. Endpoint добавляет заголовок Access-Control-Allow-Origin, поэтому TemplatePreview.vue может грузить его с любого фронтового домена.
- Импорт (POST /api/templates/{id}/import): создаётся новый Project из snapshot. Если Definition отсутствует, он создаётся/обновляется на основе данных шаблона.

## 5. Блоки и Block Admin
- Каталог (/api/catalog/blocks) отдаёт список BlockDefinition (schema + default_config + мета). SPA использует его в BlockPalette и BlockForm.
- Block Admin даёт CRUD плюс поля Custom template. После сохранения publisher/Live Preview автоматически используют новые шаблоны.
- Пример urora-showcase хранится в сид-данных (pps/api/app/seeds/block_definitions.json). Он демонстрирует использование badge/градиента/CTA и списка stats.

## 6. Публикация и домены
1. Пользователь запускает Publish → POST /api/publish. В фоне worker генерирует HTML, складывает его и ассеты в MinIO, обновляет запись проекта (версия, published_at).
2. Если подключены домены, Domain Manager проверяет CNAME, создаёт статическую директорию под домен и проксирует через nginx.
3. Для custom доменов в .env задаются CUSTOM_DOMAIN_*, PROJECT_SUBDOMAIN_ROOT и PORTAL_URL.

## 7. Share links и SSR
- Share link (ProjectShareLink) содержит токен, права (allow_comments), срок действия. Ссылки создаются в UI ProjectSettings.
- ShareView.vue рендерит проект через SSR endpoint /api/share-links/{token}: HTML тот же, что используется при публикации.
- Комментарии хранятся в ProjectShareComment и показываются в ShareView/Marketplace.

## 8. Фоновые задачи и вебхуки
- RQ-воркер (pps/api/app/worker.py) слушает очередь webhooks: публикация, рассылки, интеграции.
- Конфигурация очереди задаётся REDIS_URL. Старт воркера см. docker-compose (service worker).

## 9. Dev / Prod
- Dev: docker compose up --build, автоматическая перезагрузка uvicorn, Vite dev server на 5173 порту.
- Prod: используем infra/DEPLOYMENT.md — там описаны требования, переменные окружения, запуск миграций и сидов.

Этот документ отражает текущую архитектуру после добавления кастомных шаблонов в Block Admin и поддержки marketplace-предпросмотра.
