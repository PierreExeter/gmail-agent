"""Gmail API service wrapper for email operations."""

import base64
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from html.parser import HTMLParser
from typing import Any

from googleapiclient.discovery import Resource

from auth.google_auth import get_gmail_service

logger = logging.getLogger(__name__)


class HTMLTextExtractor(HTMLParser):
    """Extract plain text from HTML content."""

    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "head"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "head"):
            self._skip = False
        elif tag in ("p", "br", "div", "li", "tr"):
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.text_parts.append(data)

    def get_text(self) -> str:
        text = "".join(self.text_parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


@dataclass
class EmailMessage:
    """Represents an email message."""

    id: str
    thread_id: str
    subject: str
    sender: str
    sender_email: str
    recipients: list[str]
    date: datetime
    snippet: str
    body: str
    labels: list[str]
    is_unread: bool
    has_attachments: bool
    attachment_names: list[str]


class GmailService:
    """Service for interacting with Gmail API."""

    def __init__(self, service: Resource | None = None) -> None:
        """Initialize Gmail service."""
        self._service = service

    @property
    def service(self) -> Resource:
        """Get or create Gmail service."""
        if self._service is None:
            self._service = get_gmail_service()
        return self._service

    def fetch_emails(
        self,
        max_results: int = 20,
        query: str = "",
        unread_only: bool = False,
    ) -> list[EmailMessage]:
        """
        Fetch emails from inbox.

        Args:
            max_results: Maximum number of emails to fetch.
            query: Gmail search query string.
            unread_only: If True, fetch only unread emails.

        Returns:
            List of EmailMessage objects.
        """
        if unread_only:
            query = f"is:unread {query}".strip()

        try:
            results = self.service.users().messages().list(userId="me", maxResults=max_results, q=query).execute()
        except Exception:
            logger.exception("Failed to fetch email list")
            return []

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            email = self.get_email(msg["id"])
            if email:
                emails.append(email)

        return emails

    def get_email(self, message_id: str) -> EmailMessage | None:
        """
        Get a single email by ID.

        Args:
            message_id: Gmail message ID.

        Returns:
            EmailMessage object or None if not found.
        """
        try:
            msg = self.service.users().messages().get(userId="me", id=message_id, format="full").execute()
            return self._parse_message(msg)
        except Exception:
            logger.exception("Failed to fetch email")
            return None

    def get_thread(self, thread_id: str) -> list[EmailMessage]:
        """
        Get all messages in a thread.

        Args:
            thread_id: Gmail thread ID.

        Returns:
            List of EmailMessage objects in the thread.
        """
        try:
            thread = self.service.users().threads().get(userId="me", id=thread_id).execute()
            messages = []
            for msg in thread.get("messages", []):
                email = self._parse_message(msg)
                if email:
                    messages.append(email)
            return messages
        except Exception:
            logger.exception("Failed to fetch thread")
            return []

    def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        thread_id: str | None = None,
        in_reply_to: str | None = None,
    ) -> str | None:
        """
        Send an email.

        Args:
            to: Recipient email address(es).
            subject: Email subject.
            body: Email body (plain text).
            thread_id: Optional thread ID to reply to.
            in_reply_to: Optional Message-ID header for threading.

        Returns:
            Sent message ID or None if failed.
        """
        if isinstance(to, str):
            to = [to]

        message = MIMEText(body)
        message["to"] = ", ".join(to)
        message["subject"] = subject

        if in_reply_to:
            message["In-Reply-To"] = in_reply_to
            message["References"] = in_reply_to

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body_data: dict[str, Any] = {"raw": raw}
        if thread_id:
            body_data["threadId"] = thread_id

        try:
            sent = self.service.users().messages().send(userId="me", body=body_data).execute()
            return sent.get("id")
        except Exception:
            logger.exception("Failed to send email")
            return None

    def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read."""
        return self._modify_labels(message_id, remove_labels=["UNREAD"])

    def mark_as_unread(self, message_id: str) -> bool:
        """Mark an email as unread."""
        return self._modify_labels(message_id, add_labels=["UNREAD"])

    def add_label(self, message_id: str, label: str) -> bool:
        """Add a label to an email."""
        return self._modify_labels(message_id, add_labels=[label])

    def remove_label(self, message_id: str, label: str) -> bool:
        """Remove a label from an email."""
        return self._modify_labels(message_id, remove_labels=[label])

    def _modify_labels(
        self,
        message_id: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> bool:
        """Modify labels on an email."""
        body: dict[str, list[str]] = {}
        if add_labels:
            body["addLabelIds"] = add_labels
        if remove_labels:
            body["removeLabelIds"] = remove_labels

        try:
            self.service.users().messages().modify(userId="me", id=message_id, body=body).execute()
            return True
        except Exception:
            logger.exception("Failed to modify labels")
            return False

    def get_labels(self) -> list[dict[str, str]]:
        """Get all labels for the user."""
        try:
            results = self.service.users().labels().list(userId="me").execute()
            return results.get("labels", [])
        except Exception:
            logger.exception("Failed to fetch labels")
            return []

    def _parse_message(self, msg: dict[str, Any]) -> EmailMessage | None:
        """Parse a Gmail API message into an EmailMessage object."""
        try:
            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}

            sender = headers.get("from", "")
            sender_email = self._extract_email(sender)
            sender_name = self._extract_name(sender)

            to_header = headers.get("to", "")
            recipients = [self._extract_email(r) for r in to_header.split(",")]

            date_str = headers.get("date", "")
            date = self._parse_date(date_str)

            body = self._extract_body(msg.get("payload", {}))
            labels = msg.get("labelIds", [])
            attachments = self._extract_attachments(msg.get("payload", {}))

            return EmailMessage(
                id=msg["id"],
                thread_id=msg["threadId"],
                subject=headers.get("subject", "(No Subject)"),
                sender=sender_name or sender_email,
                sender_email=sender_email,
                recipients=recipients,
                date=date,
                snippet=msg.get("snippet", ""),
                body=body,
                labels=labels,
                is_unread="UNREAD" in labels,
                has_attachments=len(attachments) > 0,
                attachment_names=attachments,
            )
        except Exception:
            logger.exception("Failed to parse message")
            return None

    def _extract_email(self, sender: str) -> str:
        """Extract email address from sender string."""
        match = re.search(r"<([^>]+)>", sender)
        if match:
            return match.group(1)
        if "@" in sender:
            return sender.strip()
        return sender

    def _extract_name(self, sender: str) -> str:
        """Extract name from sender string."""
        match = re.search(r"^([^<]+)<", sender)
        if match:
            return match.group(1).strip().strip('"')
        return ""

    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date string."""
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return datetime.now()

    def _extract_body(self, payload: dict[str, Any]) -> str:
        """Extract email body from payload."""
        if "body" in payload and payload["body"].get("data"):
            return self._decode_body(payload["body"]["data"], payload.get("mimeType", ""))

        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                if mime_type == "text/plain" or mime_type == "text/html":
                    if part.get("body", {}).get("data"):
                        return self._decode_body(part["body"]["data"], mime_type)
                elif mime_type.startswith("multipart/"):
                    nested = self._extract_body(part)
                    if nested:
                        return nested

        return ""

    def _decode_body(self, data: str, mime_type: str) -> str:
        """Decode base64 email body."""
        try:
            decoded = base64.urlsafe_b64decode(data).decode("utf-8")
            if mime_type == "text/html":
                parser = HTMLTextExtractor()
                parser.feed(decoded)
                return parser.get_text()
            return decoded
        except Exception:
            logger.exception("Failed to decode body")
            return ""

    def _extract_attachments(self, payload: dict[str, Any]) -> list[str]:
        """Extract attachment filenames from payload."""
        attachments = []
        if "parts" in payload:
            for part in payload["parts"]:
                filename = part.get("filename")
                if filename:
                    attachments.append(filename)
                if "parts" in part:
                    attachments.extend(self._extract_attachments(part))
        return attachments
