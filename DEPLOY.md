# Запуск «Домашняя аптека» (сервер)

1. Установить Docker Desktop.
2. Скопировать шаблон настроек и задать свои пароли:
   `cp .env.example .env`
3. Запустить: `docker compose up --build -d` (миграции Alembic применяются автоматически)
4. Проверить: `curl http://localhost:8000/health` → `{"status":"ok"}`
5. Документация API: http://localhost:8000/docs
6. Автотесты (на отдельной базе pharmacy_test): `docker compose run --rm api pytest -v`
7. Остановить: `docker compose down` (с удалением данных: `docker compose down -v`)
