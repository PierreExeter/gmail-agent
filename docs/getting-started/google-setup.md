# Google Cloud Setup

Gmail Agent requires access to the Gmail and Google Calendar APIs. This guide walks you through setting up OAuth credentials in Google Cloud Console.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top of the page
3. Click **New Project**
4. Enter a project name (e.g., "Gmail Agent")
5. Click **Create**

## Step 2: Enable Required APIs

Enable both the Gmail API and Google Calendar API:

### Enable Gmail API

1. In the Cloud Console, go to **APIs & Services > Library**
2. Search for "Gmail API"
3. Click on **Gmail API**
4. Click **Enable**

### Enable Google Calendar API

1. Return to **APIs & Services > Library**
2. Search for "Google Calendar API"
3. Click on **Google Calendar API**
4. Click **Enable**

## Step 3: Configure OAuth Consent Screen

Before creating credentials, you need to configure the OAuth consent screen:

1. Go to **APIs & Services > OAuth consent screen**
2. Select **External** as the user type (unless you have a Google Workspace account)
3. Click **Create**

Fill in the required information:

| Field | Value |
|-------|-------|
| App name | Gmail Agent |
| User support email | Your email address |
| Developer contact email | Your email address |

4. Click **Save and Continue**

### Add Scopes

1. Click **Add or Remove Scopes**
2. Search for and select these scopes:
    - `https://www.googleapis.com/auth/gmail.readonly`
    - `https://www.googleapis.com/auth/gmail.send`
    - `https://www.googleapis.com/auth/gmail.modify`
    - `https://www.googleapis.com/auth/calendar`
3. Click **Update**
4. Click **Save and Continue**

### Add Test Users

Since the app is in testing mode:

1. Click **Add Users**
2. Enter your Google email address
3. Click **Add**
4. Click **Save and Continue**

!!! note "Test Users"
    While your app is in "Testing" status, only the email addresses you add as test users can authorize the app.

## Step 4: Create OAuth Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Select **Desktop app** as the application type
4. Enter a name (e.g., "Gmail Agent Desktop")
5. Click **Create**

You will see a dialog with your credentials:

- **Client ID** - Copy this value
- **Client Secret** - Copy this value

## Step 5: Configure Gmail Agent

Add the credentials to your `.env` file:

```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
```

!!! tip "Download Credentials"
    You can also download the credentials as a JSON file by clicking the download button. This can be useful as a backup.

## Required Permissions

Gmail Agent requests the following permissions:

| Scope | Purpose |
|-------|---------|
| `gmail.readonly` | Read email messages and labels |
| `gmail.send` | Send emails and reply drafts |
| `gmail.modify` | Modify email labels (read/unread) |
| `calendar` | Read and create calendar events |

## Troubleshooting

### "Access blocked: This app's request is invalid"

This usually means the OAuth consent screen is not configured correctly. Verify:

- All required fields are filled in
- You added yourself as a test user
- The app is published or in testing mode

### "Error 400: redirect_uri_mismatch"

Make sure you selected **Desktop app** when creating OAuth credentials, not Web application.

## Next Steps

Continue to [HuggingFace Setup](huggingface-setup.md) to configure your LLM API access.
