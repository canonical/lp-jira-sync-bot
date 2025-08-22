from typing import Optional, Dict, Any
from jira import JIRA
from lp_jira_sync_app.utils.config import global_config

JIRA_ISSUE_TEMPLETE = '''
This issue was created from Launchpad issue {launchpad_bug_url}
Issue was submitted by Launchpad user: {launchpad_username}

{launchpad_bug_description}

'''
JIRA_COMMENT_TEMPLETE = '''
Launchpad user {launchpad_username} is commented:
{launchpad_comment}

'''

def build_jira_client() -> JIRA:
    """Build and return a JIRA client using app configuration.

    Expects keys: jira_instance, jira_username, jira_token.
    Raises ValueError if any required configuration is missing.
    """
    server =   global_config.get('app').get("jira_instance")
    username = global_config.get('app').get("jira_username")
    token =    global_config.get('app').get("jira_token")

    if not server or not username or not token:
        raise ValueError("Jira credentials are not configured")
    return JIRA(server=server, basic_auth=(username, token))

def find_jira_issue(jira_client: JIRA, project_key: str, issue_key: str) -> Optional[dict]:
    """Find and return a JIRA issue by project key and issue key."""
    jql = f'project = "{project_key}" AND text ~ "{issue_key}" ORDER BY created DESC'
    issues = jira_client.search_issues(jql, maxResults=1,json_result=False)
    return issues[0] if issues else None

def create_jira_issue(jira_client: JIRA, bug_object: dict, project_config) -> Optional[dict]:
    """Create a JIRA issue and return the issue object."""

    sync_description = project_config.get('sync_description',False)
    components = project_config.get('components') or []
    status_mapping = project_config.get('status_mapping')
    severity_mapping = project_config.get('severity_mapping')
    issue_type = project_config.get('jira_issue_type')
    project_key = project_config.get('jira_project_key')
    epic_key = project_config.get('jira_epic_key') or ''
    importance = bug_object.get('new').get('importance')
    status = bug_object.get('new').get('status')
    description = JIRA_ISSUE_TEMPLETE.format(
        launchpad_bug_url=f"{global_config.get('app').get('launchpad_url')}{bug_object.get('target')}{bug_object.get('bug')}",
        launchpad_username=bug_object.get('new').get('reporter').lstrip('/'),
        launchpad_bug_description=bug_object.get('new').get('description') if sync_description else ""

    )

    fields = {
        "summary": bug_object.get('new').get('title'),
        "project": {"key": project_key},
        "description": description,
        "issuetype": {"name": issue_type},

    }

    if severity_mapping and isinstance(severity_mapping, dict):
        importance = severity_mapping.get(importance) or 'Medium'
        fields["priority"] = {"name": importance}

    jira_componenta = [{'name':k} for k in components]
    if jira_componenta:
        fields["components"] = jira_componenta
    if epic_key:
        fields["parent"] = {"key": epic_key}

    issue = jira_client.create_issue(fields=fields)
    if status_mapping and isinstance(status_mapping, dict):
        status = status_mapping.get(status) or 'To Do'
        transition_to_status(jira_client, issue, status)
    return issue

def transition_to_status(jira: JIRA, issue, desired_status: str) -> bool:
    """
    Transition issue to desired_status if a direct transition exists.
    Returns True if transitioned or already in the desired status.
    """
    issue = jira.issue(issue.key)  # refresh
    if issue.fields.status.name == desired_status:
        return True

    for t in jira.transitions(issue):
        if t["to"]["name"] == desired_status:
            jira.transition_issue(issue, transition=t["id"])
            return True
    return False  # not directly reachable from current state

def create_jira_comment(jira_client: JIRA, issue, bug_object):
    """Create a JIRA comment and return the comment object."""
    comment_templete = JIRA_COMMENT_TEMPLETE.format(
        launchpad_username=bug_object.get('new').get('commenter').lstrip('/'),
        launchpad_comment=bug_object.get('new').get('content')
    )
    jira_client.add_comment(issue, comment_templete)

def update_jira_issue(jira_client: JIRA, issue, bug_object, project_config):
    """Update a JIRA issue and return the issue object."""

    updatable_fields = ["title", "description", "reporter", "status", "importance"]
    sync_description = project_config.get('sync_description', False)
    updated_field = bug_object.get('action').split('-')[0]
    if updated_field in updatable_fields:
        if updated_field == "title":
            issue.update(summary=bug_object.get('new').get('title'))
        elif updated_field in [ "description", "reporter"] and sync_description:
            description = JIRA_ISSUE_TEMPLETE.format(
                launchpad_bug_url=f"{global_config.get('app').get('launchpad_url')}{bug_object.get('target')}{bug_object.get('bug')}",
                launchpad_username=bug_object.get('new').get('reporter').lstrip('/'),
                launchpad_bug_description=bug_object.get('new').get('description')
            )
            issue.update(description=description)
        elif updated_field == "status":
            status_mapping = project_config.get('status_mapping')
            if status_mapping and isinstance(status_mapping, dict):
                status = bug_object.get('new').get('status')
                status = status_mapping.get(status) or 'To Do'
                transition_to_status(jira_client, issue, status)
        elif updated_field == "importance":
            severity_mapping = project_config.get('severity_mapping')
            if severity_mapping and isinstance(severity_mapping, dict):
                severity = bug_object.get('new').get('importance')
                severity = severity_mapping.get(severity) or 'Medium'
            issue.update(priority={"name": severity})
    return issue

