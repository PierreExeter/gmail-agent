# Drafts

The Drafts view is where you review, edit, and approve AI-generated email replies before sending.

![Draft Review](../assets/images/drafts.png)

## Overview

When you click "Draft Reply" on an email in the Inbox, Gmail Agent:

1. Analyzes the original email context
2. Generates an appropriate response
3. Saves the draft for your review

All pending drafts appear in this view.

## Draft List

Each draft card displays:

| Field | Description |
|-------|-------------|
| **To** | Recipient email address |
| **Subject** | Reply subject (typically "Re: Original Subject") |
| **Original Email** | Preview of the email being replied to |
| **Draft Content** | The AI-generated response |
| **Created** | When the draft was generated |

## Reviewing Drafts

### Reading the Draft

Click on a draft to expand its full content. Review:

- **Tone**: Is it appropriate for the recipient?
- **Content**: Does it address all points in the original email?
- **Accuracy**: Are facts and details correct?
- **Length**: Is it appropriately concise or detailed?

### Editing Content

Click **Edit** to modify the draft:

1. Make your changes in the text editor
2. Adjust tone, add details, or fix errors
3. Click **Save** to update the draft

!!! tip "Keep AI Context"
    Minor edits work best. For major rewrites, consider regenerating the draft.

### Regenerating

If the draft doesn't meet your needs, click **Regenerate** to:

1. Create a new AI-generated response
2. Use updated context if available
3. Replace the current draft

You can regenerate as many times as needed.

## Approval Process

### Approve and Send

Click **Approve & Send** to:

1. Finalize the draft
2. Send via Gmail API
3. Move the email to sent folder
4. Remove from drafts list

!!! warning "No Undo"
    Once sent, the email cannot be recalled. Review carefully before approving.

### Reject

Click **Reject** to:

1. Discard the draft
2. Remove from drafts list
3. Keep the original email in inbox

Use reject when:

- You decide not to reply
- You want to write manually instead
- The draft is not salvageable

## Draft Status

Drafts can have different statuses:

| Status | Description |
|--------|-------------|
| **Pending** | Awaiting your review |
| **Edited** | You've made modifications |
| **Flagged** | Contains sensitive content or unknown recipient |

## Sensitive Draft Handling

Drafts flagged for extra review show warning indicators:

### Sensitive Keywords

If the original email or draft contains sensitive keywords, a warning appears. Review:

- Financial implications
- Legal language
- Commitment or promises

### Unknown Recipient

If replying to someone not in your trusted list, verify:

- Email address is correct
- You intend to send to this person
- Content is appropriate for a new contact

## Best Practices

### Review Checklist

Before approving a draft:

- [ ] Greeting matches relationship (formal/informal)
- [ ] All questions from original email are addressed
- [ ] No factual errors or hallucinations
- [ ] Tone is appropriate
- [ ] No sensitive information accidentally shared
- [ ] Spelling and grammar are correct

### Common Edits

Typical changes you might make:

- **Personalization**: Add specific details or context
- **Softening**: Make requests less demanding
- **Clarification**: Expand on brief AI responses
- **Sign-off**: Use your preferred closing

### When to Regenerate

Consider regenerating when:

- Wrong tone (too formal/informal)
- Misunderstood the original email
- Missing key points
- Factually incorrect
