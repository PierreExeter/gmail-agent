"""Configuration settings for the Gmail Agent application."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Google OAuth settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]
TOKEN_PATH = DATA_DIR / "token.json"
CREDENTIALS_PATH = DATA_DIR / "credentials.json"

# HuggingFace settings
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "meta-llama/Llama-3.1-8B-Instruct")

# Agent settings
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
SENSITIVE_KEYWORDS = [
    "urgent",
    "deadline",
    "contract",
    "payment",
    "$",
    "invoice",
    "legal",
    "confidential",
    "asap",
    "immediately",
]

# Database settings
DATABASE_URL = f"sqlite:///{DATA_DIR / 'gmail_agent.db'}"


# Email classification categories
class EmailCategory:
    """Email classification categories."""

    NEEDS_REPLY = "NEEDS_REPLY"
    FYI_ONLY = "FYI_ONLY"
    MEETING_REQUEST = "MEETING_REQUEST"
    TASK_ACTION = "TASK_ACTION"


# Approval flags
class ApprovalFlag:
    """Reasons for requiring approval."""

    UNKNOWN_SENDER = "unknown_sender"
    SENSITIVE_CONTENT = "sensitive_content"
    LOW_CONFIDENCE = "low_confidence"
