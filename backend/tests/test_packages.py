from .conftest import days


def add(client, auth, medicine_id, d, quantity=1, **extra):
    return client.post("/packages", json={"medicine_id": medicine_id, "expiry_date": days(d), "quantity": quantity, **extra}, headers=auth)


def test_create_package(client, auth, medicine):
    r = add(client, auth, medicine["id"], 100, quantity=2, location="кухня")
    assert r.status_code == 201
    body = r.json()
    assert body["medicine_name"] == "Парацетамол"
    assert body["quantity"] == 2 and body["location"] == "кухня"
    assert body["days_left"] == 100 and body["status"] == "ok"


def test_quantity_must_be_positive(client, auth, medicine):
    assert add(client, auth, medicine["id"], 10, quantity=0).status_code == 422
    assert add(client, auth, medicine["id"], 10, quantity=-1).status_code == 422


def test_bad_date_rejected(client, auth, medicine):
    r = client.post("/packages", json={"medicine_id": medicine["id"], "expiry_date": "2026-02-30", "quantity": 1}, headers=auth)
    assert r.status_code == 422


def test_unknown_medicine_rejected(client, auth):
    assert add(client, auth, 999, 10).status_code == 404


def test_two_packages_same_medicine(client, auth, medicine):
    add(client, auth, medicine["id"], 10)
    add(client, auth, medicine["id"], 200)
    assert len(client.get("/packages", headers=auth).json()) == 2


def test_list_sorted_by_expiry(client, auth, medicine):
    for d in [200, -5, 10]:
        add(client, auth, medicine["id"], d)
    got = [p["days_left"] for p in client.get("/packages", headers=auth).json()]
    assert got == [-5, 10, 200]


def test_update_package(client, auth, medicine):
    pid = add(client, auth, medicine["id"], 100).json()["id"]
    r = client.put(f"/packages/{pid}", json={"quantity": 5, "expiry_date": days(3)}, headers=auth)
    assert r.status_code == 200
    assert r.json()["quantity"] == 5 and r.json()["status"] == "expiring"
    assert client.get(f"/packages/{pid}", headers=auth).json()["quantity"] == 5


def test_update_cannot_clear_required_fields(client, auth, medicine):
    pid = add(client, auth, medicine["id"], 100).json()["id"]
    assert client.put(f"/packages/{pid}", json={"quantity": None}, headers=auth).status_code == 422
    assert client.put(f"/packages/{pid}", json={"expiry_date": None}, headers=auth).status_code == 422


def test_delete_package(client, auth, medicine):
    pid = add(client, auth, medicine["id"], 100).json()["id"]
    assert client.delete(f"/packages/{pid}", headers=auth).status_code == 204
    assert client.get(f"/packages/{pid}", headers=auth).status_code == 404
    assert client.get("/packages", headers=auth).json() == []
