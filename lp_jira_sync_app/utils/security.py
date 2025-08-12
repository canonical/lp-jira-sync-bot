import hmac
import hashlib
from typing import Optional


def parse_signature(sig_header: Optional[str]) -> Optional[str]:
    """Extract the hex digest from X-Hub-Signature header.
    Accepts formats like 'sha1=<hex>' or just '<hex>'.
    Returns hex digest string or None if not present/invalid.
    """
    if not sig_header:
        return None
    sig_header = sig_header.strip()
    if sig_header.lower().startswith("sha1="):
        return sig_header.split("=", 1)[1].strip()
    return sig_header


def verify_hmac_sha1(body: bytes, provided_hex: str, secret: str) -> bool:
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha1)
    expected_hex = mac.hexdigest()
    return hmac.compare_digest(expected_hex, provided_hex)
