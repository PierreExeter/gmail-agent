"""Draft review view component for Streamlit UI."""

import logging

import streamlit as st

from db.database import Database
from db.models import Draft
from services.gmail_service import GmailService

logger = logging.getLogger(__name__)


def render_drafts() -> None:
    """Render the drafts review view."""
    st.header("Draft Replies")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Refresh", type="primary"):
            st.session_state.pop("pending_drafts", None)
            st.rerun()

    drafts = _fetch_pending_drafts()

    if not drafts:
        st.info("No pending drafts. Drafts will appear here when you create them from the Inbox.")
        return

    for draft in drafts:
        _render_draft_card(draft)


def _fetch_pending_drafts() -> list[Draft]:
    """Fetch pending drafts from database."""
    if "pending_drafts" not in st.session_state:
        try:
            db = Database()
            st.session_state["pending_drafts"] = db.get_pending_drafts()
        except Exception:
            logger.exception("Failed to fetch drafts")
            st.error("Failed to load drafts")
            return []
    return st.session_state["pending_drafts"]


def _render_draft_card(draft: Draft) -> None:
    """Render a single draft card."""
    with st.expander(
        f" **{draft.subject}** - Created {draft.created_at.strftime('%Y-%m-%d %H:%M')}",
        expanded=True,
    ):
        _render_draft_details(draft)


def _render_draft_details(draft: Draft) -> None:
    """Render draft details inside the expander."""
    email = draft.email
    if email:
        st.markdown(f"**Original from:** {email.sender} <{email.sender_email}>")
        st.markdown(f"**Original subject:** {email.subject}")
        st.divider()

    st.markdown("**Draft Reply:**")

    edited_body = st.text_area(
        "Edit draft",
        value=draft.body,
        height=300,
        key=f"draft_body_{draft.id}",
        label_visibility="collapsed",
    )

    if edited_body != draft.body and st.button("Save Changes", key=f"save_{draft.id}"):
        _save_draft_changes(draft.id, edited_body)

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Approve & Send", key=f"approve_{draft.id}", type="primary"):
            _approve_and_send(draft, edited_body)

    with col2:
        if st.button("Reject", key=f"reject_{draft.id}"):
            _reject_draft(draft.id)

    with col3:
        feedback = st.selectbox(
            "Feedback",
            ["Rate quality...", "Good draft", "Needs improvement", "Poor quality"],
            key=f"feedback_{draft.id}",
            label_visibility="collapsed",
        )
        if feedback != "Rate quality...":
            _save_feedback(draft.id, feedback, draft.body, edited_body)

    with col4:
        if st.button("Improve", key=f"improve_{draft.id}"):
            _improve_draft(draft, edited_body)


def _save_draft_changes(draft_id: int, new_body: str) -> None:
    """Save changes to a draft."""
    try:
        db = Database()
        if db.update_draft(draft_id, new_body):
            st.success("Draft saved")
            st.session_state.pop("pending_drafts", None)
            st.rerun()
        else:
            st.error("Failed to save draft")
    except Exception:
        logger.exception("Failed to save draft")
        st.error("Failed to save draft")


def _approve_and_send(draft: Draft, body: str) -> None:
    """Approve and send a draft reply."""
    email = draft.email
    if not email:
        st.error("Original email not found")
        return

    with st.spinner("Sending email..."):
        try:
            gmail = GmailService()

            message_id = gmail.send_email(
                to=email.sender_email,
                subject=draft.subject,
                body=body,
                thread_id=email.thread_id,
            )

            if message_id:
                db = Database()
                db.approve_draft(draft.id)
                db.mark_draft_sent(draft.id, message_id)

                st.success("Email sent successfully!")
                st.session_state.pop("pending_drafts", None)
                st.rerun()
            else:
                st.error("Failed to send email")
        except Exception:
            logger.exception("Failed to send email")
            st.error("Failed to send email. Check your authentication.")


def _reject_draft(draft_id: int) -> None:
    """Reject and discard a draft."""
    try:
        db = Database()
        if db.reject_draft(draft_id):
            st.success("Draft rejected")
            st.session_state.pop("pending_drafts", None)
            st.rerun()
        else:
            st.error("Failed to reject draft")
    except Exception:
        logger.exception("Failed to reject draft")
        st.error("Failed to reject draft")


def _save_feedback(draft_id: int, rating: str, original: str, edited: str) -> None:
    """Save feedback on a draft."""
    try:
        db = Database()
        db.save_feedback(
            draft_id=draft_id,
            rating=rating,
            original_body=original,
            edited_body=edited if edited != original else "",
        )
        st.success("Feedback saved")
    except Exception:
        logger.exception("Failed to save feedback")


def _improve_draft(draft: Draft, current_body: str) -> None:
    """Improve a draft using LLM."""
    feedback = st.text_input(
        "What should be improved?",
        key=f"improve_input_{draft.id}",
        placeholder="e.g., Make it more formal, Add specific details about the project",
    )

    if feedback:
        with st.spinner("Improving draft..."):
            try:
                from agent.drafter import ReplyDrafter

                drafter = ReplyDrafter()
                improved = drafter.improve_draft(current_body, feedback)

                if improved:
                    db = Database()
                    db.update_draft(draft.id, improved)
                    st.session_state.pop("pending_drafts", None)
                    st.success("Draft improved!")
                    st.rerun()
                else:
                    st.error("Failed to improve draft")
            except Exception:
                logger.exception("Failed to improve draft")
                st.error("Failed to improve draft")
