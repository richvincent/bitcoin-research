from tests.conftest import auth_headers


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["integrations"]["stripe"] == "stub"


def test_signup_login_me(client):
    headers = auth_headers(client, "a@floyde.app", "password123", "client", "Ada")
    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "a@floyde.app"
    assert me.json()["role"] == "client"


def test_duplicate_signup_conflicts(client):
    client.post("/auth/signup", json={"email": "b@floyde.app", "password": "password123"})
    again = client.post(
        "/auth/signup", json={"email": "b@floyde.app", "password": "password123"}
    )
    assert again.status_code == 409


def test_protected_requires_auth(client):
    assert client.get("/auth/me").status_code == 401


def test_role_enforced_on_shop_create(client):
    # a plain client may not create a shop
    headers = auth_headers(client, "c@floyde.app", "password123", "client")
    resp = client.post("/shops", json={"name": "X", "slug": "x"}, headers=headers)
    assert resp.status_code == 403
