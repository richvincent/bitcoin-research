"""Staff dashboard endpoints: manage schedule, staff booking, complete."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests.conftest import auth_headers


def _tomorrow_at(hour: int) -> str:
    dt = datetime.now(UTC) + timedelta(days=1)
    return dt.replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()


def _setup(client):
    owner = auth_headers(client, "owner@floyde.app", "password123", "owner")
    bu = auth_headers(client, "barber@floyde.app", "password123", "barber")
    barber_user_id = client.get("/auth/me", headers=bu).json()["id"]
    shop = client.post(
        "/shops", json={"name": "M", "slug": "m"}, headers=owner
    ).json()
    barber = client.post(
        "/shops/barbers",
        json={"user_id": barber_user_id, "shop_id": shop["id"],
              "display_name": "Floyd", "specialties": ["fade"]},
        headers=owner,
    ).json()
    service = client.post(
        "/services",
        json={"shop_id": shop["id"], "name": "Cut", "duration_minutes": 30,
              "price_cents": 4000},
        headers=owner,
    ).json()
    return owner, shop, barber, service


def test_staff_booking_and_manage_and_complete(client):
    owner, shop, barber, service = _setup(client)
    # the walk-in client needs an account first
    auth_headers(client, "walkin@floyde.app", "password123", "client", "Otis")

    booked = client.post(
        "/bookings/staff",
        json={"client_email": "walkin@floyde.app", "barber_id": barber["id"],
              "service_id": service["id"], "start_time": _tomorrow_at(11),
              "source": "walk_in"},
        headers=owner,
    )
    assert booked.status_code == 201, booked.text
    bid = booked.json()["id"]
    # walk-ins carry no deposit
    assert booked.json()["deposit_cents"] == 0

    # manage schedule resolves names
    sched = client.get(
        "/bookings/manage", params={"shop_id": shop["id"]}, headers=owner
    )
    assert sched.status_code == 200
    row = sched.json()[0]
    assert row["client_name"] == "Otis"
    assert row["barber_name"] == "Floyd"
    assert row["service_name"] == "Cut"
    assert row["price_cents"] == 4000

    # complete it
    done = client.post(f"/bookings/{bid}/complete", headers=owner)
    assert done.status_code == 200
    assert done.json()["status"] == "completed"


def test_staff_booking_unknown_client_404(client):
    owner, shop, barber, service = _setup(client)
    resp = client.post(
        "/bookings/staff",
        json={"client_email": "ghost@floyde.app", "barber_id": barber["id"],
              "service_id": service["id"], "start_time": _tomorrow_at(12)},
        headers=owner,
    )
    assert resp.status_code == 404


def test_manage_requires_staff(client):
    _setup(client)
    cust = auth_headers(client, "c@floyde.app", "password123", "client")
    assert client.get("/bookings/manage", headers=cust).status_code == 403


def test_complete_requires_staff(client):
    owner, shop, barber, service = _setup(client)
    auth_headers(client, "w2@floyde.app", "password123", "client", "W")
    bid = client.post(
        "/bookings/staff",
        json={"client_email": "w2@floyde.app", "barber_id": barber["id"],
              "service_id": service["id"], "start_time": _tomorrow_at(13)},
        headers=owner,
    ).json()["id"]
    cust = auth_headers(client, "c2@floyde.app", "password123", "client")
    assert client.post(f"/bookings/{bid}/complete", headers=cust).status_code == 403
