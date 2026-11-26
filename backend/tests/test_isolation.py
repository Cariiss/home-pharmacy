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
