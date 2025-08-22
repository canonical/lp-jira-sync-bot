import pytest
from fastapi import HTTPException

# We'll import the module under test so we can monkeypatch its imported symbols
import lp_jira_sync_app.utils.launchpad_utils as lu

CREATE_BUG_PAYLOAD = {
  "action": "created",
  "target": "/testproject",
  "bug": "/bugs/1",
  "new": {
    "title": "newbugtest",
    "description": "newbugtest desc",
    "reporter": "/~user1",
    "tags": [],
    "status": "In Progress",
    "importance": "Undecided",
    "assignee": None,
    "date_created": "2025-08-20T06:37:15.674488+00:00"
  }
}

UPDATE_BUG_PAYLOAD = {
  "action": "title-changed",
  "target": "/testproject",
  "bug": "/bugs/1",
  "old": {
        "title": "newbugtest",
        "description": "newbugtest desc",
        "reporter": "/~user1",
        "tags": [],
        "status": "In Progress",
        "importance": "Undecided",
        "assignee": None,
        "date_created": "2025-08-20T06:37:15.674488+00:00"
      },
  "new": {
    "title": "newbugtest new title",
    "description": "newbugtest desc",
    "reporter": "/~user1",
    "tags": [],
    "status": "In Progress",
    "importance": "Undecided",
    "assignee": None,
    "date_created": "2025-08-20T06:37:15.674488+00:00"
  }
}
def test_handle_create_bug_lp_event(monkeypatch):

    payload = CREATE_BUG_PAYLOAD
    jira_client = object()
    calls = {"find": 0, "create": 0}
    def find_jira_issue(jira_client, project_key, bug_path):
        calls["find"] += 1
        return None
    def create_jira_issue(jira_client, payload, project_config):
        calls["create"] += 1
        return object()

    monkeypatch.setattr(lu, "find_jira_issue", find_jira_issue)
    monkeypatch.setattr(lu, "create_jira_issue", create_jira_issue)
    lu.sync_launchpad_action(payload, jira_client, {})
    assert calls["create"] == 1
    assert calls["find"] == 1

    ###Handle issue already exists in jira

    def find_jira_issue(jira_client, project_key, bug_path):
        calls["find"] += 1
        return object()
    monkeypatch.setattr(lu, "find_jira_issue", find_jira_issue)
    with pytest.raises(HTTPException) as e:
        lu.sync_launchpad_action(payload, jira_client, {})
    assert calls["create"] == 1
    assert calls["find"] == 2
    assert e.value.status_code == 404

def test_handle_update_bug_lp_event(monkeypatch):
    payload = UPDATE_BUG_PAYLOAD
    jira_client = object()
    calls = {"find": 0, "update": 0}

    def find_jira_issue(jira_client, project_key, bug_path):
        calls["find"] += 1
        return object()

    def update_jira_issue(jira_client, payload, project_config):
        calls["update"] += 1
        return object()

    monkeypatch.setattr(lu, "find_jira_issue", find_jira_issue)
    monkeypatch.setattr(lu, "update_jira_issue", update_jira_issue)
    lu.sync_launchpad_action(payload, jira_client, {})

    assert calls["update"] == 1
    assert calls["find"] == 1

    ##Handle issue not found in jira
    def find_jira_issue(jira_client, project_key, bug_path):
        calls["find"] += 1
        return None
    monkeypatch.setattr(lu, "find_jira_issue", find_jira_issue)
    with pytest.raises(HTTPException) as e:
        lu.sync_launchpad_action(payload, jira_client, {})
    assert calls["update"] == 1
    assert calls["find"] == 2
    assert e.value.status_code == 404
