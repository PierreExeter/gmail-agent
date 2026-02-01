# Inbox

The Inbox is your primary workspace for viewing and processing emails. Gmail Agent connects to your Gmail account and displays recent emails with AI-powered classification.

![Inbox View](../assets/images/inbox.png)

## Overview

The Inbox view shows:

- List of recent emails from your Gmail inbox
- Sender, subject, and preview for each email
- Classification badges for processed emails
- Action buttons for classification and drafting

## Email List

Emails are displayed in reverse chronological order (newest first). Each email card shows:

| Field | Description |
|-------|-------------|
| **From** | Sender name and email address |
| **Subject** | Email subject line |
| **Preview** | First few lines of email content |
| **Date** | When the email was received |
| **Classification** | Category badge (if classified) |

## Classification

Click **Classify** on any email to analyze it with AI. The classifier:

1. Reads the email content and metadata
2. Determines the appropriate category
3. Calculates a confidence score
4. Flags emails requiring manual review

### Categories

| Category | Badge Color | Description |
|----------|-------------|-------------|
| **NEEDS_REPLY** | Blue | Email requires a response from you |
| **FYI_ONLY** | Gray | Informational only, no action needed |
| **MEETING_REQUEST** | Purple | Contains meeting invitation or scheduling request |
| **TASK_ACTION** | Orange | Requires action but not an email reply |

### Confidence Score

Each classification includes a confidence score (0.0 to 1.0):

- **High confidence (0.7+)**: Classification is likely accurate
- **Medium confidence (0.5-0.7)**: Review recommended
- **Low confidence (<0.5)**: Manual review required

The confidence threshold can be adjusted in [Settings](settings.md).

## Approval Flags

Emails may be flagged for additional review. Flags appear as warning badges:

### Unknown Sender

The sender is not in your trusted senders list. This helps catch:

- Potential phishing attempts
- Unsolicited emails
- First-time correspondents

**Action**: Review the email carefully. Add the sender to trusted list if legitimate.

### Sensitive Content

The email contains sensitive keywords such as:

- Financial terms: "payment", "invoice", "$"
- Urgency: "urgent", "asap", "immediately"
- Legal: "contract", "legal", "confidential"

**Action**: Review the classification and draft carefully before taking action.

### Low Confidence

The AI classification confidence is below your configured threshold.

**Action**: Review the email content and manually verify the classification.

## Generating Drafts

For emails classified as **NEEDS_REPLY**, click **Draft Reply** to:

1. Generate an AI-written response
2. Maintain appropriate tone and context
3. Create a draft for your review

The draft appears in the [Drafts](drafts.md) section for editing and approval.

## Workflow Tips

### Efficient Processing

1. Start with high-confidence, trusted sender emails
2. Process flagged emails with extra attention
3. Batch similar emails together

### Managing Volume

- Focus on **NEEDS_REPLY** emails first
- Archive **FYI_ONLY** emails after reviewing
- Handle **MEETING_REQUEST** emails in the Calendar view
- Track **TASK_ACTION** items separately

### Building Trust

Add legitimate senders to your trusted list to:

- Reduce approval friction
- Speed up classification
- Build a personalized sender database

## Refreshing Emails

Click **Refresh** to fetch the latest emails from Gmail. The inbox automatically syncs when you:

- Open the application
- Navigate to the Inbox view
- Complete a classification action
