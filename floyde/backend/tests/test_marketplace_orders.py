"""Marketplace transactions: orders, commission split, fulfillment."""

from __future__ import annotations

from tests.conftest import auth_headers


def _provider_with_offerings(client):
    seller = auth_headers(client, "seller@floyde.app", "password123", full_name="Seller")
    pid = client.post(
        "/marketplace/providers",
        json={"name": "Detroit Barber Supply", "category": "supplies"},
        headers=seller,
    ).json()["id"]
    o1 = client.post(
        f"/marketplace/providers/{pid}/offerings",
        json={"title": "Clippers", "price_cents": 9900, "unit": "each"},
        headers=seller,
    ).json()
    o2 = client.post(
        f"/marketplace/providers/{pid}/offerings",
        json={"title": "Capes", "price_cents": 2500},
        headers=seller,
    ).json()
    contact = client.post(
        f"/marketplace/providers/{pid}/offerings",
        json={"title": "Custom signage"},  # no price
        headers=seller,
    ).json()
    return seller, pid, o1, o2, contact


def test_place_order_computes_commission(client):
    _seller, pid, o1, o2, _ = _provider_with_offerings(client)
    buyer = auth_headers(client, "buyer@floyde.app", "password123", full_name="Buyer")

    resp = client.post(
        "/marketplace/orders",
        json={
            "provider_id": pid,
            "items": [
                {"offering_id": o1["id"], "quantity": 2},  # 19800
                {"offering_id": o2["id"], "quantity": 1},  # 2500
            ],
        },
        headers=buyer,
    )
    assert resp.status_code == 201, resp.text
    o = resp.json()
    assert o["subtotal_cents"] == 22300
    assert o["commission_rate"] == 0.10
    assert o["commission_cents"] == 2230
    assert o["provider_payout_cents"] == 20070
    assert o["status"] == "paid"  # stub payment auto-succeeds
    assert len(o["items"]) == 2
    assert o["items"][0]["line_total_cents"] == 19800


def test_contact_for_pricing_rejected(client):
    _seller, pid, _o1, _o2, contact = _provider_with_offerings(client)
    buyer = auth_headers(client, "b2@floyde.app", "password123")
    resp = client.post(
        "/marketplace/orders",
        json={"provider_id": pid, "items": [{"offering_id": contact["id"]}]},
        headers=buyer,
    )
    assert resp.status_code == 400
    assert "pricing" in resp.json()["detail"].lower()


def test_offering_must_belong_to_provider(client):
    _seller, pid, _o1, _o2, _c = _provider_with_offerings(client)
    other = auth_headers(client, "other@floyde.app", "password123")
    other_pid = client.post(
        "/marketplace/providers",
        json={"name": "Other Co", "category": "other"},
        headers=other,
    ).json()["id"]
    buyer = auth_headers(client, "b3@floyde.app", "password123")
    # order against other_pid but using an offering from pid
    resp = client.post(
        "/marketplace/orders",
        json={"provider_id": other_pid, "items": [{"offering_id": _o1["id"]}]},
        headers=buyer,
    )
    assert resp.status_code == 400


def test_buyer_and_seller_views(client):
    seller, pid, o1, _o2, _c = _provider_with_offerings(client)
    buyer = auth_headers(client, "b4@floyde.app", "password123")
    oid = client.post(
        "/marketplace/orders",
        json={"provider_id": pid, "items": [{"offering_id": o1["id"]}]},
        headers=buyer,
    ).json()["id"]

    buyer_view = client.get("/marketplace/orders", headers=buyer)
    assert [x["id"] for x in buyer_view.json()] == [oid]

    seller_view = client.get(
        "/marketplace/orders", params={"role": "seller"}, headers=seller
    )
    assert [x["id"] for x in seller_view.json()] == [oid]

    # buyer sees nothing as a seller
    assert client.get(
        "/marketplace/orders", params={"role": "seller"}, headers=buyer
    ).json() == []


def test_fulfill_and_cancel_rules(client):
    seller, pid, o1, _o2, _c = _provider_with_offerings(client)
    buyer = auth_headers(client, "b5@floyde.app", "password123")
    oid = client.post(
        "/marketplace/orders",
        json={"provider_id": pid, "items": [{"offering_id": o1["id"]}]},
        headers=buyer,
    ).json()["id"]

    # buyer can't fulfill (seller-only)
    assert client.post(f"/marketplace/orders/{oid}/fulfill", headers=buyer).status_code == 403

    # seller fulfills
    done = client.post(f"/marketplace/orders/{oid}/fulfill", headers=seller)
    assert done.status_code == 200
    assert done.json()["status"] == "fulfilled"

    # fulfilled orders can't be cancelled
    assert client.post(f"/marketplace/orders/{oid}/cancel", headers=buyer).status_code == 400


def test_order_access_control(client):
    seller, pid, o1, _o2, _c = _provider_with_offerings(client)
    buyer = auth_headers(client, "b6@floyde.app", "password123")
    oid = client.post(
        "/marketplace/orders",
        json={"provider_id": pid, "items": [{"offering_id": o1["id"]}]},
        headers=buyer,
    ).json()["id"]
    stranger = auth_headers(client, "stranger@floyde.app", "password123")
    assert client.get(f"/marketplace/orders/{oid}", headers=stranger).status_code == 403
    assert client.get(f"/marketplace/orders/{oid}", headers=buyer).status_code == 200
    assert client.get(f"/marketplace/orders/{oid}", headers=seller).status_code == 200
