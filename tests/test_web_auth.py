from fastapi.testclient import TestClient

from chaoscomms.api import create_app
from chaoscomms.web_auth import make_password_hash


def test_login_sets_secure_session_cookie(monkeypatch) -> None:
    monkeypatch.setenv("CHAOSCOMMS_WEB_USERNAME", "admin")
    monkeypatch.setenv("CHAOSCOMMS_WEB_PASSWORD_HASH", make_password_hash("test"))

    client = TestClient(create_app(web_auth_required=True), base_url="https://testserver")

    response = client.post("/api/v1/login", json={"username": "admin", "password": "test"})

    assert response.status_code == 200
    assert "session=" in response.headers["set-cookie"]
    assert client.get("/").status_code == 200


def test_web_auth_redirects_dashboard_when_not_authenticated() -> None:
    client = TestClient(create_app(web_auth_required=True), base_url="https://testserver")

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/login"


def test_login_page_is_public() -> None:
    client = TestClient(create_app(web_auth_required=True), base_url="https://testserver")

    response = client.get("/login")

    assert response.status_code == 200
    assert "Log in" in response.text
