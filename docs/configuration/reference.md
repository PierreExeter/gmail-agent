# Configuration Reference

This page documents all configuration options available in Gmail Agent.

## Environment Variables

Configure Gmail Agent by setting these variables in your `.env` file.

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `HUGGINGFACE_API_KEY` | HuggingFace API token for LLM inference | `hf_xxxxxxxxxx` |
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 client ID | `xxxxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 2.0 client secret | `GOCSPX-xxxxxxxxxx` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_MODEL_ID` | HuggingFace model for AI tasks | `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` |
| `CONFIDENCE_THRESHOLD` | Minimum confidence for auto-approval (0.0-1.0) | `0.7` |

## Example .env File

```bash
# HuggingFace API Configuration
HUGGINGFACE_API_KEY=hf_your_api_key_here

# Google OAuth Configuration
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_client_secret

# LLM Configuration (optional)
LLM_MODEL_ID=deepseek-ai/DeepSeek-R1-Distill-Qwen-7B

# Agent Configuration (optional)
CONFIDENCE_THRESHOLD=0.7
```

## Google OAuth Scopes

Gmail Agent requests these OAuth scopes:

| Scope | Purpose |
|-------|---------|
| `gmail.readonly` | Read email messages and labels |
| `gmail.send` | Send emails via Gmail |
| `gmail.modify` | Modify email labels (mark read/unread) |
| `calendar` | Read and create calendar events |

## Email Classification Categories

Emails are classified into four categories:

| Category | Constant | Description |
|----------|----------|-------------|
| Needs Reply | `NEEDS_REPLY` | Requires a response from user |
| FYI Only | `FYI_ONLY` | Informational, no action needed |
| Meeting Request | `MEETING_REQUEST` | Contains meeting/scheduling request |
| Task/Action | `TASK_ACTION` | Requires action but not email reply |

## Approval Flags

Emails may be flagged for manual review:

| Flag | Constant | Trigger |
|------|----------|---------|
| Unknown Sender | `unknown_sender` | Sender not in trusted list |
| Sensitive Content | `sensitive_content` | Contains sensitive keywords |
| Low Confidence | `low_confidence` | Classification confidence below threshold |

## Sensitive Keywords

Default keywords that trigger sensitive content flags:

```python
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
```

To customize this list, edit `config.py`.

## File Paths

Gmail Agent uses these default paths:

| Path | Purpose |
|------|---------|
| `data/` | Data directory |
| `data/token.json` | Google OAuth token |
| `data/credentials.json` | Google OAuth credentials (optional) |
| `data/gmail_agent.db` | SQLite database |

## Database Schema

Gmail Agent uses SQLite with SQLAlchemy. Key tables:

### Classifications

Stores email classification history:

- `email_id`: Gmail message ID
- `category`: Classification category
- `confidence`: Confidence score
- `flags`: Approval flags (JSON)
- `created_at`: Timestamp

### Drafts

Stores generated reply drafts:

- `draft_id`: Unique identifier
- `email_id`: Original email ID
- `content`: Draft text
- `status`: pending/approved/rejected
- `created_at`: Timestamp

### Trusted Senders

Stores trusted email addresses:

- `email`: Email address
- `name`: Display name (optional)
- `added_at`: Timestamp

## Confidence Threshold

The confidence threshold determines when emails need manual review:

| Threshold | Auto-Approved | Flagged for Review |
|-----------|---------------|-------------------|
| 0.5 | > 50% confidence | ≤ 50% confidence |
| 0.7 | > 70% confidence | ≤ 70% confidence |
| 0.9 | > 90% confidence | ≤ 90% confidence |

**Lower threshold** = More automation, less oversight
**Higher threshold** = Less automation, more oversight

## LLM Models

Compatible models for the Inference API:

### Recommended

| Model ID | Parameters | Notes |
|----------|------------|-------|
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | 7B | Default, well-balanced |
| `meta-llama/Llama-2-7b-chat-hf` | 7B | Requires license acceptance |
| `HuggingFaceH4/zephyr-7b-beta` | 7B | Good for helpful responses |

### Requirements

Models must:

- Be available on HuggingFace Inference API
- Support text generation
- Accept instruction-style prompts

## Logging

Gmail Agent logs to stdout with this format:

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Default level is `INFO`. To change, modify `app.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Performance Tuning

### Request Timeouts

HuggingFace API requests have default timeouts. For slow models:

```python
# In services/llm_service.py
timeout = 60  # seconds
```

### Rate Limiting

Free HuggingFace tier has rate limits. Consider:

- Batching classification requests
- Using Inference Endpoints for production
- Adding delays between requests
