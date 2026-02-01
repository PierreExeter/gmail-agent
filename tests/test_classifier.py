"""Tests for the email classifier agent."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from agent.classifier import ClassificationResult, EmailClassifier
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


def test_classification_result_dataclass() -> None:
    """Test ClassificationResult dataclass."""
    result = ClassificationResult(
        category="NEEDS_REPLY",
        confidence=0.95,
        reasoning="Contains a question",
    )
    assert result.category == "NEEDS_REPLY"
    assert result.confidence == 0.95
    assert result.reasoning == "Contains a question"


def test_classifier_initialization() -> None:
    """Test EmailClassifier initialization."""
    classifier = EmailClassifier(
        model_id="test-model",
        api_key="test-key",
    )
    assert classifier.model_id == "test-model"
    assert classifier.api_key == "test-key"


def test_classifier_fallback_meeting() -> None:
    """Test fallback classification for meeting requests."""
    classifier = EmailClassifier()
    email = create_test_email(
        subject="Can we schedule a meeting?",
        body="Hi, I'd like to schedule a call to discuss the project.",
    )

    result = classifier._fallback_classification(email)
    assert result.category == "MEETING_REQUEST"
    assert result.confidence == 0.6


def test_classifier_fallback_needs_reply() -> None:
    """Test fallback classification for emails needing reply."""
    classifier = EmailClassifier()
    email = create_test_email(
        subject="Question about the report",
        body="Could you please send me the latest version?",
    )

    result = classifier._fallback_classification(email)
    assert result.category == "NEEDS_REPLY"
    assert result.confidence == 0.6


def test_classifier_fallback_task_action() -> None:
    """Test fallback classification for task emails."""
    classifier = EmailClassifier()
    email = create_test_email(
        subject="Action items for project",
        body="Here are the todo items with deadline next week.",
    )

    result = classifier._fallback_classification(email)
    assert result.category == "TASK_ACTION"
    assert result.confidence == 0.6


def test_classifier_fallback_fyi() -> None:
    """Test fallback classification for FYI emails."""
    classifier = EmailClassifier()
    email = create_test_email(
        subject="Weekly newsletter",
        body="Here's what happened this week in tech.",
    )

    result = classifier._fallback_classification(email)
    assert result.category == "FYI_ONLY"
    assert result.confidence == 0.5


def test_parse_result_valid() -> None:
    """Test parsing valid classification result."""
    classifier = EmailClassifier()
    result = classifier._parse_result(
        {
            "category": "NEEDS_REPLY",
            "confidence": 0.85,
            "reasoning": "Contains direct question",
        }
    )

    assert result.category == "NEEDS_REPLY"
    assert result.confidence == 0.85
    assert result.reasoning == "Contains direct question"


def test_parse_result_invalid_category() -> None:
    """Test parsing result with invalid category."""
    classifier = EmailClassifier()
    result = classifier._parse_result(
        {
            "category": "INVALID_CATEGORY",
            "confidence": 0.85,
            "reasoning": "Test",
        }
    )

    assert result.category == "FYI_ONLY"


def test_parse_result_confidence_bounds() -> None:
    """Test parsing result clamps confidence to valid range."""
    classifier = EmailClassifier()

    result_high = classifier._parse_result(
        {
            "category": "NEEDS_REPLY",
            "confidence": 1.5,
            "reasoning": "Test",
        }
    )
    assert result_high.confidence == 1.0

    result_low = classifier._parse_result(
        {
            "category": "NEEDS_REPLY",
            "confidence": -0.5,
            "reasoning": "Test",
        }
    )
    assert result_low.confidence == 0.0


@patch.object(EmailClassifier, "chain")
def test_classify_uses_chain(mock_chain: MagicMock) -> None:
    """Test classify method uses the LangChain chain."""
    mock_chain.invoke.return_value = {
        "category": "MEETING_REQUEST",
        "confidence": 0.9,
        "reasoning": "Meeting request detected",
    }

    classifier = EmailClassifier()
    classifier._chain = mock_chain

    email = create_test_email(subject="Meeting request")
    result = classifier.classify(email)

    mock_chain.invoke.assert_called_once()
    assert result.category == "MEETING_REQUEST"
    assert result.confidence == 0.9


@patch.object(EmailClassifier, "chain")
def test_classify_handles_chain_error(mock_chain: MagicMock) -> None:
    """Test classify falls back on chain error."""
    mock_chain.invoke.side_effect = Exception("API error")

    classifier = EmailClassifier()
    classifier._chain = mock_chain

    email = create_test_email(
        subject="Can we meet?",
        body="Let's schedule a call.",
    )
    result = classifier.classify(email)

    assert result.category == "MEETING_REQUEST"
    assert result.confidence == 0.6


def test_classify_batch() -> None:
    """Test batch classification."""
    classifier = EmailClassifier()

    emails = [
        create_test_email(subject="Meeting", body="Let's schedule a call"),
        create_test_email(subject="Question", body="Could you help me?"),
    ]

    with patch.object(classifier, "classify") as mock_classify:
        mock_classify.side_effect = [
            ClassificationResult("MEETING_REQUEST", 0.9, "test"),
            ClassificationResult("NEEDS_REPLY", 0.8, "test"),
        ]

        results = classifier.classify_batch(emails)

        assert len(results) == 2
        assert results[0].category == "MEETING_REQUEST"
        assert results[1].category == "NEEDS_REPLY"


def test_set_model() -> None:
    """Test changing the model."""
    classifier = EmailClassifier(model_id="original-model")
    classifier._llm = MagicMock()
    classifier._chain = MagicMock()

    classifier.set_model("new-model")

    assert classifier.model_id == "new-model"
    assert classifier._llm is None
    assert classifier._chain is None
