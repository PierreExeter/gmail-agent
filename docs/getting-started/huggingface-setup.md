# HuggingFace Setup

Gmail Agent uses HuggingFace's Inference API to power its AI features. This guide walks you through creating and configuring your API token.

## Step 1: Create a HuggingFace Account

If you don't already have a HuggingFace account:

1. Go to [HuggingFace](https://huggingface.co/)
2. Click **Sign Up** in the top right
3. Complete the registration process
4. Verify your email address

## Step 2: Generate an API Token

1. Log in to HuggingFace
2. Go to [Settings > Access Tokens](https://huggingface.co/settings/tokens)
3. Click **New token**

Configure the token:

| Field | Value |
|-------|-------|
| Name | Gmail Agent (or any descriptive name) |
| Type | Read |

4. Click **Generate token**
5. Copy the token (starts with `hf_`)

!!! warning "Save Your Token"
    You can only see the full token once. Copy it immediately and store it securely.

## Step 3: Configure Gmail Agent

Add the token to your `.env` file:

```bash
HUGGINGFACE_API_KEY=hf_your_api_key_here
```

## Choosing a Model

Gmail Agent uses the HuggingFace Inference API to access LLMs. By default, it uses Mistral-7B-Instruct:

```bash
LLM_MODEL_ID=meta-llama/Llama-3.1-8B-Instruct
```

### Recommended Models

| Model | Description |
|-------|-------------|
| `meta-llama/Llama-3.1-8B-Instruct` | Default. Good balance of speed and quality |
| `meta-llama/Llama-2-7b-chat-hf` | Meta's Llama 2 chat model |
| `HuggingFaceH4/zephyr-7b-beta` | Fine-tuned for helpful responses |

!!! note "Model Availability"
    Some models may require accepting terms of use on the model page before you can use them via the API.

## API Rate Limits

The free HuggingFace Inference API has rate limits:

- Requests are queued during high traffic
- Large inputs may be truncated
- Some models have longer inference times

For production use, consider [HuggingFace Inference Endpoints](https://huggingface.co/inference-endpoints) for dedicated resources.

## Verifying Your Setup

Test your API key with this quick check:

```bash
curl -X POST \
  -H "Authorization: Bearer hf_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "Hello, how are you?"}' \
  https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct
```

A successful response will return generated text.

## Troubleshooting

### "Model is currently loading"

The first request to a model may take longer as HuggingFace loads it into memory. Wait a moment and try again.

### "Rate limit exceeded"

You've made too many requests. Wait a few minutes before trying again, or upgrade to a paid plan.

### "Authorization header is invalid"

Verify your token:

- Starts with `hf_`
- Has no extra spaces
- Is correctly copied to `.env`

## Next Steps

Your setup is almost complete. Continue to [First Run](first-run.md) to launch Gmail Agent and connect your Google account.
