"""End-to-end: owner sets up a shop, a client books, deposit auto-confirms."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests.conftest import auth_headers


def _next_weekday_at(hour: int) -> datetime:
    dt = datetime.now(UTC) + timedelta(days=1)
    return dt.replace(hour=hour, minute=0, second=0, microsecond=0)


def _setup_shop(client):
    owner = auth_headers(client, "owner@floyde.app", "password123", "owner")
    barber_user = auth_headers(client, "barber@floyde.app", "password123", "barber")
    barber_id_user = client.get("/auth/me", headers=barber_user).json()["id"]

    shop = client.post(
        "/shops",
        json={"name": "Mayberry", "slug": "mayberry", "latitude": 42.33,
              "longitude": -83.04},
        headers=owner,
    ).json()
    barber = client.post(
        "/shops/barbers",
        json={"user_id": barber_id_user, "shop_id": shop["id"],
              "display_name": "Floyd", "specialties": ["skin fade", "beard"]},
        headers=owner,
    ).json()
    service = client.post(
        "/services",
        json={"shop_id": shop["id"], "name": "Cut", "duration_minutes": 45,
              "price_cents": 5000, "tags": ["skin fade"]},
        headers=owner,
    ).json()
    return shop, barber, service


def test_full_booking_flow(client):
    shop, barber, service = _setup_shop(client)
    cust = auth_headers(client, "cust@floyde.app", "password123", "client")

    # set a style profile so matching has something to chew on
    client.put(
        "/clients/me/profile",
        json={"preferred_styles": ["skin fade", "beard"], "style_notes": "low fade"},
        headers=cust,
    )

    # availability returns slots
    avail = client.get(
        "/bookings/availability",
        params={"barber_id": barber["id"], "service_id": service["id"]},
        headers=cust,
    )
    assert avail.status_code == 200
    assert len(avail.json()) >= 1

    # book
    start = _next_weekday_at(10).isoformat()
    resp = client.post(
        "/bookings",
        json={"barber_id": barber["id"], "service_id": service["id"],
              "start_time": start, "source": "online"},
        headers=cust,
    )
    assert resp.status_code == 201, resp.text
    booking = resp.json()
    # deposit = 20% of $50.00 = $10.00, auto-confirmed in stub payment mode
    assert booking["deposit_cents"] == 1000
    assert booking["status"] == "confirmed"

    # double-booking the same slot conflicts
    dup = client.post(
        "/bookings",
        json={"barber_id": barber["id"], "service_id": service["id"],
              "start_time": start, "source": "online"},
        headers=cust,
    )
    assert dup.status_code == 409


def test_matching_ranks_by_style(client):
    shop, barber, service = _setup_shop(client)
    cust = auth_headers(client, "cust2@floyde.app", "password123", "client")
    client.put(
        "/clients/me/profile",
        json={"preferred_styles": ["skin fade"]},
        headers=cust,
    )
    matches = client.get(
        "/matching/barbers",
        params={"service_id": service["id"], "lat": 42.33, "lng": -83.04},
        headers=cust,
    )
    assert matches.status_code == 200
    data = matches.json()
    assert len(data) >= 1
    assert data[0]["barber"]["display_name"] == "Floyd"
    assert any("skin fade" in r for r in data[0]["reasons"])
