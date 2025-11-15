# Руководство по возможностям Renderly

Документ связывает пользовательские сценарии с конкретными UI‑компонентами и API‑эндпоинтами. Он пригодится при демонстрациях, тестировании и дальнейшей разработке.

## 1. Карта функциональных модулей

| Модуль / сценарий             | UI (Vue)                                                | API / сервисы                                      |
|------------------------------|---------------------------------------------------------|----------------------------------------------------|
| Аутентификация               | `LoginView.vue`, `useAuthStore`                         | `/api/auth/login`, `/api/users/me`                 |
| Дашборд проектов             | `DashboardView.vue`                                     | `/api/projects`, `/api/catalog/definitions`        |
| Drag‑and‑drop редактор       | `EditorView.vue`, `BlockPalette.vue`, `BlockForm.vue`   | `/api/projects/{id}/blocks`, `services/revision`   |
| Theme Designer               | `ThemeDesigner.vue`, `ThemeToggle.vue`                  | `/api/themes`, поле `project.theme`                |
| Настройки проекта            | `ProjectSettings.vue`                                   | `/api/projects/{id}`, `/project_members`, `/domains`, `/share-links` |
| Публикация / предпросмотр    | `LivePreview.vue`, `TemplatePreview.vue`                | `/api/publish/{id}`, `services/publisher.py`, MinIO |
| Marketplace шаблонов         | `MarketplaceView.vue`, `TemplatePreview.vue`            | `/api/templates`, `/api/projects/import`           |
| Assets / медиа               | `BlockForm.vue` (asset‑picker)                          | `/api/assets`, `services/assets.py`                |
| Формы и лиды                 | блок form, `AnalyticsView.vue`                          | `/api/forms/submit`, `/api/analytics/leads`, RQ worker |
| Share‑links и комментарии    | `ProjectSettings.vue`, `ShareView.vue`                  | `/api/projects/{id}/share-links`, `/api/shares/{token}` |
| Управление блоками (Admin)   | `BlockAdminView.vue`, `BlockPalette.vue`                | `/api/catalog/definitions`, `/api/templates`       |

## 2. Аутентификация и роли

- `LoginView.vue` использует `useAuthStore` → `auth.login(credentials)`; токен хранится в `localStorage`, на каждый запрос добавляется через axios interceptor.
- `/api/auth/login` выдаёт JWT + refresh (в базе пользователи создаются seed‑скриптом `python -m app.seeds.seed_data`).
- Роли:
  - **Owner** — создатель проекта (`Project.owner_id`), полный доступ.
  - **Editor** — через `ProjectMember.role`, может редактировать и публиковать.
  - **Viewer** — доступ только на чтение (например, для аналитики).

## 3. Управление блоками и редактор

1. При загрузке `EditorView`:
   - SPA делает `GET /api/projects/{id}` и `GET /api/catalog/definitions`.
   - `BlockPalette` строит карточки блоков на основе дефиниций (`key`, `thumbnail`, `default_config`).
2. Добавление блока:
   - `BlockPalette` → `projectStore.addBlock(definitionKey)` → `POST /projects/{id}/blocks`.
   - API создаёт `BlockInstance` со ссылкой на `BlockDefinition`.
3. Редактирование:
   - `BlockForm` генерирует форму по JSON‑схеме из `definition.fields`.
   - `PUT /projects/{id}/blocks/{blockId}` сохраняет `config` + `translations`.
   - `revision_service` пишет ревизию (`project_revision`) на ключевые изменения.
4. Предпросмотр:
   - `LivePreview` строит HTML прямо в браузере на основе Pinia‑состояния, но кнопку «Показать как HTML» вызывает `/api/projects/{id}/export/html`.

## 4. Темы и локализация

- Состояние темы (`project.theme`) содержит цвета, шрифты, spacing, фоновые градиенты. `ThemeDesigner.vue` редактирует объект и отправляет `PUT /api/projects/{id}`.
- Локали хранятся в `project.settings.locales` (default + список доступных). API нормализует коды (`services/localization.py`).
- Inline‑переводы блоков лежат в `BlockInstance.translations`. UI позволяет переключать вкладки локалей и редактировать поля отдельно.

