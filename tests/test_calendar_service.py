"""Tests for the Calendar service."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from services.calendar_service import CalendarEvent, CalendarService, MeetingDetails, TimeSlot


def test_calendar_event_dataclass() -> None:
    """Test CalendarEvent dataclass."""
    event = CalendarEvent(
        id="event123",
        summary="Team Meeting",
        description="Weekly sync",
        start=datetime(2024, 1, 15, 10, 0),
        end=datetime(2024, 1, 15, 11, 0),
        location="Conference Room A",
        attendees=["john@example.com", "jane@example.com"],
        is_all_day=False,
        status="confirmed",
        html_link="https://calendar.google.com/event/123",
    )

    assert event.id == "event123"
    assert event.summary == "Team Meeting"
    assert len(event.attendees) == 2


def test_time_slot_dataclass() -> None:
    """Test TimeSlot dataclass."""
    slot = TimeSlot(
        start=datetime(2024, 1, 15, 14, 0),
        end=datetime(2024, 1, 15, 15, 0),
        duration_minutes=60,
    )

    assert slot.duration_minutes == 60


def test_meeting_details_dataclass() -> None:
    """Test MeetingDetails dataclass."""
    meeting = MeetingDetails(
        summary="Project Review",
        description="Quarterly review",
        start=datetime(2024, 1, 15, 14, 0),
        duration_minutes=90,
        attendees=["team@example.com"],
        location="Zoom",
        timezone="America/New_York",
    )

    assert meeting.summary == "Project Review"
    assert meeting.duration_minutes == 90


def test_parse_event_timed() -> None:
    """Test parsing a timed event."""
    service = CalendarService()

    event_data = {
        "id": "event123",
        "summary": "Meeting",
        "description": "Test meeting",
        "start": {"dateTime": "2024-01-15T10:00:00+00:00"},
        "end": {"dateTime": "2024-01-15T11:00:00+00:00"},
        "location": "Room A",
        "attendees": [
            {"email": "john@example.com"},
            {"email": "jane@example.com"},
        ],
        "status": "confirmed",
        "htmlLink": "https://calendar.google.com/event/123",
    }

    event = service._parse_event(event_data)

    assert event.id == "event123"
    assert event.summary == "Meeting"
    assert event.is_all_day is False
    assert len(event.attendees) == 2


def test_parse_event_all_day() -> None:
    """Test parsing an all-day event."""
    service = CalendarService()

    event_data = {
        "id": "event456",
        "summary": "Holiday",
        "start": {"date": "2024-01-15"},
        "end": {"date": "2024-01-16"},
        "status": "confirmed",
    }

    event = service._parse_event(event_data)

    assert event.id == "event456"
    assert event.is_all_day is True


@patch("services.calendar_service.get_calendar_service")
def test_list_events(mock_get_service: MagicMock) -> None:
    """Test listing calendar events."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service

    mock_service.events().list().execute.return_value = {
        "items": [
            {
                "id": "event1",
                "summary": "Meeting 1",
                "start": {"dateTime": "2024-01-15T10:00:00+00:00"},
                "end": {"dateTime": "2024-01-15T11:00:00+00:00"},
                "status": "confirmed",
            },
            {
                "id": "event2",
                "summary": "Meeting 2",
                "start": {"dateTime": "2024-01-15T14:00:00+00:00"},
                "end": {"dateTime": "2024-01-15T15:00:00+00:00"},
                "status": "confirmed",
            },
        ]
    }

    calendar = CalendarService(service=mock_service)
    events = calendar.list_events()

    assert len(events) == 2
    assert events[0].summary == "Meeting 1"
    assert events[1].summary == "Meeting 2"


