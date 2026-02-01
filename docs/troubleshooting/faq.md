# Troubleshooting & FAQ

Common issues and solutions for Gmail Agent.

## Authentication Issues

### "Access blocked: This app's request is invalid"

**Cause**: OAuth consent screen not configured correctly.

**Solution**:

1. Go to Google Cloud Console > APIs & Services > OAuth consent screen
2. Verify all required fields are filled
3. Add your email as a test user
4. Ensure app is in "Testing" mode

### "Error 400: redirect_uri_mismatch"

**Cause**: Wrong OAuth credential type.

**Solution**:

1. Go to Google Cloud Console > APIs & Services > Credentials
2. Delete the existing OAuth 2.0 Client ID
3. Create a new one with type **Desktop app** (not Web application)
4. Update `.env` with new credentials

### "Token has been expired or revoked"

**Cause**: OAuth token is no longer valid.

**Solution**:

1. Delete `data/token.json`
2. Restart Gmail Agent
3. Re-authenticate via Settings > Connect Google Account

### "The caller does not have permission"

**Cause**: Required API not enabled or scope missing.

**Solution**:

1. Verify Gmail API is enabled in Google Cloud Console
2. Verify Google Calendar API is enabled
3. Delete `data/token.json` and re-authenticate

## API Issues

### "Model is currently loading"

**Cause**: HuggingFace is loading the model into memory.

**Solution**: Wait 30-60 seconds and try again. First requests after idle periods are slower.

### "Rate limit exceeded"

**Cause**: Too many HuggingFace API requests.

**Solution**:

- Wait a few minutes before retrying
- Consider upgrading to HuggingFace Pro
- Use a dedicated Inference Endpoint for production

### "Authorization header is invalid"

**Cause**: Invalid HuggingFace API token.

**Solution**:

1. Generate a new token at [HuggingFace Settings](https://huggingface.co/settings/tokens)
2. Ensure token starts with `hf_`
3. Update `.env` with the new token
4. Restart the application

### "Model not found"

**Cause**: Invalid model ID or model requires authorization.

**Solution**:

1. Verify the model exists on HuggingFace Hub
2. Accept any license/terms on the model page
3. Check if model is available for Inference API
4. Use a different model

## Email Issues

### Emails not loading

**Cause**: Gmail API connection issue.

**Solution**:

1. Check connection status in Settings
2. If disconnected, re-authenticate
3. Verify Gmail API is enabled in Google Cloud Console
4. Check browser console for error messages

### Classification taking too long

**Cause**: LLM inference delay.

**Solution**:

- Wait for response (can take 30+ seconds)
- Try a smaller/faster model
- Check HuggingFace status for outages

### Wrong classifications

**Cause**: LLM interpretation varies.

**Solution**:

- Review and manually correct
- Adjust confidence threshold higher
- Try a different LLM model
- Report persistent issues

## Calendar Issues

### Calendar events not showing

**Cause**: Calendar API not authorized.

**Solution**:

1. Verify Google Calendar API is enabled
2. Delete `data/token.json`
3. Re-authenticate to get calendar scope
4. Refresh the Calendar view

### Can't create events

**Cause**: Permission or API issue.

**Solution**:

1. Verify calendar write permission in OAuth scopes
2. Check that calendar is not read-only
3. Re-authenticate if needed

## Application Issues

### Streamlit won't start

**Cause**: Missing dependencies or Python version.

**Solution**:

```bash
# Ensure Python 3.11+
python --version

# Reinstall dependencies
uv sync

# Try running directly
uv run streamlit run app.py --server.port 8501
```

### Port 8501 already in use

**Cause**: Another instance running.

**Solution**:

```bash
# Find and kill existing process
lsof -i :8501
kill -9 <PID>

# Or use different port
uv run streamlit run app.py --server.port 8502
```

### Database errors

**Cause**: Corrupted database file.

**Solution**:

```bash
# Backup and remove database
mv data/gmail_agent.db data/gmail_agent.db.backup

# Restart app to create fresh database
uv run streamlit run app.py
```

### "Module not found" errors

**Cause**: Dependencies not installed.

**Solution**:

```bash
# Sync dependencies
uv sync

# If still failing, recreate environment
rm -rf .venv
uv sync
```

## Configuration Issues

### Environment variables not loading

**Cause**: `.env` file issues.

**Solution**:

1. Verify `.env` exists in project root
2. Check for syntax errors (no quotes around values usually)
3. Restart the application after changes

### Settings not saving

**Cause**: File permission or path issue.

**Solution**:

1. Check write permissions on `data/` directory
2. Verify `.env` file is writable
3. Check for disk space issues

## Getting Help

### Reporting Issues

When reporting issues, include:

1. Python version (`python --version`)
2. Operating system
3. Error messages (full traceback)
4. Steps to reproduce

### Debug Mode

Enable debug logging:

```python
# In app.py, change:
logging.basicConfig(level=logging.DEBUG)
```

### Checking Logs

View application logs in the terminal where Streamlit is running.

For more verbose output:

```bash
uv run streamlit run app.py --logger.level debug
```

## FAQ

### Is my email data stored?

Gmail Agent stores:

- Classification history (email IDs and categories)
- Draft content you generate
- Trusted sender list

Email content is processed in memory and not persisted.

### Can Gmail Agent send emails without approval?

No. All email actions require explicit user approval. There is no automatic sending.

### Does Gmail Agent work offline?

No. Gmail Agent requires internet access for:

- Gmail API
- Google Calendar API
- HuggingFace Inference API

### Can I use a local LLM?

Not currently. Gmail Agent is designed for HuggingFace Inference API. Local model support may be added in future versions.

### How do I revoke Google access?

1. Disconnect in Gmail Agent Settings
2. Visit [Google Account Permissions](https://myaccount.google.com/permissions)
3. Find "Gmail Agent" and click Remove Access

### Is Gmail Agent secure?

Gmail Agent follows security best practices:

- OAuth 2.0 for authentication
- Tokens stored locally only
- No data sent to third parties (except APIs)
- Human approval required for all actions

Always keep your `.env` file and `data/` directory secure.
