"""Agent module for email classification, drafting, and scheduling."""

from agent.approval import ApprovalChecker
from agent.classifier import EmailClassifier
from agent.drafter import ReplyDrafter
from agent.scheduler import MeetingScheduler

__all__ = ["EmailClassifier", "ReplyDrafter", "MeetingScheduler", "ApprovalChecker"]
