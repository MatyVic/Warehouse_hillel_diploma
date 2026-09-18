# 📦 Warehouse Service (ProjectB)

[![Coverage](https://img.shields.io/badge/coverage-88%25-brightgreen)]()
![Django Version](https://img.shields.io/badge/django-6.0-092E20?logo=django)
![Python Version](https://img.shields.io/badge/python-3.12-blue?logo=python)

Допоміжний мікросервіс складського обліку для книжкового магазину
([ProjectA — Bookstore](https://github.com/MatyVic/HillelDjangoHW)). Відповідає
за облік складів, книг і залишків, і обмінюється даними з ProjectA через REST
API.

## Архітектура

\`\`\`mermaid
flowchart LR
    subgraph ProjectA["ProjectA — Bookstore (:8000)"]
        A_admin[Django Admin]
        A_shop[shop app]
        A_signal[post_save signal]
        A_task1[Celery: sync_stock_quantities]
        A_success[order: success_handler]
    end

    subgraph ProjectB["ProjectB — Warehouse (:8001)"]
        B_admin[Django Admin]
        B_signal[post_save signal]
        B_task[Celery: sync_book_with_shop]
        B_api[DRF API: books / stock]
    end

    B_admin -->|"нова книга"| B_signal --> B_task
    B_task -->|"POST /api/v1/books/sync/"| A_shop
    A_signal --> A_task1
    A_task1 -->|"GET /api/v1/stock/availability/?isbn=..."| B_api
    A_success -->|"POST /api/v1/stock/deduct/"| B_api
    B_api --> DB_B[(PostgreSQL)]
    A_shop --> DB_A[(PostgreSQL)]
\`\`\`

**Три напрямки міжсервісної комунікації:**

| Напрямок | Тригер | Що відбувається |
|---|---|---|
| ProjectB → ProjectA | Нова книга створена на складі | Сигнал ставить Celery-таск у чергу → `POST /api/v1/books/sync/` у ProjectA → там створюється чернетка товару (`price=0`, `amount=0`, `available=False`) |
| ProjectA ← ProjectB | Періодичний Celery Beat таск | ProjectA питає `GET /api/v1/stock/availability/?isbn=...` для кожної синхронізованої книги й оновлює `amount` |
| ProjectA → ProjectB | Успішна оплата замовлення (Stripe) | `POST /api/v1/stock/deduct/` списує продану кількість зі складу |

Усі виклики обгорнуті в `try/except` з логуванням і retry на мережеві збої
(`requests.exceptions.Timeout`, `ConnectionError`); 4xx-помилки не ретраяться.

## Технології

Django 6.0 · Django REST Framework · PostgreSQL · Redis (cache + Celery
broker) · Celery + Celery Beat (`django_celery_beat`, `DatabaseScheduler`) ·
JWT (`djangorestframework-simplejwt`) · drf-spectacular (Swagger/Redoc) ·
i18n (uk/en) · pytest + pytest-django + pytest-cov · Docker Compose · Sentry

## Основні застосунки

- **`warehouse`** — моделі `Warehouse`/`Book`/`Stock`, HTML-адмінка складу
  (список складів, перегляд залишків, експорт CSV), автогенерація ISBN-13 для
  книг.
- **`warehouse_api`** — DRF API: `BookViewSet`, `StockViewSet` + кастомні
  action'и `availability` (перевірка наявності за ISBN) і `deduct`
  (атомарне списання, стійке до паралельних запитів через
  `select_for_update`).
- **`user_management`** — Custom User Model, реєстрація/логін/логаут.

## API

Повна інтерактивна документація — Swagger UI: `http://localhost:8001/api/v1/docs/`
(Redoc: `/api/v1/redoc/`, OpenAPI schema: `/api/v1/schema/`).

Ключові ендпоінти:

| Метод | URL | Опис |
|---|---|---|
| `GET/POST` | `/api/v1/books/` | Список книг / створення (тільки адмін) |
| `GET/POST` | `/api/v1/stock/` | Список залишків / створення (тільки адмін) |
| `GET` | `/api/v1/stock/availability/?isbn=...` | Сумарна кількість книги по всіх складах |
| `POST` | `/api/v1/stock/deduct/` | Списати кількість (`{"isbn": "...", "quantity": N}`) |
| `POST` | `/api/v1/token/` | Отримати JWT-пару |
| `GET` | `/health/` | Перевірка стану БД і кешу |

## Запуск

### 1. Клонувати і налаштувати оточення

\`\`\`bash
git clone https://github.com/MatyVic/Warehouse_hillel_diploma.git
cd Warehouse_hillel_diploma
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
\`\`\`

Створіть `.env_local` (для локального запуску Django) і `.env_docker` (для
контейнерів `celery`/`celery-beat`) — приклад:

**`.env_local`**
\`\`\`
DJANGO_SECRET_KEY=...
DB_HOST=localhost
DB_PORT=5433
DB_NAME=db
DB_USER=my_user
DB_PASSWORD=my_secretpass_word
REDIS_HOST=localhost
REDIS_PORT=6380
CELERY_BROKER_URL=redis://localhost:6380/0
SHOP_SERVICE_URL=http://localhost:8000
SENTRY_DSN=...
\`\`\`

**`.env_docker`**
\`\`\`
DB_HOST=db
DB_PORT=5432
REDIS_HOST=redis_cache
CELERY_BROKER_URL=redis://redis_cache:6379/0
SHOP_SERVICE_URL=http://host.docker.internal:8000
SENTRY_DSN=...
\`\`\`

> `SHOP_SERVICE_URL` вказує на ProjectA. Якщо ProjectA теж запущений локально
> поза Docker — з середини контейнера використовуйте `host.docker.internal`,
> а не `localhost`.

### 2. Підняти інфраструктуру (БД, Redis, Celery — у Docker)

\`\`\`bash
docker-compose up -d db redis_cache celery celery-beat
\`\`\`

### 3. Мігрувати БД і запустити Django локально

\`\`\`bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8001
\`\`\`

### 4. Зареєструвати періодичні таски (один раз)

\`\`\`bash
python manage.py setup_cleanup_task
\`\`\`

### 5. Локалізація (якщо змінювали тексти)

\`\`\`bash
python manage.py makemessages -l uk
python manage.py compilemessages
\`\`\`

## Тести

\`\`\`bash
python -m pytest -o python_files="tests.py test_*.py" \\
  --cov=warehouse --cov=warehouse_api --cov=user_management \\
  --cov-report=term-missing
\`\`\`

Поточне покриття: **88%** , 41 тест — unit-тести на
моделі, integration-тести на CBV, API-тести на весь DRF-шар включно з
`availability`/`deduct`.

## Пов'язаний проєкт

[ProjectA — Bookstore (HillelDjangoHW)](https://github.com/MatyVic/HillelDjangoHW)
— основний книжковий магазин, з яким цей сервіс обмінюється даними.