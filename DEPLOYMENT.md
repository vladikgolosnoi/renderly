# DEPLOYMENT

Инструкция описывает, как поднять Renderly на любом VPS (Ubuntu 22.04). Все команды выполняются от пользователя с правами sudo.

---
## 1. Требования к окружению
| Компонент | Значение |
| --- | --- |
| OS | Ubuntu 22.04 LTS |
| RAM | ≥ 4 GB |
| Диск | ≥ 40 GB |
| DNS | studio.<domain>, api.<domain>, sites.<domain>, *.sites.<domain> указывают на один IP |
| Порты | 80/443 снаружи, внутри docker использует 3000 (web), 8000 (api) |

---
## 2. Базовая настройка сервера
`bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin nginx certbot python3-certbot-nginx
sudo usermod -aG docker 
`
Перелогиньтесь, затем клонируйте проект:
`bash
sudo mkdir -p /opt/renderly && sudo chown  /opt/renderly
cd /opt/renderly
git clone https://github.com/your-org/renderly.git .
`

---
## 3. Настройка конфигов
1. Скопируйте infra/env.production.example → infra/.env.production и заполните:
   - POSTGRES_*, REDIS_URL, MINIO_* — пароли и адреса сервисов.
   - JWT_SECRET_KEY, PORTAL_URL, VITE_API_URL.
   - CUSTOM_DOMAIN_* — параметры менеджера доменов.
2. При необходимости создайте .env в корне (dev overrides).

---
## 4. Запуск docker-compose
`bash
cd infra
docker compose --env-file .env.production up -d --build
`
Контейнеры: api, web, worker, postgres, 
edis, minio, 
ginx-proxy, domain-manager.
Проверка:
`bash
docker compose ps
docker compose logs -f api
`

---
## 5. Миграции и сиды
После первого запуска (и при обновлениях схемы) выполните:
`bash
# миграции
docker compose exec api alembic upgrade head
# сиды (создаёт дефолтные блоки, в т.ч. aurora-showcase)
docker compose exec api python -m app.seeds.seed_data
`
> Без сидов Block Admin не увидит новых блоков и примеров для демо.

---
## 6. HTTPS и nginx
1. Настройте nginx как прокси (пример в infra/nginx/prod.renderly.conf).
2. Выпустите сертификаты:
`bash
sudo certbot --nginx -d studio.<domain> -d api.<domain> -d sites.<domain> -d *.sites.<domain>
`
3. Перезапустите nginx: sudo systemctl reload nginx.

---
## 7. Резервные копии
- **PostgreSQL**: docker compose exec db pg_dump -U   > backup.sql.
- **MinIO**: mc mirror minio/renderly-pages s3://renderly-backup/pages.
- **.env/.certs**: храните в менеджере секретов.

---
## 8. Обновления
`bash
cd /opt/renderly
git pull
cd infra
docker compose pull
docker compose up -d --build
# обязательные шаги
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seeds.seed_data
`
Если обновляли блоки в Block Admin (markup/styles), они сохраняются в базе — бэкап БД обязателен перед релизами.

---
## 9. Отладка
| Симптом | Действие |
| --- | --- |
| API не стартует | docker compose logs api, проверьте Alembic upgrade и .env |
| SPA не видит API | убедитесь, что VITE_API_URL указывает на https://api.<domain>/api |
| Нет блоков в Block Admin | выполните python -m app.seeds.seed_data и перезагрузите страницу |
| Публикация висит в очереди | docker compose logs worker, проверьте Redis и webhooks |

---
## 10. Что показать организаторам
1. Зайдите админом на /admin/blocks.
2. Откройте блок **aurora-showcase** → измените текст/градиент → сохраните.
3. Откройте проект в редакторе, добавьте блок из палитры и покажите живой предпросмотр и inline-редактирование.
4. Экспортируйте HTML (/api/projects/{id}/export/html) или поделитесь через share-link.

Такой сценарий демонстрирует новую возможность — создание и публикацию шаблонов через Block Admin без изменения кода.
