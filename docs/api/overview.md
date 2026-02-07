# AgentHR API Overview

Welcome to the AgentHR API documentation. This comprehensive API enables you to integrate AgentHR's AI-powered recruitment platform into your applications, build custom workflows, and extend functionality through plugins and webhooks.

## Base URL

```
https://api.agenthr.com
```

For development and testing:
```
http://localhost:8000
```

## API Versions

The current API version is **v1**. All endpoints are prefixed with `/api/`.

## Getting Started

### 1. Create an API Key

First, generate an API key through the Developer Portal or API:

```bash
curl -X POST https://api.agenthr.com/api/api-keys/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "My Integration",
    "scopes": ["read:candidates", "write:candidates"],
    "rate_limit": {
      "requests_per_minute": 60,
      "requests_per_hour": 1000
    }
  }'
```

**Important:** Save the returned API key securely. You won't be able to see it again.

### 2. Authenticate Your Requests

Include your API key in the `X-API-Key` header:

```bash
curl -X GET https://api.agenthr.com/api/candidates \
  -H "X-API-Key: your_api_key_here"
```

### 3. Make Your First Request

List all candidates:

```bash
curl -X GET https://api.agenthr.com/api/candidates?limit=10 \
  -H "X-API-Key: your_api_key_here"
```

## Response Format

All API responses return JSON:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Pagination

List endpoints support pagination via `skip` and `limit` parameters:

```bash
curl -X GET "https://api.agenthr.com/api/candidates?skip=0&limit=20"
```

Response includes pagination metadata:
```json
{
  "items": [...],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

## Error Handling

The API uses standard HTTP status codes:

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden (insufficient scopes) |
| 404 | Not Found |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

Error response format:
```json
{
  "detail": "Invalid API key",
  "error_code": "INVALID_API_KEY"
}
```

## Rate Limiting

API requests are rate limited based on your API key configuration. Check your headers:

```
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 45
X-RateLimit-Limit-Hour: 1000
X-RateLimit-Remaining-Hour: 920
```

When rate limited:
```json
{
  "detail": "Rate limit exceeded",
  "retry-after": 30
}
```

## API Scopes

API keys use scopes for granular permission control:

| Category | Scopes |
|----------|--------|
| Candidates | `read:candidates`, `write:candidates`, `delete:candidates` |
| Resumes | `read:resumes`, `write:resumes`, `delete:resumes` |
| Vacancies | `read:vacancies`, `write:vacancies`, `delete:vacancies` |
| Analytics | `read:analytics` |
| Webhooks | `read:webhooks`, `write:webhooks`, `delete:webhooks` |
| Workflows | `read:workflows`, `write:workflows`, `delete:workflows` |
| Plugins | `read:plugins`, `write:plugins`, `delete:plugins` |
| API Keys | `read:api_keys`, `write:api_keys`, `delete:api_keys` |

## Interactive Documentation

Explore and test the API interactively using Swagger UI:

```
https://api.agenthr.com/docs
```

Or access the OpenAPI specification:

```
https://api.agenthr.com/openapi.json
```

## SDKs

Official SDKs are available for:

- **Python** - `pip install agenthr`
- **JavaScript/TypeScript** - `npm install @agenthr/sdk`
- **Java** - Available via Maven Central
- **Go** - `go get github.com/agenthr/go-sdk`

## Support

- Documentation: https://docs.agenthr.com
- GitHub Issues: https://github.com/agenthr/agenthr/issues
- Email Support: api-support@agenthr.com
- Community Forum: https://community.agenthr.com

## Changelog

Stay updated with API changes:

- **v1.0.0** (2024-01-15) - Initial API release
- **v1.1.0** (2024-02-01) - Added webhooks and workflows
- **v1.2.0** (2024-02-15) - Added plugin marketplace

## Next Steps

- [Authentication Guide](./authentication.md) - Learn about API key authentication
- [Endpoints Reference](./endpoints.md) - Browse all available endpoints
- [Webhooks Guide](./webhooks.md) - Set up real-time event notifications
- [Examples](../examples/) - View code examples and tutorials
