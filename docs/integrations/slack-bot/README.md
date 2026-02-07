# AgentHR Slack Bot Integration

Build a Slack bot that integrates with AgentHR to receive notifications, query candidate information, and manage recruitment workflows directly from Slack.

## Overview

This integration enables you to:
- Receive real-time notifications in Slack when candidates are created, ranked, or status changes occur
- Query candidate information with simple slash commands
- Get vacancy updates and statistics
- Trigger workflows and automations from Slack

## Prerequisites

- AgentHR API key with appropriate scopes
- Slack workspace with admin permissions
- Python 3.8+ or Node.js 16+
- ngrok or a public webhook URL (for development)

## Setup Guide

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App**
2. Choose **From scratch** and enter:
   - App name: `AgentHR Bot`
   - Pick a workspace where you'll develop the app
3. Click **Create App**

### 2. Configure Bot Permissions

1. Navigate to **OAuth & Permissions** in the left sidebar
2. Add the following Bot Token Scopes:
   ```
   chat:write          - Send messages to channels
   channels:read       - View channel information
   incoming-webhook    - Receive webhooks
   commands            - Handle slash commands
   app_mentions:read   - Read @mentions
   ```

3. Scroll to **OAuth Tokens for Your Workspace** and click **Install to Workspace**
4. Save the **Bot User OAuth Token** (starts with `xoxb-`)

### 3. Enable Interactive Components

1. Navigate to **Interactivity & Shortcuts**
2. Toggle **Interactivity** to **On**
3. Set your Request URL:
   ```
   https://your-domain.com/slack/interactions
   ```
4. Click **Save Changes**

### 4. Create Slash Commands

Create the following commands under **Slash Commands**:

| Command | Request URL | Description |
|---------|-------------|-------------|
| `/agenthr` | `https://your-domain.com/slack/command` | Main command interface |
| `/candidate` | `https://your-domain.com/slack/candidate` | Query candidate info |
| `/vacancy` | `https://your-domain.com/slack/vacancy` | Query vacancy info |

### 5. Configure AgentHR Webhooks

Create a webhook subscription in AgentHR to send events to your Slack bot:

```python
import httpx

async def setup_slack_webhook():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.agenthr.com/api/webhooks/subscribe",
            headers={
                "X-API-Key": "your_agenthr_api_key",
                "Content-Type": "application/json"
            },
            json={
                "url": "https://your-domain.com/webhooks/agenthr",
                "events": [
                    "candidate.created",
                    "candidate.updated",
                    "stage.changed",
                    "ranking.created"
                ],
                "secret": "your_webhook_secret"
            }
        )
        return response.json()
```

## Implementation

### Python Implementation

Install dependencies:
```bash
pip install slack-sdk fastapi uvicorn httpx
```

Create `slack_bot.py`:

