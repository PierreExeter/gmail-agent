"""Tests for the approval checker."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from agent.approval import ApprovalCheck, ApprovalChecker
from agent.classifier import ClassificationResult
from services.gmail_service import EmailMessage


def create_test_email(
    subject: str = "Test Subject",
    body: str = "Test body content",
    sender: str = "Test Sender",
    sender_email: str = "test@example.com",
) -> EmailMessage:
    """Create a test email message."""
    return EmailMessage(
        id="test123",
        thread_id="thread123",
        subject=subject,
        sender=sender,
        sender_email=sender_email,
        recipients=["recipient@example.com"],
        date=datetime.now(),
        snippet=body[:100],
        body=body,
        labels=["INBOX"],
        is_unread=True,
        has_attachments=False,
        attachment_names=[],
    )


def test_approval_check_dataclass() -> None:
    """Test ApprovalCheck dataclass."""
    check = ApprovalCheck(
        requires_approval=True,
        reasons=["unknown_sender", "sensitive_content"],
        risk_level="high",
    )

    assert check.requires_approval is True
    assert len(check.reasons) == 2
    assert check.risk_level == "high"


def test_approval_check_defaults() -> None:
    """Test ApprovalCheck default values."""
    check = ApprovalCheck(requires_approval=False)

    assert check.reasons == []
    assert check.risk_level == "low"


def test_checker_initialization() -> None:
    """Test ApprovalChecker initialization."""
    checker = ApprovalChecker(
        confidence_threshold=0.8,
        sensitive_keywords=["urgent", "payment"],
    )

    assert checker.confidence_threshold == 0.8
    assert checker.sensitive_keywords == ["urgent", "payment"]


@patch("agent.approval.Database")
def test_check_email_unknown_sender(mock_db_class: MagicMock) -> None:
    """Test checking email from unknown sender."""
    mock_db = MagicMock()
    mock_db.is_known_sender.return_value = False
    mock_db_class.return_value = mock_db

    checker = ApprovalChecker(db=mock_db)
    email = create_test_email(sender_email="unknown@example.com")

    result = checker.check_email(email)

    assert result.requires_approval is True
    assert "unknown_sender" in result.reasons
    assert result.risk_level == "medium"


@patch("agent.approval.Database")
def test_check_email_known_sender(mock_db_class: MagicMock) -> None:
    """Test checking email from known sender."""
    mock_db = MagicMock()
    mock_db.is_known_sender.return_value = True
    mock_db_class.return_value = mock_db

    checker = ApprovalChecker(db=mock_db)
    email = create_test_email(sender_email="known@example.com")

    result = checker.check_email(email)

    assert "unknown_sender" not in result.reasons


@patch("agent.approval.Database")
def test_check_email_sensitive_keywords(mock_db_class: MagicMock) -> None:
    """Test checking email with sensitive keywords."""
    mock_db = MagicMock()
    mock_db.is_known_sender.return_value = True
    mock_db_class.return_value = mock_db

    checker = ApprovalChecker(db=mock_db, sensitive_keywords=["urgent", "payment", "$"])
    email = create_test_email(
        subject="URGENT: Payment required",
        body="Please pay $500 immediately.",
    )

    result = checker.check_email(email)

    assert result.requires_approval is True
    assert "sensitive_content" in result.reasons
    assert result.risk_level == "high"


@patch("agent.approval.Database")
def test_check_email_low_confidence(mock_db_class: MagicMock) -> None:
    """Test checking email with low classification confidence."""
    mock_db = MagicMock()
    mock_db.is_known_sender.return_value = True
    mock_db_class.return_value = mock_db

    checker = ApprovalChecker(db=mock_db, confidence_threshold=0.7)
    email = create_test_email()
    classification = ClassificationResult(
        category="NEEDS_REPLY",
        confidence=0.5,
        reasoning="Uncertain classification",
    )

    result = checker.check_email(email, classification)

    assert result.requires_approval is True
    assert "low_confidence" in result.reasons


@patch("agent.approval.Database")
def test_check_draft_commitments(mock_db_class: MagicMock) -> None:
    """Test checking draft with commitment language."""
    mock_db = MagicMock()
    mock_db.is_known_sender.return_value = True
    mock_db_class.return_value = mock_db

    checker = ApprovalChecker(db=mock_db)
    email = create_test_email()
    draft = "I will deliver the project by Friday. I guarantee this will work."

    result = checker.check_draft(draft, email)

    assert result.requires_approval is True
    assert "contains_commitments" in result.reasons
    assert result.risk_level == "high"


@patch("agent.approval.Database")
def test_check_draft_sensitive_keywords(mock_db_class: MagicMock) -> None:
    """Test checking draft with sensitive keywords."""
    mock_db = MagicMock()
    mock_db.is_known_sender.return_value = True
    mock_db_class.return_value = mock_db

    checker = ApprovalChecker(db=mock_db, sensitive_keywords=["payment", "invoice"])
    email = create_test_email()
    draft = "Please send the payment for the invoice attached."

    result = checker.check_draft(draft, email)

    assert result.requires_approval is True
    assert "draft_contains_sensitive_keywords" in result.reasons


@patch("agent.approval.Database")
def test_check_calendar_action_external_attendees(mock_db_class: MagicMock) -> None:
    """Test checking calendar action with external attendees."""
    mock_db = MagicMock()
    mock_db.is_known_sender.return_value = False
    mock_db_class.return_value = mock_db

    checker = ApprovalChecker(db=mock_db)

    result = checker.check_calendar_action(
        summary="Project Meeting",
        attendees=["external@other.com"],
        is_external=True,
    )

    assert result.requires_approval is True
    assert "external_attendees" in result.reasons


@patch("agent.approval.Database")
def test_should_auto_approve_fyi(mock_db_class: MagicMock) -> None:
    """Test auto-approval for FYI emails."""
    mock_db = MagicMock()
    mock_db.is_known_sender.return_value = True
    mock_db_class.return_value = mock_db

    checker = ApprovalChecker(db=mock_db)
    email = create_test_email(
        subject="Newsletter",
        body="Weekly update",
    )
    classification = ClassificationResult(
        category="FYI_ONLY",
        confidence=0.9,
        reasoning="Newsletter",
    )

    result = checker.should_auto_approve(email, classification)

    assert result is True


@patch("agent.approval.Database")
def test_should_not_auto_approve_low_confidence(mock_db_class: MagicMock) -> None:
    """Test no auto-approval for low confidence."""
    mock_db = MagicMock()
    mock_db.is_known_sender.return_value = True
    mock_db_class.return_value = mock_db

    checker = ApprovalChecker(db=mock_db, confidence_threshold=0.7)
    email = create_test_email()
    classification = ClassificationResult(
        category="NEEDS_REPLY",
        confidence=0.6,
        reasoning="Uncertain",
    )

    result = checker.should_auto_approve(email, classification)

    assert result is False


def test_contains_commitments() -> None:
    """Test commitment language detection."""
    checker = ApprovalChecker()

    assert checker._contains_commitments("I will send it tomorrow") is True
    assert checker._contains_commitments("I'll get back to you") is True
    assert checker._contains_commitments("I promise to deliver") is True
    assert checker._contains_commitments("We guarantee results") is True
    assert checker._contains_commitments("Thank you for your email") is False


def test_find_sensitive_keywords() -> None:
    """Test sensitive keyword detection."""
    checker = ApprovalChecker(sensitive_keywords=["urgent", "payment", "deadline"])

    found = checker._find_sensitive_keywords("This is URGENT and requires payment")
    assert "urgent" in found
    assert "payment" in found
    assert "deadline" not in found


def test_get_risk_summary() -> None:
    """Test risk summary generation."""
    checker = ApprovalChecker()

    check = ApprovalCheck(
        requires_approval=True,
        reasons=["unknown_sender", "sensitive_content"],
        risk_level="high",
    )

    summary = checker.get_risk_summary(check)

    assert "HIGH" in summary
    assert "Unknown sender" in summary


def test_get_risk_summary_no_approval() -> None:
    """Test risk summary when no approval needed."""
    checker = ApprovalChecker()

    check = ApprovalCheck(requires_approval=False)

    summary = checker.get_risk_summary(check)

    assert summary == "No approval required"
