# API Authentication

The AgentHR API uses API key-based authentication. All requests to protected endpoints must include a valid API key.

## Authentication Method

Include your API key in the `X-API-Key` HTTP header:

```bash
curl -X GET https://api.agenthr.com/api/candidates \
  -H "X-API-Key: your_api_key_here"
```

## API Keys

### Key Structure

API keys are 64-character hexadecimal strings:

```
aghr_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f
```

- **Prefix**: `aghr_` (identifies AgentHR keys)
- **Key**: 64 hexadecimal characters
- **Storage**: Only the SHA-256 hash is stored in our database

### Security Best Practices

1. **Never expose API keys** in client-side code (browsers, mobile apps)
2. **Use environment variables** to store keys
3. **Rotate keys regularly** (recommended every 90 days)
4. **Set expiration dates** for temporary access
5. **Use minimal scopes** - only request permissions you need
6. **Monitor usage** - review API usage analytics regularly
7. **Revoke compromised keys** immediately

### Example: Secure Key Storage

```bash
# .env file (never commit to version control)
AGENTHR_API_KEY=aghr_1a2b3c4d...

# Load in your application
export AGENTHR_API_KEY=$(grep AGENTHR_API_KEY .env | cut -d '=' -f2)
```

## Generating API Keys

### Via Developer Portal

1. Navigate to https://app.agenthr.com/developer/api-keys
2. Click "Create API Key"
3. Configure name, scopes, and rate limits
4. Copy the key - it won't be shown again

### Via API

```bash
curl -X POST https://api.agenthr.com/api/api-keys/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_admin_key" \
  -d '{
    "name": "Production Integration",
    "scopes": [
      "read:candidates",
      "write:candidates",
      "read:resumes"
    ],
    "rate_limit": {
      "requests_per_minute": 60,
      "requests_per_hour": 1000,
      "requests_per_day": 10000
    },
    "expires_at": "2024-12-31T23:59:59Z"
  }'
```

Response:
```json
{
  "id": "key_id_here",
  "name": "Production Integration",
  "api_key": "aghr_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f",
  "key_prefix": "aghr_1a2b",
  "scopes": ["read:candidates", "write:candidates", "read:resumes"],
  "rate_limit": {
    "requests_per_minute": 60,
    "requests_per_hour": 1000,
    "requests_per_day": 10000
  },
  "expires_at": "2024-12-31T23:59:59Z",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## API Key Scopes

Scopes provide granular control over API key permissions.

### Available Scopes

#### Candidate Operations
- `read:candidates` - List and view candidates
- `write:candidates` - Create and update candidates
- `delete:candidates` - Delete candidates

#### Resume Operations
- `read:resumes` - View resumes and parsed data
- `write:resumes` - Upload and update resumes
- `delete:resumes` - Delete resumes

#### Vacancy Operations
- `read:vacancies` - List and view job vacancies
- `write:vacancies` - Create and update vacancies
- `delete:vacancies` - Delete vacancies

#### Analytics
- `read:analytics` - Access analytics and reports

#### Webhooks
- `read:webhooks` - View webhook subscriptions
- `write:webhooks` - Create and update webhooks
- `delete:webhooks` - Delete webhooks

#### Workflows
- `read:workflows` - View workflow definitions
- `write:workflows` - Create and update workflows
- `delete:workflows` - Delete workflows

#### Plugins
- `read:plugins` - Browse plugin marketplace
- `write:plugins` - Install and configure plugins
- `delete:plugins` - Uninstall plugins

#### API Keys
- `read:api_keys` - List API keys
- `write:api_keys` - Generate and manage API keys
- `delete:api_keys` - Revoke API keys

### Scope Examples

**Read-only access:**
```json
{
  "scopes": ["read:candidates", "read:vacancies", "read:analytics"]
}
```

**Full candidate management:**
```json
{
  "scopes": ["read:candidates", "write:candidates", "delete:candidates"]
}
```

**Integration with webhooks:**
```json
{
  "scopes": [
    "read:candidates",
    "write:candidates",
    "read:webhooks",
    "write:webhooks"
  ]
}
```

## Rate Limiting

API keys have configurable rate limits to prevent abuse and ensure fair usage.

### Rate Limit Headers

Every API response includes rate limit information:

```
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 45
X-RateLimit-Reset-Minute: 1698765432
X-RateLimit-Limit-Hour: 1000
X-RateLimit-Remaining-Hour: 920
X-RateLimit-Reset-Hour: 1698768000
X-RateLimit-Limit-Day: 10000
X-RateLimit-Remaining-Day: 9500
X-RateLimit-Reset-Day: 1698825600
```

### Handling Rate Limits

When you exceed a rate limit, you'll receive a 429 status:

```json
{
  "detail": "Rate limit exceeded: 60 requests per minute",
  "retry-after": 30
}
```

Implement exponential backoff:

```python
import time
import requests

