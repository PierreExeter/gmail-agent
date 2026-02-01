"""Meeting scheduling agent using LangChain."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEndpoint

import config
from services.calendar_service import CalendarService, MeetingDetails, TimeSlot
from services.gmail_service import EmailMessage

logger = logging.getLogger(__name__)


@dataclass
class MeetingExtraction:
    """Extracted meeting details from email."""

    has_meeting_request: bool
    title: str
    proposed_times: list[str]
    duration_minutes: int
    attendees: list[str]
    location: str
    notes: str


@dataclass
class SchedulingProposal:
    """Proposed meeting schedule."""

    meeting: MeetingDetails
    available_slots: list[TimeSlot]
    conflicts: list[str]
    suggested_reply: str


EXTRACTION_PROMPT = """Extract meeting details from this email. Identify if a meeting is being requested.

Email:
From: {sender}
Subject: {subject}
Content: {body}

Respond with a JSON object:
{{
    "has_meeting_request": true/false,
    "title": "meeting title or subject",
    "proposed_times": ["any mentioned times/dates"],
    "duration_minutes": estimated duration (default 60),
    "attendees": ["email addresses if mentioned"],
    "location": "location if mentioned",
    "notes": "relevant details"
}}

JSON:"""


class MeetingScheduler:
    """Handles meeting extraction and scheduling."""

    def __init__(
        self,
        model_id: str | None = None,
        api_key: str | None = None,
        calendar_service: CalendarService | None = None,
        timezone: str = "UTC",
    ) -> None:
        """
        Initialize the meeting scheduler.

        Args:
            model_id: HuggingFace model ID.
            api_key: HuggingFace API key.
            calendar_service: Optional CalendarService instance.
            timezone: Default timezone for scheduling.
        """
        self.model_id = model_id or config.LLM_MODEL_ID
        self.api_key = api_key or config.HUGGINGFACE_API_KEY
        self.timezone = timezone
        self._calendar = calendar_service
        self._llm: HuggingFaceEndpoint | None = None
        self._extraction_chain = None

    @property
    def llm(self) -> HuggingFaceEndpoint:
        """Get or create LLM instance."""
        if self._llm is None:
            self._llm = HuggingFaceEndpoint(
                repo_id=self.model_id,
                huggingfacehub_api_token=self.api_key,
                max_new_tokens=256,
                temperature=0.1,
                task="text-generation",
                provider="hf-inference",
            )
        return self._llm

    @property
    def calendar(self) -> CalendarService:
        """Get or create calendar service."""
        if self._calendar is None:
            self._calendar = CalendarService(timezone=self.timezone)
        return self._calendar

    @property
    def extraction_chain(self):
        """Get or create extraction chain."""
        if self._extraction_chain is None:
            prompt = ChatPromptTemplate.from_template(EXTRACTION_PROMPT)
            parser = JsonOutputParser()
            self._extraction_chain = prompt | self.llm | parser
        return self._extraction_chain

    def extract_meeting_details(self, email: EmailMessage) -> MeetingExtraction:
        """
        Extract meeting details from an email.

        Args:
            email: EmailMessage to analyze.

        Returns:
            MeetingExtraction with parsed details.
        """
        body = email.body[:2000] if email.body else email.snippet

        try:
            result = self.extraction_chain.invoke(
                {
                    "sender": email.sender,
                    "subject": email.subject,
                    "body": body,
                }
            )
            return self._parse_extraction(result, email)
        except Exception:
            logger.exception("Meeting extraction failed")
            return self._fallback_extraction(email)

    def create_scheduling_proposal(
        self,
        extraction: MeetingExtraction,
        email: EmailMessage,
    ) -> SchedulingProposal:
        """
        Create a scheduling proposal based on extracted details.

        Args:
            extraction: Extracted meeting details.
            email: Original email for context.

        Returns:
            SchedulingProposal with available slots and suggested reply.
        """
        now = datetime.now(ZoneInfo(self.timezone))
        end_range = now + timedelta(days=14)

        available_slots = self.calendar.find_free_slots(
            start_date=now,
            end_date=end_range,
            duration_minutes=extraction.duration_minutes,
        )

        conflicts = self._check_proposed_times(extraction.proposed_times)

        attendees = extraction.attendees or []
        if email.sender_email and email.sender_email not in attendees:
            attendees.append(email.sender_email)

        meeting = MeetingDetails(
            summary=extraction.title or f"Meeting: {email.subject}",
            description=extraction.notes,
            duration_minutes=extraction.duration_minutes,
            attendees=attendees,
            location=extraction.location,
            timezone=self.timezone,
        )

        suggested_reply = self._generate_scheduling_reply(extraction, available_slots[:5], conflicts)

        return SchedulingProposal(
            meeting=meeting,
            available_slots=available_slots[:10],
            conflicts=conflicts,
            suggested_reply=suggested_reply,
        )

    def schedule_meeting(
        self,
        meeting: MeetingDetails,
        slot: TimeSlot | None = None,
        start_time: datetime | None = None,
    ) -> str | None:
        """
        Schedule a meeting on the calendar.

        Args:
            meeting: MeetingDetails to schedule.
            slot: Optional TimeSlot to use.
            start_time: Optional specific start time.

        Returns:
            Event ID if successful, None otherwise.
        """
        if slot:
            meeting.start = slot.start
            meeting.end = slot.end
        elif start_time:
            meeting.start = start_time
            meeting.end = start_time + timedelta(minutes=meeting.duration_minutes)
        elif not meeting.start:
            logger.error("No start time provided for meeting")
            return None

        event = self.calendar.create_event(meeting)
        return event.id if event else None

    def _parse_extraction(self, result: dict, email: EmailMessage) -> MeetingExtraction:
        """Parse extraction result into MeetingExtraction."""
        has_meeting = result.get("has_meeting_request", False)

        if isinstance(has_meeting, str):
            has_meeting = has_meeting.lower() in ("true", "yes", "1")

        proposed_times = result.get("proposed_times", [])
        if isinstance(proposed_times, str):
            proposed_times = [proposed_times] if proposed_times else []

        attendees = result.get("attendees", [])
        if isinstance(attendees, str):
            attendees = [a.strip() for a in attendees.split(",") if a.strip()]

        return MeetingExtraction(
            has_meeting_request=bool(has_meeting),
            title=result.get("title", "") or email.subject,
            proposed_times=proposed_times,
            duration_minutes=int(result.get("duration_minutes", 60)),
            attendees=attendees,
            location=result.get("location", ""),
            notes=result.get("notes", ""),
        )

    def _fallback_extraction(self, email: EmailMessage) -> MeetingExtraction:
        """Fallback meeting extraction using heuristics."""
        combined = f"{email.subject} {email.body or email.snippet}".lower()

        has_meeting = any(
            word in combined
            for word in [
                "meeting",
                "call",
                "schedule",
                "calendar",
                "invite",
                "available",
                "discuss",
                "catch up",
                "sync",
            ]
        )

        duration = 60
        if "30 min" in combined or "half hour" in combined:
            duration = 30
        elif "2 hour" in combined:
            duration = 120
        elif "15 min" in combined:
            duration = 15

        return MeetingExtraction(
            has_meeting_request=has_meeting,
            title=email.subject,
            proposed_times=[],
            duration_minutes=duration,
            attendees=[email.sender_email] if email.sender_email else [],
            location="",
            notes="",
        )

    def _check_proposed_times(self, proposed_times: list[str]) -> list[str]:
        """Check for conflicts with proposed times."""
        conflicts = []
        for time_str in proposed_times:
            parsed = self._parse_time_string(time_str)
            if parsed:
                start, end = parsed
                if not self.calendar.check_availability(start, end):
                    conflicts.append(f"{time_str} - conflict detected")
        return conflicts

    def _parse_time_string(self, time_str: str) -> tuple[datetime, datetime] | None:
        """Attempt to parse a natural language time string."""
        tz = ZoneInfo(self.timezone)
        now = datetime.now(tz)

        patterns = [
            r"(\d{1,2}):(\d{2})\s*(am|pm)?",
            r"(\d{1,2})\s*(am|pm)",
        ]

        for pattern in patterns:
            match = re.search(pattern, time_str.lower())
            if match:
                try:
                    groups = match.groups()
                    hour = int(groups[0])
                    minute = int(groups[1]) if len(groups) > 1 and groups[1] and groups[1].isdigit() else 0
                    period = groups[-1] if groups[-1] in ("am", "pm") else None

                    if period == "pm" and hour < 12:
                        hour += 12
                    elif period == "am" and hour == 12:
                        hour = 0

                    start = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if start < now:
                        start += timedelta(days=1)
                    end = start + timedelta(hours=1)
                    return (start, end)
                except (ValueError, IndexError):
                    continue

        return None

    def _generate_scheduling_reply(
        self,
        extraction: MeetingExtraction,
        available_slots: list[TimeSlot],
        conflicts: list[str],
    ) -> str:
        """Generate a suggested reply for scheduling."""
        if conflicts:
            conflict_text = "\n".join(f"- {c}" for c in conflicts)
            slot_text = self._format_slots(available_slots[:3])
            return f"""Thank you for reaching out about scheduling a meeting.

Unfortunately, some of the proposed times have conflicts:
{conflict_text}

Here are some alternative times that work for me:
{slot_text}

Please let me know which of these works best for you.

Best regards"""

        if available_slots:
            slot_text = self._format_slots(available_slots[:3])
            return f"""Thank you for reaching out about scheduling a meeting.

I'm available at the following times:
{slot_text}

Please let me know which works best for you, and I'll send a calendar invite.

Best regards"""

        return """Thank you for reaching out about scheduling a meeting.

I'll check my calendar and get back to you with some available times.

Best regards"""

    def _format_slots(self, slots: list[TimeSlot]) -> str:
        """Format time slots for display."""
        lines = []
        for slot in slots:
            date_str = slot.start.strftime("%A, %B %d")
            time_str = slot.start.strftime("%I:%M %p")
            lines.append(f"- {date_str} at {time_str}")
        return "\n".join(lines)

    def set_model(self, model_id: str) -> None:
        """Change the scheduler model."""
        self.model_id = model_id
        self._llm = None
        self._extraction_chain = None
