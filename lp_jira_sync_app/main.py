import os
from fastapi import FastAPI, Request, HTTPException, status

from .utils.config import load_config
from .utils.security import parse_signature, verify_hmac_sha1

# Allow overriding the config path via environment
CONFIG_PATH = os.getenv("CONFIG_PATH", "config.yaml")

# Load configuration and secret
_config = load_config(CONFIG_PATH)
SECRET_CODE = (_config.get("app") or {}).get("secret_code") or ""

app = FastAPI()


@app.post("/")
async def webhook_handler(request: Request):
    # Read raw body to compute HMAC
    body = await request.body()

    # Extract signature from header
    sig_header = request.headers.get("X-Hub-Signature")
    hex_sig = parse_signature(sig_header)

    if not SECRET_CODE:
        # If no secret is configured, treat as unauthorized for safety
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Server HMAC secret not configured",
        )

    if not hex_sig or not verify_hmac_sha1(body, hex_sig, SECRET_CODE):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing HMAC-SHA1 signature",
        )

    # If signature valid, try parsing JSON payload for logging/response
    payload = None
    try:
        payload = await request.json()
    except Exception:
        # Leave payload as None if not JSON; still accept the request since signature matched
        pass

    print("/ webhook received payload:", payload)
    return {"message": "Signature verified", "ok": True}
