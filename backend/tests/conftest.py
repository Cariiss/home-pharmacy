"""Тесты работают на отдельной базе pharmacy_test, рабочие данные не затрагиваются."""
from datetime import date, timedelta

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.config import DATABASE_URL
from app.database import get_db
from app.main import app

TEST_DB = "pharmacy_test"
test_url = make_url(DATABASE_URL).set(database=TEST_DB)


def alembic_config() -> Config:
    """Настройки Alembic для тестовой базы."""
    cfg = Config("alembic.ini")
    cfg.attributes["database_url"] = test_url.render_as_string(hide_password=False)
    return cfg


@pytest.fixture(scope="session")
def engine():
    admin = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB}"))
        conn.execute(text(f"CREATE DATABASE {TEST_DB}"))
    # схема строится теми же миграциями, что и рабочая база
    command.upgrade(alembic_config(), "head")
    eng = create_engine(test_url)
    yield eng
    eng.dispose()
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB}"))
    admin.dispose()


@pytest.fixture()
def client(engine):
    Session = sessionmaker(bind=engine, autoflush=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE users, medicines, packages, reminder_settings RESTART IDENTITY CASCADE"))


def register_and_login(client, email="anna@test.ru", password="Secret123"):
    client.post("/auth/register", json={"email": email, "password": password})
    r = client.post("/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def auth(client):
    return register_and_login(client)


@pytest.fixture()
def medicine(client, auth):
    r = client.post("/medicines", json={"name": "Парацетамол", "form": "таблетки", "dosage": "500 мг"}, headers=auth)
    return r.json()


def days(n: int) -> str:
    return (date.today() + timedelta(days=n)).isoformat()
