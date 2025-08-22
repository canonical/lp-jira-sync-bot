from fastapi import HTTPException
from jira import JIRA

from lp_jira_sync_app.utils.config import logger
from lp_jira_sync_app.utils.jira_utils import find_jira_issue, create_jira_issue, create_jira_comment, \
    update_jira_issue, find_jira_comment


def sync_launchpad_action(payload: dict, jira_client: JIRA, project_config: dict):
    action = payload.get('action')
    bug_path = payload.get('bug')
    project_in_jira = project_config.get('jira_project_key')
    sync_comments = project_config.get('sync_comments',False)
    try:
        if action == 'created':
            issue = find_jira_issue(jira_client, project_in_jira, bug_path)

            # Handle comment creation on an existing issue
            if 'bug_comment' in payload:
                if not sync_comments:
                    return

                if not issue:
                    logger.error(f"Jira issue not found for Launchpad Bug {bug_path}")
                    raise HTTPException(status_code=404)

                if find_jira_comment(issue, payload.get('bug_comment')):
                    logger.error(
                        f"Jira issue already has comment for Launchpad Bug comment {payload.get('bug_comment')}")
                    raise HTTPException(status_code=404)

                create_jira_comment(jira_client, issue, payload)
                return

            # Handle new issue creation
            if issue:
                logger.error(f"Jira issue already exists for Launchpad Bug {bug_path}")
                raise HTTPException(status_code=404)

            create_jira_issue(jira_client, payload, project_config)
            return

        if '-changed' in action:
            issue = find_jira_issue(jira_client, project_in_jira, bug_path)
            if not issue:
                logger.error(f"Jira issue not found for edit event for Launchpad Bug {bug_path}")
                raise HTTPException(status_code=404)

            update_jira_issue(jira_client, issue, payload, project_config)
            return

    except HTTPException:
        raise
    except Exception as e:
        # Convert unexpected JIRA errors to 500
        logger.error(f"Error during jira operation {e} , Payload: {payload}, Project Config: {project_config}")
        raise HTTPException(status_code=500)










