"""SQLAlchemy models for the Gmail Agent database."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Email(Base):
    """Cached email data."""

    __tablename__ = "emails"

    id = Column(Integer, primary_key=True)
    gmail_id = Column(String(255), unique=True, nullable=False, index=True)
    thread_id = Column(String(255), nullable=False, index=True)
    subject = Column(String(500))
    sender = Column(String(255))
    sender_email = Column(String(255), index=True)
    recipients = Column(Text)
    date = Column(DateTime)
    snippet = Column(Text)
    body = Column(Text)
    labels = Column(Text)
    is_unread = Column(Boolean, default=True)
    has_attachments = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    classifications = relationship("Classification", back_populates="email", cascade="all, delete-orphan")
    drafts = relationship("Draft", back_populates="email", cascade="all, delete-orphan")


class Classification(Base):
    """Email classification history."""

    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    category = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text)
    requires_approval = Column(Boolean, default=False)
    approval_reasons = Column(Text)
    is_approved = Column(Boolean, default=False)
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    email = relationship("Email", back_populates="classifications")


class Draft(Base):
    """Draft email replies."""

    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    subject = Column(String(500))
    body = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    is_approved = Column(Boolean, default=False)
    approved_at = Column(DateTime)
    sent_at = Column(DateTime)
    sent_message_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    email = relationship("Email", back_populates="drafts")
    feedback = relationship("Feedback", back_populates="draft", cascade="all, delete-orphan")


class Feedback(Base):
    """User feedback on drafts for learning."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), nullable=False)
    rating = Column(String(50))
    original_body = Column(Text)
    edited_body = Column(Text)
    comments = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    draft = relationship("Draft", back_populates="feedback")


class CalendarAction(Base):
    """Log of calendar actions taken."""

    __tablename__ = "calendar_actions"

    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=True)
    action_type = Column(String(50), nullable=False)
    event_id = Column(String(255))
    summary = Column(String(500))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    attendees = Column(Text)
    status = Column(String(50), default="pending")
    is_approved = Column(Boolean, default=False)
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnownSender(Base):
    """Known/trusted email senders."""

    __tablename__ = "known_senders"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    trust_level = Column(String(50), default="normal")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