def make_request_with_retry(url, api_key, max_retries=5):
    for attempt in range(max_retries):
        response = requests.get(
            url,
            headers={"X-API-Key": api_key}
        )

        if response.status_code != 429:
            return response

        # Exponential backoff
        retry_after = int(response.headers.get("retry-after", 2 ** attempt))
        time.sleep(retry_after)

    raise Exception("Max retries exceeded")
```

## Managing API Keys

### List API Keys

```bash
curl -X GET https://api.agenthr.com/api/api-keys/ \
  -H "X-API-Key: your_admin_key"
```

### Revoke an API Key

```bash
curl -X POST https://api.agenthr.com/api/api-keys/{key_id}/revoke \
  -H "X-API-Key: your_admin_key"
```

### Get API Key Usage

```bash
curl -X GET https://api.agenthr.com/api/api-keys/{key_id} \
  -H "X-API-Key: your_admin_key"
```

Response includes usage statistics:
```json
{
  "id": "key_id",
  "name": "Production Integration",
  "last_used_at": "2024-01-15T14:30:00Z",
  "usage_stats": {
    "total_requests": 15420,
    "requests_today": 342,
    "success_rate": 99.2,
    "avg_response_time_ms": 120
  }
}
```

## Security Features

### Key Hashing

API keys are hashed using SHA-256 before storage. The raw key is never persisted.

### Expiration

Set expiration dates for temporary access:
```json
{
  "expires_at": "2024-12-31T23:59:59Z"
}
```

Expired keys return 401 Unauthorized:
```json
{
  "detail": "API key has expired",
  "error_code": "KEY_EXPIRED"
}
```

### Last Used Tracking

Track key activity via `last_used_at` timestamp. Keys unused for 180+ days should be reviewed and potentially revoked.

### IP Whitelisting (Coming Soon)

Future versions will support IP-based restrictions:
```json
{
  "allowed_ips": ["192.168.1.0/24", "10.0.0.1"]
}
```

## Troubleshooting

### Common Errors

**401 Unauthorized - Invalid API Key**
```json
{
  "detail": "Invalid API key",
  "error_code": "INVALID_API_KEY"
}
```
Solution: Verify your API key is correct and active.

**403 Forbidden - Insufficient Scopes**
```json
{
  "detail": "Insufficient permissions for this endpoint",
  "error_code": "INSUFFICIENT_SCOPES",
  "required_scopes": ["write:candidates"]
}
```
Solution: Create a new API key with the required scopes.

**429 Too Many Requests**
```json
{
  "detail": "Rate limit exceeded",
  "retry-after": 30
}
```
Solution: Implement retry logic with exponential backoff.

## gRPC Authentication

For gRPC API access, include the API key in metadata:

```python
import grpc

metadata = [
    ('x-api-key', 'your_api_key_here')
]
response = stub.ListCandidates(request, metadata=metadata)
```

## SDK Authentication

### Python SDK

```python
from agenthr import Client

client = Client(api_key="your_api_key_here")
candidates = client.candidates.list()
```

### JavaScript SDK

```javascript
const { AgentHRClient } = require('@agenthr/sdk');

const client = new AgentHRClient({
  apiKey: 'your_api_key_here'
});

const candidates = await client.candidates.list();
```

## Best Practices Summary

1. **Environment Variables** - Store keys in environment variables
2. **Minimal Scopes** - Request only necessary permissions
3. **Regular Rotation** - Rotate keys every 90 days
4. **Monitoring** - Review usage analytics regularly
5. **Expiration** - Set expiration dates for temporary access
6. **Revocation** - Revoke unused or compromised keys immediately
7. **Never Commit** - Never add keys to version control
8. **Server-Side Only** - Use API keys only on servers, not in clients

For more information, see:
- [API Overview](./overview.md)
- [Endpoints Reference](./endpoints.md)
- [Rate Limiting Guide](../guides/rate-limiting.md)
