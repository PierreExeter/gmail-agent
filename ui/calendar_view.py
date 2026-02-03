"""Calendar view component for Streamlit UI."""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from db.database import Database
from db.models import CalendarAction
from services.calendar_service import CalendarEvent, CalendarService, MeetingDetails

logger = logging.getLogger(__name__)


def _clear_calendar_events_cache() -> None:
    """Clear all calendar events cache entries."""
    keys_to_remove = [k for k in st.session_state if k.startswith("calendar_events_")]
    for key in keys_to_remove:
        st.session_state.pop(key, None)


def render_calendar() -> None:
    """Render the calendar view."""
    st.header("Calendar")

    tabs = st.tabs(["Upcoming Events", "Pending Meetings", "Create Event"])

    with tabs[0]:
        _render_upcoming_events()

    with tabs[1]:
        _render_pending_meetings()

    with tabs[2]:
        _render_create_event()


def _render_upcoming_events() -> None:
    """Render upcoming calendar events."""
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        days_ahead = st.slider("Days to show", 1, 30, 7)
    with col2:
        timezone = st.selectbox(
            "Timezone",
            ["UTC", "America/New_York", "America/Los_Angeles", "Europe/London", "Europe/Paris", "Asia/Tokyo"],
            index=0,
        )
    with col3:
        if st.button("Refresh", type="primary"):
            _clear_calendar_events_cache()
            st.rerun()

    events = _fetch_events(days_ahead, timezone)

    if not events:
        st.info("No upcoming events found.")
        return

    for event in events:
        _render_event_card(event)


def _fetch_events(days_ahead: int, timezone: str) -> list[CalendarEvent]:
    """Fetch calendar events."""
    cache_key = f"calendar_events_{days_ahead}_{timezone}"
    if cache_key not in st.session_state:
        try:
            tz = ZoneInfo(timezone)
            now = datetime.now(tz)
            end = now + timedelta(days=days_ahead)

            calendar = CalendarService(timezone=timezone)
            st.session_state[cache_key] = calendar.list_events(
                start_date=now,
                end_date=end,
            )
        except Exception:
            logger.exception("Failed to fetch events")
            st.error("Failed to load calendar. Check your authentication.")
            return []
    return st.session_state[cache_key]


def _render_event_card(event: CalendarEvent) -> None:
    """Render a single event card."""
    time_str = "All day" if event.is_all_day else f"{event.start.strftime('%H:%M')} - {event.end.strftime('%H:%M')}"
    date_str = event.start.strftime("%A, %B %d")

    with st.expander(f" **{event.summary}** - {date_str} ({time_str})", expanded=False):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**Time:** {time_str}")
            st.markdown(f"**Date:** {date_str}")
            if event.location:
                st.markdown(f"**Location:** {event.location}")
            if event.attendees:
                st.markdown(f"**Attendees:** {', '.join(event.attendees[:5])}")
                if len(event.attendees) > 5:
                    st.caption(f"... and {len(event.attendees) - 5} more")

        with col2:
            status_colors = {
                "confirmed": "green",
                "tentative": "orange",
                "cancelled": "red",
            }
            color = status_colors.get(event.status, "gray")
            st.markdown(
                f"<span style='background-color:{color};color:white;padding:2px 8px;border-radius:4px;'>"
                f"{event.status.upper()}</span>",
                unsafe_allow_html=True,
            )

        if event.description:
            st.divider()
            st.markdown("**Description:**")
            st.text(event.description[:500])

        if event.html_link:
            st.markdown(f"[Open in Google Calendar]({event.html_link})")


def _render_pending_meetings() -> None:
    """Render pending meeting requests."""
    pending = _fetch_pending_calendar_actions()

    if not pending:
        st.info("No pending meeting requests.")
        return

    for action in pending:
        _render_pending_action(action)


def _fetch_pending_calendar_actions() -> list[CalendarAction]:
    """Fetch pending calendar actions."""
    if "pending_calendar_actions" not in st.session_state:
        try:
            db = Database()
            st.session_state["pending_calendar_actions"] = db.get_pending_calendar_actions()
        except Exception:
            logger.exception("Failed to fetch pending actions")
            return []
    return st.session_state["pending_calendar_actions"]


