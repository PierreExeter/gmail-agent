"""Google Calendar API service wrapper."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from googleapiclient.discovery import Resource

from auth.google_auth import get_calendar_service

logger = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    """Represents a calendar event."""

    id: str
    summary: str
    description: str
    start: datetime
    end: datetime
    location: str
    attendees: list[str]
    is_all_day: bool
    status: str
    html_link: str


@dataclass
class TimeSlot:
    """Represents an available time slot."""

    start: datetime
    end: datetime
    duration_minutes: int


@dataclass
class MeetingDetails:
    """Details for creating a meeting."""

    summary: str
    description: str = ""
    start: datetime | None = None
    end: datetime | None = None
    duration_minutes: int = 60
    attendees: list[str] | None = None
    location: str = ""
    timezone: str = "UTC"


class CalendarService:
    """Service for interacting with Google Calendar API."""

    def __init__(self, service: Resource | None = None, timezone: str = "UTC") -> None:
        """Initialize Calendar service."""
        self._service = service
        self.timezone = timezone

    @property
    def service(self) -> Resource:
        """Get or create Calendar service."""
        if self._service is None:
            self._service = get_calendar_service()
        return self._service

    def list_events(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        max_results: int = 50,
        calendar_id: str = "primary",
    ) -> list[CalendarEvent]:
        """
        List calendar events within a date range.

        Args:
            start_date: Start of date range (defaults to now).
            end_date: End of date range (defaults to 7 days from now).
            max_results: Maximum number of events to return.
            calendar_id: Calendar ID (defaults to primary).

        Returns:
            List of CalendarEvent objects.
        """
        if start_date is None:
            start_date = datetime.now(ZoneInfo(self.timezone))
        if end_date is None:
            end_date = start_date + timedelta(days=7)

        time_min = start_date.isoformat()
        time_max = end_date.isoformat()

        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])
            return [self._parse_event(e) for e in events]
        except Exception:
            logger.exception("Failed to list events")
            return []

    def get_event(self, event_id: str, calendar_id: str = "primary") -> CalendarEvent | None:
        """Get a single event by ID."""
        try:
            event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            return self._parse_event(event)
        except Exception:
            logger.exception("Failed to get event")
            return None

    def create_event(
        self,
        details: MeetingDetails,
        calendar_id: str = "primary",
        send_notifications: bool = True,
    ) -> CalendarEvent | None:
        """
        Create a new calendar event.

        Args:
            details: MeetingDetails object with event information.
            calendar_id: Calendar ID (defaults to primary).
            send_notifications: Whether to send invite notifications.

        Returns:
            Created CalendarEvent or None if failed.
        """
        if details.start is None:
            logger.error("Event start time is required")
            return None

        if details.end is None:
            details.end = details.start + timedelta(minutes=details.duration_minutes)

        event_body: dict[str, Any] = {
            "summary": details.summary,
            "description": details.description,
            "location": details.location,
            "start": {
                "dateTime": details.start.isoformat(),
                "timeZone": details.timezone,
            },
            "end": {
                "dateTime": details.end.isoformat(),
                "timeZone": details.timezone,
            },
        }

        if details.attendees:
            event_body["attendees"] = [{"email": email} for email in details.attendees]

        try:
            event = (
                self.service.events()
                .insert(
                    calendarId=calendar_id,
                    body=event_body,
                    sendNotifications=send_notifications,
                )
                .execute()
            )
            return self._parse_event(event)
        except Exception:
            logger.exception("Failed to create event")
            return None

    def update_event(
        self,
        event_id: str,
        updates: dict[str, Any],
        calendar_id: str = "primary",
        send_notifications: bool = True,
    ) -> CalendarEvent | None:
        """
        Update an existing calendar event.

        Args:
            event_id: Event ID to update.
            updates: Dictionary of fields to update.
            calendar_id: Calendar ID.
            send_notifications: Whether to send update notifications.

        Returns:
            Updated CalendarEvent or None if failed.
        """
        try:
            event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()

            for key, value in updates.items():
                if key in ("start", "end") and isinstance(value, datetime):
                    event[key] = {"dateTime": value.isoformat(), "timeZone": self.timezone}
                else:
                    event[key] = value

            updated = (
                self.service.events()
                .update(
                    calendarId=calendar_id,
                    eventId=event_id,
                    body=event,
                    sendNotifications=send_notifications,
                )
                .execute()
            )
            return self._parse_event(updated)
        except Exception:
            logger.exception("Failed to update event")
            return None

    def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        send_notifications: bool = True,
    ) -> bool:
        """Delete a calendar event."""
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendNotifications=send_notifications,
            ).execute()
            return True
        except Exception:
            logger.exception("Failed to delete event")
            return False

    def find_free_slots(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        duration_minutes: int = 60,
        working_hours: tuple[int, int] = (9, 17),
        calendar_id: str = "primary",
    ) -> list[TimeSlot]:
        """
        Find available time slots in the calendar.

        Args:
            start_date: Start of search range (defaults to now).
            end_date: End of search range (defaults to 7 days from now).
            duration_minutes: Required duration for the slot.
            working_hours: Tuple of (start_hour, end_hour) for working hours.
            calendar_id: Calendar ID.

        Returns:
            List of available TimeSlot objects.
        """
        tz = ZoneInfo(self.timezone)
        if start_date is None:
            start_date = datetime.now(tz)
        if end_date is None:
            end_date = start_date + timedelta(days=7)

        events = self.list_events(start_date, end_date, calendar_id=calendar_id)
        busy_times = [(e.start, e.end) for e in events if not e.is_all_day]
        busy_times.sort(key=lambda x: x[0])

        free_slots = []
        current = start_date

        while current < end_date:
            if current.hour < working_hours[0]:
                current = current.replace(hour=working_hours[0], minute=0, second=0, microsecond=0)
            elif current.hour >= working_hours[1]:
                current = (current + timedelta(days=1)).replace(
                    hour=working_hours[0], minute=0, second=0, microsecond=0
                )
                continue

            day_end = current.replace(hour=working_hours[1], minute=0, second=0, microsecond=0)
            slot_end = min(current + timedelta(minutes=duration_minutes), day_end)

            if slot_end > end_date:
                break

            is_free = True
            for busy_start, busy_end in busy_times:
                if current < busy_end and slot_end > busy_start:
                    is_free = False
                    current = busy_end
                    break

            if is_free:
                if (slot_end - current).total_seconds() >= duration_minutes * 60:
                    free_slots.append(
                        TimeSlot(
                            start=current,
                            end=slot_end,
                            duration_minutes=duration_minutes,
                        )
                    )
                current = current + timedelta(minutes=30)

        return free_slots

    def check_availability(
        self,
        start: datetime,
        end: datetime,
        calendar_id: str = "primary",
    ) -> bool:
        """
        Check if a time slot is available.

        Args:
            start: Start time to check.
            end: End time to check.
            calendar_id: Calendar ID.

        Returns:
            True if the slot is available, False otherwise.
        """
        events = self.list_events(start, end, calendar_id=calendar_id)
        for event in events:
            if event.is_all_day:
                continue
            if start < event.end and end > event.start:
                return False
        return True

    def _parse_event(self, event: dict[str, Any]) -> CalendarEvent:
        """Parse a Calendar API event into a CalendarEvent object."""
        start_data = event.get("start", {})
        end_data = event.get("end", {})

        is_all_day = "date" in start_data

        if is_all_day:
            start = datetime.fromisoformat(start_data["date"])
            end = datetime.fromisoformat(end_data["date"])
        else:
            start = datetime.fromisoformat(start_data.get("dateTime", ""))
            end = datetime.fromisoformat(end_data.get("dateTime", ""))

        attendees = [a.get("email", "") for a in event.get("attendees", []) if a.get("email")]

        return CalendarEvent(
            id=event["id"],
            summary=event.get("summary", "(No Title)"),
            description=event.get("description", ""),
            start=start,
            end=end,
            location=event.get("location", ""),
            attendees=attendees,
            is_all_day=is_all_day,
            status=event.get("status", "confirmed"),
            html_link=event.get("htmlLink", ""),
        )
