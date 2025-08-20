import os
import re
import copy
from typing import Optional, Tuple
from fastapi import FastAPI, Request, HTTPException, status

from .utils.config import load_config, merge_project_config
from .utils.security import require_hmac_signature
from .utils.jira_utils import build_jira_client

# Allow overriding the config path via environment
CONFIG_PATH = os.getenv("CONFIG_PATH", "config.yaml")

# Load configuration and secret
global_config = load_config(CONFIG_PATH)
SECRET_CODE = (global_config.get("app") or {}).get("webhook_secret_code") or ""

app = FastAPI()


def _extract_bug_id_from_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    # Expect numeric id at end of path like '/bugs/2121020' or '/project/+bug/2121020'
    m = re.search(r"/(\d+)(?:$|[/?#])", path)
    return m.group(1) if m else None


@app.post("/")
@require_hmac_signature(SECRET_CODE)
async def webhook_handler(request: Request):
    # Parse JSON body (if present)
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    # Merge per-request sync overrides via ?yaml=
    yaml_param = request.query_params.get("yaml") if hasattr(request, "query_params") else None
    project_config = merge_project_config(yaml_param)

    # Prepare Jira client
    app_cfg = global_config.get('app') or {}
    try:
        jira = build_jira_client(app_cfg)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


    action = payload.get('action')
    target = payload.get('target')  # launchpad project path
    bug_path = payload.get('bug')
    bug_id = _extract_bug_id_from_path(bug_path)

    print("/ webhook received payload:", payload)
    return {"message": "Signature verified"}
