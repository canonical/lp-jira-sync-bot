from typing import Optional, Dict, Any
from jira import JIRA


def build_jira_client(app_cfg: Dict[str, Any]) -> JIRA:
    """Build and return a JIRA client using app configuration.

    Expects keys: jira_instance, jira_username, jira_token.
    Raises ValueError if any required configuration is missing.
    """
    server = (app_cfg or {}).get("jira_instance")
    username = (app_cfg or {}).get("jira_username")
    token = (app_cfg or {}).get("jira_token")
    if not server or not username or not token:
        raise ValueError("Jira credentials are not configured")
    return JIRA(server=server, basic_auth=(username, token))