```python
import os
from slack_sdk.web import WebClient
from slack_sdk.adapter.fastapi import SlackRequestHandler
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import hmac
import hashlib

app = FastAPI()

# Slack client
slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
slack_handler = SlackRequestHandler(app)

# AgentHR configuration
AGENTHR_API_KEY = os.environ["AGENTHR_API_KEY"]
AGENTHR_API_URL = os.environ.get("AGENTHR_API_URL", "https://api.agenthr.com")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

@app.post("/slack/command")
async def handle_command(request: Request):
    """Handle Slack slash commands"""
    form_data = await request.form()
    command = form_data.get("command")
    text = form_data.get("text", "")
    user_id = form_data.get("user_id")
    channel_id = form_data.get("channel_id")

    if command == "/agenthr":
        return await handle_agenthr_command(text, user_id, channel_id)
    elif command == "/candidate":
        return await handle_candidate_command(text, user_id, channel_id)
    elif command == "/vacancy":
        return await handle_vacancy_command(text, user_id, channel_id)

    return {"text": f"Unknown command: {command}"}

async def handle_agenthr_command(text: str, user_id: str, channel_id: str):
    """Handle /agenthr commands"""
    if not text or text == "help":
        return {
            "text": (
                "*AgentHR Bot Commands*\n\n"
                "• `/agenthr` - Show this help\n"
                "• `/candidate <email_or_id>` - Get candidate info\n"
                "• `/vacancy list` - List vacancies\n"
                "• `/vacancy <id>` - Get vacancy details\n"
            )
        }

async def handle_candidate_command(text: str, user_id: str, channel_id: str):
    """Handle /candidate commands"""
    if not text:
        return {"text": "Usage: `/candidate <email_or_id>`"}

    # Query AgentHR API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AGENTHR_API_URL}/api/candidates",
            headers={"X-API-Key": AGENTHR_API_KEY},
            params={"search": text, "limit": 5}
        )
        response.raise_for_status()
        data = response.json()

    if not data.get("items"):
        return {"text": f"No candidates found for '{text}'"}

    # Format response
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Found {len(data['items'])} candidate(s)*"
            }
        }
    ]

    for candidate in data["items"][:3]:  # Show max 3
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{candidate.get('name', 'Unknown')}*\n"
                    f"Email: {candidate.get('email', 'N/A')}\n"
                    f"Stage: {candidate.get('current_stage', 'N/A')}\n"
                    f"Vacancy: {candidate.get('vacancy_title', 'N/A')}"
                )
            }
        })

    return {"blocks": blocks}

async def handle_vacancy_command(text: str, user_id: str, channel_id: str):
    """Handle /vacancy commands"""
    if text == "list":
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AGENTHR_API_URL}/api/vacancies",
                headers={"X-API-Key": AGENTHR_API_KEY},
                params={"limit": 10}
            )
            response.raise_for_status()
            data = response.json()

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Open Vacancies ({len(data['items'])})*"
                }
            }
        ]

        for vacancy in data["items"]:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{vacancy['title']}*\n"
                        f"Location: {vacancy.get('location', 'N/A')}\n"
                        f"Status: {vacancy.get('status', 'N/A')}"
                    )
                }
            })

        return {"blocks": blocks}

    return {"text": "Usage: `/vacancy list` or `/vacancy <id>`"}

@app.post("/webhooks/agenthr")
async def handle_agenthr_webhook(request: Request):
    """Handle AgentHR webhook events"""
    payload = await request.json()

    # Verify webhook signature if secret is set
    if WEBHOOK_SECRET:
        signature = request.headers.get("X-AgentHR-Signature", "")
        body = await request.body()
        expected = hmac.new(
            WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, f"sha256={expected}"):
            raise HTTPException(status_code=401, detail="Invalid signature")

    event = payload.get("event")
    data = payload.get("data", {})

    # Route to appropriate handler
    if event == "candidate.created":
        await notify_candidate_created(data)
    elif event == "stage.changed":
        await notify_stage_changed(data)
    elif event == "ranking.created":
        await notify_ranking_created(data)

    return {"status": "ok"}

async def notify_candidate_created(data: dict):
    """Send Slack notification for new candidate"""
    candidate_name = data.get("name", "Unknown")
    vacancy_title = data.get("vacancy_title", "Unknown")
    candidate_id = data.get("candidate_id", "")

    message = (
        f":new: *New Candidate Created*\n\n"
        f"*Name:* {candidate_name}\n"
        f"*Vacancy:* {vacancy_title}\n"
        f"*Email:* {data.get('email', 'N/A')}\n"
    )

    # Post to configured channel
    await slack_client.chat_postMessage(
        channel=os.environ.get("SLACK_CHANNEL_ID", "#recruiting"),
        text=message
    )

async def notify_stage_changed(data: dict):
    """Send Slack notification for stage change"""
    candidate_id = data.get("candidate_id")
    previous_stage = data.get("previous_stage", "Unknown")
    new_stage = data.get("new_stage", "Unknown")

    # Get candidate details
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AGENTHR_API_URL}/api/candidates/{candidate_id}",
            headers={"X-API-Key": AGENTHR_API_KEY}
        )
        response.raise_for_status()
        candidate = response.json()

    message = (
        f":arrows_counterclockwise: *Candidate Stage Changed*\n\n"
        f"*Candidate:* {candidate.get('name', 'Unknown')}\n"
        f"*Previous Stage:* {previous_stage}\n"
        f"*New Stage:* {new_stage}\n"
    )

    await slack_client.chat_postMessage(
        channel=os.environ.get("SLACK_CHANNEL_ID", "#recruiting"),
        text=message
    )

async def notify_ranking_created(data: dict):
    """Send Slack notification for new ranking"""
    candidate_id = data.get("candidate_id")
    score = data.get("score", 0)

    message = (
        f":star: *New Candidate Ranking*\n\n"
        f"*Candidate ID:* {candidate_id}\n"
        f"*Match Score:* {score:.1f}%\n"
    )

    await slack_client.chat_postMessage(
        channel=os.environ.get("SLACK_CHANNEL_ID", "#recruiting"),
        text=message
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Node.js Implementation

Install dependencies:
```bash
npm install slack-sdk @slack/bolt fastify httpc
```

Create `slack_bot.js`:

```javascript
const { App } = require('@slack/bolt');
const fastify = require('fastify')({ logger: true });
const axios = require('axios');

const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET
});

const AGENTHR_API_KEY = process.env.AGENTHR_API_KEY;
const AGENTHR_API_URL = process.env.AGENTHR_API_URL || 'https://api.agenthr.com';

// Slash command: /agenthr
app.command('/agenthr', async ({ command, ack, respond }) => {
  await ack();

  if (!command.text || command.text === 'help') {
    await respond({
      text: `*AgentHR Bot Commands*\n\n` +
            `• /agenthr - Show this help\n` +
            `• /candidate <email_or_id> - Get candidate info\n` +
            `• /vacancy list - List vacancies`
    });
    return;
  }
});

