"""Approval system for flagging emails requiring human review."""

import logging
import re
from dataclasses import dataclass, field

import config
from agent.classifier import ClassificationResult
from db.database import Database
from services.gmail_service import EmailMessage

logger = logging.getLogger(__name__)


@dataclass
class ApprovalCheck:
    """Result of approval check."""

    requires_approval: bool
    reasons: list[str] = field(default_factory=list)
    risk_level: str = "low"


class ApprovalChecker:
    """Checks if emails/actions require human approval."""

    def __init__(
        self,
        db: Database | None = None,
        confidence_threshold: float | None = None,
        sensitive_keywords: list[str] | None = None,
    ) -> None:
        """
        Initialize the approval checker.

        Args:
            db: Optional Database instance for sender lookup.
            confidence_threshold: Minimum confidence for auto-approval.
            sensitive_keywords: Keywords that trigger approval requirement.
        """
        self._db = db
        self.confidence_threshold = confidence_threshold or config.CONFIDENCE_THRESHOLD
        self.sensitive_keywords = sensitive_keywords or config.SENSITIVE_KEYWORDS

    @property
    def db(self) -> Database:
        """Get or create database instance."""
        if self._db is None:
            self._db = Database()
        return self._db

    def check_email(
        self,
        email: EmailMessage,
        classification: ClassificationResult | None = None,
    ) -> ApprovalCheck:
        """
        Check if an email requires human approval.

        Args:
            email: EmailMessage to check.
            classification: Optional classification result.

        Returns:
            ApprovalCheck with approval requirements.
        """
        reasons = []
        risk_level = "low"

        if not self._is_known_sender(email.sender_email):
            reasons.append(config.ApprovalFlag.UNKNOWN_SENDER)
            risk_level = "medium"

        sensitive_found = self._check_sensitive_content(email)
        if sensitive_found:
            reasons.append(config.ApprovalFlag.SENSITIVE_CONTENT)
            reasons.extend([f"keyword:{kw}" for kw in sensitive_found])
            risk_level = "high"

        if classification and classification.confidence < self.confidence_threshold:
            reasons.append(config.ApprovalFlag.LOW_CONFIDENCE)
            if risk_level == "low":
                risk_level = "medium"

        return ApprovalCheck(
            requires_approval=len(reasons) > 0,
            reasons=reasons,
            risk_level=risk_level,
        )

    def check_draft(
        self,
        draft_body: str,
        original_email: EmailMessage,
    ) -> ApprovalCheck:
        """
        Check if a draft reply requires approval.

        Args:
            draft_body: Draft reply text.
            original_email: Original email being replied to.

        Returns:
            ApprovalCheck with approval requirements.
        """
        reasons = []
        risk_level = "low"

        sensitive_in_draft = self._find_sensitive_keywords(draft_body)
        if sensitive_in_draft:
            reasons.append("draft_contains_sensitive_keywords")
            reasons.extend([f"keyword:{kw}" for kw in sensitive_in_draft])
            risk_level = "medium"

        if self._contains_commitments(draft_body):
            reasons.append("contains_commitments")
            risk_level = "high"

        if not self._is_known_sender(original_email.sender_email):
            reasons.append("replying_to_unknown_sender")
            if risk_level == "low":
                risk_level = "medium"

        return ApprovalCheck(
            requires_approval=len(reasons) > 0,
            reasons=reasons,
            risk_level=risk_level,
        )

    def check_calendar_action(
        self,
        summary: str,
        attendees: list[str],
        is_external: bool = False,
    ) -> ApprovalCheck:
        """
        Check if a calendar action requires approval.

        Args:
            summary: Event summary.
            attendees: List of attendee emails.
            is_external: Whether attendees include external parties.

        Returns:
            ApprovalCheck with approval requirements.
        """
        reasons = []
        risk_level = "low"

        if is_external:
            reasons.append("external_attendees")
            risk_level = "medium"

        unknown_attendees = [email for email in attendees if not self._is_known_sender(email)]
        if unknown_attendees:
            reasons.append("unknown_attendees")
            reasons.extend([f"attendee:{email}" for email in unknown_attendees[:3]])
            risk_level = "medium"

        sensitive = self._find_sensitive_keywords(summary)
        if sensitive:
            reasons.append("sensitive_meeting_topic")
            risk_level = "high"

        return ApprovalCheck(
            requires_approval=len(reasons) > 0,
            reasons=reasons,
            risk_level=risk_level,
        )

    def should_auto_approve(
        self,
        email: EmailMessage,
        classification: ClassificationResult,
    ) -> bool:
        """
        Determine if an email can be auto-approved.

        Args:
            email: EmailMessage to check.
            classification: Classification result.

        Returns:
            True if can be auto-approved, False otherwise.
        """
        check = self.check_email(email, classification)
        if check.requires_approval:
            return False

        if classification.category == "FYI_ONLY":
            return True

        return classification.confidence >= 0.9 and self._is_known_sender(email.sender_email)

    def _is_known_sender(self, email: str) -> bool:
        """Check if sender is known/trusted."""
        if not email:
            return False
        try:
            return self.db.is_known_sender(email)
        except Exception:
            logger.exception("Failed to check known sender")
            return False

    def _check_sensitive_content(self, email: EmailMessage) -> list[str]:
        """Check email for sensitive content."""
        combined = f"{email.subject} {email.body or email.snippet}".lower()
        return self._find_sensitive_keywords(combined)

    def _find_sensitive_keywords(self, text: str) -> list[str]:
        """Find sensitive keywords in text."""
        text_lower = text.lower()
        found = []
        for keyword in self.sensitive_keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)
        return found

    def _contains_commitments(self, text: str) -> bool:
        """Check if text contains commitment language."""
        commitment_patterns = [
            r"\bi will\b",
            r"\bi'll\b",
            r"\bi commit\b",
            r"\bi promise\b",
            r"\bi agree\b",
            r"\bwe will\b",
            r"\bwe'll\b",
            r"\bguarantee\b",
            r"\bconfirm(ed|ing)?\b.*\b(payment|delivery|date|deadline)\b",
        ]
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in commitment_patterns)

    def add_known_sender(self, email: str, name: str = "") -> bool:
        """Add a sender to the known senders list."""
        try:
            self.db.add_known_sender(email, name)
            return True
        except Exception:
            logger.exception("Failed to add known sender")
            return False

    def get_risk_summary(self, check: ApprovalCheck) -> str:
        """Get a human-readable summary of the approval check."""
        if not check.requires_approval:
            return "No approval required"

        risk_emoji = {"low": "", "medium": "", "high": ""}
        emoji = risk_emoji.get(check.risk_level, "")

        reason_descriptions = {
            config.ApprovalFlag.UNKNOWN_SENDER: "Unknown sender",
            config.ApprovalFlag.SENSITIVE_CONTENT: "Sensitive content detected",
            config.ApprovalFlag.LOW_CONFIDENCE: "Low classification confidence",
            "draft_contains_sensitive_keywords": "Draft contains sensitive keywords",
            "contains_commitments": "Draft contains commitments",
            "replying_to_unknown_sender": "Replying to unknown sender",
            "external_attendees": "Meeting includes external attendees",
            "unknown_attendees": "Meeting includes unknown attendees",
            "sensitive_meeting_topic": "Sensitive meeting topic",
        }

        summaries = []
        for reason in check.reasons:
            if reason.startswith("keyword:") or reason.startswith("attendee:"):
                continue
            desc = reason_descriptions.get(reason, reason)
            summaries.append(desc)

        return f"{emoji} {check.risk_level.upper()} risk: {', '.join(summaries)}"
