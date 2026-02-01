# First Run

With your environment configured, you're ready to launch Gmail Agent and connect your Google account.

## Starting the Application

Launch Gmail Agent with:

```bash
uv run streamlit run app.py
```

The application opens in your default browser at `http://localhost:8501`.

## Connecting Your Google Account

On first launch, you'll see a warning that you're not connected. Follow these steps to authenticate:

### Step 1: Navigate to Settings

Click **Settings** in the sidebar navigation.

### Step 2: Connect Google Account

Click the **Connect Google Account** button. This opens a new browser window for Google OAuth.

### Step 3: Complete OAuth Flow

1. Select your Google account
2. Review the requested permissions
3. Click **Allow**

!!! note "Unverified App Warning"
    Since your app is in testing mode, Google will show a warning. Click **Advanced** then **Go to Gmail Agent (unsafe)** to proceed. This is normal for development.

### Step 4: Authorization Complete

After successful authorization:

- The browser window will close automatically
- Gmail Agent shows "Connected" in the sidebar
- Your OAuth token is saved locally in `data/token.json`

## Exploring the Interface

Once connected, you can explore the four main sections:

### Inbox

View and process your emails:

- See recent emails from your inbox
- Classify emails with AI
- Generate reply drafts

![Inbox View](../assets/images/inbox.png)

### Drafts

Review AI-generated replies:

- Edit draft content
- Approve and send
- Reject and regenerate

![Draft Review](../assets/images/drafts.png)

### Calendar

Manage your schedule:

- View upcoming events
- Process meeting requests from emails
- Find available time slots

![Calendar View](../assets/images/calendar.png)

### Settings

Configure the application:

- API credentials
- LLM model selection
- Confidence thresholds
- Trusted sender management

![Settings Page](../assets/images/settings.png)

## Basic Workflow

Here's a typical workflow for processing emails:

1. **Go to Inbox** - View your recent emails
2. **Classify an Email** - Click "Classify" to analyze the email content
3. **Review Classification** - See the category and confidence score
4. **Generate Reply** - Click "Draft Reply" for emails that need responses
5. **Review Draft** - Go to Drafts to edit and approve the reply
6. **Send** - Approve the draft to send via Gmail

## Understanding Classifications

Gmail Agent categorizes emails into four types:

| Category | Description | Typical Action |
|----------|-------------|----------------|
| **NEEDS_REPLY** | Email requires a response | Generate a draft reply |
| **FYI_ONLY** | Informational, no action needed | Archive or mark as read |
| **MEETING_REQUEST** | Contains a meeting invitation | Check calendar availability |
| **TASK_ACTION** | Requires action but not a reply | Add to your task list |

## Approval Flags

Certain emails are flagged for manual review:

| Flag | Reason |
|------|--------|
| **Unknown Sender** | Sender is not in your trusted list |
| **Sensitive Content** | Email contains keywords like "urgent", "contract", "payment" |
| **Low Confidence** | AI classification confidence is below threshold |

## Next Steps

- Learn about [Inbox features](../features/inbox.md) in detail
- Configure [Settings](../features/settings.md) for your preferences
- Review the [Configuration Reference](../configuration/reference.md) for all options