def _render_pending_action(action: CalendarAction) -> None:
    """Render a pending calendar action."""
    with st.expander(f" **{action.summary}** - {action.action_type}", expanded=True):
        if action.start_time:
            st.markdown(f"**Proposed time:** {action.start_time.strftime('%Y-%m-%d %H:%M')}")
        if action.end_time:
            duration = (action.end_time - action.start_time).total_seconds() / 60
            st.markdown(f"**Duration:** {int(duration)} minutes")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Approve", key=f"approve_cal_{action.id}", type="primary"):
                _approve_calendar_action(action)

        with col2:
            if st.button("Reject", key=f"reject_cal_{action.id}"):
                _reject_calendar_action(action.id)


def _approve_calendar_action(action: CalendarAction) -> None:
    """Approve and create a calendar event."""
    with st.spinner("Creating event..."):
        try:
            import json

            calendar = CalendarService()
            attendees = json.loads(action.attendees) if action.attendees else []

            meeting = MeetingDetails(
                summary=action.summary,
                start=action.start_time,
                end=action.end_time,
                attendees=attendees,
            )

            event = calendar.create_event(meeting)
            if event:
                db = Database()
                db.approve_calendar_action(action.id, event.id)
                st.success("Event created!")
                st.session_state.pop("pending_calendar_actions", None)
                _clear_calendar_events_cache()
            else:
                st.error("Failed to create event")
                return
        except Exception:
            logger.exception("Failed to create event")
            st.error("Failed to create event")
            return

    st.rerun()


def _reject_calendar_action(action_id: int) -> None:
    """Reject a calendar action."""
    try:
        db = Database()
        db.reject_calendar_action(action_id)
        st.success("Meeting request rejected")
        st.session_state.pop("pending_calendar_actions", None)
    except Exception:
        logger.exception("Failed to reject action")
        st.error("Failed to reject")
        return

    st.rerun()


def _render_create_event() -> None:
    """Render the create event form."""
    st.subheader("Create New Event")

    with st.form("create_event_form"):
        summary = st.text_input("Event Title", placeholder="Meeting with John")
        description = st.text_area("Description", placeholder="Discussion about project X")

        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date")
            start_time = st.time_input("Start Time")
        with col2:
            duration = st.selectbox("Duration", [15, 30, 45, 60, 90, 120], index=3)
            timezone = st.selectbox(
                "Timezone",
                ["UTC", "America/New_York", "America/Los_Angeles", "Europe/London"],
                index=0,
            )

        location = st.text_input("Location", placeholder="Conference Room A or Zoom link")
        attendees = st.text_input("Attendees", placeholder="email1@example.com, email2@example.com")

        submitted = st.form_submit_button("Create Event", type="primary")

        if submitted:
            if not summary:
                st.error("Event title is required")
            else:
                _create_event(
                    summary=summary,
                    description=description,
                    date=date,
                    start_time=start_time,
                    duration=duration,
                    timezone=timezone,
                    location=location,
                    attendees=attendees,
                )


def _create_event(
    summary: str,
    description: str,
    date,
    start_time,
    duration: int,
    timezone: str,
    location: str,
    attendees: str,
) -> None:
    """Create a new calendar event."""
    with st.spinner("Creating event..."):
        try:
            tz = ZoneInfo(timezone)
            start = datetime.combine(date, start_time, tzinfo=tz)
            end = start + timedelta(minutes=duration)

            attendee_list = [a.strip() for a in attendees.split(",") if a.strip()]

            meeting = MeetingDetails(
                summary=summary,
                description=description,
                start=start,
                end=end,
                attendees=attendee_list if attendee_list else None,
                location=location,
                timezone=timezone,
            )

            calendar = CalendarService(timezone=timezone)
            event = calendar.create_event(meeting)

            if event:
                st.success(f"Event created: {event.summary}")
                _clear_calendar_events_cache()
            else:
                st.error("Failed to create event")
        except Exception:
            logger.exception("Failed to create event")
            st.error("Failed to create event. Check your authentication.")
