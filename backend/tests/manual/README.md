# Manual Verification Tests

This directory contains manual verification scripts for testing API functionality when automated tests cannot run (e.g., in isolated worktree environments).

## API Key Authentication Flow Test

**Script:** `test_api_key_auth_flow.sh`

**Purpose:** Verify that the API key authentication flow works end-to-end, including:
- API key generation
- Authentication with valid API key
- Rejection of invalid API keys
- Handling of requests without API keys

### Prerequisites

1. Backend server must be running:
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn main:app --reload
   ```

   Or using Docker:
   ```bash
   docker-compose up -d postgres redis backend
   ```

2. Database must be initialized with migrations applied

3. `curl` and `python3` must be available in PATH

### Running the Test

**Default (local development):**
```bash
./test_api_key_auth_flow.sh
```

**Custom base URL:**
```bash
BASE_URL=http://localhost:8001 ./test_api_key_auth_flow.sh
```

### Expected Results

All tests should pass with the following outcomes:

1. **Test 1: Generate API key**
   - HTTP Status: `201 Created`
   - Response includes: `id`, `key`, `key_prefix`, `name`, `scopes`, `rate_limit`, `created_at`, `message`
   - `key` field contains a 64-character hexadecimal string

2. **Test 2: Authenticate with generated API key**
   - HTTP Status: `200 OK`
   - Response includes list of API keys or successful data retrieval
   - Request includes `X-API-Key` header with the generated key

3. **Test 3: Authenticate with invalid API key**
   - HTTP Status: `401 Unauthorized` or `403 Forbidden`
   - Response includes error message indicating invalid or unauthorized API key

4. **Test 4: Request without API key header**
   - HTTP Status: Varies based on endpoint configuration
   - May return `401 Unauthorized` for protected endpoints
   - May return `200 OK` for endpoints that support optional authentication

### Troubleshooting

**Backend not running:**
```
curl: (7) Failed to connect to localhost port 8000: Connection refused
```
→ Start the backend server (see Prerequisites)

**Database not initialized:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "api_keys" does not exist
```
→ Run migrations: `cd backend && alembic upgrade head`

**Python not found:**
```
python3: command not found
```
→ Install Python 3 or use an environment with Python 3 available

### Integration Points Verified

This test verifies the following Phase 1 implementation components:

- ✅ API key generation endpoint (`/api/api-keys/generate`)
- ✅ API key authentication middleware (`APIKeyAuthMiddleware`)
- ✅ API key authentication dependency (`get_api_key`)
- ✅ API routes registration in `main.py`
- ✅ Database models and migrations
- ✅ SHA-256 key hashing
- ✅ Scope validation
- ✅ Rate limit configuration

### Related Subtasks

- **subtask-1-1:** API key authentication middleware
- **subtask-1-2:** API key authentication dependency
- **subtask-1-4:** Middlewares registered in main.py
- **subtask-1-5:** API routes registered in main.py
- **subtask-2-3:** Test API key authentication flow (this test)

---

## Rate Limiting with API Key Test

**Script:** `test_rate_limit_with_api_key.sh`

