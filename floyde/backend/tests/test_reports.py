"""Reports & analytics rollup."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests.conftest import auth_headers


def _setup(client):
    owner = auth_headers(client, "owner@floyde.app", "password123", "owner")
    bu = auth_headers(client, "barber@floyde.app", "password123", "barber")
    barber_user_id = client.get("/auth/me", headers=bu).json()["id"]
    shop = client.post("/shops", json={"name": "M", "slug": "m"}, headers=owner).json()
    barber = client.post(
        "/shops/barbers",
        json={"user_id": barber_user_id, "shop_id": shop["id"],
              "display_name": "Floyd"},
        headers=owner,
    ).json()
    service = client.post(
        "/services",
        json={"shop_id": shop["id"], "name": "Cut", "duration_minutes": 30,
              "price_cents": 5000},
        headers=owner,
    ).json()
    return owner, shop, barber, service


def _tomorrow(hour: int) -> str:
    dt = datetime.now(UTC) + timedelta(days=1)
    return dt.replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()


def test_summary_requires_staff(client):
    owner, shop, _b, _s = _setup(client)
    cust = auth_headers(client, "c@floyde.app", "password123", "client")
    assert client.get(
        "/reports/summary", params={"shop_id": shop["id"]}, headers=cust
    ).status_code == 403


def test_summary_rolls_up_revenue_and_bookings(client):
    owner, shop, barber, service = _setup(client)
    cust = auth_headers(client, "buyer@floyde.app", "password123", "client", "Andy")

    # an online booking → 20% deposit ($10) auto-paid in stub mode
    bk = client.post(
        "/bookings",
        json={"barber_id": barber["id"], "service_id": service["id"],
              "start_time": _tomorrow(10), "source": "online"},
        headers=cust,
    ).json()
    # a POS service charge of $50
    client.post(
        "/pos/charge",
        json={"shop_id": shop["id"], "amount_cents": 5000, "type": "final"},
        headers=owner,
    )
    # complete the booking so it counts in the leaderboard
    client.post(f"/bookings/{bk['id']}/complete", headers=owner)

    rep = client.get(
        "/reports/summary", params={"shop_id": shop["id"], "days": 30},
        headers=owner,
    )
    assert rep.status_code == 200
    data = rep.json()
    # revenue = $10 deposit + $50 service = $60
    assert data["revenue_cents"] == 6000
    assert data["revenue_by_type"]["deposit"] == 1000
    assert data["revenue_by_type"]["final"] == 5000
    assert data["bookings_completed"] == 1
    assert data["barber_leaderboard"][0]["name"] == "Floyd"
    assert data["barber_leaderboard"][0]["completed"] == 1
    assert len(data["revenue_by_day"]) == 30
    assert sum(p["cents"] for p in data["revenue_by_day"]) == 6000


def test_summary_counts_supply_spend(client):
    owner, shop, _b, _s = _setup(client)
    # owner lists a provider + offering, then buys for the shop
    pid = client.post(
        "/marketplace/providers",
        json={"name": "Supply Co", "category": "supplies"},
        headers=owner,
    ).json()["id"]
    off = client.post(
        f"/marketplace/providers/{pid}/offerings",
        json={"title": "Capes", "price_cents": 3000},
        headers=owner,
    ).json()
    client.post(
        "/marketplace/orders",
        json={"provider_id": pid, "items": [{"offering_id": off["id"], "quantity": 2}],
              "buyer_shop_id": shop["id"]},
        headers=owner,
    )
    data = client.get(
        "/reports/summary", params={"shop_id": shop["id"]}, headers=owner
    ).json()
    assert data["supply_spend_cents"] == 6000
    assert data["net_cents"] == data["revenue_cents"] - 6000
