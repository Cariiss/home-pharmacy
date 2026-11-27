"""Пользователь B не должен видеть и менять данные пользователя A."""
from .conftest import days, register_and_login


def test_users_are_isolated(client):
    a = register_and_login(client, "anna@test.ru")
    b = register_and_login(client, "boris@test.ru")
    assert client.get("/auth/me", headers=a).json()["email"] != client.get("/auth/me", headers=b).json()["email"]

    mid = client.post("/medicines", json={"name": "Парацетамол"}, headers=a).json()["id"]
    pid = client.post("/packages", json={"medicine_id": mid, "expiry_date": days(30), "quantity": 1}, headers=a).json()["id"]

    assert client.get("/medicines", headers=b).json() == []
    assert client.get("/packages", headers=b).json() == []
    assert client.get(f"/medicines/{mid}", headers=b).status_code == 404
    assert client.get(f"/packages/{pid}", headers=b).status_code == 404
    assert client.put(f"/medicines/{mid}", json={"name": "Взлом"}, headers=b).status_code == 404
    assert client.put(f"/packages/{pid}", json={"quantity": 99}, headers=b).status_code == 404
    assert client.delete(f"/packages/{pid}", headers=b).status_code == 404
    assert client.delete(f"/medicines/{mid}", headers=b).status_code == 404
    # B не может добавить упаковку к лекарству A
    r = client.post("/packages", json={"medicine_id": mid, "expiry_date": days(5), "quantity": 1}, headers=b)
    assert r.status_code == 404
    # у A всё на месте
    assert client.get(f"/packages/{pid}", headers=a).json()["quantity"] == 1


def _setup(client):
    a = register_and_login(client, "anna@test.ru")
    b = register_and_login(client, "boris@test.ru")
    mid = client.post("/medicines", json={"name": "Парацетамол"}, headers=a).json()["id"]
    pid = client.post("/packages", json={"medicine_id": mid, "expiry_date": days(10), "quantity": 2}, headers=a).json()["id"]
    return a, b, mid, pid


def test_foreign_and_missing_look_the_same(client):
    a, b, mid, pid = _setup(client)
    foreign = client.get(f"/medicines/{mid}", headers=b)
    missing = client.get("/medicines/999", headers=b)
    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json()
    foreign = client.get(f"/packages/{pid}", headers=b)
    missing = client.get("/packages/999", headers=b)
    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json()


def test_data_of_a_untouched_after_attacks(client):
    a, b, mid, pid = _setup(client)
    client.put(f"/medicines/{mid}", json={"name": "Взлом"}, headers=b)
    client.delete(f"/medicines/{mid}", headers=b)
    client.put(f"/packages/{pid}", json={"quantity": 99, "location": "чужая"}, headers=b)
    client.delete(f"/packages/{pid}", headers=b)
    assert client.get(f"/medicines/{mid}", headers=a).json()["name"] == "Парацетамол"
    pkg = client.get(f"/packages/{pid}", headers=a).json()
    assert pkg["quantity"] == 2 and pkg["location"] is None


def test_search_and_filter_isolated(client):
    a, b, mid, pid = _setup(client)
    assert client.get("/medicines?q=пара", headers=b).json() == []
    assert client.get("/packages?q=пара", headers=b).json() == []
    assert client.get("/packages?status=expiring", headers=b).json() == []
    # у B своё лекарство с тем же названием — каждый видит только своё
    client.post("/medicines", json={"name": "Парацетамол"}, headers=b)
    assert [m["id"] for m in client.get("/medicines", headers=a).json()] == [mid]
    assert len(client.get("/medicines", headers=b).json()) == 1


def test_settings_isolated(client):
    a, b, mid, pid = _setup(client)
    client.put("/settings", json={"threshold_days": 7, "notifications_enabled": False}, headers=b)
    assert client.get("/settings", headers=a).json() == {"threshold_days": 30, "notifications_enabled": True}
    # статус упаковки A считается по порогу A (30), а не B (7)
    assert client.get(f"/packages/{pid}", headers=a).json()["status"] == "expiring"