@patch("services.calendar_service.get_calendar_service")
def test_create_event(mock_get_service: MagicMock) -> None:
    """Test creating a calendar event."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service

    mock_service.events().insert().execute.return_value = {
        "id": "new_event",
        "summary": "New Meeting",
        "start": {"dateTime": "2024-01-15T10:00:00+00:00"},
        "end": {"dateTime": "2024-01-15T11:00:00+00:00"},
        "status": "confirmed",
    }

    calendar = CalendarService(service=mock_service)
    meeting = MeetingDetails(
        summary="New Meeting",
        start=datetime(2024, 1, 15, 10, 0, tzinfo=ZoneInfo("UTC")),
        duration_minutes=60,
    )

    event = calendar.create_event(meeting)

    assert event is not None
    assert event.id == "new_event"
    assert event.summary == "New Meeting"


@patch("services.calendar_service.get_calendar_service")
def test_create_event_with_attendees(mock_get_service: MagicMock) -> None:
    """Test creating event with attendees."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service

    mock_service.events().insert().execute.return_value = {
        "id": "event_with_attendees",
        "summary": "Team Meeting",
        "start": {"dateTime": "2024-01-15T10:00:00+00:00"},
        "end": {"dateTime": "2024-01-15T11:00:00+00:00"},
        "attendees": [{"email": "john@example.com"}, {"email": "jane@example.com"}],
        "status": "confirmed",
    }

    calendar = CalendarService(service=mock_service)
    meeting = MeetingDetails(
        summary="Team Meeting",
        start=datetime(2024, 1, 15, 10, 0, tzinfo=ZoneInfo("UTC")),
        duration_minutes=60,
        attendees=["john@example.com", "jane@example.com"],
    )

    event = calendar.create_event(meeting)

    assert event is not None
    assert len(event.attendees) == 2


def test_create_event_no_start_time() -> None:
    """Test creating event without start time fails."""
    calendar = CalendarService()
    meeting = MeetingDetails(
        summary="Meeting without time",
        duration_minutes=60,
    )

    event = calendar.create_event(meeting)
    assert event is None


@patch("services.calendar_service.get_calendar_service")
def test_delete_event(mock_get_service: MagicMock) -> None:
    """Test deleting a calendar event."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service

    mock_service.events().delete().execute.return_value = None

    calendar = CalendarService(service=mock_service)
    result = calendar.delete_event("event123")

    assert result is True
    mock_service.events().delete.assert_called_with(
        calendarId="primary",
        eventId="event123",
        sendNotifications=True,
    )


@patch("services.calendar_service.get_calendar_service")
def test_check_availability_free(mock_get_service: MagicMock) -> None:
    """Test checking availability when time is free."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service

    mock_service.events().list().execute.return_value = {"items": []}

    calendar = CalendarService(service=mock_service)
    start = datetime(2024, 1, 15, 10, 0, tzinfo=ZoneInfo("UTC"))
    end = datetime(2024, 1, 15, 11, 0, tzinfo=ZoneInfo("UTC"))

    is_available = calendar.check_availability(start, end)

    assert is_available is True


@patch("services.calendar_service.get_calendar_service")
def test_check_availability_busy(mock_get_service: MagicMock) -> None:
    """Test checking availability when time is busy."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service

    mock_service.events().list().execute.return_value = {
        "items": [
            {
                "id": "blocking_event",
                "summary": "Existing Meeting",
                "start": {"dateTime": "2024-01-15T09:30:00+00:00"},
                "end": {"dateTime": "2024-01-15T10:30:00+00:00"},
                "status": "confirmed",
            }
        ]
    }

    calendar = CalendarService(service=mock_service)
    start = datetime(2024, 1, 15, 10, 0, tzinfo=ZoneInfo("UTC"))
    end = datetime(2024, 1, 15, 11, 0, tzinfo=ZoneInfo("UTC"))

    is_available = calendar.check_availability(start, end)

    assert is_available is False


def test_find_free_slots_empty_calendar() -> None:
    """Test finding free slots with empty calendar."""
    with patch.object(CalendarService, "list_events", return_value=[]):
        calendar = CalendarService(timezone="UTC")
        now = datetime.now(ZoneInfo("UTC")).replace(hour=10, minute=0, second=0, microsecond=0)

        slots = calendar.find_free_slots(
            start_date=now,
            end_date=now + timedelta(days=1),
            duration_minutes=60,
            working_hours=(9, 17),
        )

        assert len(slots) > 0
        for slot in slots:
            assert slot.duration_minutes == 60


def test_find_free_slots_respects_working_hours() -> None:
    """Test that free slots respect working hours."""
    with patch.object(CalendarService, "list_events", return_value=[]):
        calendar = CalendarService(timezone="UTC")
        now = datetime.now(ZoneInfo("UTC")).replace(hour=9, minute=0, second=0, microsecond=0)

        slots = calendar.find_free_slots(
            start_date=now,
            end_date=now + timedelta(hours=10),
            duration_minutes=60,
            working_hours=(9, 17),
        )

        for slot in slots:
            assert slot.start.hour >= 9
            assert slot.end.hour <= 17
