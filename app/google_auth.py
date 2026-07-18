"""Google ID token verification.

The app runs the Google sign-in flow and gets an ID token (a JWT signed by
Google). We never trust it blind — google-auth checks the signature against
Google's rotating public keys, the expiry, the issuer, and that the audience
matches one of OUR client IDs. Skipping the audience check is the classic
mistake: it would let a token minted for any other Google app log in here.
"""
from dataclasses import dataclass

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.config import get_settings

settings = get_settings()

# Reused across calls; it caches Google's public keys internally.
_request = google_requests.Request()


class GoogleAuthError(Exception):
    """Raised when a Google ID token can't be trusted."""


@dataclass
class GoogleIdentity:
    google_id: str          # stable, unique per Google account ("sub")
    email: str | None
    email_verified: bool
    name: str | None


def verify_google_token(token: str) -> GoogleIdentity:
    allowed = settings.google_client_id_list
    if not allowed:
        # Misconfiguration, not a client error — fail loudly rather than
        # silently accepting tokens for no audience.
        raise GoogleAuthError("Google sign-in is not configured on the server")

    try:
        # Passing audience=None here and checking manually below lets us accept
        # several client IDs (iOS/Android/web) with one call.
        claims = google_id_token.verify_oauth2_token(token, _request)
    except ValueError as e:
        raise GoogleAuthError(f"Invalid Google token: {e}") from e

    if claims.get("aud") not in allowed:
        raise GoogleAuthError("Google token was issued for a different app")

    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise GoogleAuthError("Unexpected token issuer")

    sub = claims.get("sub")
    if not sub:
        raise GoogleAuthError("Google token missing subject")

    return GoogleIdentity(
        google_id=sub,
        email=claims.get("email"),
        email_verified=bool(claims.get("email_verified")),
        name=claims.get("name"),
    )