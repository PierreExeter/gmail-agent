"""Gmail Agent - Email + Calendar Admin AI Agent.

A Streamlit application that uses LangChain and LLMs to manage Gmail inbox
and Google Calendar with AI-powered classification, drafting, and scheduling.
"""

import logging
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from auth.google_auth import is_authenticated
from ui.calendar_view import render_calendar
from ui.draft_view import render_drafts
from ui.inbox_view import render_inbox
from ui.settings_view import render_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Gmail Agent",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    """Main application entry point."""
    st.sidebar.title(" Gmail Agent")
    st.sidebar.markdown("AI-powered email & calendar assistant")

    st.sidebar.divider()

    if is_authenticated():
        st.sidebar.success(" Connected")
    else:
        st.sidebar.warning(" Not connected")

    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigation",
        [" Inbox", " Drafts", " Calendar", " Settings"],
        label_visibility="collapsed",
    )

    st.sidebar.divider()

    st.sidebar.markdown("""
    **Quick Actions**
    - Classify emails automatically
    - Review and edit AI drafts
    - Schedule meetings from emails
    - Manage trusted senders
    """)

    if not is_authenticated() and page != " Settings":
        st.warning(" Please connect your Google account in Settings to use the Gmail Agent.")
        render_settings()
        return

    if page == " Inbox":
        render_inbox()
    elif page == " Drafts":
        render_drafts()
    elif page == " Calendar":
        render_calendar()
    elif page == " Settings":
        render_settings()


if __name__ == "__main__":
    main()
