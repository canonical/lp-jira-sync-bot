from fastapi import HTTPException
from jira import JIRA
from lp_jira_sync_app.utils.jira_utils import find_jira_issue, create_jira_issue, create_jira_comment, update_jira_issue

def sync_launchpad_action(payload: dict, jira_client: JIRA, project_config: dict):
    action = payload.get('action')
    bug_path = payload.get('bug')
    project_in_jira = project_config.get('jira_project_key')
    sync_comments = project_config.get('sync_comments',False)
    try:
        if action == 'created':
            if 'bug_comment' in payload and sync_comments:
                issue = find_jira_issue(jira_client, project_in_jira, bug_path)
                if issue:
                    create_jira_comment(jira_client, issue, payload)
                else:
                  raise HTTPException(status_code=404, detail="Related Jira issue not found for comment event")

            else:
                issue = find_jira_issue(jira_client, project_in_jira, bug_path)
                if not issue:
                    create_jira_issue(jira_client, payload, project_config)
                else:
                  raise HTTPException(status_code=404, detail="Jira issue already exists for this Launchpad Bug")
        elif '-changed' in action:
            updated_field = action.split('-')[0]
            issue = find_jira_issue(jira_client, project_in_jira, bug_path)
            if issue:
                update_jira_issue(jira_client, issue, payload, updated_field)
            else:
                raise HTTPException(status_code=404, detail="Related Jira issue not found for comment event")

    except HTTPException:
        raise
    except Exception as e:
        # Convert unexpected JIRA errors to 500
        raise HTTPException(status_code=500, detail=f"Jira operation failed: {e}")









