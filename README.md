# Сервис обработки задач

Сервис на FastAPI: создаёт задачи через HTTP API, кладёт их в очередь Redis (Taskiq), а отдельный воркер обрабатывает задачи асинхронно и обновляет статус в PostgreSQL.

## Как запустить

### Docker (основной способ)

```bash
cp .env.example .env
docker compose up --build
```

Что поднимется:
- `postgres` — база данных.
- `redis` — очередь.
- `migrate` — отдельный контейнер, который применяет Alembic миграции.
- `web` — FastAPI приложение (`http://localhost:8000`).
- `worker` — Taskiq-воркер фоновой обработки.

`web` и `worker` стартуют только после успешного завершения `migrate`.

### Локально (без Docker)

```bash
uv sync --group dev
cp .env.example .env
set -a && source .env && set +a
alembic upgrade head
PYTHONPATH=src uv run uvicorn task_service.main:app --reload
```

Во втором терминале запустить воркер:

```bash
set -a && source .env && set +a
PYTHONPATH=src uv run taskiq worker task_service.presentation.taskiq.broker:broker
```

Проверка тестов:

```bash
PYTHONPATH=src uv run pytest -q
```

## Описание архитектуры

Проект разделён на слои: `presentation`, `app`, `domain`, `ports`, `adapters`: бизнес-логика не зависит от FastAPI, SQLAlchemy и Redis

В `domain` лежат сущности и правила предметной области (статусы задачи и расчёт результата). В `app` интеракторы: создание задачи, чтение списка/одной задачи и фоновая обработка. Транзакционный контракт задан протоколом `TransactionManager`, и `AsyncSession` подходит ему напрямую.

В `ports` описаны интерфейсы (`TaskRepository`, `TaskQueue`, `TransactionManager`), а в `adapters` их реализации: SQLAlchemy-репозиторий и адаптер очереди Taskiq. Для БД используется императивный маппинг SQLAlchemy, чтобы соблюдать ЧА.

В `presentation` два входа: HTTP API (`/tasks`) и Taskiq-слой воркера (`presentation/taskiq`). DI собран через Dishka: use-case’ы получают зависимости из контейнера, а конфиг читается через `pydantic-settings` с nested env (`APP__...`).

## Что улучшить в production

- Добавить ретраи с backoff и DLQ для задач, которые не удалось обработать.
- Добавить идемпотентность задач и защиту от дубликатов на уровне очереди/ключей.
- Подключить наблюдаемость: структурированные логи, метрики, tracing, health/readiness checks.
- Настроить безопасные политики подключения (TLS, ротация секретов, отдельные роли БД).
- Добавить нагрузочные тесты и контрактные тесты API/воркера.
- В CI запускать линтеры, типизацию, тесты и миграции на временной БД.