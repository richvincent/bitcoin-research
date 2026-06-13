"""Marketplace lite: directory, offerings, reviews, rating aggregation."""

from __future__ import annotations

from tests.conftest import auth_headers


def _make_provider(client, headers, name="Acme Supply", category="supplies"):
    return client.post(
        "/marketplace/providers",
        json={"name": name, "category": category, "description": "Stuff"},
        headers=headers,
    )


def test_categories_listed(client):
    headers = auth_headers(client, "u@floyde.app", "password123")
    resp = client.get("/marketplace/categories")
    assert resp.status_code == 200
    assert "insurance" in resp.json()


def test_create_and_list_providers(client):
    owner = auth_headers(client, "vendor@floyde.app", "password123")
    created = _make_provider(client, owner, "Detroit Barber Supply")
    assert created.status_code == 201, created.text
    assert created.json()["slug"] == "detroit-barber-supply"

    # slug uniqueness
    again = _make_provider(client, owner, "Detroit Barber Supply")
    assert again.json()["slug"] == "detroit-barber-supply-2"

    listing = client.get("/marketplace/providers")
    assert listing.status_code == 200
    assert len(listing.json()) == 2

    # category filter
    filtered = client.get("/marketplace/providers", params={"category": "insurance"})
    assert filtered.json() == []

    # search
    found = client.get("/marketplace/providers", params={"q": "detroit"})
    assert len(found.json()) == 2


def test_offerings_owner_only(client):
    owner = auth_headers(client, "vendor2@floyde.app", "password123")
    pid = _make_provider(client, owner).json()["id"]

    ok = client.post(
        f"/marketplace/providers/{pid}/offerings",
        json={"title": "Clippers", "price_cents": 9900, "unit": "each"},
        headers=owner,
    )
    assert ok.status_code == 201

    intruder = auth_headers(client, "someoneelse@floyde.app", "password123")
    denied = client.post(
        f"/marketplace/providers/{pid}/offerings",
        json={"title": "Hijack"},
        headers=intruder,
    )
    assert denied.status_code == 403

    detail = client.get(f"/marketplace/providers/{pid}")
    assert detail.status_code == 200
    assert len(detail.json()["offerings"]) == 1


def test_reviews_and_rating_aggregation(client):
    owner = auth_headers(client, "vendor3@floyde.app", "password123")
    pid = _make_provider(client, owner).json()["id"]

    # owner cannot review own listing
    self_review = client.post(
        f"/marketplace/providers/{pid}/reviews",
        json={"rating": 5},
        headers=owner,
    )
    assert self_review.status_code == 400

    a = auth_headers(client, "rev-a@floyde.app", "password123", full_name="Ann")
    b = auth_headers(client, "rev-b@floyde.app", "password123", full_name="Bob")
    client.post(f"/marketplace/providers/{pid}/reviews",
                json={"rating": 5, "title": "Great"}, headers=a)
    client.post(f"/marketplace/providers/{pid}/reviews",
                json={"rating": 3}, headers=b)

    prov = client.get(f"/marketplace/providers/{pid}").json()
    assert prov["review_count"] == 2
    assert prov["rating"] == 4.0
    assert prov["reviews"][0]["author_name"] in ("Ann", "Bob")

    # re-reviewing updates in place (no double count)
    client.post(f"/marketplace/providers/{pid}/reviews",
                json={"rating": 1}, headers=a)
    prov2 = client.get(f"/marketplace/providers/{pid}").json()
    assert prov2["review_count"] == 2
    assert prov2["rating"] == 2.0


def test_review_requires_auth(client):
    owner = auth_headers(client, "vendor4@floyde.app", "password123")
    pid = _make_provider(client, owner).json()["id"]
    assert client.post(f"/marketplace/providers/{pid}/reviews",
                       json={"rating": 5}).status_code == 401
