"""Проверки исправлений после ревью: миграции, русские тексты ошибок, поиск, пустые поля."""
from alembic import command

from tests.conftest import alembic_config, days


def test_migrations_match_models(engine):
    # падает, если таблицы или столбцы в models.py разошлись с миграциями
    command.check(alembic_config())


def test_no_token_message_in_russian(client):
    r = client.get("/auth/me")
    assert r.status_code == 401
    assert r.json()["detail"] == "Недействительный или просроченный токен"


def test_validation_messages_in_russian(client, auth):
    r = client.post("/auth/register", json={"email": "не-email"})
    assert r.status_code == 422
    assert r.json()["detail"] == "email: некорректное значение; password: обязательное поле"

    r = client.post("/medicines", json={"name": "   "}, headers=auth)
    assert r.json()["detail"] == "name: Название не может быть пустым"


def test_search_wildcards_are_literal(client, auth):
    for name in ("Парацетамол", "Витамин_C 100%"):
        med = client.post("/medicines", json={"name": name}, headers=auth).json()
        client.post("/packages", json={"medicine_id": med["id"], "expiry_date": days(30), "quantity": 1}, headers=auth)

    for q in ("%", "_"):
        meds = client.get("/medicines", params={"q": q}, headers=auth).json()
        assert [m["name"] for m in meds] == ["Витамин_C 100%"]
        packs = client.get("/packages", params={"q": q}, headers=auth).json()
        assert [p["medicine_name"] for p in packs] == ["Витамин_C 100%"]


def test_form_and_dosage_blank_become_null(client, auth):
    r = client.post("/medicines", json={"name": "Ибупрофен", "form": "  таблетки ", "dosage": "   "}, headers=auth)
    assert r.status_code == 201
    assert r.json()["form"] == "таблетки"
    assert r.json()["dosage"] is None
