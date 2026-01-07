# Setup Guide: Getting Your Slack Tokens

This guide will help you obtain the required tokens for your Slack Assistant bot.

## Prerequisites

1. **Slack Developer Program Account** (Free)
   - Sign up at: https://api.slack.com/developer-program
   - Join the Developer Program to get access to developer sandboxes

2. **Slack Workspace**
   - Use a developer sandbox (recommended): https://docs.slack.dev/tools/developer-sandboxes/
   - Or use your own workspace

## Step 1: Create a Slack App

### Option A: Using Slack CLI (Recommended)

1. Install Slack CLI: https://docs.slack.dev/tools/slack-cli/guides/installing-the-slack-cli
2. Login: `slack login`
3. Create app from manifest:
   ```bash
   slack create my-slack-assistant --template slack-samples/bolt-python-assistant-template
   cd my-slack-assistant
   ```
4. Install to workspace: `slack install`
5. Tokens will be automatically configured

### Option B: Using Web Interface

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From an app manifest"**
3. Select your workspace
4. Copy the contents of `manifest.json` into the text box
5. Click **"Next"** → **"Create"**
6. Click **"Install to Workspace"** → **"Allow"**

## Step 2: Get SLACK_BOT_TOKEN

1. Go to https://api.slack.com/apps
2. Select your app
3. In the left sidebar, click **"OAuth & Permissions"**
4. Scroll to **"Bot User OAuth Token"**
5. Copy the token (starts with `xoxb-`)
6. Add it to your `.env` file:
   ```
   SLACK_BOT_TOKEN=xoxb-your-actual-token-here
   ```

## Step 3: Get SLACK_APP_TOKEN

1. In your app settings, click **"Basic Information"** in the left sidebar
2. Scroll down to **"App-Level Tokens"**
3. Click **"Generate Token and Scopes"**
4. Enter a name (e.g., "Socket Mode Token")
5. Add scope: `connections:write`
6. Click **"Generate"**
7. Copy the token (starts with `xapp-`)
8. Add it to your `.env` file:
   ```
   SLACK_APP_TOKEN=xapp-your-actual-token-here
   ```

## Step 4: Get GOOGLE_API_KEY

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the API key
5. Add it to your `.env` file:
   ```
   GOOGLE_API_KEY=your-actual-api-key-here
   ```

## Step 5: Create Your .env File

1. Copy `.env.sample` to `.env`:
   ```bash
   cp .env.sample .env
   ```
2. Open `.env` and replace the placeholder values with your actual tokens

## Final .env File Should Look Like:

```
SLACK_BOT_TOKEN=xoxb-YOUR-BOT-TOKEN-HERE
SLACK_APP_TOKEN=xapp-YOUR-APP-TOKEN-HERE
GOOGLE_API_KEY=YOUR-GOOGLE-API-KEY-HERE
```

## Verify Your Setup

1. Make sure `.env` is in your `.gitignore` (it should be)
2. Never commit `.env` to version control
3. Test your setup by running:
   ```bash
   python app.py
   ```

## Troubleshooting

### "Invalid token" error
- Double-check you copied the entire token (they're long!)
- Make sure there are no extra spaces
- Verify the token hasn't expired (regenerate if needed)

### "Missing scope" error
- Ensure your app has the required scopes in `manifest.json`
- Reinstall the app to your workspace after updating scopes

### Socket Mode connection issues
- Verify `SLACK_APP_TOKEN` has `connections:write` scope
- Check that Socket Mode is enabled in your app settings

## Resources

- Slack Developer Program: https://api.slack.com/developer-program
- Developer Sandboxes: https://docs.slack.dev/tools/developer-sandboxes/
- Slack API Documentation: https://api.slack.com/docs/apps/ai
- Google AI Studio: https://makersuite.google.com/app/apikey

