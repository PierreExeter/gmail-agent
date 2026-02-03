"""Inbox view component for Streamlit UI."""

import logging
from datetime import datetime

import streamlit as st

from agent.approval import ApprovalChecker
from agent.classifier import ClassificationResult, EmailClassifier
from agent.drafter import ReplyDrafter
from db.database import Database
from services.gmail_service import EmailMessage, GmailService

logger = logging.getLogger(__name__)

CATEGORY_COLORS = {
    "NEEDS_REPLY": "red",
    "FYI_ONLY": "gray",
    "MEETING_REQUEST": "blue",
    "TASK_ACTION": "orange",
}

CATEGORY_ICONS = {
    "NEEDS_REPLY": "",
    "FYI_ONLY": "",
    "MEETING_REQUEST": "",
    "TASK_ACTION": "",
}


def render_inbox() -> None:
    """Render the inbox view."""
    st.header("Inbox")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        unread_only = st.checkbox("Show unread only", value=True)
    with col2:
        max_emails = st.selectbox("Show", [10, 20, 50], index=1)
    with col3:
        if st.button("Refresh", type="primary"):
            st.session_state.pop("emails", None)
            st.rerun()

    emails = _fetch_emails(unread_only, max_emails)

    if not emails:
        st.info("No emails found. Check your authentication or filters.")
        return

    for email in emails:
        _render_email_card(email)


def _fetch_emails(unread_only: bool, max_results: int) -> list[EmailMessage]:
    """Fetch emails from Gmail."""
    cache_key = f"emails_{unread_only}_{max_results}"
    if cache_key not in st.session_state:
        try:
            gmail = GmailService()
            st.session_state[cache_key] = gmail.fetch_emails(
                max_results=max_results,
                unread_only=unread_only,
            )
        except Exception:
            logger.exception("Failed to fetch emails")
            st.error("Failed to fetch emails. Please check your authentication.")
            return []
    return st.session_state[cache_key]


def _render_email_card(email: EmailMessage) -> None:
    """Render a single email card."""
    classification = _get_classification(email)
    approval_check = _get_approval_check(email, classification)

    with st.expander(
        _format_email_header(email, classification, approval_check.requires_approval),
        expanded=False,
    ):
        _render_email_details(email, classification, approval_check)


def _format_email_header(
    email: EmailMessage,
    classification: ClassificationResult | None,
    needs_approval: bool,
) -> str:
    """Format the email header for the expander."""
    date_str = _format_date(email.date)
    unread_marker = "" if email.is_unread else ""

    category = classification.category if classification else "PENDING"
    icon = CATEGORY_ICONS.get(category, "")
    approval_marker = " NEEDS APPROVAL" if needs_approval else ""

    return f"{unread_marker} **{email.sender}** - {email.subject} {icon}{approval_marker} _{date_str}_"


def _render_email_details(
    email: EmailMessage,
    classification: ClassificationResult | None,
    approval_check,
) -> None:
    """Render email details inside the expander."""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"**From:** {email.sender} <{email.sender_email}>")
        st.markdown(f"**Subject:** {email.subject}")
        st.markdown(f"**Date:** {email.date.strftime('%Y-%m-%d %H:%M')}")

    with col2:
        if classification:
            color = CATEGORY_COLORS.get(classification.category, "gray")
            st.markdown(
                f"<span style='background-color:{color};color:white;padding:2px 8px;border-radius:4px;'>"
                f"{classification.category}</span>",
                unsafe_allow_html=True,
            )
            st.caption(f"Confidence: {classification.confidence:.0%}")

    if approval_check.requires_approval:
        st.warning(f" {approval_check.risk_level.upper()} risk - Approval required")
        for reason in approval_check.reasons:
            if not reason.startswith("keyword:"):
                st.caption(f"  {reason}")

    st.divider()

    st.markdown("**Content:**")
    content = email.body if email.body else email.snippet
    st.text_area("Email body", value=content, height=200, disabled=True, label_visibility="collapsed")

    if email.has_attachments:
        st.caption(f" Attachments: {', '.join(email.attachment_names)}")

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Classify", key=f"classify_{email.id}"):
            _classify_email(email)

    with col2:
        if (
            classification
            and classification.category in ["NEEDS_REPLY", "MEETING_REQUEST"]
            and st.button("Draft Reply", key=f"draft_{email.id}")
        ):
            _draft_reply(email)

    with col3:
        if email.is_unread and st.button("Mark Read", key=f"read_{email.id}"):
            _mark_as_read(email)

    with col4:
        if st.button("Trust Sender", key=f"trust_{email.id}"):
            _add_known_sender(email)


def _get_classification(email: EmailMessage) -> ClassificationResult | None:
    """Get cached classification for an email."""
    cache_key = f"classification_{email.id}"
    return st.session_state.get(cache_key)


def _get_approval_check(email: EmailMessage, classification: ClassificationResult | None):
    """Get approval check for an email."""
    checker = ApprovalChecker()
    return checker.check_email(email, classification)


def _classify_email(email: EmailMessage) -> None:
    """Classify an email and cache the result."""
    with st.spinner("Classifying email..."):
        try:
            classifier = EmailClassifier()
            result = classifier.classify(email)
            st.session_state[f"classification_{email.id}"] = result

            db = Database()
            db_email = db.save_email(email)
            approval = _get_approval_check(email, result)
            db.save_classification(
                email_id=db_email.id,
                category=result.category,
                confidence=result.confidence,
                reasoning=result.reasoning,
                requires_approval=approval.requires_approval,
                approval_reasons=approval.reasons,
            )

            st.success(f"Classified as {result.category} ({result.confidence:.0%})")
            st.rerun()
        except Exception:
            logger.exception("Classification failed")
            st.error("Failed to classify email")


def _draft_reply(email: EmailMessage) -> None:
    """Draft a reply to an email."""
    with st.spinner("Drafting reply..."):
        try:
            drafter = ReplyDrafter()
            draft = drafter.draft_reply(email)

            st.session_state[f"draft_content_{email.id}"] = draft

            db = Database()
            db_email = db.save_email(email)
            db.save_draft(
                email_id=db_email.id,
                subject=f"Re: {email.subject}",
                body=draft,
            )

            st.success("Draft created! Check the Drafts page.")
        except Exception:
            logger.exception("Drafting failed")
            st.error("Failed to create draft")


def _mark_as_read(email: EmailMessage) -> None:
    """Mark an email as read."""
    try:
        gmail = GmailService()
        if gmail.mark_as_read(email.id):
            st.success("Marked as read")
            st.session_state.pop("emails", None)
            st.rerun()
    except Exception:
        logger.exception("Failed to mark as read")
        st.error("Failed to mark as read")


def _add_known_sender(email: EmailMessage) -> None:
    """Add sender to known senders list."""
    checker = ApprovalChecker()
    if checker.add_known_sender(email.sender_email, email.sender):
        st.success(f"Added {email.sender_email} to trusted senders")
    else:
        st.error("Failed to add sender")


def _format_date(date: datetime) -> str:
    """Format date for display."""
    now = datetime.now(date.tzinfo) if date.tzinfo else datetime.now()
    diff = now - date

    if diff.days == 0:
        return date.strftime("%H:%M")
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return date.strftime("%A")
    else:
        return date.strftime("%b %d")
