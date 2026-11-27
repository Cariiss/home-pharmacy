from .conftest import days, register_and_login


def test_create_medicine(client, auth):
    r = client.post("/medicines", json={"name": "Ибупрофен", "form": "таблетки", "dosage": "200 мг"}, headers=auth)
    assert r.status_code == 201
    assert r.json()["name"] == "Ибупрофен"


def test_create_medicine_without_token(client):
    assert client.post("/medicines", json={"name": "Ибупрофен"}).status_code == 401


def test_blank_name_rejected(client, auth):
    assert client.post("/medicines", json={"name": "   "}, headers=auth).status_code == 422


def test_name_trimmed(client, auth):
    r = client.post("/medicines", json={"name": "  Но-шпа  "}, headers=auth)
    assert r.json()["name"] == "Но-шпа"


def test_list_and_search(client, auth):
    for name in ["Парацетамол", "Ибупрофен", "Аспирин"]:
        client.post("/medicines", json={"name": name}, headers=auth)
    assert len(client.get("/medicines", headers=auth).json()) == 3
    found = client.get("/medicines?q=ибу", headers=auth).json()
    assert [m["name"] for m in found] == ["Ибупрофен"]


def test_get_update_medicine(client, auth, medicine):
    mid = medicine["id"]
    assert client.get(f"/medicines/{mid}", headers=auth).status_code == 200
    r = client.put(f"/medicines/{mid}", json={"name": "Парацетамол", "form": "сироп", "dosage": "120 мг/5 мл"}, headers=auth)
    assert r.status_code == 200
    assert r.json()["form"] == "сироп"


def test_delete_medicine(client, auth, medicine):
    mid = medicine["id"]
    assert client.delete(f"/medicines/{mid}", headers=auth).status_code == 204
    assert client.get(f"/medicines/{mid}", headers=auth).status_code == 404


def test_delete_medicine_with_packages_blocked(client, auth, medicine):
    client.post("/packages", json={"medicine_id": medicine["id"], "expiry_date": days(100), "quantity": 1}, headers=auth)
    r = client.delete(f"/medicines/{medicine['id']}", headers=auth)
    assert r.status_code == 409
    assert client.get(f"/medicines/{medicine['id']}", headers=auth).status_code == 200


def test_missing_medicine_404(client, auth):
    assert client.get("/medicines/999", headers=auth).status_code == 404


def test_missing_name_rejected(client, auth):
    assert client.post("/medicines", json={"form": "таблетки"}, headers=auth).status_code == 422


def test_field_length_limits(client, auth):
    assert client.post("/medicines", json={"name": "а" * 200}, headers=auth).status_code == 201
    assert client.post("/medicines", json={"name": "а" * 201}, headers=auth).status_code == 422
    assert client.post("/medicines", json={"name": "Йод", "form": "ф" * 101}, headers=auth).status_code == 422
    assert client.post("/medicines", json={"name": "Йод", "dosage": "д" * 101}, headers=auth).status_code == 422


def test_list_sorted_by_name(client, auth):
    for name in ["Цитрамон", "Аспирин", "Но-шпа"]:
        client.post("/medicines", json={"name": name}, headers=auth)
    assert [m["name"] for m in client.get("/medicines", headers=auth).json()] == ["Аспирин", "Но-шпа", "Цитрамон"]


def test_search_case_insensitive_and_empty(client, auth):
    client.post("/medicines", json={"name": "Ибупрофен"}, headers=auth)
    assert [m["name"] for m in client.get("/medicines?q=ИБУПР", headers=auth).json()] == ["Ибупрофен"]
    assert client.get("/medicines?q=аспирин", headers=auth).json() == []
    # пустой q не фильтрует
    assert len(client.get("/medicines?q=", headers=auth).json()) == 1


def test_update_blank_name_rejected(client, auth, medicine):
    r = client.put(f"/medicines/{medicine['id']}", json={"name": "  "}, headers=auth)
    assert r.status_code == 422
    assert client.get(f"/medicines/{medicine['id']}", headers=auth).json()["name"] == "Парацетамол"


def test_update_name_trimmed(client, auth, medicine):
    r = client.put(f"/medicines/{medicine['id']}", json={"name": "  Цитрамон "}, headers=auth)
    assert r.status_code == 200 and r.json()["name"] == "Цитрамон"


def test_update_delete_missing_medicine_404(client, auth):
    assert client.put("/medicines/999", json={"name": "Йод"}, headers=auth).status_code == 404
    assert client.delete("/medicines/999", headers=auth).status_code == 404


def test_delete_medicine_after_packages_removed(client, auth, medicine):
    pid = client.post(
        "/packages", json={"medicine_id": medicine["id"], "expiry_date": days(100), "quantity": 1}, headers=auth
    ).json()["id"]
    r = client.delete(f"/medicines/{medicine['id']}", headers=auth)
    assert r.status_code == 409
    assert "упаков" in r.json()["detail"]
    assert client.delete(f"/packages/{pid}", headers=auth).status_code == 204
    assert client.delete(f"/medicines/{medicine['id']}", headers=auth).status_code == 204


def test_rename_medicine_reflected_in_packages(client, auth, medicine):
    client.post("/packages", json={"medicine_id": medicine["id"], "expiry_date": days(100), "quantity": 1}, headers=auth)
    client.put(f"/medicines/{medicine['id']}", json={"name": "Панадол"}, headers=auth)
    assert client.get("/packages", headers=auth).json()[0]["medicine_name"] == "Панадол"