**Purpose:** Verify that rate limiting works correctly with API key authentication, including:
- API key generation with custom rate limits
- Rate limit header presence (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- 429 Too Many Requests response when rate limit exceeded
- Retry-After header on rate limit responses
- Rate limit enforcement across multiple requests

### Prerequisites

Same as API Key Authentication Flow Test (see above), plus:

1. Redis must be running and accessible (rate limiting uses Redis for tracking)
2. Rate limiting middleware must be registered in `backend/main.py`

### Running the Test

**Default (100 requests, 10/minute rate limit):**
```bash
./test_rate_limit_with_api_key.sh
```

**Custom configuration:**
```bash
# Custom number of requests
REQUEST_COUNT=50 ./test_rate_limit_with_api_key.sh

# Custom rate limit (requests per minute)
RATE_LIMIT=5 REQUEST_COUNT=20 ./test_rate_limit_with_api_key.sh

# Custom base URL
BASE_URL=http://localhost:8001 ./test_rate_limit_with_api_key.sh
```

### Expected Results

The test should demonstrate:

1. **API Key Generation**
   - HTTP Status: `201 Created`
   - API key created with specified rate limit (default: 10 requests/minute)

2. **Successful Requests (Before Rate Limit)**
   - HTTP Status: `200 OK`
   - Headers present: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
   - `X-RateLimit-Remaining` decreases with each request

3. **Rate Limit Exceeded**
   - HTTP Status: `429 Too Many Requests`
   - Headers present: `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
   - `X-RateLimit-Remaining` should be `0`
   - Error response body with detailed information

4. **Summary Statistics**
   - Shows count of successful requests (200)
   - Shows count of rate limited requests (429)
   - Shows count of errors
   - Timeline of first 20 and last 5 requests

### Example Output

```
=========================================
Rate Limiting with API Key Test
=========================================

Configuration:
  Base URL: http://localhost:8000
  Test Endpoint: http://localhost:8000/api/candidates
  Request Count: 100
  Rate Limit: 10/minute

Step 1: Generating API key with rate limit of 10/minute
---------------------------------------------------------------
✅ API key generated successfully
  API Key ID: 550e8400-e29b-41d4-a716-446655440000
  API Key: 1a2b3c4d... (truncated)

Step 2: Making 100 requests with rate limit monitoring
-------------------------------------------------------------------

Request 1/100: 200 OK | Limit: 10 | Remaining: 9
Request 2/100: 200 OK | Limit: 10 | Remaining: 8
...
Request 10/100: 200 OK | Limit: 10 | Remaining: 0

⚠️  Rate limit exceeded at request 11
  HTTP Status: 429 Too Many Requests
  Retry-After: 60 seconds
  X-RateLimit-Limit: 10
  X-RateLimit-Remaining: 0
  X-RateLimit-Reset: 1711043520

Request 11/100: 429 Rate Limited | Retry-After: 60s
...

=========================================
Test Results Summary
=========================================

Total Requests: 100
Successful (200): 10
Rate Limited (429): 90
Errors: 0

Step 3: Verification
-------------------

✅ Received successful responses (200 OK)
✅ Rate limiting enforced (429 responses received)
✅ Rate limit headers present in responses
✅ Rate limit header matches expected value (10)
✅ Retry-After header present on 429 responses

=========================================
✅ All Verifications Passed
=========================================
```

### Troubleshooting

**No 429 responses received:**
- Rate limit may be too high for the number of requests
- Requests may be spread out enough to not trigger limit
- RateLimitMiddleware may not be registered in main.py
- Redis may not be running or accessible

**Redis connection errors:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```
→ Start Redis: `docker-compose up -d redis` or `redis-server`

**Rate limit headers missing:**
- Verify RateLimitMiddleware is registered in `backend/main.py`
- Check that middleware is executing (not bypassed for the test endpoint)

### Integration Points Verified

This test verifies the following Phase 1 implementation components:

- ✅ API key generation with custom rate limits (`/api/api-keys/generate`)
- ✅ Rate limiting middleware (`RateLimitMiddleware`)
- ✅ API key authentication middleware (`APIKeyAuthMiddleware`)
- ✅ Rate limit header injection (X-RateLimit-*)
- ✅ 429 response with Retry-After header
- ✅ Redis-based rate limit tracking
- ✅ Per-API-key rate limiting
- ✅ Rate limit configuration from API key model

### Related Subtasks

- **subtask-1-1:** API key authentication middleware
- **subtask-1-2:** API key authentication dependency
- **subtask-1-4:** Middlewares registered in main.py (including RateLimitMiddleware)
- **subtask-1-5:** API routes registered in main.py
- **subtask-1-6:** Rate limiting environment variables
- **subtask-2-4:** Test rate limiting with API key (this test)
