# Webhooks Guide

Webhooks enable real-time notifications from AgentHR to your application. When events occur (like a candidate being created or a stage changing), AgentHR sends HTTP POST requests to your configured endpoints.

## How Webhooks Work

1. **Subscribe** - Register your endpoint URL for specific events
2. **Receive** - AgentHR sends POST requests when events occur
3. **Verify** - Validate the webhook signature (if secret is set)
4. **Respond** - Return 2xx status code to acknowledge receipt
5. **Retry** - Failed deliveries are retried with exponential backoff

## Webhook Events

### Candidate Events

#### candidate.created
Fired when a new candidate profile is created.

```json
{
  "event": "candidate.created",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "candidate_id": "uuid_here",
    "name": "Jane Smith",
    "email": "jane@example.com",
    "vacancy_id": "vacancy_uuid",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### candidate.updated
Fired when candidate details are updated.

```json
{
  "event": "candidate.updated",
  "timestamp": "2024-01-15T11:00:00Z",
  "data": {
    "candidate_id": "uuid_here",
    "changes": {
      "email": {
        "old": "jane@example.com",
        "new": "jane.new@example.com"
      }
    },
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

#### candidate.deleted
Fired when a candidate is deleted.

```json
{
  "event": "candidate.deleted",
  "timestamp": "2024-01-15T12:00:00Z",
  "data": {
    "candidate_id": "uuid_here",
    "deleted_at": "2024-01-15T12:00:00Z"
  }
}
```

### Stage Events

#### stage.changed
Fired when a candidate moves to a different pipeline stage.

```json
{
  "event": "stage.changed",
  "timestamp": "2024-01-15T14:30:00Z",
  "data": {
    "candidate_id": "uuid_here",
    "vacancy_id": "vacancy_uuid",
    "previous_stage": "screening",
    "new_stage": "interview",
    "notes": "Candidate passed screening",
    "changed_at": "2024-01-15T14:30:00Z"
  }
}
```

### Ranking Events

#### ranking.created
Fired when a candidate is ranked for a vacancy.

```json
{
  "event": "ranking.created",
  "timestamp": "2024-01-15T15:00:00Z",
  "data": {
    "candidate_id": "uuid_here",
    "vacancy_id": "vacancy_uuid",
    "score": 85.5,
    "rank": 3,
    "created_at": "2024-01-15T15:00:00Z"
  }
}
```

#### ranking.updated
Fired when a ranking score is updated.

```json
{
  "event": "ranking.updated",
  "timestamp": "2024-01-15T15:30:00Z",
  "data": {
    "candidate_id": "uuid_here",
    "vacancy_id": "vacancy_uuid",
    "old_score": 75.0,
    "new_score": 85.5,
    "old_rank": 5,
    "new_rank": 3,
    "updated_at": "2024-01-15T15:30:00Z"
  }
}
```

### Resume Events

#### resume.uploaded
Fired when a resume is uploaded.

```json
{
  "event": "resume.uploaded",
  "timestamp": "2024-01-15T16:00:00Z",
  "data": {
    "resume_id": "uuid_here",
    "candidate_id": "candidate_uuid",
    "filename": "resume.pdf",
    "uploaded_at": "2024-01-15T16:00:00Z"
  }
}
```

#### resume.processed
Fired when resume parsing is complete.

```json
{
  "event": "resume.processed",
  "timestamp": "2024-01-15T16:05:00Z",
  "data": {
    "resume_id": "uuid_here",
    "candidate_id": "candidate_uuid",
    "status": "completed",
    "parsed_data": {
      "name": "Jane Smith",
      "email": "jane@example.com",
      "skills": ["Python", "FastAPI"]
    },
    "processed_at": "2024-01-15T16:05:00Z"
  }
}
```

#### resume.analyzed
Fired when resume analysis (NER, keyword extraction) is complete.

```json
{
  "event": "resume.analyzed",
  "timestamp": "2024-01-15T16:10:00Z",
  "data": {
    "resume_id": "uuid_here",
    "entities": ["PERSON", "ORG", "DATE"],
    "keywords": ["Python", "machine learning"],
    "analyzed_at": "2024-01-15T16:10:00Z"
  }
}
```

### Vacancy Events

#### vacancy.created
Fired when a new vacancy is created.

```json
{
  "event": "vacancy.created",
  "timestamp": "2024-01-15T17:00:00Z",
  "data": {
    "vacancy_id": "uuid_here",
    "title": "Senior Python Developer",
    "location": "Remote",
    "created_at": "2024-01-15T17:00:00Z"
  }
}
```

#### vacancy.updated
Fired when vacancy details are updated.

#### vacancy.filled
Fired when a vacancy is marked as filled.

```json
{
  "event": "vacancy.filled",
  "timestamp": "2024-01-15T18:00:00Z",
  "data": {
    "vacancy_id": "uuid_here",
    "hired_candidate_id": "candidate_uuid",
    "filled_at": "2024-01-15T18:00:00Z"
  }
}
```

### Match Events

#### match.created
Fired when a candidate-vacancy match is created.

```json
{
  "event": "match.created",
  "timestamp": "2024-01-15T19:00:00Z",
  "data": {
    "candidate_id": "uuid_here",
    "vacancy_id": "vacancy_uuid",
    "score": 92.5,
    "created_at": "2024-01-15T19:00:00Z"
  }
}
```

#### match.updated
Fired when a match score is updated.

### Other Events

#### feedback.created
Fired when interview feedback is submitted.

#### report.generated
Fired when an analytics report is generated.

#### note.created
Fired when a note is added to a candidate.

## Creating Webhooks

### Via API

```bash
curl -X POST https://api.agenthr.com/api/webhooks/subscribe \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/agenthr",
    "events": ["candidate.created", "stage.changed", "ranking.created"],
    "secret": "your_hmac_secret_here",
    "api_key_id": "optional_api_key_id"
  }'
```

Response:
```json
{
  "id": "webhook_uuid",
  "url": "https://your-app.com/webhooks/agenthr",
  "events": ["candidate.created", "stage.changed", "ranking.created"],
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Via Developer Portal

1. Navigate to https://app.agenthr.com/developer/webhooks
2. Click "Create Webhook"
3. Enter your endpoint URL
4. Select events to subscribe to
5. (Optional) Set a secret for signature verification
6. Click "Create"

## Webhook Signature Verification

To verify webhook authenticity, AgentHR signs each webhook payload using HMAC-SHA256.

### Headers

```
X-Webhook-Signature: sha256=signature_hash_here
X-Webhook-Timestamp: 2024-01-15T10:30:00Z
X-Webhook-Event: candidate.created
```

### Verification (Python)

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    """
    Verify webhook signature
    """
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        f"sha256={expected_signature}",
        signature
    )

# Usage
import json
from flask import request

@app.route('/webhooks/agenthr', methods=['POST'])
def handle_webhook():
    payload = request.data.decode('utf-8')
    signature = request.headers.get('X-Webhook-Signature')
    secret = 'your_webhook_secret'

    if not verify_webhook(payload, signature, secret):
        return 'Invalid signature', 401

    event = json.loads(payload)
    # Process event...

    return 'OK', 200
```

### Verification (Node.js)

```javascript
const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(payload);
  const expectedSignature = `sha256=${hmac.digest('hex')}`;

  return crypto.timingSafeEqual(
    Buffer.from(expectedSignature),
    Buffer.from(signature)
  );
}

// Usage (Express)
app.post('/webhooks/agenthr', (req, res) => {
  const payload = JSON.stringify(req.body);
  const signature = req.headers['x-webhook-signature'];
  const secret = 'your_webhook_secret';

  if (!verifyWebhook(payload, signature, secret)) {
    return res.status(401).send('Invalid signature');
  }

  // Process event...
  res.status(200).send('OK');
});
```

## Handling Webhooks

### Best Practices

1. **Return 2xx Quickly** - Process webhooks asynchronously
2. **Use Queues** - Don't block the webhook handler
3. **Idempotency** - Handle duplicate webhook deliveries
4. **Verify Signatures** - Always verify HMAC signature
5. **Handle Errors** - Return appropriate status codes

### Example Handler (Python with Celery)

```python
from celery import Celery
from flask import Flask, request

celery = Celery('webhooks', broker='redis://localhost')
app = Flask(__name__)

@app.route('/webhooks/agenthr', methods=['POST'])
def handle_webhook():
    # Verify signature
    if not verify_webhook(request.data, request.headers['X-Webhook-Signature'], secret):
        return 'Invalid signature', 401

    event = request.get_json()

    # Process asynchronously
    process_webhook_event.delay(event)

    return 'OK', 200

@celery.task
def process_webhook_event(event):
    """Process webhook event asynchronously"""
    event_type = event['event']
    data = event['data']

    if event_type == 'candidate.created':
        handle_candidate_created(data)
    elif event_type == 'stage.changed':
        handle_stage_changed(data)
    # ... handle other events
```

### Response Codes

| Code | Action |
|------|--------|
| 200 | Delivery successful, no retry |
| 202 | Delivery accepted (async processing) |
| 400 | Invalid payload (will retry) |
| 401 | Signature verification failed (will retry) |
| 404 | Endpoint not found (will retry) |
| 429 | Rate limiting (will retry) |
| 500 | Server error (will retry) |

## Retry Logic

Webhooks that fail are automatically retried with exponential backoff:

| Attempt | Delay |
|---------|-------|
| 1 | Immediate |
| 2 | 30 seconds |
| 3 | 2 minutes |
| 4 | 5 minutes |
| 5 | 10 minutes |
| 6 | 30 minutes |
| 7 | 1 hour |
| 8 | 2 hours |
| 9+ | 4 hours |

After 10 consecutive failures, the webhook is automatically disabled.

### Checking Delivery Status

```bash
curl -X GET "https://api.agenthr.com/api/webhooks/{subscription_id}/logs?limit=10" \
  -H "X-API-Key: your_api_key"
```

Response:
```json
{
  "items": [
    {
      "id": "log_uuid",
      "event_type": "candidate.created",
      "status": "success",
      "status_code": 200,
      "attempt_count": 1,
      "delivered_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "log_uuid",
      "event_type": "stage.changed",
      "status": "failed",
      "status_code": 500,
      "attempt_count": 3,
      "next_retry_at": "2024-01-15T11:00:00Z",
      "error_message": "Internal server error"
    }
  ]
}
```

## Managing Webhooks

### List Subscriptions

```bash
curl -X GET https://api.agenthr.com/api/webhooks \
  -H "X-API-Key: your_api_key"
```

### Get Subscription Details

```bash
curl -X GET https://api.agenthr.com/api/webhooks/{subscription_id} \
  -H "X-API-Key: your_api_key"
```

### Update Subscription

```bash
curl -X PUT https://api.agenthr.com/api/webhooks/{subscription_id} \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://new-url.com/webhooks",
    "events": ["candidate.created", "stage.changed"]
  }'
```

### Disable Webhook

```bash
curl -X POST https://api.agenthr.com/api/webhooks/{subscription_id}/disable \
  -H "X-API-Key: your_api_key"
```

### Enable Webhook

```bash
curl -X POST https://api.agenthr.com/api/webhooks/{subscription_id}/enable \
  -H "X-API-Key: your_api_key"
```

### Delete Subscription

```bash
curl -X DELETE https://api.agenthr.com/api/webhooks/{subscription_id} \
  -H "X-API-Key: your_api_key"
```

## Testing Webhooks

### Using Webhook.site

1. Visit https://webhook.site
2. Copy your unique URL
3. Create webhook subscription with that URL
4. Trigger an event in AgentHR
5. View the received payload

### Using Ngrok for Local Testing

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com

# Start ngrok
ngrok http 3000

# Use the HTTPS URL in your webhook subscription
# e.g., https://abc123.ngrok.io/webhooks/agenthr
```

### Example Test Server (Python Flask)

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhooks/agenthr', methods=['POST'])
def handle_webhook():
    event = request.get_json()
    print(f"Received event: {event['event']}")
    print(f"Data: {event['data']}")

    # Log to file for inspection
    with open('webhooks.log', 'a') as f:
        f.write(f"{event}\n")

    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(port=3000, debug=True)
```

## Troubleshooting

### Common Issues

**Webhook not received:**
- Check subscription is active
- Verify correct event types are subscribed
- Check delivery logs for failures
- Ensure endpoint returns 2xx status

**Signature verification failing:**
- Verify secret matches subscription
- Check raw payload (not parsed)
- Ensure UTF-8 encoding

**Endpoint timing out:**
- Process asynchronously
- Return 202 immediately
- Use queue for processing

### Debug Mode

Add `print_debug=true` to subscription to receive test pings:

```bash
curl -X POST https://api.agenthr.com/api/webhooks/subscribe \
  -H "X-API-Key: your_api_key" \
  -d '{
    "url": "https://your-app.com/webhooks",
    "events": ["test.ping"]
  }'
```

## Webhook Workflows

Webhooks can trigger automated workflows:

1. **New Candidate Created** → Add to CRM / Send Slack notification
2. **Stage Changed** → Update candidate in ATS / Email hiring manager
3. **Ranking Created** → Auto-schedule interview if score > 90
4. **Resume Processed** → Extract skills → Update candidate tags

Example workflow using AgentHR's workflow automation:

```json
{
  "name": "New Candidate Slack Notification",
  "trigger_type": "webhook",
  "trigger_config": {
    "event": "candidate.created"
  },
  "actions": [
    {
      "type": "send_slack",
      "channel": "#recruiting",
      "message": "New candidate: {{candidate.name}} applied for {{vacancy.title}}"
    }
  ]
}
```

## Rate Limits

Webhook delivery endpoints have the following rate limits:

- **Per IP**: 1000 requests/minute
- **Per Subscription**: 100 requests/minute

If your endpoint cannot handle the volume, consider:
1. Using message queues (RabbitMQ, Kafka)
2. Implementing rate limiting on your side
3. Batching webhook processing

## Resources

- [API Reference](./endpoints.md)
- [Authentication Guide](./authentication.md)
- [Code Examples](../examples/)
- [Webhook Playground](https://app.agenthr.com/developer/webhooks)

## Support

For webhook-related issues:
- Check delivery logs in Developer Portal
- Review [API Status](https://status.agenthr.com)
- Email: webhooks@agenthr.com
