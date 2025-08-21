from fastapi import HTTPException
from jira import JIRA

from lp_jira_sync_app.utils.config import logger
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
                    logger.error(f"Jira issue not found for Launchpad Bug {bug_path}")
                    raise HTTPException(status_code=404)

            else:
                issue = find_jira_issue(jira_client, project_in_jira, bug_path)
                if not issue:
                    create_jira_issue(jira_client, payload, project_config)
                else:
                    logger.error(f"Jira issue already exists for Launchpad Bug {bug_path}")
                    raise HTTPException(status_code=404)
        elif '-changed' in action:
            issue = find_jira_issue(jira_client, project_in_jira, bug_path)
            if issue:
                update_jira_issue(jira_client, issue, payload)
            else:
                logger.error(f"Jira issue not found for edit event for Launchpad Bug {bug_path}")
                raise HTTPException(status_code=404)

    except HTTPException:
        raise
    except Exception as e:
        # Convert unexpected JIRA errors to 500
        logger.error(f"Error during jira operation {e}/n/n Payload: {payload}, Project Config: {project_config}")
        raise HTTPException(status_code=500)









