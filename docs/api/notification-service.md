# Notification Service API Documentation

## Overview

The Notification Service handles all types of notifications including email, SMS, webhook, and in-app notifications. It provides endpoints for sending notifications, managing notification history, and configuring notification templates.

## Base URL

```
http://localhost:8008
```

Via API Gateway:
```
http://localhost:8888/api/notifications
```

## Authentication

All endpoints require JWT authentication via the API Gateway. Include the `Authorization` header with your Bearer token:

```
Authorization: Bearer <your-jwt-token>
```

---

## Endpoints

### Send Notification

Send a notification to a recipient.

**Endpoint:** `POST /api/notifications/send`

**Request Body:**
```json
{
  "type": "email",
  "recipient": "candidate@example.com",
  "subject": "Interview Invitation",
  "body": "You are invited for an interview...",
  "priority": "high",
  "metadata": {
    "candidate_id": "candidate-123",
    "vacancy_id": "vacancy-456"
  }
}
```

**Notification Types:**
- `email` - Email notification
- `sms` - SMS notification
- `webhook` - Webhook notification
- `in_app` - In-app notification

**Priority Levels:**
- `low` - Low priority
- `normal` - Normal priority (default)
- `high` - High priority
- `urgent` - Urgent priority

**Response:** `201 Created`

```json
{
  "id": "notification-1",
  "type": "email",
  "recipient": "candidate@example.com",
  "status": "pending",
  "priority": "high",
  "subject": "Interview Invitation",
  "sent_at": null,
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8888/api/notifications/send" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "email",
    "recipient": "candidate@example.com",
    "subject": "Interview Invitation",
    "body": "You are invited for an interview...",
    "priority": "high"
  }'
```

---

### Send Templated Notification

Send a notification using a template.

**Endpoint:** `POST /api/notifications/send-templated`

**Request Body:**
```json
{
  "type": "email",
  "recipient": "candidate@example.com",
  "template_name": "interview_invitation",
  "template_vars": {
    "candidate_name": "John Doe",
    "position": "Senior Python Developer",
    "interview_date": "2025-01-20",
    "interview_time": "10:00 AM"
  }
}
```

**Response:** `201 Created`

Same response format as `POST /api/notifications/send`.

---

### List Notifications

Get notifications with optional filtering.

**Endpoint:** `GET /api/notifications/`

**Query Parameters:**
- `type` (optional) - Filter by notification type
- `status` (optional) - Filter by status (pending, sent, failed)
- `priority` (optional) - Filter by priority
- `recipient` (optional) - Filter by recipient
- `skip` (optional, default: 0) - Records to skip
- `limit` (optional, default: 50) - Maximum records to return

**Response:** `200 OK`

```json
{
  "total": 100,
  "skip": 0,
  "limit": 50,
  "notifications": [
    {
      "id": "notification-1",
      "type": "email",
      "recipient": "candidate@example.com",
      "status": "sent",
      "priority": "high",
      "subject": "Interview Invitation",
      "sent_at": "2025-01-15T10:35:00Z",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

**Status Values:**
- `pending` - Waiting to be sent
- `sending` - Currently sending
- `sent` - Successfully sent
- `failed` - Failed to send
- `cancelled` - Cancelled

**Example:**
```bash
# Get all pending notifications
curl -X GET "http://localhost:8888/api/notifications/?status=pending" \
  -H "Authorization: Bearer <token>"

# Get notifications for a recipient
curl -X GET "http://localhost:8888/api/notifications/?recipient=candidate@example.com" \
  -H "Authorization: Bearer <token>"
