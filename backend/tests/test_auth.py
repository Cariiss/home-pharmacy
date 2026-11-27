from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import JWT_SECRET

from .conftest import register_and_login


def test_register_ok(client):
    r = client.post("/auth/register", json={"email": "anna@test.ru", "password": "Secret123"})
    assert r.status_code == 201
    assert r.json()["email"] == "anna@test.ru"
    assert "password" not in r.text


def test_register_duplicate_email(client):
    client.post("/auth/register", json={"email": "anna@test.ru", "password": "Secret123"})
    r = client.post("/auth/register", json={"email": "anna@test.ru", "password": "Secret123"})
    assert r.status_code == 409


def test_email_case_insensitive(client):
    client.post("/auth/register", json={"email": "Anna@Test.ru", "password": "Secret123"})
    r = client.post("/auth/register", json={"email": "anna@test.ru", "password": "Secret123"})
    assert r.status_code == 409
    r = client.post("/auth/login", data={"username": "ANNA@test.ru", "password": "Secret123"})
    assert r.status_code == 200


def test_register_short_password(client):
    r = client.post("/auth/register", json={"email": "anna@test.ru", "password": "123"})
    assert r.status_code == 422


def test_register_bad_email(client):
    r = client.post("/auth/register", json={"email": "not-an-email", "password": "Secret123"})
    assert r.status_code == 422


def test_register_long_cyrillic_password(client):
    # 40 русских букв = 80 байт, больше лимита bcrypt в 72 байта
    r = client.post("/auth/register", json={"email": "anna@test.ru", "password": "п" * 40})
    assert r.status_code == 422


def test_password_stored_as_hash(client, engine):
    from sqlalchemy import text
    client.post("/auth/register", json={"email": "anna@test.ru", "password": "Secret123"})
    with engine.connect() as conn:
        stored = conn.execute(text("SELECT password_hash FROM users")).scalar_one()
    assert stored != "Secret123" and stored.startswith("$2b$")


def test_login_ok(client):
    client.post("/auth/register", json={"email": "anna@test.ru", "password": "Secret123"})
    r = client.post("/auth/login", data={"username": "anna@test.ru", "password": "Secret123"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "anna@test.ru", "password": "Secret123"})
    r = client.post("/auth/login", data={"username": "anna@test.ru", "password": "Wrong1234"})
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post("/auth/login", data={"username": "nobody@test.ru", "password": "Secret123"})
    assert r.status_code == 401


def test_me_with_token(client, auth):
    r = client.get("/auth/me", headers=auth)
    assert r.status_code == 200
    assert r.json()["email"] == "anna@test.ru"


def test_me_without_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_forged_token(client, auth):
    fake = jwt.encode({"sub": "1"}, "wrong-secret", algorithm="HS256")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {fake}"}).status_code == 401


def test_me_expired_token(client, auth):
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, JWT_SECRET, algorithm="HS256"
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_login_long_password_rejected(client):
    client.post("/auth/register", json={"email": "anna@test.ru", "password": "Secret123"})
    r = client.post("/auth/login", data={"username": "anna@test.ru", "password": "п" * 40})
    assert r.status_code == 401


# --- границы пароля (bcrypt: не больше 72 байт) ---

def test_password_72_bytes_cyrillic_ok(client):
    # 36 русских букв = ровно 72 байта
    pwd = "п" * 36
    assert client.post("/auth/register", json={"email": "anna@test.ru", "password": pwd}).status_code == 201
    assert client.post("/auth/login", data={"username": "anna@test.ru", "password": pwd}).status_code == 200


def test_password_length_boundaries(client):
    assert client.post("/auth/register", json={"email": "anna@test.ru", "password": "a" * 7}).status_code == 422
    assert client.post("/auth/register", json={"email": "anna@test.ru", "password": "a" * 8}).status_code == 201
    assert client.post("/auth/register", json={"email": "boris@test.ru", "password": "a" * 73}).status_code == 422


def test_register_missing_fields(client):
    assert client.post("/auth/register", json={"email": "anna@test.ru"}).status_code == 422
    assert client.post("/auth/register", json={"password": "Secret123"}).status_code == 422


def test_login_missing_fields(client):
    assert client.post("/auth/login", data={"username": "anna@test.ru"}).status_code == 422


def test_register_creates_default_settings(client):
    headers = register_and_login(client, "boris@test.ru")
    assert client.get("/settings", headers=headers).json() == {"threshold_days": 30, "notifications_enabled": True}


# --- 401 на всех защищённых адресах ---

PROTECTED = [
    ("get", "/auth/me", None),
    ("get", "/medicines", None),
    ("post", "/medicines", {"name": "Ибупрофен"}),
    ("get", "/medicines/1", None),
    ("put", "/medicines/1", {"name": "Ибупрофен"}),
    ("delete", "/medicines/1", None),
    ("get", "/packages", None),
    ("post", "/packages", {"medicine_id": 1, "expiry_date": "2030-01-01", "quantity": 1}),
    ("get", "/packages/1", None),
    ("put", "/packages/1", {"quantity": 2}),
    ("delete", "/packages/1", None),
    ("get", "/settings", None),
    ("put", "/settings", {"threshold_days": 7, "notifications_enabled": True}),
]


@pytest.mark.parametrize("method, url, body", PROTECTED)
def test_protected_without_token(client, method, url, body):
    kwargs = {"json": body} if body is not None else {}
    assert client.request(method, url, **kwargs).status_code == 401


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
