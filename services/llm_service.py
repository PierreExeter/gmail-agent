"""LLM service for HuggingFace API integration."""

import json
import logging
import re
from dataclasses import dataclass

from huggingface_hub import InferenceClient

import config

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of email classification."""

    category: str
    confidence: float
    reasoning: str


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


class LLMService:
    """Service for LLM operations using HuggingFace Inference API."""

    def __init__(
        self,
        model_id: str | None = None,
        api_key: str | None = None,
    ) -> None:
        """
        Initialize LLM service.

        Args:
            model_id: HuggingFace model ID.
            api_key: HuggingFace API key.
        """
        self.model_id = model_id or config.LLM_MODEL_ID
        self.api_key = api_key or config.HUGGINGFACE_API_KEY
        self._client: InferenceClient | None = None

    @property
    def client(self) -> InferenceClient:
        """Get or create inference client."""
        if self._client is None:
            self._client = InferenceClient(model=self.model_id, token=self.api_key)
        return self._client

    def classify_email(self, email_content: str, sender: str, subject: str) -> ClassificationResult:
        """
        Classify an email into categories.

        Args:
            email_content: Email body text.
            sender: Email sender.
            subject: Email subject.

        Returns:
            ClassificationResult with category, confidence, and reasoning.
        """
        prompt = f"""Classify the following email into ONE of these categories:
- NEEDS_REPLY: Email requires a response from the recipient
- FYI_ONLY: Informational email, no action needed
- MEETING_REQUEST: Email contains a meeting request or scheduling discussion
- TASK_ACTION: Email contains action items or tasks to complete

Email details:
From: {sender}
Subject: {subject}
Content: {email_content[:2000]}

Respond in this exact JSON format:
{{"category": "CATEGORY_NAME", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}

JSON response:"""

        try:
            response = self.client.text_generation(
                prompt,
                max_new_tokens=200,
                temperature=0.1,
                do_sample=True,
            )
            return self._parse_classification(response)
        except Exception:
            logger.exception("Failed to classify email")
            return ClassificationResult(
                category="FYI_ONLY",
                confidence=0.5,
                reasoning="Classification failed, defaulting to FYI_ONLY",
            )

    def draft_reply(
        self,
        email_content: str,
        sender: str,
        subject: str,
        context: str = "",
        tone: str = "professional",
    ) -> str:
        """
        Generate a draft reply to an email.

        Args:
            email_content: Original email body.
            sender: Email sender name.
            subject: Email subject.
            context: Additional context for the reply.
            tone: Desired tone (professional, friendly, formal).

        Returns:
            Draft reply text.
        """
        prompt = f"""Write a {tone} email reply to the following email.
Keep it concise and helpful. Do not include a subject line.

Original email:
From: {sender}
Subject: {subject}
Content: {email_content[:2000]}

{f"Additional context: {context}" if context else ""}

Reply (do not include subject line, start with greeting):"""

        try:
            response = self.client.text_generation(
                prompt,
                max_new_tokens=500,
                temperature=0.7,
                do_sample=True,
            )
            return self._clean_reply(response)
        except Exception:
            logger.exception("Failed to generate draft reply")
            return ""

    def extract_meeting_details(self, email_content: str, subject: str) -> MeetingExtraction:
        """
        Extract meeting details from an email.

        Args:
            email_content: Email body text.
            subject: Email subject.

        Returns:
            MeetingExtraction with parsed meeting details.
        """
        prompt = f"""Extract meeting details from this email. If no meeting is requested, set has_meeting_request to false.

Email:
Subject: {subject}
Content: {email_content[:2000]}

Respond in this exact JSON format:
{{
    "has_meeting_request": true/false,
    "title": "meeting title or empty",
    "proposed_times": ["time1", "time2"],
    "duration_minutes": 60,
    "attendees": ["email1", "email2"],
    "location": "location or empty",
    "notes": "any additional notes"
}}

JSON response:"""

        try:
            response = self.client.text_generation(
                prompt,
                max_new_tokens=300,
                temperature=0.1,
                do_sample=True,
            )
            return self._parse_meeting_extraction(response)
        except Exception:
            logger.exception("Failed to extract meeting details")
            return MeetingExtraction(
                has_meeting_request=False,
                title="",
                proposed_times=[],
                duration_minutes=60,
                attendees=[],
                location="",
                notes="",
            )

    def summarize_email(self, email_content: str, max_words: int = 50) -> str:
        """
        Generate a brief summary of an email.

        Args:
            email_content: Email body text.
            max_words: Maximum words in summary.

        Returns:
            Email summary.
        """
        prompt = f"""Summarize this email in {max_words} words or less:

{email_content[:2000]}

Summary:"""

        try:
            response = self.client.text_generation(
                prompt,
                max_new_tokens=100,
                temperature=0.3,
                do_sample=True,
            )
            return response.strip()
        except Exception:
            logger.exception("Failed to summarize email")
            return ""

    def _parse_classification(self, response: str) -> ClassificationResult:
        """Parse classification response from LLM."""
        try:
            json_match = re.search(r"\{[^}]+\}", response)
            if json_match:
                data = json.loads(json_match.group())
                category = data.get("category", "FYI_ONLY").upper()
                valid_categories = ["NEEDS_REPLY", "FYI_ONLY", "MEETING_REQUEST", "TASK_ACTION"]
                if category not in valid_categories:
                    category = "FYI_ONLY"
                return ClassificationResult(
                    category=category,
                    confidence=float(data.get("confidence", 0.5)),
                    reasoning=data.get("reasoning", ""),
                )
        except (json.JSONDecodeError, ValueError, KeyError):
            logger.exception("Failed to parse classification response")

        return ClassificationResult(
            category="FYI_ONLY",
            confidence=0.5,
            reasoning="Failed to parse response",
        )

    def _parse_meeting_extraction(self, response: str) -> MeetingExtraction:
        """Parse meeting extraction response from LLM."""
        try:
            json_match = re.search(r"\{[^}]*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return MeetingExtraction(
                    has_meeting_request=bool(data.get("has_meeting_request", False)),
                    title=str(data.get("title", "")),
                    proposed_times=list(data.get("proposed_times", [])),
                    duration_minutes=int(data.get("duration_minutes", 60)),
                    attendees=list(data.get("attendees", [])),
                    location=str(data.get("location", "")),
                    notes=str(data.get("notes", "")),
                )
        except (json.JSONDecodeError, ValueError, KeyError):
            logger.exception("Failed to parse meeting extraction response")

        return MeetingExtraction(
            has_meeting_request=False,
            title="",
            proposed_times=[],
            duration_minutes=60,
            attendees=[],
            location="",
            notes="",
        )

    def _clean_reply(self, response: str) -> str:
        """Clean up generated reply text."""
        lines = response.strip().split("\n")
        cleaned_lines = []
        for line in lines:
            lower = line.lower().strip()
            if lower.startswith("subject:") or lower.startswith("re:"):
                continue
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines).strip()

    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        Generate text from a custom prompt.

        Args:
            prompt: Input prompt.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            Generated text.
        """
        try:
            response = self.client.text_generation(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
            )
            return response.strip()
        except Exception:
            logger.exception("Failed to generate text")
            return ""

    def set_model(self, model_id: str) -> None:
        """Change the model being used."""
        self.model_id = model_id
        self._client = None
