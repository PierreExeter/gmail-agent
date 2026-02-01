"""Email classification agent using LangChain."""

import logging
from dataclasses import dataclass

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEndpoint

import config
from services.gmail_service import EmailMessage

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of email classification."""

    category: str
    confidence: float
    reasoning: str


CLASSIFICATION_PROMPT = """You are an email classification assistant. Classify the given email into exactly ONE category.

Categories:
- NEEDS_REPLY: Email requires a response from the recipient (questions, requests, invitations needing confirmation)
- FYI_ONLY: Informational email with no action needed (newsletters, notifications, receipts, confirmations)
- MEETING_REQUEST: Email explicitly about scheduling a meeting or call
- TASK_ACTION: Email contains specific tasks or action items to complete

Email to classify:
From: {sender}
Subject: {subject}
Body: {body}

Respond with a JSON object containing:
- category: one of NEEDS_REPLY, FYI_ONLY, MEETING_REQUEST, TASK_ACTION
- confidence: a number between 0 and 1 indicating confidence
- reasoning: brief explanation for the classification

JSON response:"""


class EmailClassifier:
    """Classifies emails using LangChain and HuggingFace."""

    def __init__(
        self,
        model_id: str | None = None,
        api_key: str | None = None,
    ) -> None:
        """
        Initialize the email classifier.

        Args:
            model_id: HuggingFace model ID.
            api_key: HuggingFace API key.
        """
        self.model_id = model_id or config.LLM_MODEL_ID
        self.api_key = api_key or config.HUGGINGFACE_API_KEY
        self._llm: HuggingFaceEndpoint | None = None
        self._chain = None

    @property
    def llm(self) -> HuggingFaceEndpoint:
        """Get or create LLM instance."""
        if self._llm is None:
            self._llm = HuggingFaceEndpoint(
                repo_id=self.model_id,
                huggingfacehub_api_token=self.api_key,
                max_new_tokens=256,
                temperature=0.1,
            )
        return self._llm

    @property
    def chain(self):
        """Get or create classification chain."""
        if self._chain is None:
            prompt = ChatPromptTemplate.from_template(CLASSIFICATION_PROMPT)
            parser = JsonOutputParser()
            self._chain = prompt | self.llm | parser
        return self._chain

    def classify(self, email: EmailMessage) -> ClassificationResult:
        """
        Classify an email message.

        Args:
            email: EmailMessage to classify.

        Returns:
            ClassificationResult with category, confidence, and reasoning.
        """
        body = email.body[:2000] if email.body else email.snippet

        try:
            result = self.chain.invoke(
                {
                    "sender": email.sender,
                    "subject": email.subject,
                    "body": body,
                }
            )
            return self._parse_result(result)
        except Exception:
            logger.exception("Classification chain failed")
            return self._fallback_classification(email)

    def classify_batch(self, emails: list[EmailMessage]) -> list[ClassificationResult]:
        """
        Classify multiple emails.

        Args:
            emails: List of EmailMessage objects.

        Returns:
            List of ClassificationResult objects.
        """
        return [self.classify(email) for email in emails]

    def _parse_result(self, result: dict) -> ClassificationResult:
        """Parse chain output into ClassificationResult."""
        category = result.get("category", "FYI_ONLY").upper()
        valid_categories = ["NEEDS_REPLY", "FYI_ONLY", "MEETING_REQUEST", "TASK_ACTION"]
        if category not in valid_categories:
            category = "FYI_ONLY"

        confidence = float(result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        return ClassificationResult(
            category=category,
            confidence=confidence,
            reasoning=result.get("reasoning", ""),
        )

    def _fallback_classification(self, email: EmailMessage) -> ClassificationResult:
        """Provide fallback classification using heuristics."""
        subject_lower = email.subject.lower()
        body_lower = (email.body or email.snippet).lower()
        combined = f"{subject_lower} {body_lower}"

        if any(word in combined for word in ["meeting", "call", "schedule", "calendar", "invite"]):
            return ClassificationResult(
                category="MEETING_REQUEST",
                confidence=0.6,
                reasoning="Contains meeting-related keywords",
            )

        if any(word in combined for word in ["?", "please", "could you", "can you", "would you"]):
            return ClassificationResult(
                category="NEEDS_REPLY",
                confidence=0.6,
                reasoning="Contains question or request patterns",
            )

        if any(word in combined for word in ["todo", "task", "action", "deadline", "due"]):
            return ClassificationResult(
                category="TASK_ACTION",
                confidence=0.6,
                reasoning="Contains task-related keywords",
            )

        return ClassificationResult(
            category="FYI_ONLY",
            confidence=0.5,
            reasoning="Fallback classification",
        )

    def set_model(self, model_id: str) -> None:
        """Change the classification model."""
        self.model_id = model_id
        self._llm = None
        self._chain = None