## 5. Настройки проекта: участники, домены, share‑links

- **Участники** (`ProjectSettings.vue` → вкладка «Команда»):
  - `GET /projects/{id}/members` → список `ProjectMember`.
  - `POST`/`PUT`/`DELETE` для приглашений, смены ролей и удаления.
- **Домены**:
  - `POST /projects/{id}/domains` создаёт запись с `verification_token`.
  - `POST /projects/{id}/domains/{domain_id}/verify` вызывает сервис `domain_manager` (в контейнере) → проверка CNAME.
  - После успешной проверки HTML пишется в `custom-domains` и проксируется nginx (`infra/nginx/domains`).
- **Share‑links**:
  - `ProjectSettings` формирует ссылку `https://studio.../share/<token>`.
  - Публичная страница `ShareView.vue` читает `/api/shares/{token}` (SSR HTML + JSON проекта) и показывает комментарии.

## 6. Marketplace и шаблоны

- Компоненты: `MarketplaceView.vue`, `TemplatePreview.vue`.
- API:
  - `GET /api/templates` — список community шаблонов (карточка показывает owner, превью, блоки).
  - `POST /api/templates` — публикация текущего проекта в маркетплейс (использует `publisher.snapshot_project`).
  - `POST /api/projects/import` — разворачивает проект из JSON‑снапшота (обходит `block_definition` по `key`, создаёт `BlockInstance`).
- Шаблоны можно фильтровать/искать; хранение — таблица `community_template`.

## 7. Ассеты и галереи

- Любой блок, который требует загрузку файлов (галерея, hero‑изображения), вызывает `AssetUploader` внутри `BlockForm`.
- `/api/assets/upload` (multipart) проверяет размер, MIME, генерирует название (`services/assets.generate_object_name`) и сохраняет файл в MinIO (`renderly-assets`).
- Ответ содержит `url` (presigned) и `thumbnail_url` (если Pillow доступен).
- Для клиентских отображений к ассету добавляется подпись HMAC (`generate_asset_token`); API выдаёт файл через `GET /api/assets/{id}/content?token=...`.

## 8. Формы, webhook и аналитика

- Блок `form` хранит набор полей и опциональный `webhook_url`.
- Публичная форма отправляет POST на `/api/forms/submit` без авторизации (в payload передаются `project_id` и `block_id` — они валидируются).
- После сохранения submission ставится в очередь `webhooks`, worker (`services/forms.py`) пытается отправить webhook (в демо — заглушка), пишет статус `sent/failed`.
- `AnalyticsView.vue`:
  - `GET /api/analytics/leads?project_id=&date_from=&date_to=` → summary (количество заявок, количество форм, конверсия), timeseries, распределение статусов.
  - Графики рисуются кастомными Vue‑компонентами внутри `AnalyticsView.vue` (bar/line/цифровые карточки).

## 9. Публикация и кастомные домены

- Кнопка «Опубликовать» в `ProjectSettings` вызывает `POST /api/publish/{project_id}`.
- `services/publisher.render_project_html` собирает HTML: header, sequence блоков, footer. Для каждого блока выбирается конфиг с учётом локалей (`block_payload_for_locale`).
- Файл сохраняется в `renderly-pages/<project_id>/<version>.html` в MinIO, ссылка возвращается клиенту.
- Для проектов с кастомным доменом `services/custom_domains.persist_domain_html` пишет HTML на диск (`/var/renderly/domains/<domain>/index.html`), а контейнер `proxy` отдаёт его по запросам.

## 10. Администрирование блоков

- `BlockAdminView.vue` доступен только для `auth.isAdmin`.
- Позволяет:
  - создать новую дефиницию (`POST /api/catalog/definitions`) с полями, схемой форм, превью;
  - обновить существующую (`PUT /api/catalog/definitions/{id}`) — обновления подтягиваются на клиент при следующей загрузке;
  - выгрузить/импортировать набор блоков (JSON).
- Сервисы: `app/api/routes/catalog.py`, `app/models/block_definition.py`.

---

Если добавляете новый сценарий (например, интеграцию с CRM), фиксируйте его здесь: какая страница UI задействована, какие эндпоинты/сервисы нужно расширить и где лежит доменная логика.
