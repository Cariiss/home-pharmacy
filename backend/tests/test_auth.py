from datetime import datetime, timedelta, timezone

import jwt

from app.config import JWT_SECRET


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
