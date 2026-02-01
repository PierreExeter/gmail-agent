"""Settings view component for Streamlit UI."""

import logging
import os

import streamlit as st

import config
from auth.google_auth import is_authenticated, revoke_credentials
from db.database import Database

logger = logging.getLogger(__name__)


def render_settings() -> None:
    """Render the settings view."""
    st.header("Settings")

    tabs = st.tabs(["API Configuration", "Agent Settings", "Google Account", "Known Senders"])

    with tabs[0]:
        _render_api_settings()

    with tabs[1]:
        _render_agent_settings()

    with tabs[2]:
        _render_google_settings()

    with tabs[3]:
        _render_known_senders()


def _render_api_settings() -> None:
    """Render API configuration settings."""
    st.subheader("HuggingFace API")

    current_key = os.getenv("HUGGINGFACE_API_KEY", "")
    masked_key = f"{current_key[:8]}...{current_key[-4:]}" if len(current_key) > 12 else "Not set"

    st.info(f"Current API key: {masked_key}")

    new_key = st.text_input(
        "HuggingFace API Key",
        type="password",
        placeholder="hf_...",
        help="Get your API key from huggingface.co/settings/tokens",
    )

    if new_key and st.button("Save API Key"):
        _save_api_key(new_key)

    st.divider()
    st.subheader("LLM Model")

    models = [
        "mistralai/Mistral-7B-Instruct-v0.2",
        "meta-llama/Llama-2-7b-chat-hf",
        "meta-llama/Llama-2-13b-chat-hf",
        "tiiuae/falcon-7b-instruct",
        "google/flan-t5-xxl",
    ]

    current_model = os.getenv("LLM_MODEL_ID", config.LLM_MODEL_ID)

    try:
        current_index = models.index(current_model)
    except ValueError:
        current_index = 0

    selected_model = st.selectbox(
        "Select Model",
        models,
        index=current_index,
        help="Choose the LLM model for email classification and drafting",
    )

    if selected_model != current_model and st.button("Update Model"):
        _save_model_setting(selected_model)


def _render_agent_settings() -> None:
    """Render agent configuration settings."""
    st.subheader("Classification Settings")

    threshold = st.slider(
        "Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        value=config.CONFIDENCE_THRESHOLD,
        step=0.05,
        help="Classifications below this threshold require manual approval",
    )

    if threshold != config.CONFIDENCE_THRESHOLD and st.button("Update Threshold"):
        _save_threshold_setting(threshold)

    st.divider()
    st.subheader("Sensitive Keywords")

    st.caption("Emails containing these keywords will require approval:")

    current_keywords = "\n".join(config.SENSITIVE_KEYWORDS)
    new_keywords = st.text_area(
        "Keywords (one per line)",
        value=current_keywords,
        height=200,
        label_visibility="collapsed",
    )

    if new_keywords != current_keywords and st.button("Update Keywords"):
        keywords_list = [k.strip() for k in new_keywords.split("\n") if k.strip()]
        _save_keywords_setting(keywords_list)


def _render_google_settings() -> None:
    """Render Google account settings."""
    st.subheader("Google Account")

    if is_authenticated():
        st.success(" Connected to Google")

        if st.button("Disconnect Account", type="secondary"):
            if revoke_credentials():
                st.success("Disconnected from Google")
                st.session_state.clear()
                st.rerun()
            else:
                st.error("Failed to disconnect")
    else:
        st.warning(" Not connected to Google")

        st.markdown("""
        To connect your Google account:
        1. Ensure you have OAuth credentials configured
        2. Click the button below to start the authentication flow
        """)

        if st.button("Connect Google Account", type="primary"):
            try:
                from auth.google_auth import get_credentials

                get_credentials()
                st.success("Connected to Google!")
                st.rerun()
            except FileNotFoundError as e:
                st.error(str(e))
            except Exception:
                logger.exception("Failed to authenticate")
                st.error("Failed to connect. Check your credentials configuration.")

    st.divider()
    st.subheader("OAuth Configuration")

    st.markdown("""
    To set up OAuth credentials:
    1. Go to [Google Cloud Console](https://console.cloud.google.com/)
    2. Create a new project or select an existing one
    3. Enable the Gmail API and Google Calendar API
    4. Create OAuth 2.0 credentials (Desktop app type)
    5. Download the credentials and save as `data/credentials.json`

    Or set environment variables:
    - `GOOGLE_CLIENT_ID`
    - `GOOGLE_CLIENT_SECRET`
    """)


def _render_known_senders() -> None:
    """Render known senders management."""
    st.subheader("Trusted Senders")

    st.caption("Emails from trusted senders won't require approval for unknown sender.")

    try:
        db = Database()
        senders = db.get_known_senders()

        if senders:
            for sender in senders:
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(sender.email)
                with col2:
                    st.text(sender.name or "-")
                with col3:
                    if st.button("Remove", key=f"remove_{sender.id}"):
                        _remove_known_sender(sender.id)
        else:
            st.info("No trusted senders configured.")

        st.divider()
        st.subheader("Add Trusted Sender")

        col1, col2 = st.columns(2)
        with col1:
            new_email = st.text_input("Email", placeholder="sender@example.com")
        with col2:
            new_name = st.text_input("Name (optional)", placeholder="John Doe")

        if st.button("Add Sender"):
            if new_email:
                db.add_known_sender(new_email, new_name)
                st.success(f"Added {new_email} to trusted senders")
                st.rerun()
            else:
                st.error("Email is required")

    except Exception:
        logger.exception("Failed to load known senders")
        st.error("Failed to load known senders")


def _save_api_key(key: str) -> None:
    """Save HuggingFace API key."""
    env_path = config.BASE_DIR / ".env"
    _update_env_file(env_path, "HUGGINGFACE_API_KEY", key)
    os.environ["HUGGINGFACE_API_KEY"] = key
    st.success("API key saved. Restart the app to apply changes.")


def _save_model_setting(model_id: str) -> None:
    """Save LLM model setting."""
    env_path = config.BASE_DIR / ".env"
    _update_env_file(env_path, "LLM_MODEL_ID", model_id)
    os.environ["LLM_MODEL_ID"] = model_id
    st.success("Model updated. Restart the app to apply changes.")


def _save_threshold_setting(threshold: float) -> None:
    """Save confidence threshold setting."""
    env_path = config.BASE_DIR / ".env"
    _update_env_file(env_path, "CONFIDENCE_THRESHOLD", str(threshold))
    st.success("Threshold updated. Restart the app to apply changes.")


def _save_keywords_setting(keywords: list[str]) -> None:
    """Save sensitive keywords setting."""
    st.success("Keywords updated in memory. To persist, update config.py")


def _remove_known_sender(sender_id: int) -> None:
    """Remove a known sender."""
    try:
        db = Database()
        with db._get_session() as session:
            from db.models import KnownSender

            sender = session.query(KnownSender).filter(KnownSender.id == sender_id).first()
            if sender:
                session.delete(sender)
        st.success("Sender removed")
        st.rerun()
    except Exception:
        logger.exception("Failed to remove sender")
        st.error("Failed to remove sender")


def _update_env_file(env_path, key: str, value: str) -> None:
    """Update or add a key in the .env file."""
    lines = []
    found = False

    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)

    if not found:
        lines.append(f"{key}={value}\n")

    with open(env_path, "w") as f:
        f.writelines(lines)
