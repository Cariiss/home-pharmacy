from datetime import date, timedelta

import pytest

from app.services import expiry_status

from .conftest import days

TODAY = date(2026, 11, 26)


@pytest.mark.parametrize(
    "delta, expected",
    [(-1, "expired"), (0, "expiring"), (30, "expiring"), (31, "ok"), (365, "ok")],
)
def test_expiry_status_boundaries(delta, expected):
    days_left, status = expiry_status(TODAY + timedelta(days=delta), 30, today=TODAY)
    assert days_left == delta
    assert status == expected


def test_leap_year_february():
    days_left, status = expiry_status(date(2028, 2, 29), 30, today=date(2028, 2, 1))
    assert days_left == 28 and status == "expiring"


def test_default_settings(client, auth):
    assert client.get("/settings", headers=auth).json() == {"threshold_days": 30, "notifications_enabled": True}


def test_invalid_threshold(client, auth):
    assert client.put("/settings", json={"threshold_days": 5}, headers=auth).status_code == 422


def test_threshold_change_recalculates_status(client, auth, medicine):
    client.post("/packages", json={"medicine_id": medicine["id"], "expiry_date": days(10), "quantity": 1}, headers=auth)
    assert client.get("/packages", headers=auth).json()[0]["status"] == "expiring"
    client.put("/settings", json={"threshold_days": 7, "notifications_enabled": True}, headers=auth)
    assert client.get("/packages", headers=auth).json()[0]["status"] == "ok"


def test_filter_by_status(client, auth, medicine):
    for d in [-3, 5, 100]:
        client.post("/packages", json={"medicine_id": medicine["id"], "expiry_date": days(d), "quantity": 1}, headers=auth)
    assert [p["days_left"] for p in client.get("/packages?status=expired", headers=auth).json()] == [-3]
    assert [p["days_left"] for p in client.get("/packages?status=expiring", headers=auth).json()] == [5]
    assert [p["days_left"] for p in client.get("/packages?status=ok", headers=auth).json()] == [100]


def test_search_packages_by_name(client, auth, medicine):
    other = client.post("/medicines", json={"name": "Ибупрофен"}, headers=auth).json()
    for mid in [medicine["id"], other["id"]]:
        client.post("/packages", json={"medicine_id": mid, "expiry_date": days(50), "quantity": 1}, headers=auth)
    got = client.get("/packages?q=ибуп", headers=auth).json()
    assert [p["medicine_name"] for p in got] == ["Ибупрофен"]
