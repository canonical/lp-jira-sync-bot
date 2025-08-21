import json
import hmac
import hashlib
import importlib

from fastapi.testclient import TestClient


def hmac_header(body: bytes, secret: str) -> dict:
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha1)
    return {"X-Hub-Signature": f"sha1={mac.hexdigest()}"}


def build_app_with_secret(monkeypatch, secret: str):
    from lp_jira_sync_app.utils import config as cfg
    cfg.global_config["app"] = {
        "launchpad_webhook_secret_code": secret,
        "jira_instance": "https://example.atlassian.net",
        "jira_username": "user",
        "jira_token": "token",
        "launchpad_url": "https://launchpad.net",
    }
    cfg.global_config["project"] = {
        "jira_project_key": "PRJ",
        "jira_issue_type": "Task",
        "status_mapping": {"New": "To Do"},
        "severity_mapping": {"High": "High"},
        "sync_description": False,
    }

    # Reload main to re-evaluate decorator with the new SECRET_CODE
    import lp_jira_sync_app.main as main
    importlib.reload(main)
    return main


def test_post_requires_valid_signature(monkeypatch):
    main = build_app_with_secret(monkeypatch, secret="s3cr3t")
    monkeypatch.setattr(main, "sync_launchpad_action", lambda *args: None)
    monkeypatch.setattr(main, "build_jira_client", lambda: None)
    client = TestClient(main.app)

    payload = {"action": "created", "bug": "/bugs/1", "new": {"title": "t"}}
    body = json.dumps(payload).encode("utf-8")

    # Missing signature -> 401
    r = client.post("/", data=body, headers={"Content-Type": "application/json"})
    assert r.status_code == 401

    # Invalid signature -> 401
    r = client.post(
        "/",
        data=body,
        headers={"Content-Type": "application/json", "X-Hub-Signature": "sha1=deadbeef"},
    )
    assert r.status_code == 401

    # Valid signature -> 200
    headers = {"Content-Type": "application/json"}
    headers.update(hmac_header(body, secret="s3cr3t"))
    r = client.post("/", data=body, headers=headers)
    assert r.status_code == 200
    assert r.json().get("message")


def test_post_returns_400_on_empty_payload(monkeypatch):
    main = build_app_with_secret(monkeypatch, secret="xyz")
    monkeypatch.setattr(main, "sync_launchpad_action", lambda *args: None)
    monkeypatch.setattr(main, "build_jira_client", lambda: None)

    client = TestClient(main.app)

    r = client.post(
        "/",
        headers={"Content-Type": "application/json", **hmac_header(b"null", "xyz")},
    )
    assert r.status_code == 400


def test_post_root_returns_500_when_jira_client_fails(monkeypatch):
    main = build_app_with_secret(monkeypatch, secret="abc")

    def build_jira_client():
        raise RuntimeError("no jira")

    monkeypatch.setattr(main, "build_jira_client", build_jira_client)

    client = TestClient(main.app)

    payload = {"action": "created", "bug": "/bugs/1", "new": {"title": "t"}}
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", **hmac_header(body, "abc")}

    r = client.post("/", data=body, headers=headers)
    assert r.status_code == 500
