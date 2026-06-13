"""Shared pytest fixtures: in-memory DB + authenticated test client."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, StaticPool, create_engine

from app.api.deps import get_session
from app.main import app


@pytest.fixture(name="engine")
def engine_fixture():
    # Single shared in-memory SQLite connection for the whole test.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import app.models  # noqa: F401  (register tables)

    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(engine):
    def _get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def auth_headers(client: TestClient, email: str, password: str, role: str = "client",
                 full_name: str = "") -> dict:
    """Sign up (ignore conflict) + log in, return Authorization header."""
    client.post(
        "/auth/signup",
        json={"email": email, "password": password, "role": role,
              "full_name": full_name},
    )
    resp = client.post(
        "/auth/login", data={"username": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
