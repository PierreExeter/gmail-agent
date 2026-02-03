"""Reply drafting agent using LangChain."""

import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

import config
from services.gmail_service import EmailMessage

logger = logging.getLogger(__name__)


DRAFTING_PROMPT = """You are an email assistant helping to draft professional replies.

Write a reply to the following email. Keep it concise, helpful, and match the appropriate tone.

Original email:
From: {sender}
Subject: {subject}
Content: {body}

{context_section}

Guidelines:
- Start with an appropriate greeting
- Address the main points of the email
- Be helpful and professional
- Keep it concise (aim for 2-4 paragraphs)
- End with an appropriate closing
- Do NOT include a subject line

Tone: {tone}

Draft reply:"""


class ReplyDrafter:
    """Generates email reply drafts using LangChain."""

    def __init__(
        self,
        model_id: str | None = None,
        api_key: str | None = None,
    ) -> None:
        """
        Initialize the reply drafter.

        Args:
            model_id: HuggingFace model ID.
            api_key: HuggingFace API key.
        """
        self.model_id = model_id or config.LLM_MODEL_ID
        self.api_key = api_key or config.HUGGINGFACE_API_KEY
        self._llm: ChatHuggingFace | None = None
        self._chain = None

    @property
    def llm(self) -> ChatHuggingFace:
        """Get or create LLM instance."""
        if self._llm is None:
            endpoint = HuggingFaceEndpoint(
                repo_id=self.model_id,
                huggingfacehub_api_token=self.api_key,
                max_new_tokens=512,
                temperature=0.7,
            )
            self._llm = ChatHuggingFace(llm=endpoint)
        return self._llm

    @property
    def chain(self):
        """Get or create drafting chain."""
        if self._chain is None:
            prompt = ChatPromptTemplate.from_template(DRAFTING_PROMPT)
            self._chain = prompt | self.llm
        return self._chain

    def draft_reply(
        self,
        email: EmailMessage,
        context: str = "",
        tone: str = "professional",
        thread_history: list[EmailMessage] | None = None,
    ) -> str:
        """
        Generate a draft reply for an email.

        Args:
            email: EmailMessage to reply to.
            context: Additional context for the reply.
            tone: Desired tone (professional, friendly, formal).
            thread_history: Previous messages in the thread for context.

        Returns:
            Draft reply text.
        """
        body = email.body[:2000] if email.body else email.snippet

        context_section = ""
        if context:
            context_section = f"Additional context: {context}\n"
        if thread_history:
            history_text = self._format_thread_history(thread_history)
            context_section += f"\nThread history:\n{history_text}\n"

        try:
            result = self.chain.invoke(
                {
                    "sender": email.sender,
                    "subject": email.subject,
                    "body": body,
                    "context_section": context_section,
                    "tone": tone,
                }
            )
            return self._clean_draft(result.content)
        except Exception:
            logger.exception("Drafting chain failed")
            return self._fallback_draft(email)

    def draft_with_template(
        self,
        email: EmailMessage,
        template: str,
        variables: dict[str, str] | None = None,
    ) -> str:
        """
        Generate a draft using a custom template.

        Args:
            email: EmailMessage to reply to.
            template: Custom prompt template.
            variables: Additional template variables.

        Returns:
            Draft reply text.
        """
        body = email.body[:2000] if email.body else email.snippet

        base_vars = {
            "sender": email.sender,
            "subject": email.subject,
            "body": body,
        }
        if variables:
            base_vars.update(variables)

        try:
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.llm
            result = chain.invoke(base_vars)
            return self._clean_draft(result.content)
        except Exception:
            logger.exception("Custom template drafting failed")
            return ""

    def improve_draft(self, draft: str, feedback: str) -> str:
        """
        Improve an existing draft based on feedback.

        Args:
            draft: Current draft text.
            feedback: User feedback for improvement.

        Returns:
            Improved draft text.
        """
        prompt_template = """Improve the following email draft based on the feedback provided.

Current draft:
{draft}

Feedback:
{feedback}

Improved draft:"""

        try:
            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | self.llm
            result = chain.invoke({"draft": draft, "feedback": feedback})
            return self._clean_draft(result.content)
        except Exception:
            logger.exception("Draft improvement failed")
            return draft

    def _format_thread_history(self, thread: list[EmailMessage]) -> str:
        """Format thread history for context."""
        history_parts = []
        for msg in thread[-3:]:
            history_parts.append(f"---\nFrom: {msg.sender}\nDate: {msg.date.strftime('%Y-%m-%d %H:%M')}\n{msg.snippet}")
        return "\n".join(history_parts)

    def _clean_draft(self, draft: str) -> str:
        """Clean up generated draft text."""
        if not draft:
            return ""

        lines = draft.strip().split("\n")
        cleaned_lines = []
        skip_next = False

        for line in lines:
            if skip_next:
                skip_next = False
                continue

            lower = line.lower().strip()
            if lower.startswith("subject:") or lower.startswith("re:"):
                continue
            if lower.startswith("draft reply:"):
                continue
            if lower.startswith("improved draft:"):
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def _fallback_draft(self, email: EmailMessage) -> str:
        """Generate a simple fallback draft."""
        sender_name = email.sender.split()[0] if email.sender else "there"
        return f"""Hi {sender_name},

Thank you for your email regarding "{email.subject}".

I've received your message and will review it carefully. I'll get back to you with a detailed response shortly.

Best regards"""

    def set_model(self, model_id: str) -> None:
        """Change the drafting model."""
        self.model_id = model_id
        self._llm = None
        self._chain = None
