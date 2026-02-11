# Gmail Agent — AI-Powered Email & Calendar Assistant

## Situation

Managing a busy inbox involves repetitive tasks — classifying emails, drafting replies, and scheduling meetings — that consume significant time but follow predictable patterns. Modern LLMs have made it possible to automate these workflows intelligently, but most solutions operate as black boxes without meaningful human oversight.

## Task

I built a full-stack AI assistant that automates email classification, reply drafting, and meeting scheduling while keeping the user firmly in control. The project served as a deep dive into LLM application development, integrating LangChain orchestration, Google APIs, and a human-in-the-loop approval system into a cohesive product.

## Action

Built a **Streamlit** web app with a modular architecture:

- **AI Agents** (LangChain + HuggingFace Llama 3.1): An email classifier that categorises messages (needs reply, FYI, meeting request, action item) with confidence scoring; a reply drafter with tone control and iterative improvement; and a meeting scheduler that extracts details and proposes free calendar slots.
- **Human-in-the-Loop Approval**: Every action (sending emails, creating calendar events) requires explicit user approval. A risk assessment layer automatically flags unknown senders, sensitive content, and low-confidence classifications.
- **Google API Integration**: Full OAuth 2.0 flow with Gmail (fetch, send, label) and Google Calendar (availability checking, event creation, free slot detection with working-hours awareness).
- **Persistence & Learning**: SQLAlchemy/SQLite database tracking classifications, drafts, approvals, and user feedback to build an audit trail and support future model improvement.
- **Graceful Degradation**: Every AI agent includes fallback strategies (heuristic keyword matching, template-based drafts) so the app remains functional even when the LLM is unavailable.

## Result

A fully functional, production-structured application that demonstrates end-to-end LLM integration — from prompt engineering and chain composition to API orchestration and state management. The security-first design (layered approvals, sensitive content detection, trusted sender lists) reflects real-world considerations for AI-assisted communication. The project solidified practical skills in **LangChain**, **Google Cloud APIs**, **OAuth 2.0**, **SQLAlchemy**, and **Streamlit**, with clean separation of concerns across agents, services, database, and UI layers.

**Tech stack:** Python · LangChain · HuggingFace · Streamlit · SQLAlchemy · Gmail API · Google Calendar API · OAuth 2.0
