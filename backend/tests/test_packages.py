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


def test_create_package_missing_fields(client, auth, medicine):
    assert client.post("/packages", json={"medicine_id": medicine["id"], "quantity": 1}, headers=auth).status_code == 422
    assert client.post("/packages", json={"medicine_id": medicine["id"], "expiry_date": days(10)}, headers=auth).status_code == 422
    assert client.post("/packages", json={"expiry_date": days(10), "quantity": 1}, headers=auth).status_code == 422


def test_location_too_long(client, auth, medicine):
    assert add(client, auth, medicine["id"], 10, location="ш" * 101).status_code == 422


def test_quantity_too_large(client, auth, medicine):
    # без ограничения большое число не помещалось в столбец INTEGER и сервер отвечал 500
    assert add(client, auth, medicine["id"], 10, quantity=10001).status_code == 422


def test_partial_update_only_location(client, auth, medicine):
    pid = add(client, auth, medicine["id"], 100, quantity=3, location="кухня").json()["id"]
    r = client.put(f"/packages/{pid}", json={"location": "спальня"}, headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert body["location"] == "спальня"
    assert body["quantity"] == 3 and body["expiry_date"] == days(100)


def test_partial_update_empty_body(client, auth, medicine):
    created = add(client, auth, medicine["id"], 100, quantity=3, location="кухня").json()
    r = client.put(f"/packages/{created['id']}", json={}, headers=auth)
    assert r.status_code == 200 and r.json() == created


def test_update_location_can_be_cleared(client, auth, medicine):
    pid = add(client, auth, medicine["id"], 100, location="кухня").json()["id"]
    r = client.put(f"/packages/{pid}", json={"location": None}, headers=auth)
    assert r.status_code == 200 and r.json()["location"] is None


def test_update_invalid_values(client, auth, medicine):
    pid = add(client, auth, medicine["id"], 100, quantity=3).json()["id"]
    assert client.put(f"/packages/{pid}", json={"quantity": 0}, headers=auth).status_code == 422
    assert client.put(f"/packages/{pid}", json={"expiry_date": "2026-13-01"}, headers=auth).status_code == 422
    assert client.get(f"/packages/{pid}", headers=auth).json()["quantity"] == 3


def test_update_null_does_not_change_record(client, auth, medicine):
    pid = add(client, auth, medicine["id"], 100, quantity=3).json()["id"]
    client.put(f"/packages/{pid}", json={"quantity": None, "location": "кухня"}, headers=auth)
    body = client.get(f"/packages/{pid}", headers=auth).json()
    assert body["quantity"] == 3 and body["location"] is None


def test_missing_package_404(client, auth):
    assert client.get("/packages/999", headers=auth).status_code == 404
    assert client.put("/packages/999", json={"quantity": 2}, headers=auth).status_code == 404
    assert client.delete("/packages/999", headers=auth).status_code == 404


def test_invalid_status_filter(client, auth):
    assert client.get("/packages?status=bad", headers=auth).status_code == 422


def test_filter_and_search_combined_keep_order(client, auth, medicine):
    other = client.post("/medicines", json={"name": "Ибупрофен"}, headers=auth).json()
    for mid, d in [(medicine["id"], 3), (other["id"], 20), (other["id"], 2), (other["id"], 200)]:
        add(client, auth, mid, d)
    got = client.get("/packages?status=expiring&q=ИБУ", headers=auth).json()
    assert [(p["medicine_name"], p["days_left"]) for p in got] == [("Ибупрофен", 2), ("Ибупрофен", 20)]
    assert client.get("/packages?q=аспирин", headers=auth).json() == []


def test_sort_after_update(client, auth, medicine):
    first = add(client, auth, medicine["id"], 10).json()["id"]
    add(client, auth, medicine["id"], 50)
    client.put(f"/packages/{first}", json={"expiry_date": days(100)}, headers=auth)
    assert [p["days_left"] for p in client.get("/packages", headers=auth).json()] == [50, 100]