// Slash command: /candidate
app.command('/candidate', async ({ command, ack, respond }) => {
  await ack();

  if (!command.text) {
    await respond({ text: 'Usage: /candidate <email_or_id>' });
    return;
  }

  try {
    const response = await axios.get(`${AGENTHR_API_URL}/api/candidates`, {
      headers: { 'X-API-Key': AGENTHR_API_KEY },
      params: { search: command.text, limit: 5 }
    });

    const candidates = response.data.items || [];
    if (candidates.length === 0) {
      await respond({ text: `No candidates found for '${command.text}'` });
      return;
    }

    const blocks = [
      {
        type: 'section',
        text: { type: 'mrkdwn', text: `*Found ${candidates.length} candidate(s)*` }
      }
    ];

    candidates.slice(0, 3).forEach(candidate => {
      blocks.push({
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `*${candidate.name || 'Unknown'}*\n` +
                `Email: ${candidate.email || 'N/A'}\n` +
                `Stage: ${candidate.current_stage || 'N/A'}`
        }
      });
    });

    await respond({ blocks });
  } catch (error) {
    await respond({ text: `Error: ${error.message}` });
  }
});

// Slash command: /vacancy
app.command('/vacancy', async ({ command, ack, respond }) => {
  await ack();

  if (command.text === 'list') {
    try {
      const response = await axios.get(`${AGENTHR_API_URL}/api/vacancies`, {
        headers: { 'X-API-Key': AGENTHR_API_KEY },
        params: { limit: 10 }
      });

      const vacancies = response.data.items || [];
      const blocks = [
        {
          type: 'section',
          text: { type: 'mrkdwn', text: `*Open Vacancies (${vacancies.length})*` }
        }
      ];

      vacancies.forEach(vacancy => {
        blocks.push({
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `*${vacancy.title}*\n` +
                  `Location: ${vacancy.location || 'N/A'}\n` +
                  `Status: ${vacancy.status || 'N/A'}`
          }
        });
      });

      await respond({ blocks });
    } catch (error) {
      await respond({ text: `Error: ${error.message}` });
    }
  }
});

// Fastify webhook endpoint
fastify.post('/webhooks/agenthr', async (request, reply) => {
  const { event, data } = request.body;

  if (event === 'candidate.created') {
    await notifyCandidateCreated(data);
  } else if (event === 'stage.changed') {
    await notifyStageChanged(data);
  }

  return { status: 'ok' });
});

async function notifyCandidateCreated(data) {
  const message = `:new: *New Candidate Created*\n\n` +
                 `*Name:* ${data.name || 'Unknown'}\n` +
                 `*Vacancy:* ${data.vacancy_title || 'Unknown'}\n`;

  await app.client.chat.postMessage({
    channel: process.env.SLACK_CHANNEL_ID || '#recruiting',
    text: message
  });
}

async function notifyStageChanged(data) {
  const message = `:arrows_counterclockwise: *Candidate Stage Changed*\n\n` +
                 `*Previous Stage:* ${data.previous_stage}\n` +
                 `*New Stage:* ${data.new_stage}\n`;

  await app.client.chat.postMessage({
    channel: process.env.SLACK_CHANNEL_ID || '#recruiting',
    text: message
  });
}

// Start server
(async () => {
  await app.start(process.env.PORT || 3000);
  console.log('Slack bot running');
})();
```

## Environment Variables

Create a `.env` file:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_CHANNEL_ID=C1234567890

# AgentHR Configuration
AGENTHR_API_KEY=your_agenthr_api_key
AGENTHR_API_URL=https://api.agenthr.com
WEBHOOK_SECRET=your_webhook_secret

# Server Configuration
PORT=8000
```

## Deployment

### Development with ngrok

1. Install ngrok: `brew install ngrok` (macOS) or download from ngrok.com
2. Start your bot: `python slack_bot.py`
3. In another terminal: `ngrok http 8000`
4. Use the ngrok URL for your Slack app's Request URL

### Production Deployment

Deploy to a cloud platform with a public URL:

**Heroku:**
```bash
heroku create agenthr-slack-bot
heroku config:set SLACK_BOT_TOKEN=xoxb-...
heroku config:set AGENTHR_API_KEY=...
git push heroku main
```

**Docker:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "slack_bot.py"]
```

## Advanced Features

### Interactive Buttons

Add action buttons to candidate notifications:

```python
blocks.append({
    "type": "actions",
    "elements": [
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "View Profile"},
            "action_id": "view_candidate",
            "value": candidate_id
        },
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "Schedule Interview"},
            "action_id": "schedule_interview",
            "value": candidate_id
        }
    ]
})
```

### Modal Forms

Open a modal for detailed candidate information:

```python
await slack_client.views_open(
    trigger_id=trigger_id,
    view={
        "type": "modal",
        "title": {"type": "plain_text", "text": "Candidate Details"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Name:* {candidate['name']}"}
            }
        ]
    }
)
```

## Troubleshooting

**Bot not responding to commands:**
- Verify bot token is correct
- Check bot is invited to the channel
- Verify Request URL matches your server

**Webhooks not delivering:**
- Check ngrok is running (development)
- Verify AgentHR webhook subscription is active
- Check webhook logs in AgentHR portal

**Permission errors:**
- Ensure bot has required scopes
- Reinstall app to workspace after adding scopes

## Resources

- [Slack API Documentation](https://api.slack.com/)
- [AgentHR API Reference](/api/endpoints.md)
- [AgentHR Webhooks Guide](/api/webhooks.md)
