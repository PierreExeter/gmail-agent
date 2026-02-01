"""Google OAuth2 authentication for Gmail and Calendar APIs."""

import json
import logging
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

import config

logger = logging.getLogger(__name__)


def get_credentials() -> Credentials:
    """
    Get valid Google OAuth2 credentials.

    If no valid credentials exist, initiates the OAuth flow.
    Credentials are cached in token.json for reuse.

    Returns:
        Valid Google OAuth2 credentials.

    Raises:
        FileNotFoundError: If credentials.json is not found and no token exists.
    """
    creds: Credentials | None = None

    if config.TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(config.TOKEN_PATH), config.GOOGLE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                logger.exception("Failed to refresh credentials")
                creds = None

        if not creds:
            creds = _run_oauth_flow()

        _save_credentials(creds)

    return creds


def _run_oauth_flow() -> Credentials:
    """Run the OAuth2 flow to get new credentials."""
    if not config.CREDENTIALS_PATH.exists():
        credentials_data = _create_credentials_from_env()
        if credentials_data:
            config.CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(config.CREDENTIALS_PATH, "w") as f:
                json.dump(credentials_data, f)
        else:
            raise FileNotFoundError(
                f"credentials.json not found at {config.CREDENTIALS_PATH}. "
                "Please download it from Google Cloud Console or set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
            )

    flow = InstalledAppFlow.from_client_secrets_file(str(config.CREDENTIALS_PATH), config.GOOGLE_SCOPES)
    return flow.run_local_server(port=0)


def _create_credentials_from_env() -> dict[str, Any] | None:
    """Create credentials.json content from environment variables."""
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
        return None

    return {
        "installed": {
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"],
        }
    }


def _save_credentials(creds: Credentials) -> None:
    """Save credentials to token.json."""
    config.TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(config.TOKEN_PATH, "w") as token:
        token.write(creds.to_json())


def get_gmail_service() -> Resource:
    """
    Get an authenticated Gmail API service.

    Returns:
        Gmail API service resource.
    """
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def get_calendar_service() -> Resource:
    """
    Get an authenticated Google Calendar API service.

    Returns:
        Calendar API service resource.
    """
    creds = get_credentials()
    return build("calendar", "v3", credentials=creds)


def revoke_credentials() -> bool:
    """
    Revoke stored credentials and delete token file.

    Returns:
        True if successfully revoked, False otherwise.
    """
    if config.TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(config.TOKEN_PATH), config.GOOGLE_SCOPES)
            if creds.token:
                import requests

                requests.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": creds.token},
                    headers={"content-type": "application/x-www-form-urlencoded"},
                )
            config.TOKEN_PATH.unlink()
            return True
        except Exception:
            logger.exception("Failed to revoke credentials")
            return False
    return True


def is_authenticated() -> bool:
    """Check if valid credentials exist."""
    if not config.TOKEN_PATH.exists():
        return False
    try:
        creds = Credentials.from_authorized_user_file(str(config.TOKEN_PATH), config.GOOGLE_SCOPES)
        return creds.valid or (creds.expired and creds.refresh_token is not None)
    except Exception:
        return False
