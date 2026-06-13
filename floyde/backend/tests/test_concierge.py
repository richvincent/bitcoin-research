"""Concierge (Ruby) requests: queueing, listing, and desk status updates."""

from __future__ import annotations

from tests.conftest import auth_headers


def test_client_queues_and_sees_own_request(client):
    cust = auth_headers(client, "c@floyde.app", "password123", "client", "Andy")
    resp = client.post(
        "/concierge/call",
        json={"phone": "+13135550100", "topic": "wedding cut advice"},
        headers=cust,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "queued"
    assert body["request_id"].startswith("ccg_")
    assert body["client_name"] == "Andy"

    mine = client.get("/concierge/requests", headers=cust)
    assert mine.status_code == 200
    assert len(mine.json()) == 1


def test_requires_auth(client):
    assert client.post("/concierge/call", json={"phone": "x"}).status_code == 401


def test_client_cannot_see_others_requests(client):
    a = auth_headers(client, "a@floyde.app", "password123", "client")
    b = auth_headers(client, "b@floyde.app", "password123", "client")
    client.post("/concierge/call", json={"phone": "1", "topic": "t"}, headers=a)
    # b has none of their own
    assert client.get("/concierge/requests", headers=b).json() == []


def test_staff_sees_queue_and_updates_status(client):
    cust = auth_headers(client, "cust@floyde.app", "password123", "client")
    req = client.post(
        "/concierge/call",
        json={"phone": "+13135550100", "topic": "help"},
        headers=cust,
    ).json()
    rid = req["id"]

    staff = auth_headers(client, "owner@floyde.app", "password123", "owner")
    queue = client.get("/concierge/requests", headers=staff)
    assert queue.status_code == 200
    assert any(r["id"] == rid for r in queue.json())

    done = client.post(
        f"/concierge/requests/{rid}/status",
        params={"new_status": "completed"},
        headers=staff,
    )
    assert done.status_code == 200
    assert done.json()["status"] == "completed"


def test_status_update_requires_staff(client):
    cust = auth_headers(client, "cust2@floyde.app", "password123", "client")
    rid = client.post(
        "/concierge/call", json={"phone": "1", "topic": "t"}, headers=cust
    ).json()["id"]
    denied = client.post(
        f"/concierge/requests/{rid}/status",
        params={"new_status": "completed"},
        headers=cust,
    )
    assert denied.status_code == 403
