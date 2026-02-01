# Settings

The Settings view allows you to configure Gmail Agent's behavior, manage API credentials, and customize AI parameters.

![Settings Page](../assets/images/settings.png)

## Google Account

### Connection Status

Shows your current connection status:

- **Connected**: Google account is linked
- **Not Connected**: Authentication required

### Connect / Disconnect

**Connect Google Account**: Initiates OAuth flow to authorize Gmail and Calendar access.

**Disconnect**: Removes saved credentials. You'll need to re-authenticate to use Gmail Agent.

!!! note "Revoking Access"
    Disconnecting removes local tokens. To fully revoke access, visit [Google Account Permissions](https://myaccount.google.com/permissions).

## API Configuration

### HuggingFace API Key

Your HuggingFace API token for LLM inference:

```
hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Click **Update** to save a new token. The token is stored in your `.env` file.

### LLM Model

Select which HuggingFace model to use for classification and drafting:

| Model | Description |
|-------|-------------|
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | Default. Balanced speed and quality |
| `meta-llama/Llama-2-7b-chat-hf` | Alternative instruction-tuned model |
| `HuggingFaceH4/zephyr-7b-beta` | Optimized for helpful responses |

Enter a custom model ID to use any HuggingFace Inference API compatible model.

## Classification Settings

### Confidence Threshold

Minimum confidence score (0.0 - 1.0) for automatic acceptance:

| Threshold | Behavior |
|-----------|----------|
| **0.5** | Accept more classifications, more manual reviews |
| **0.7** | Default. Balanced automation and oversight |
| **0.9** | Stricter. Most emails flagged for review |

Lower values = more automation, higher risk of errors.
Higher values = more manual review, better accuracy.

### Sensitive Keywords

List of keywords that trigger sensitive content flags:

**Default keywords:**

- `urgent`, `deadline`
- `contract`, `payment`, `invoice`
- `legal`, `confidential`
- `asap`, `immediately`
- `$` (currency symbol)

Add custom keywords by editing the `config.py` file.

## Trusted Senders

### Managing Trusted List

Email addresses in your trusted list don't trigger the "unknown sender" flag.

**Add Sender**: Enter an email address to add to the trusted list.

**Remove**: Click the X next to an address to remove it.

**Import**: Bulk import from a text file (one address per line).

### Benefits

Trusted senders:

- Skip unknown sender warnings
- Process faster in workflows
- Reduce approval friction

### Recommendations

Add to trusted list:

- Colleagues and team members
- Frequent contacts
- Known automated senders (calendars, receipts)

Do NOT add:

- Unknown addresses
- Marketing/newsletter senders
- Anyone you want extra review for

## Data Management

### Database Location

Gmail Agent stores data in:

```
data/gmail_agent.db
```

This SQLite database contains:

- Classification history
- Draft records
- Trusted sender list
- Application state

### Clearing Data

**Clear Classification History**: Removes past classifications while keeping settings.

**Clear All Data**: Resets the database to initial state.

!!! warning "Data Loss"
    Clearing data cannot be undone. Export important information first.

### Token Storage

OAuth tokens are stored in:

```
data/token.json
```

This file contains your Google authentication credentials. Keep it secure and never share it.

## Environment Variables

Settings can also be configured via environment variables in `.env`:

| Variable | Setting |
|----------|---------|
| `HUGGINGFACE_API_KEY` | HuggingFace API Key |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret |
| `LLM_MODEL_ID` | LLM Model |
| `CONFIDENCE_THRESHOLD` | Confidence Threshold |

Environment variables take precedence over UI settings on application restart.

## Saving Settings

Most settings save automatically when changed. For environment variable changes:

1. Edit the `.env` file
2. Restart the application

```bash
# Stop with Ctrl+C, then restart
uv run streamlit run app.py
```