```

---

### Get Notification

Get details of a specific notification.

**Endpoint:** `GET /api/notifications/{notification_id}`

**Path Parameters:**
- `notification_id` (required) - ID of the notification

**Response:** `200 OK`

```json
{
  "id": "notification-1",
  "type": "email",
  "recipient": "candidate@example.com",
  "status": "sent",
  "priority": "high",
  "subject": "Interview Invitation",
  "body": "You are invited for an interview...",
  "metadata": {
    "candidate_id": "candidate-123"
  },
  "sent_at": "2025-01-15T10:35:00Z",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:35:00Z"
}
```

---

### Cancel Notification

Cancel a pending notification.

**Endpoint:** `POST /api/notifications/{notification_id}/cancel`

**Path Parameters:**
- `notification_id` (required) - ID of the notification

**Response:** `200 OK`

```json
{
  "id": "notification-1",
  "status": "cancelled",
  "message": "Notification cancelled successfully"
}
```

---

## Webhook Subscriptions

### Create Webhook Subscription

Subscribe to webhook notifications for events.

**Endpoint:** `POST /api/webhooks/subscribe`

**Request Body:**
```json
{
  "url": "https://your-app.com/webhooks",
  "events": ["candidate.created", "candidate.status_changed", "notification.sent"],
  "secret": "webhook_secret_key"
}
```

**Events:**
- `candidate.created` - New candidate created
- `candidate.status_changed` - Candidate status changed
- `resume.uploaded` - Resume uploaded
- `resume.analyzed` - Resume analysis completed
- `notification.sent` - Notification sent
- `notification.failed` - Notification failed

**Response:** `201 Created`

```json
{
  "id": "webhook-sub-1",
  "url": "https://your-app.com/webhooks",
  "events": ["candidate.created", "candidate.status_changed"],
  "status": "active",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### List Webhooks

Get all webhook subscriptions.

**Endpoint:** `GET /api/webhooks`

**Response:** `200 OK`

```json
{
  "total": 5,
  "webhooks": [
    {
      "id": "webhook-sub-1",
      "url": "https://your-app.com/webhooks",
      "events": ["candidate.created"],
      "status": "active",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

### Delete Webhook

Delete a webhook subscription.

**Endpoint:** `DELETE /api/webhooks/{webhook_id}`

**Path Parameters:**
- `webhook_id` (required) - ID of the webhook subscription

**Response:** `204 No Content`

---

## Communications Endpoints

### Send Communication

Send a communication (email, SMS, etc.) to a candidate.

**Endpoint:** `POST /api/communications/send`

**Request Body:**
```json
{
  "candidate_id": "candidate-123",
  "type": "email",
  "channel": "email",
  "subject": "Follow-up: Your Application",
  "message": "Thank you for your interest...",
  "scheduled_for": null
}
```

**Response:** `201 Created`

```json
{
  "id": "comm-1",
  "candidate_id": "candidate-123",
  "type": "email",
  "channel": "email",
  "status": "sent",
  "sent_at": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### Get Communications History

Get communication history for a candidate.

**Endpoint:** `GET /api/communications/candidate/{candidate_id}`

**Path Parameters:**
- `candidate_id` (required) - ID of the candidate

**Response:** `200 OK`

```json
{
  "candidate_id": "candidate-123",
  "communications": [
    {
      "id": "comm-1",
      "type": "email",
      "channel": "email",
      "subject": "Interview Invitation",
      "status": "sent",
      "sent_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

## Email Templates Endpoints

### Create Email Template

Create a new email template.

**Endpoint:** `POST /api/email-templates`

**Request Body:**
```json
{
  "name": "interview_invitation",
  "subject": "Interview Invitation - {{position}}",
  "body_html": "<p>Dear {{candidate_name}},</p><p>You are invited for an interview for the position of {{position}}...</p>",
  "body_text": "Dear {{candidate_name}},\n\nYou are invited for an interview...",
  "variables": ["candidate_name", "position", "interview_date", "interview_time"]
}
```

**Response:** `201 Created`

```json
{
  "id": "template-1",
  "name": "interview_invitation",
  "subject": "Interview Invitation - {{position}}",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### List Email Templates

Get all email templates.

**Endpoint:** `GET /api/email-templates`

**Response:** `200 OK`

```json
{
  "total": 10,
  "templates": [
    {
      "id": "template-1",
      "name": "interview_invitation",
      "subject": "Interview Invitation - {{position}}",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

## Data Models

### NotificationStatus Enum

| Status | Description |
|--------|-------------|
| `pending` | Waiting to be sent |
| `sending` | Currently sending |
| `sent` | Successfully sent |
| `failed` | Failed to send |
| `cancelled` | Cancelled |

### NotificationPriority Enum

| Priority | Description |
|----------|-------------|
| `low` | Low priority |
| `normal` | Normal priority (default) |
| `high` | High priority |
| `urgent` | Urgent priority |

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid authentication
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Via API Gateway:
- 100 requests per second
- 10,000 requests per hour

---

## gRPC Service

The Notification Service also exposes a gRPC interface on port `50058`.

**Available RPC Methods:**
- `SendNotification` - Send notification
- `GetNotification` - Get notification details
- `ListNotifications` - List notifications with filters
- `CancelNotification` - Cancel pending notification
- `CreateWebhook` - Create webhook subscription
- `DeleteWebhook` - Delete webhook subscription

See `protos/notifications.proto` for the complete service definition.
