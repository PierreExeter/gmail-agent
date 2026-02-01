"""Tests for the Gmail service."""

import base64
from datetime import datetime
from unittest.mock import MagicMock, patch

from services.gmail_service import EmailMessage, GmailService, HTMLTextExtractor


def test_email_message_dataclass() -> None:
    """Test EmailMessage dataclass."""
    email = EmailMessage(
        id="msg123",
        thread_id="thread123",
        subject="Test Subject",
        sender="John Doe",
        sender_email="john@example.com",
        recipients=["jane@example.com"],
        date=datetime(2024, 1, 15, 10, 30),
        snippet="This is a test...",
        body="This is a test email body.",
        labels=["INBOX", "UNREAD"],
        is_unread=True,
        has_attachments=False,
        attachment_names=[],
    )

    assert email.id == "msg123"
    assert email.sender == "John Doe"
    assert email.is_unread is True


def test_html_text_extractor() -> None:
    """Test HTML to text extraction."""
    html = """
    <html>
    <head><style>body{color:red}</style></head>
    <body>
        <p>Hello World</p>
        <div>This is a test</div>
        <script>alert('test')</script>
    </body>
    </html>
    """

    extractor = HTMLTextExtractor()
    extractor.feed(html)
    text = extractor.get_text()

    assert "Hello World" in text
    assert "This is a test" in text
    assert "alert" not in text
    assert "color:red" not in text


def test_extract_email_from_sender() -> None:
    """Test extracting email from sender string."""
    service = GmailService()

    assert service._extract_email("John Doe <john@example.com>") == "john@example.com"
    assert service._extract_email("john@example.com") == "john@example.com"
    assert service._extract_email("<test@test.com>") == "test@test.com"


def test_extract_name_from_sender() -> None:
    """Test extracting name from sender string."""
    service = GmailService()

    assert service._extract_name("John Doe <john@example.com>") == "John Doe"
    assert service._extract_name('"Jane Smith" <jane@example.com>') == "Jane Smith"
    assert service._extract_name("john@example.com") == ""


def test_parse_date() -> None:
    """Test parsing email date strings."""
    service = GmailService()

    date1 = service._parse_date("Mon, 15 Jan 2024 10:30:00 +0000")
    assert date1.year == 2024
    assert date1.month == 1
    assert date1.day == 15

    date2 = service._parse_date("15 Jan 2024 10:30:00 +0000")
    assert date2.year == 2024


def test_decode_body_plain_text() -> None:
    """Test decoding plain text body."""
    service = GmailService()

    original = "Hello, World!"
    encoded = base64.urlsafe_b64encode(original.encode()).decode()

    decoded = service._decode_body(encoded, "text/plain")
    assert decoded == original


def test_decode_body_html() -> None:
    """Test decoding HTML body."""
    service = GmailService()

    html = "<html><body><p>Hello</p></body></html>"
    encoded = base64.urlsafe_b64encode(html.encode()).decode()

    decoded = service._decode_body(encoded, "text/html")
    assert "Hello" in decoded


@patch("services.gmail_service.get_gmail_service")
def test_fetch_emails(mock_get_service: MagicMock) -> None:
    """Test fetching emails."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service

    mock_service.users().messages().list().execute.return_value = {
        "messages": [
            {"id": "msg1", "threadId": "thread1"},
            {"id": "msg2", "threadId": "thread2"},
        ]
    }

    mock_msg = {
        "id": "msg1",
        "threadId": "thread1",
        "snippet": "Test snippet",
        "labelIds": ["INBOX", "UNREAD"],
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "Subject", "value": "Test Subject"},
                {"name": "Date", "value": "Mon, 15 Jan 2024 10:30:00 +0000"},
                {"name": "To", "value": "recipient@example.com"},
            ],
            "body": {
                "data": base64.urlsafe_b64encode(b"Test body").decode(),
            },
            "mimeType": "text/plain",
        },
    }

    mock_service.users().messages().get().execute.return_value = mock_msg

    gmail = GmailService(service=mock_service)
    emails = gmail.fetch_emails(max_results=2)

    assert len(emails) == 2
    mock_service.users().messages().list.assert_called()


@patch("services.gmail_service.get_gmail_service")
def test_send_email(mock_get_service: MagicMock) -> None:
    """Test sending an email."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service

    mock_service.users().messages().send().execute.return_value = {"id": "sent123"}

    gmail = GmailService(service=mock_service)
    result = gmail.send_email(
        to="recipient@example.com",
        subject="Test Subject",
        body="Test body",
    )

    assert result == "sent123"
    mock_service.users().messages().send.assert_called()


@patch("services.gmail_service.get_gmail_service")
def test_mark_as_read(mock_get_service: MagicMock) -> None:
    """Test marking email as read."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service

    mock_service.users().messages().modify().execute.return_value = {}

    gmail = GmailService(service=mock_service)
    result = gmail.mark_as_read("msg123")

    assert result is True
    mock_service.users().messages().modify.assert_called_with(
        userId="me",
        id="msg123",
        body={"removeLabelIds": ["UNREAD"]},
    )


def test_extract_attachments() -> None:
    """Test extracting attachment names."""
    service = GmailService()

    payload = {
        "parts": [
            {"filename": "document.pdf", "mimeType": "application/pdf"},
            {"filename": "", "mimeType": "text/plain"},
            {"filename": "image.jpg", "mimeType": "image/jpeg"},
            {
                "mimeType": "multipart/alternative",
                "parts": [
                    {"filename": "nested.docx", "mimeType": "application/docx"},
                ],
            },
        ]
    }

    attachments = service._extract_attachments(payload)

    assert "document.pdf" in attachments
    assert "image.jpg" in attachments
    assert "nested.docx" in attachments
    assert "" not in attachments


def test_parse_message() -> None:
    """Test parsing a full message."""
    service = GmailService()

    msg = {
        "id": "msg123",
        "threadId": "thread123",
        "snippet": "This is a snippet",
        "labelIds": ["INBOX", "UNREAD"],
        "payload": {
            "headers": [
                {"name": "From", "value": "John Doe <john@example.com>"},
                {"name": "Subject", "value": "Test Email"},
                {"name": "Date", "value": "Mon, 15 Jan 2024 10:30:00 +0000"},
                {"name": "To", "value": "jane@example.com, bob@example.com"},
            ],
            "body": {
                "data": base64.urlsafe_b64encode(b"Email body text").decode(),
            },
            "mimeType": "text/plain",
        },
    }

    email = service._parse_message(msg)

    assert email is not None
    assert email.id == "msg123"
    assert email.sender == "John Doe"
    assert email.sender_email == "john@example.com"
    assert email.subject == "Test Email"
    assert email.is_unread is True
    assert "jane@example.com" in email.recipients
