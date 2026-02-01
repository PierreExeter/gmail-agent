# Installation

This guide walks you through installing Gmail Agent and its dependencies.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or higher** - [Download Python](https://www.python.org/downloads/)
- **uv package manager** - [Install uv](https://docs.astral.sh/uv/)
- **Git** - [Download Git](https://git-scm.com/downloads/)

You will also need:

- A Google Cloud account (for Gmail and Calendar APIs)
- A HuggingFace account (for LLM API access)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/PierreExeter/gmail-agent.git
cd gmail-agent
```

### 2. Install Dependencies

Gmail Agent uses `uv` for dependency management. Install all dependencies with:

```bash
uv sync
```

This creates a virtual environment and installs all required packages.

### 3. Set Up Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` in your editor and configure the required variables:

```bash
# Required
HUGGINGFACE_API_KEY=hf_your_api_key
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret

# Optional (with defaults shown)
LLM_MODEL_ID=mistralai/Mistral-7B-Instruct-v0.2
CONFIDENCE_THRESHOLD=0.7
```

!!! warning "Keep Your Secrets Safe"
    Never commit your `.env` file to version control. It contains sensitive credentials.

## Verify Installation

Run a quick check to ensure everything is set up correctly:

```bash
uv run python -c "import streamlit; import langchain; print('Installation successful!')"
```

## Next Steps

Before you can use Gmail Agent, you need to:

1. [Set up Google Cloud credentials](google-setup.md)
2. [Configure your HuggingFace API token](huggingface-setup.md)
3. [Complete your first run](first-run.md)
