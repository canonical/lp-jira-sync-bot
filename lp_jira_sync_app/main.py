from fastapi import FastAPI, Request, HTTPException, status
from starlette.responses import JSONResponse
from .utils.config import merge_project_config, global_config, logger
from .utils.launchpad_utils import sync_launchpad_action
from .utils.security import require_hmac_signature
from .utils.jira_utils import build_jira_client

SECRET_CODE = (global_config.get("app") or {}).get("launchpad_webhook_secret_code") or ""


app = FastAPI()

@app.post("/")
@require_hmac_signature(SECRET_CODE)
async def webhook_handler(request: Request):

    payload = await request.json()
    yaml_param = request.query_params.get("yaml") if hasattr(request, "query_params") else None
    project_config = merge_project_config(yaml_param)
    # Prepare Jira client
    try:
        jira = build_jira_client()
    except Exception as e:
        logger.error(f"Failed to build JIRA client: {e}")
        raise HTTPException(status_code=500)

    sync_launchpad_action(payload, jira, project_config)

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Webhook received and validated"})

