"""Database operations for the Gmail Agent."""

import json
import logging
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, joinedload, sessionmaker

import config
from db.models import Base, CalendarAction, Classification, Draft, Email, Feedback, KnownSender
from services.gmail_service import EmailMessage

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(config.DATABASE_URL, echo=False)
        Base.metadata.create_all(_engine)
    return _engine


def get_session_factory():
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get a database session context manager."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class Database:
    """Database operations wrapper."""

    def __init__(self, session: Session | None = None) -> None:
        """Initialize with optional session."""
        self._session = session

    @contextmanager
    def _get_session(self) -> Generator[Session, None, None]:
        """Get session context."""
        if self._session:
            yield self._session
        else:
            with get_db() as session:
                yield session

    def save_email(self, email: EmailMessage) -> Email:
        """Save or update an email in the database."""
        with self._get_session() as session:
            db_email = session.query(Email).filter(Email.gmail_id == email.id).first()
            if db_email is None:
                db_email = Email(gmail_id=email.id)
                session.add(db_email)

            db_email.thread_id = email.thread_id
            db_email.subject = email.subject
            db_email.sender = email.sender
            db_email.sender_email = email.sender_email
            db_email.recipients = json.dumps(email.recipients)
            db_email.date = email.date
            db_email.snippet = email.snippet
            db_email.body = email.body
            db_email.labels = json.dumps(email.labels)
            db_email.is_unread = email.is_unread
            db_email.has_attachments = email.has_attachments
            db_email.updated_at = datetime.utcnow()

            session.flush()
            session.expunge(db_email)
            return db_email

    def get_email(self, gmail_id: str) -> Email | None:
        """Get an email by Gmail ID."""
        with self._get_session() as session:
            return session.query(Email).filter(Email.gmail_id == gmail_id).first()

    def get_email_by_id(self, email_id: int) -> Email | None:
        """Get an email by database ID."""
        with self._get_session() as session:
            return session.query(Email).filter(Email.id == email_id).first()

    def get_emails(self, unread_only: bool = False, limit: int = 50) -> list[Email]:
        """Get emails from database."""
        with self._get_session() as session:
            query = session.query(Email)
            if unread_only:
                query = query.filter(Email.is_unread.is_(True))
            return query.order_by(Email.date.desc()).limit(limit).all()

    def save_classification(
        self,
        email_id: int,
        category: str,
        confidence: float,
        reasoning: str = "",
        requires_approval: bool = False,
        approval_reasons: list[str] | None = None,
    ) -> Classification:
        """Save a classification for an email."""
        with self._get_session() as session:
            classification = Classification(
                email_id=email_id,
                category=category,
                confidence=confidence,
                reasoning=reasoning,
                requires_approval=requires_approval,
                approval_reasons=json.dumps(approval_reasons or []),
            )
            session.add(classification)
            session.flush()
            session.expunge(classification)
            return classification

    def get_latest_classification(self, email_id: int) -> Classification | None:
        """Get the most recent classification for an email."""
        with self._get_session() as session:
            return (
                session.query(Classification)
                .filter(Classification.email_id == email_id)
                .order_by(Classification.created_at.desc())
                .first()
            )

    def get_pending_approvals(self) -> list[Classification]:
        """Get classifications requiring approval."""
        with self._get_session() as session:
            return (
                session.query(Classification)
                .filter(
                    Classification.requires_approval.is_(True),
                    Classification.is_approved.is_(False),
                )
                .order_by(Classification.created_at.desc())
                .all()
            )

    def approve_classification(self, classification_id: int) -> bool:
        """Mark a classification as approved."""
        with self._get_session() as session:
            classification = session.query(Classification).filter(Classification.id == classification_id).first()
            if classification:
                classification.is_approved = True
                classification.approved_at = datetime.utcnow()
                return True
            return False

    def save_draft(self, email_id: int, subject: str, body: str) -> Draft:
        """Save a draft reply."""
        with self._get_session() as session:
            draft = Draft(
                email_id=email_id,
                subject=subject,
                body=body,
                status="pending",
            )
            session.add(draft)
            session.flush()
            session.expunge(draft)
            return draft

    def get_draft(self, draft_id: int) -> Draft | None:
        """Get a draft by ID."""
        with self._get_session() as session:
            return session.query(Draft).filter(Draft.id == draft_id).first()

    def get_pending_drafts(self) -> list[Draft]:
        """Get drafts awaiting approval."""
        with self._get_session() as session:
            drafts = (
                session.query(Draft)
                .options(joinedload(Draft.email))
                .filter(Draft.status == "pending", Draft.is_approved.is_(False))
                .order_by(Draft.created_at.desc())
                .all()
            )
            for draft in drafts:
                session.expunge(draft)
            return drafts

    def update_draft(self, draft_id: int, body: str) -> bool:
        """Update a draft's body."""
        with self._get_session() as session:
            draft = session.query(Draft).filter(Draft.id == draft_id).first()
            if draft:
                draft.body = body
                draft.updated_at = datetime.utcnow()
                return True
            return False

    def approve_draft(self, draft_id: int) -> bool:
        """Mark a draft as approved."""
        with self._get_session() as session:
            draft = session.query(Draft).filter(Draft.id == draft_id).first()
            if draft:
                draft.is_approved = True
                draft.approved_at = datetime.utcnow()
                draft.status = "approved"
                return True
            return False

    def mark_draft_sent(self, draft_id: int, message_id: str) -> bool:
        """Mark a draft as sent."""
        with self._get_session() as session:
            draft = session.query(Draft).filter(Draft.id == draft_id).first()
            if draft:
                draft.sent_at = datetime.utcnow()
                draft.sent_message_id = message_id
                draft.status = "sent"
                return True
            return False

    def reject_draft(self, draft_id: int) -> bool:
        """Reject a draft."""
        with self._get_session() as session:
            draft = session.query(Draft).filter(Draft.id == draft_id).first()
            if draft:
                draft.status = "rejected"
                return True
            return False

    def save_feedback(
        self,
        draft_id: int,
        rating: str,
        original_body: str = "",
        edited_body: str = "",
        comments: str = "",
    ) -> Feedback:
        """Save feedback on a draft."""
        with self._get_session() as session:
            feedback = Feedback(
                draft_id=draft_id,
                rating=rating,
                original_body=original_body,
                edited_body=edited_body,
                comments=comments,
            )
            session.add(feedback)
            session.flush()
            session.expunge(feedback)
            return feedback

    def save_calendar_action(
        self,
        action_type: str,
        summary: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        attendees: list[str] | None = None,
        email_id: int | None = None,
        event_id: str | None = None,
    ) -> CalendarAction:
        """Save a calendar action."""
        with self._get_session() as session:
            action = CalendarAction(
                email_id=email_id,
                action_type=action_type,
                event_id=event_id,
                summary=summary,
                start_time=start_time,
                end_time=end_time,
                attendees=json.dumps(attendees or []),
                status="pending",
            )
            session.add(action)
            session.flush()
            session.expunge(action)
            return action

    def get_pending_calendar_actions(self) -> list[CalendarAction]:
        """Get calendar actions awaiting approval."""
        with self._get_session() as session:
            return (
                session.query(CalendarAction)
                .filter(
                    CalendarAction.status == "pending",
                    CalendarAction.is_approved.is_(False),
                )
                .order_by(CalendarAction.created_at.desc())
                .all()
            )

    def approve_calendar_action(self, action_id: int, event_id: str | None = None) -> bool:
        """Approve a calendar action."""
        with self._get_session() as session:
            action = session.query(CalendarAction).filter(CalendarAction.id == action_id).first()
            if action:
                action.is_approved = True
                action.approved_at = datetime.utcnow()
                action.status = "approved"
                if event_id:
                    action.event_id = event_id
                return True
            return False

    def is_known_sender(self, email: str) -> bool:
        """Check if an email is from a known sender."""
        with self._get_session() as session:
            return session.query(KnownSender).filter(KnownSender.email == email.lower()).first() is not None

    def add_known_sender(self, email: str, name: str = "", trust_level: str = "normal") -> KnownSender:
        """Add a known sender."""
        with self._get_session() as session:
            # Check if sender already exists
            existing = session.query(KnownSender).filter(KnownSender.email == email.lower()).first()
            if existing:
                return existing

            sender = KnownSender(
                email=email.lower(),
                name=name,
                trust_level=trust_level,
            )
            session.add(sender)
            session.flush()
            session.expunge(sender)
            return sender

    def get_known_senders(self) -> list[KnownSender]:
        """Get all known senders."""
        with self._get_session() as session:
            return session.query(KnownSender).order_by(KnownSender.name).all()
