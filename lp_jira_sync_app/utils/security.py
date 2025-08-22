import hmac
import hashlib
from typing import Optional
from functools import wraps
from fastapi import HTTPException, status

def parse_signature(sig_header: Optional[str]) -> Optional[str]:
    """Extract the hex digest from X-Hub-Signature header.
    Returns hex digest string or None if not present/invalid.
    """
    if not sig_header:
        return None
    sig_header = sig_header.strip()
    if sig_header.lower().startswith("sha1="):
        return sig_header.split("=", 1)[1].strip()
    return None


def verify_hmac_sha1(body: bytes, provided_hex: str, secret: str) -> bool:
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha1)
    expected_hex = mac.hexdigest()
    return hmac.compare_digest(expected_hex, provided_hex)

# Decorator to require valid HMAC signature on FastAPI handlers
def require_hmac_signature(secret: str):
    """Decorator factory that enforces HMAC-SHA1 verification for webhook endpoints.
    - Reads request body and verifies X-Hub-Signature using the provided secret.
    - Raises HTTP 401 on missing server secret or invalid/missing signature.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            body = await request.body()
            if not body:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            sig_header = request.headers.get("X-Hub-Signature")
            hex_sig = parse_signature(sig_header)
            if not secret:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            if not hex_sig or not verify_hmac_sha1(body, hex_sig, secret):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
