# FEATURES

Список ключевых пользовательских сценариев Renderly и то, какие части системы их покрывают.

## 1. Аутентификация и роли
| Сценарий | UI | API |
| --- | --- | --- |
| Логин/регистрация | LoginView.vue, Pinia useAuthStore | POST /api/auth/login, POST /api/auth/register, GET /api/auth/me |
| Управление участниками проекта | ProjectSettings.vue | GET/POST/DELETE /api/projects/{id}/members |
| Роли Viewer/Editor | ProjectSettings.vue, middleware в Editor | проверка ProjectMember.role на API |  

## 2. Редактор и блоки
- **EditorView** — drag-and-drop холст, история изменений, inline-edit в Live Preview.
- **BlockPalette.vue** — каталог блоков (GET /api/catalog/blocks), вариации и комбо.
- **BlockForm.vue** — форма редактирования блока на основе JSON-schema из каталога.
- **LivePreview.vue** — синхронизированный iframe, inline-edit и drag подсветка.

## 3. Block Admin
| Возможность | Детали |
| --- | --- |
| CRUD определения блока | /admin/blocks, Pinia store BlockAdmin.ts, API /api/catalog/blocks |
| Custom template | Поля 	emplate_markup/	emplate_styles, helper-памятка, сохранение в API |
| Готовый пример | Сидовый блок Aurora-showcase показывает, как оформить hero-карточку |

## 4. Marketplace
- **MarketplaceView.vue** — фильтры, карточки шаблонов, предпросмотр.
- **TemplatePreview.vue** — запрашивает /api/templates/{id}/preview, отображает HTML.
- Публикация шаблона (POST /api/templates), импорт (POST /api/templates/{id}/import).
- Комментарии: GET/POST /api/templates/{id}/comments.

## 5. Share links и SSR-просмотр
| Сценарий | UI | API |
| --- | --- | --- |
| Создать share-link | ProjectSettings.vue | POST /api/projects/{id}/share-links |
| Просмотр / комментарии | ShareView.vue | GET /api/share-links/{token} + POST comments |
| Управление правами | переключатель allow_comments, срок действия | поля share link |

## 6. Публикация и домены
- ProjectSettings.vue → кнопка Publish → POST /api/publish.
- Результат: HTML+assets в MinIO (
ender_project_html), запись версии, статусы в таблице публикаций.
- Домены: вкладка Domains (GET/POST /api/projects/{id}/domains) + отдельный Domain Manager.

## 7. Аналитика и лиды
- **AnalyticsView.vue** — графики загрузок, таблицы заявок.
- API: GET /api/analytics/summary, GET /api/forms/submissions.

## 8. Как показать кастомный блок организаторам
1. Зайти админом на /admin/blocks, открыть блок Aurora-showcase.
2. Показать поля schema/default_config и секцию Custom template (Jinja + CSS).
3. Изменить, например, градиент/CTA → сохранить → открыть любой проект в редакторе.
4. Добавить блок Aurora Showcase из палитры и показать, как изменения из админки сразу видны в Live Preview и при экспорте HTML.

Эти сценарии покрывают основную демонстрацию платформы: от настройки блоков до публикации и обмена шаблонами.
