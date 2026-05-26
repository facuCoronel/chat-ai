import hashlib
import hmac


def validate_meta_signature(body: bytes, signature_header: str, app_secret: str) -> bool:
    """
    Validates the X-Hub-Signature-256 header sent by Meta on every webhook POST.
    Returns True if the signature matches, False otherwise.
    Always use hmac.compare_digest to prevent timing attacks.
    """
    if not signature_header.startswith("sha256="):
        return False

    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header)
